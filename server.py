from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List as ListType, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION_HOURS', '168'))

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    token: str
    user: User

class Board(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    owner_id: str
    members: ListType[str] = Field(default_factory=list)
    background: Optional[str] = "#e0f7fa"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BoardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    background: Optional[str] = "#e0f7fa"

class List(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    board_id: str
    position: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ListCreate(BaseModel):
    title: str
    board_id: str
    position: int

class Card(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    list_id: str
    board_id: str
    position: int
    assigned_to: Optional[ListType[str]] = Field(default_factory=list)
    labels: ListType[str] = Field(default_factory=list)
    due_date: Optional[datetime] = None
    priority: Optional[str] = "medium"
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    mirrored_to: ListType[str] = Field(default_factory=list)  # Board IDs where this card is mirrored
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CardCreate(BaseModel):
    title: str
    description: Optional[str] = None
    list_id: str
    board_id: str
    position: int
    assigned_to: Optional[ListType[str]] = Field(default_factory=list)
    labels: Optional[ListType[str]] = Field(default_factory=list)
    due_date: Optional[datetime] = None
    priority: Optional[str] = "medium"
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)

class CardUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    list_id: Optional[str] = None
    position: Optional[int] = None
    assigned_to: Optional[ListType[str]] = None
    labels: Optional[ListType[str]] = None
    due_date: Optional[datetime] = None
    priority: Optional[str] = None
    custom_fields: Optional[Dict[str, Any]] = None

class Activity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    board_id: str
    card_id: Optional[str] = None
    action: str  # created, updated, moved, deleted, etc.
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AIExtractRequest(BaseModel):
    text: str
    board_id: Optional[str] = None

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    token = credentials.credentials
    user_id = decode_token(token)
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    return User(**user_doc)

# Auth Routes
@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    user = User(email=user_data.email, name=user_data.name)
    user_dict = user.model_dump()
    user_dict['password'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    token = create_token(user.id)
    return TokenResponse(token=token, user=user)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc or not verify_password(credentials.password, user_doc['password']):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    user = User(**{k: v for k, v in user_doc.items() if k != 'password'})
    token = create_token(user.id)
    return TokenResponse(token=token, user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Board Routes
@api_router.post("/boards", response_model=Board)
async def create_board(board_data: BoardCreate, current_user: User = Depends(get_current_user)):
    board = Board(**board_data.model_dump(), owner_id=current_user.id, members=[current_user.id])
    board_dict = board.model_dump()
    board_dict['created_at'] = board_dict['created_at'].isoformat()
    board_dict['updated_at'] = board_dict['updated_at'].isoformat()
    
    await db.boards.insert_one(board_dict)
    return board

@api_router.get("/boards", response_model=ListType[Board])
async def get_boards(current_user: User = Depends(get_current_user)):
    boards = await db.boards.find({"members": current_user.id}, {"_id": 0}).to_list(1000)
    for board in boards:
        if isinstance(board.get('created_at'), str):
            board['created_at'] = datetime.fromisoformat(board['created_at'])
        if isinstance(board.get('updated_at'), str):
            board['updated_at'] = datetime.fromisoformat(board['updated_at'])
    return boards

@api_router.get("/boards/{board_id}", response_model=Board)
async def get_board(board_id: str, current_user: User = Depends(get_current_user)):
    board = await db.boards.find_one({"id": board_id, "members": current_user.id}, {"_id": 0})
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    if isinstance(board.get('created_at'), str):
        board['created_at'] = datetime.fromisoformat(board['created_at'])
    if isinstance(board.get('updated_at'), str):
        board['updated_at'] = datetime.fromisoformat(board['updated_at'])
    return Board(**board)

@api_router.delete("/boards/{board_id}")
async def delete_board(board_id: str, current_user: User = Depends(get_current_user)):
    board = await db.boards.find_one({"id": board_id, "owner_id": current_user.id})
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    
    await db.boards.delete_one({"id": board_id})
    await db.lists.delete_many({"board_id": board_id})
    await db.cards.delete_many({"board_id": board_id})
    return {"message": "Board deleted successfully"}

# List Routes
@api_router.post("/lists", response_model=List)
async def create_list(list_data: ListCreate, current_user: User = Depends(get_current_user)):
    board = await db.boards.find_one({"id": list_data.board_id, "members": current_user.id})
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    
    list_obj = List(**list_data.model_dump())
    list_dict = list_obj.model_dump()
    list_dict['created_at'] = list_dict['created_at'].isoformat()
    
    await db.lists.insert_one(list_dict)
    return list_obj

@api_router.get("/lists/{board_id}", response_model=ListType[List])
async def get_lists(board_id: str, current_user: User = Depends(get_current_user)):
    board = await db.boards.find_one({"id": board_id, "members": current_user.id})
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    
    lists = await db.lists.find({"board_id": board_id}, {"_id": 0}).sort("position", 1).to_list(1000)
    for list_item in lists:
        if isinstance(list_item.get('created_at'), str):
            list_item['created_at'] = datetime.fromisoformat(list_item['created_at'])
    return lists

@api_router.delete("/lists/{list_id}")
async def delete_list(list_id: str, current_user: User = Depends(get_current_user)):
    list_obj = await db.lists.find_one({"id": list_id})
    if not list_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")
    
    await db.lists.delete_one({"id": list_id})
    await db.cards.delete_many({"list_id": list_id})
    return {"message": "List deleted successfully"}

# Card Routes
@api_router.post("/cards", response_model=Card)
async def create_card(card_data: CardCreate, current_user: User = Depends(get_current_user)):
    board = await db.boards.find_one({"id": card_data.board_id, "members": current_user.id})
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    
    card = Card(**card_data.model_dump())
    card_dict = card.model_dump()
    card_dict['created_at'] = card_dict['created_at'].isoformat()
    card_dict['updated_at'] = card_dict['updated_at'].isoformat()
    if card_dict.get('due_date'):
        card_dict['due_date'] = card_dict['due_date'].isoformat()
    
    await db.cards.insert_one(card_dict)
    return card

@api_router.get("/cards/{board_id}", response_model=ListType[Card])
async def get_cards(board_id: str, current_user: User = Depends(get_current_user)):
    board = await db.boards.find_one({"id": board_id, "members": current_user.id})
    if not board:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Board not found")
    
    cards = await db.cards.find({"board_id": board_id}, {"_id": 0}).to_list(10000)
    for card in cards:
        if isinstance(card.get('created_at'), str):
            card['created_at'] = datetime.fromisoformat(card['created_at'])
        if isinstance(card.get('updated_at'), str):
            card['updated_at'] = datetime.fromisoformat(card['updated_at'])
        if card.get('due_date') and isinstance(card['due_date'], str):
            card['due_date'] = datetime.fromisoformat(card['due_date'])
    return cards

@api_router.put("/cards/{card_id}", response_model=Card)
async def update_card(card_id: str, card_update: CardUpdate, current_user: User = Depends(get_current_user)):
    card = await db.cards.find_one({"id": card_id}, {"_id": 0})
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    
    update_data = {k: v for k, v in card_update.model_dump(exclude_unset=True).items() if v is not None}
    if update_data:
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        if 'due_date' in update_data and update_data['due_date']:
            update_data['due_date'] = update_data['due_date'].isoformat()
        
        await db.cards.update_one({"id": card_id}, {"$set": update_data})
    
    updated_card = await db.cards.find_one({"id": card_id}, {"_id": 0})
    if isinstance(updated_card.get('created_at'), str):
        updated_card['created_at'] = datetime.fromisoformat(updated_card['created_at'])
    if isinstance(updated_card.get('updated_at'), str):
        updated_card['updated_at'] = datetime.fromisoformat(updated_card['updated_at'])
    if updated_card.get('due_date') and isinstance(updated_card['due_date'], str):
        updated_card['due_date'] = datetime.fromisoformat(updated_card['due_date'])
    return Card(**updated_card)

@api_router.delete("/cards/{card_id}")
async def delete_card(card_id: str, current_user: User = Depends(get_current_user)):
    card = await db.cards.find_one({"id": card_id})
    if not card:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    
    await db.cards.delete_one({"id": card_id})
    return {"message": "Card deleted successfully"}

# Inbox - Get all user's cards across boards
@api_router.get("/inbox", response_model=ListType[Card])
async def get_inbox(current_user: User = Depends(get_current_user)):
    boards = await db.boards.find({"members": current_user.id}, {"_id": 0}).to_list(1000)
    board_ids = [b['id'] for b in boards]
    
    cards = await db.cards.find({"board_id": {"$in": board_ids}}, {"_id": 0}).sort("created_at", -1).to_list(10000)
    for card in cards:
        if isinstance(card.get('created_at'), str):
            card['created_at'] = datetime.fromisoformat(card['created_at'])
        if isinstance(card.get('updated_at'), str):
            card['updated_at'] = datetime.fromisoformat(card['updated_at'])
        if card.get('due_date') and isinstance(card['due_date'], str):
            card['due_date'] = datetime.fromisoformat(card['due_date'])
    return cards

# AI Task Extraction
@api_router.post("/ai/extract-tasks")
async def extract_tasks(request: AIExtractRequest, current_user: User = Depends(get_current_user)):
    try:
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        chat = LlmChat(
            api_key=api_key,
            session_id=f"extract_{current_user.id}",
            system_message="You are a task extraction assistant. Extract actionable tasks from the given text. Return a JSON array of tasks with 'title', 'description', and 'priority' (low/medium/high) fields. Be concise and clear."
        ).with_model("openai", "gpt-4o-mini")
        
        user_message = UserMessage(
            text=f"Extract tasks from this text and return ONLY a valid JSON array:\n\n{request.text}\n\nFormat: [{{'title': '...', 'description': '...', 'priority': 'medium'}}]"
        )
        
        response = await chat.send_message(user_message)
        
        # Parse response
        import json
        response_text = response.strip()
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1])
        
        tasks = json.loads(response_text)
        
        return {"tasks": tasks, "raw_response": response}
    except Exception as e:
        logging.error(f"AI extraction error: {str(e)}")
        return {"tasks": [{"title": "Error extracting tasks", "description": str(e), "priority": "low"}], "error": str(e)}

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()