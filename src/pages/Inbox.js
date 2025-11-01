import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { ArrowLeft, Sparkles, Plus } from "lucide-react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Inbox() {
  const navigate = useNavigate();
  const [cards, setCards] = useState([]);
  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAIConverter, setShowAIConverter] = useState(false);
  const [inputText, setInputText] = useState("");
  const [extractedTasks, setExtractedTasks] = useState([]);
  const [selectedBoard, setSelectedBoard] = useState("");
  const [extracting, setExtracting] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [cardsRes, boardsRes] = await Promise.all([
        axios.get(`${API}/inbox`, { headers }),
        axios.get(`${API}/boards`, { headers })
      ]);
      
      setCards(cardsRes.data);
      setBoards(boardsRes.data);
    } catch (error) {
      toast.error("Failed to load inbox");
    } finally {
      setLoading(false);
    }
  };

  const extractTasks = async () => {
    if (!inputText.trim()) {
      toast.error("Please enter some text");
      return;
    }

    setExtracting(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/ai/extract-tasks`, {
        text: inputText
      }, { headers: { Authorization: `Bearer ${token}` } });
      
      setExtractedTasks(response.data.tasks || []);
      toast.success("Tasks extracted! Review and select a board to add them.");
    } catch (error) {
      toast.error("Failed to extract tasks");
    } finally {
      setExtracting(false);
    }
  };

  const addTasksToBoard = async () => {
    if (!selectedBoard) {
      toast.error("Please select a board");
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      // Get lists for the board
      const listsRes = await axios.get(`${API}/lists/${selectedBoard}`, { headers });
      const lists = listsRes.data;
      
      if (lists.length === 0) {
        toast.error("This board has no lists. Create a list first.");
        return;
      }
      
      // Add tasks to the first list
      const firstList = lists[0];
      const cardsRes = await axios.get(`${API}/cards/${selectedBoard}`, { headers });
      let position = cardsRes.data.filter(c => c.list_id === firstList.id).length;
      
      for (const task of extractedTasks) {
        await axios.post(`${API}/cards`, {
          title: task.title,
          description: task.description || "",
          list_id: firstList.id,
          board_id: selectedBoard,
          position: position++,
          priority: task.priority || "medium"
        }, { headers });
      }
      
      toast.success(extractedTasks.length + " task(s) added to board!");
      setShowAIConverter(false);
      setInputText("");
      setExtractedTasks([]);
      setSelectedBoard("");
      fetchData();
    } catch (error) {
      toast.error("Failed to add tasks");
    }
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #e3f2fd 0%, #f0f4f8 100%)' }}>
      {/* Header */}
      <header className="backdrop-blur-md bg-white/70 shadow-sm p-4" data-testid="inbox-header">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              data-testid="back-to-dashboard-inbox"
              onClick={() => navigate('/dashboard')}
              style={{ color: '#0277bd' }}
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Dashboard
            </Button>
            <h1 className="text-2xl font-bold" style={{ color: '#01579b' }}>Unified Inbox</h1>
          </div>
          <Dialog open={showAIConverter} onOpenChange={setShowAIConverter}>
            <DialogTrigger asChild>
              <Button data-testid="ai-converter-button" className="text-white" style={{ background: '#0288d1' }}>
                <Sparkles className="w-4 h-4 mr-2" />
                AI Task Converter
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl" data-testid="ai-converter-dialog">
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5" style={{ color: '#0288d1' }} />
                  Convert Text to Tasks
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4 mt-4">
                <div>
                  <Label>Paste email or text</Label>
                  <Textarea
                    data-testid="ai-input-text"
                    placeholder="Paste your email, message, or notes here. AI will extract actionable tasks..."
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    rows={8}
                    className="mt-1"
                  />
                </div>
                
                <Button
                  onClick={extractTasks}
                  data-testid="extract-tasks-button"
                  disabled={extracting}
                  className="w-full text-white"
                  style={{ background: '#0288d1' }}
                >
                  {extracting ? "Extracting..." : "Extract Tasks with AI"}
                </Button>
                
                {extractedTasks.length > 0 && (
                  <div className="space-y-4" data-testid="extracted-tasks-section">
                    <div>
                      <Label>Extracted Tasks ({extractedTasks.length})</Label>
                      <div className="space-y-2 mt-2 max-h-60 overflow-y-auto">
                        {extractedTasks.map((task, idx) => {
                          return (
                            <Card key={idx} className="p-3" data-testid={"extracted-task-" + idx}>
                              <h4 className="font-medium text-[#01579b]">{task.title}</h4>
                              {task.description && <p className="text-sm mt-1 text-[#0277bd]">{task.description}</p>}
                              <span className="text-xs px-2 py-1 rounded mt-2 inline-block bg-[#b3e5fc]">
                                {task.priority || 'medium'} priority
                              </span>
                            </Card>
                          );
                        })}
                      </div>
                    </div>
                    
                    <div>
                      <Label>Select Board</Label>
                      <Select value={selectedBoard} onValueChange={setSelectedBoard}>
                        <SelectTrigger data-testid="board-select">
                          <SelectValue placeholder="Choose a board" />
                        </SelectTrigger>
                        <SelectContent>
                          {boards.map((board) => {
                            return (
                              <SelectItem key={board.id} value={board.id} data-testid={"board-option-" + board.id}>
                                {board.title}
                              </SelectItem>
                            );
                          })}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <Button
                      onClick={addTasksToBoard}
                      data-testid="add-tasks-to-board-button"
                      className="w-full text-white"
                      style={{ background: '#0288d1' }}
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add to Board
                    </Button>
                  </div>
                )}
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {loading ? (
          <div className="text-center py-12" data-testid="loading-inbox">
            <p style={{ color: '#0277bd' }}>Loading your tasks...</p>
          </div>
        ) : cards.length === 0 ? (
          <div className="text-center py-12" data-testid="no-tasks-message">
            <Sparkles className="w-16 h-16 mx-auto mb-4" style={{ color: '#0288d1', opacity: 0.5 }} />
            <p className="text-lg" style={{ color: '#0277bd' }}>No tasks yet. Start by creating cards in your boards!</p>
          </div>
        ) : (
          <div className="space-y-4" data-testid="inbox-tasks">
            {cards.map((card) => {
              return (
                <Card key={card.id} data-testid={"inbox-card-" + card.id} className="card-hover border-2" style={{ borderColor: '#b3e5fc' }}>
                  <CardHeader>
                    <CardTitle style={{ color: '#01579b' }}>{card.title}</CardTitle>
                  </CardHeader>
                  {card.description && (
                    <CardContent>
                      <p style={{ color: '#0277bd' }}>{card.description}</p>
                    </CardContent>
                  )}
                </Card>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
