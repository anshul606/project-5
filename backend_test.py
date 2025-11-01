import requests
import sys
import json
from datetime import datetime

class TaskWeaverAPITester:
    def __init__(self, base_url="https://taskweaver-8.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            
            if success:
                self.log_test(name, True)
                try:
                    return True, response.json()
                except:
                    return True, {}
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                
                self.log_test(name, False, error_msg)
                return False, {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_auth_register(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "email": f"test_user_{timestamp}@example.com",
            "name": f"Test User {timestamp}",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            return True, test_user
        return False, {}

    def test_auth_login(self, user_data):
        """Test user login"""
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        
        if success and 'token' in response:
            self.token = response['token']
            return True
        return False

    def test_auth_me(self):
        """Test get current user"""
        success, _ = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_board(self):
        """Test board creation"""
        board_data = {
            "title": "Test Board",
            "description": "A test board for API testing",
            "background": "#e3f2fd"
        }
        
        success, response = self.run_test(
            "Create Board",
            "POST",
            "boards",
            200,
            data=board_data
        )
        
        return response.get('id') if success else None

    def test_get_boards(self):
        """Test get user boards"""
        success, response = self.run_test(
            "Get Boards",
            "GET",
            "boards",
            200
        )
        return success, response

    def test_get_board(self, board_id):
        """Test get specific board"""
        success, _ = self.run_test(
            "Get Board Details",
            "GET",
            f"boards/{board_id}",
            200
        )
        return success

    def test_create_list(self, board_id):
        """Test list creation"""
        list_data = {
            "title": "Test List",
            "board_id": board_id,
            "position": 0
        }
        
        success, response = self.run_test(
            "Create List",
            "POST",
            "lists",
            200,
            data=list_data
        )
        
        return response.get('id') if success else None

    def test_get_lists(self, board_id):
        """Test get board lists"""
        success, response = self.run_test(
            "Get Lists",
            "GET",
            f"lists/{board_id}",
            200
        )
        return success, response

    def test_create_card(self, list_id, board_id):
        """Test card creation"""
        card_data = {
            "title": "Test Card",
            "description": "A test card for API testing",
            "list_id": list_id,
            "board_id": board_id,
            "position": 0,
            "priority": "medium"
        }
        
        success, response = self.run_test(
            "Create Card",
            "POST",
            "cards",
            200,
            data=card_data
        )
        
        return response.get('id') if success else None

    def test_get_cards(self, board_id):
        """Test get board cards"""
        success, response = self.run_test(
            "Get Cards",
            "GET",
            f"cards/{board_id}",
            200
        )
        return success, response

    def test_update_card(self, card_id):
        """Test card update"""
        update_data = {
            "title": "Updated Test Card",
            "description": "Updated description",
            "priority": "high"
        }
        
        success, _ = self.run_test(
            "Update Card",
            "PUT",
            f"cards/{card_id}",
            200,
            data=update_data
        )
        return success

    def test_get_inbox(self):
        """Test unified inbox"""
        success, response = self.run_test(
            "Get Inbox",
            "GET",
            "inbox",
            200
        )
        return success, response

    def test_ai_extract_tasks(self):
        """Test AI task extraction"""
        extract_data = {
            "text": "I need to prepare for the meeting tomorrow at 2 PM. Also, don't forget to send the quarterly report to the team by Friday. Call the client about the project update."
        }
        
        success, response = self.run_test(
            "AI Task Extraction",
            "POST",
            "ai/extract-tasks",
            200,
            data=extract_data
        )
        
        if success:
            tasks = response.get('tasks', [])
            if len(tasks) > 0:
                print(f"   ✅ Extracted {len(tasks)} tasks")
                for i, task in enumerate(tasks):
                    print(f"      Task {i+1}: {task.get('title', 'No title')}")
                return True
            else:
                self.log_test("AI Task Extraction - Task Count", False, "No tasks extracted")
                return False
        return False

    def test_delete_card(self, card_id):
        """Test card deletion"""
        success, _ = self.run_test(
            "Delete Card",
            "DELETE",
            f"cards/{card_id}",
            200
        )
        return success

    def test_delete_list(self, list_id):
        """Test list deletion"""
        success, _ = self.run_test(
            "Delete List",
            "DELETE",
            f"lists/{list_id}",
            200
        )
        return success

    def test_delete_board(self, board_id):
        """Test board deletion"""
        success, _ = self.run_test(
            "Delete Board",
            "DELETE",
            f"boards/{board_id}",
            200
        )
        return success

def main():
    print("🚀 Starting TaskWeaver API Tests")
    print("=" * 50)
    
    tester = TaskWeaverAPITester()
    
    # Test Authentication Flow
    print("\n📝 Testing Authentication...")
    success, user_data = tester.test_auth_register()
    if not success:
        print("❌ Registration failed, stopping tests")
        return 1
    
    if not tester.test_auth_login(user_data):
        print("❌ Login failed, stopping tests")
        return 1
    
    if not tester.test_auth_me():
        print("❌ Get current user failed")
        return 1
    
    # Test Board Management
    print("\n📋 Testing Board Management...")
    board_id = tester.test_create_board()
    if not board_id:
        print("❌ Board creation failed, stopping tests")
        return 1
    
    if not tester.test_get_board(board_id):
        print("❌ Get board failed")
        return 1
    
    success, boards = tester.test_get_boards()
    if not success:
        print("❌ Get boards failed")
        return 1
    
    # Test List Management
    print("\n📝 Testing List Management...")
    list_id = tester.test_create_list(board_id)
    if not list_id:
        print("❌ List creation failed, stopping tests")
        return 1
    
    success, lists = tester.test_get_lists(board_id)
    if not success:
        print("❌ Get lists failed")
        return 1
    
    # Test Card Management
    print("\n🃏 Testing Card Management...")
    card_id = tester.test_create_card(list_id, board_id)
    if not card_id:
        print("❌ Card creation failed, stopping tests")
        return 1
    
    success, cards = tester.test_get_cards(board_id)
    if not success:
        print("❌ Get cards failed")
        return 1
    
    if not tester.test_update_card(card_id):
        print("❌ Update card failed")
        return 1
    
    # Test Inbox
    print("\n📥 Testing Inbox...")
    success, inbox_cards = tester.test_get_inbox()
    if not success:
        print("❌ Get inbox failed")
        return 1
    
    # Test AI Integration
    print("\n🤖 Testing AI Integration...")
    if not tester.test_ai_extract_tasks():
        print("❌ AI task extraction failed")
    
    # Cleanup Tests
    print("\n🗑️ Testing Cleanup Operations...")
    tester.test_delete_card(card_id)
    tester.test_delete_list(list_id)
    tester.test_delete_board(board_id)
    
    # Print Results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())