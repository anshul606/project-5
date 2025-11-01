import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { ArrowLeft, Plus, Trash2, Edit3 } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function BoardView() {
  const { boardId } = useParams();
  const navigate = useNavigate();
  const [board, setBoard] = useState(null);
  const [lists, setLists] = useState([]);
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newListTitle, setNewListTitle] = useState("");
  const [selectedCard, setSelectedCard] = useState(null);
  const [showCardDialog, setShowCardDialog] = useState(false);
  const [newCardData, setNewCardData] = useState({ title: "", listId: "" });
  const [showNewCardDialog, setShowNewCardDialog] = useState(false);

  useEffect(() => {
    fetchBoardData();
  }, [boardId]);

  const fetchBoardData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [boardRes, listsRes, cardsRes] = await Promise.all([
        axios.get(`${API}/boards/${boardId}`, { headers }),
        axios.get(`${API}/lists/${boardId}`, { headers }),
        axios.get(`${API}/cards/${boardId}`, { headers })
      ]);
      
      setBoard(boardRes.data);
      setLists(listsRes.data);
      setCards(cardsRes.data);
    } catch (error) {
      toast.error("Failed to load board data");
    } finally {
      setLoading(false);
    }
  };

  const createList = async () => {
    if (!newListTitle.trim()) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/lists`, {
        title: newListTitle,
        board_id: boardId,
        position: lists.length
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      setNewListTitle("");
      fetchBoardData();
      toast.success("List created!");
    } catch (error) {
      toast.error("Failed to create list");
    }
  };

  const createCard = async (listId) => {
    setNewCardData({ title: "", listId });
    setShowNewCardDialog(true);
  };
  
  const handleCreateCard = async () => {
    if (!newCardData.title.trim()) {
      toast.error("Card title is required");
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const listCards = cards.filter(c => c.list_id === newCardData.listId);
      await axios.post(`${API}/cards`, {
        title: newCardData.title,
        list_id: newCardData.listId,
        board_id: boardId,
        position: listCards.length
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      fetchBoardData();
      setShowNewCardDialog(false);
      setNewCardData({ title: "", listId: "" });
      toast.success("Card created!");
    } catch (error) {
      toast.error("Failed to create card");
    }
  };

  const deleteCard = async (cardId) => {
    if (!window.confirm("Delete this card?")) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/cards/${cardId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchBoardData();
      setShowCardDialog(false);
      toast.success("Card deleted");
    } catch (error) {
      toast.error("Failed to delete card");
    }
  };

  const updateCard = async (cardId, updates) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/cards/${cardId}`, updates, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchBoardData();
      toast.success("Card updated");
    } catch (error) {
      toast.error("Failed to update card");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading board...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: board?.background || '#e3f2fd' }}>
      {/* Header */}
      <header className="backdrop-blur-md bg-white/70 shadow-sm p-4" data-testid="board-header">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              data-testid="back-to-dashboard"
              onClick={() => navigate('/dashboard')}
              style={{ color: '#0277bd' }}
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-2xl font-bold" style={{ color: '#01579b' }}>{board?.title}</h1>
              {board?.description && <p className="text-sm" style={{ color: '#0277bd' }}>{board.description}</p>}
            </div>
          </div>
        </div>
      </header>

      {/* Board Content */}
      <div className="p-6 overflow-x-auto">
        <div className="flex gap-6 min-h-[calc(100vh-200px)]" data-testid="board-lists">
          {lists.map((list) => {
            const listCards = cards.filter(c => c.list_id === list.id);
            return (
              <div
                key={list.id}
                data-testid={`list-${list.id}`}
                className="flex-shrink-0 w-80 backdrop-blur-md bg-white/80 rounded-lg p-4 shadow-lg"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-lg" style={{ color: '#01579b' }}>{list.title}</h3>
                  <span className="text-sm px-2 py-1 rounded" style={{ background: '#b3e5fc', color: '#01579b' }}>
                    {listCards.length}
                  </span>
                </div>
                
                <div className="space-y-3 mb-3" data-testid={`list-cards-${list.id}`}>
                  {listCards.map((card) => (
                    <Card
                      key={card.id}
                      data-testid={`card-${card.id}`}
                      className="p-3 cursor-pointer card-hover border-2"
                      style={{ borderColor: '#b3e5fc' }}
                      onClick={() => {
                        setSelectedCard(card);
                        setShowCardDialog(true);
                      }}
                    >
                      <h4 className="font-medium mb-2" style={{ color: '#01579b' }}>{card.title}</h4>
                      {card.description && (
                        <p className="text-sm line-clamp-2" style={{ color: '#0277bd' }}>{card.description}</p>
                      )}
                      {card.labels && card.labels.length > 0 && (
                        <div className="flex gap-1 mt-2 flex-wrap">
                          {card.labels.map((label, idx) => (
                            <span key={idx} className="text-xs px-2 py-1 rounded" style={{ background: '#81d4fa' }}>
                              {label}
                            </span>
                          ))}
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
                
                <Button
                  variant="outline"
                  data-testid={`add-card-${list.id}`}
                  className="w-full border-2"
                  style={{ borderColor: '#0288d1', color: '#0277bd' }}
                  onClick={() => createCard(list.id)}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Add Card
                </Button>
              </div>
            );
          })}
          
          {/* New List */}
          <div className="flex-shrink-0 w-80 backdrop-blur-md bg-white/60 rounded-lg p-4">
            <Input
              placeholder="Enter list title..."
              data-testid="new-list-input"
              value={newListTitle}
              onChange={(e) => setNewListTitle(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && createList()}
              className="mb-2 border-2"
            />
            <Button
              onClick={createList}
              data-testid="create-list-button"
              className="w-full text-white"
              style={{ background: '#0288d1' }}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add List
            </Button>
          </div>
        </div>
      </div>

      {/* Card Detail Dialog */}
      <Dialog open={showCardDialog} onOpenChange={setShowCardDialog}>
        <DialogContent className="max-w-2xl" data-testid="card-detail-dialog">
          <DialogHeader>
            <DialogTitle className="text-2xl" style={{ color: '#01579b' }}>{selectedCard?.title}</DialogTitle>
          </DialogHeader>
          {selectedCard && (
            <div className="space-y-4 mt-4">
              <div>
                <Label>Description</Label>
                <Textarea
                  data-testid="card-description-input"
                  value={selectedCard.description || ""}
                  onChange={(e) => setSelectedCard({ ...selectedCard, description: e.target.value })}
                  onBlur={() => updateCard(selectedCard.id, { description: selectedCard.description })}
                  placeholder="Add a description..."
                  rows={4}
                  className="mt-1"
                />
              </div>
              
              <div className="flex gap-2">
                <Button
                  variant="destructive"
                  data-testid="delete-card-button"
                  onClick={() => deleteCard(selectedCard.id)}
                >
                  <Trash2 className="w-4 h-4 mr-2" />
                  Delete Card
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
      
      {/* New Card Dialog */}
      <Dialog open={showNewCardDialog} onOpenChange={setShowNewCardDialog}>
        <DialogContent data-testid="new-card-dialog">
          <DialogHeader>
            <DialogTitle>Create New Card</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="card-title">Card Title</Label>
              <Input
                id="card-title"
                data-testid="new-card-title-input"
                placeholder="Enter card title..."
                value={newCardData.title}
                onChange={(e) => setNewCardData({ ...newCardData, title: e.target.value })}
                onKeyPress={(e) => e.key === 'Enter' && handleCreateCard()}
              />
            </div>
            <Button
              onClick={handleCreateCard}
              data-testid="submit-new-card"
              className="w-full text-white"
              style={{ background: '#0288d1' }}
            >
              Create Card
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
