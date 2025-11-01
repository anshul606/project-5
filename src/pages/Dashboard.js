import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Plus, LogOut, Inbox as InboxIcon, Sparkles } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard({ user, onLogout }) {
  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showNewBoard, setShowNewBoard] = useState(false);
  const [newBoardData, setNewBoardData] = useState({ title: "", description: "" });
  const navigate = useNavigate();

  useEffect(() => {
    fetchBoards();
  }, []);

  const fetchBoards = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/boards`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBoards(response.data);
    } catch (error) {
      toast.error("Failed to load boards");
    } finally {
      setLoading(false);
    }
  };

  const createBoard = async () => {
    if (!newBoardData.title.trim()) {
      toast.error("Board title is required");
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/boards`, newBoardData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Board created successfully!");
      setShowNewBoard(false);
      setNewBoardData({ title: "", description: "" });
      fetchBoards();
    } catch (error) {
      toast.error("Failed to create board");
    }
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #e3f2fd 0%, #f0f4f8 100%)' }}>
      {/* Header */}
      <header className="backdrop-blur-md bg-white/70 shadow-sm sticky top-0 z-50" data-testid="dashboard-header">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Sparkles className="w-8 h-8" style={{ color: '#0288d1' }} />
            <h1 className="text-2xl font-bold" style={{ color: '#0277bd' }}>TaskWeaver</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm" style={{ color: '#0277bd' }}>Welcome, {user?.name}</span>
            <Button
              variant="outline"
              data-testid="inbox-button"
              onClick={() => navigate('/inbox')}
              className="border-2"
              style={{ borderColor: '#0288d1', color: '#0277bd' }}
            >
              <InboxIcon className="w-4 h-4 mr-2" />
              Inbox
            </Button>
            <Button
              variant="outline"
              data-testid="logout-button"
              onClick={onLogout}
              className="border-2"
              style={{ borderColor: '#d32f2f', color: '#d32f2f' }}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-3xl font-bold mb-2" style={{ color: '#01579b' }}>Your Boards</h2>
            <p className="text-base" style={{ color: '#0277bd' }}>Organize your tasks and projects</p>
          </div>
          <Dialog open={showNewBoard} onOpenChange={setShowNewBoard}>
            <DialogTrigger asChild>
              <Button 
                data-testid="create-board-button"
                className="text-white font-medium"
                style={{ background: '#0288d1' }}
              >
                <Plus className="w-5 h-5 mr-2" />
                New Board
              </Button>
            </DialogTrigger>
            <DialogContent data-testid="new-board-dialog">
              <DialogHeader>
                <DialogTitle>Create New Board</DialogTitle>
                <DialogDescription>Start organizing your tasks with a new board</DialogDescription>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div className="space-y-2">
                  <Label htmlFor="board-title">Board Title</Label>
                  <Input
                    id="board-title"
                    data-testid="board-title-input"
                    placeholder="e.g., Marketing Campaign"
                    value={newBoardData.title}
                    onChange={(e) => setNewBoardData({ ...newBoardData, title: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="board-description">Description (Optional)</Label>
                  <Input
                    id="board-description"
                    data-testid="board-description-input"
                    placeholder="What's this board about?"
                    value={newBoardData.description}
                    onChange={(e) => setNewBoardData({ ...newBoardData, description: e.target.value })}
                  />
                </div>
                <Button 
                  onClick={createBoard}
                  data-testid="submit-new-board"
                  className="w-full text-white"
                  style={{ background: '#0288d1' }}
                >
                  Create Board
                </Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Boards Grid */}
        {loading ? (
          <div className="text-center py-12" data-testid="loading-boards">
            <p style={{ color: '#0277bd' }}>Loading boards...</p>
          </div>
        ) : boards.length === 0 ? (
          <div className="text-center py-12" data-testid="no-boards-message">
            <Sparkles className="w-16 h-16 mx-auto mb-4" style={{ color: '#0288d1', opacity: 0.5 }} />
            <p className="text-lg mb-4" style={{ color: '#0277bd' }}>No boards yet. Create your first board to get started!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="boards-grid">
            {boards.map((board, index) => (
              <Card
                key={board.id}
                data-testid={`board-card-${board.id}`}
                className="card-hover cursor-pointer slide-in shadow-lg border-2"
                style={{ 
                  animationDelay: `${index * 0.1}s`,
                  borderColor: '#b3e5fc',
                  background: board.background || '#ffffff'
                }}
                onClick={() => navigate(`/board/${board.id}`)}
              >
                <CardHeader>
                  <CardTitle className="text-xl" style={{ color: '#01579b' }}>{board.title}</CardTitle>
                  {board.description && (
                    <CardDescription className="line-clamp-2">{board.description}</CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-sm" style={{ color: '#0277bd' }}>
                    <span>{board.members?.length || 0} member(s)</span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
