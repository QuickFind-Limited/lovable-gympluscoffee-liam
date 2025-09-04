import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Activity, MessageSquare, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { apiStreamingService, StreamEvent } from '@/services/apiStreaming';
import TypewriterText from './TypewriterText';

interface StreamingConversationProps {
  className?: string;
}

const StreamingConversation: React.FC<StreamingConversationProps> = ({ className = '' }) => {
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [finalResponse, setFinalResponse] = useState<string>('');
  const [showFinalResponse, setShowFinalResponse] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [events, finalResponse]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;

    const query = input.trim();
    setInput('');
    setEvents([]);
    setFinalResponse('');
    setShowFinalResponse(false);
    setIsStreaming(true);

    // Ajouter le message utilisateur
    const userEvent: StreamEvent = {
      id: Date.now().toString(),
      type: 'message',
      timestamp: new Date().toISOString(),
      display: `👤 Vous: ${query}`,
      data: { role: 'user', content: query },
      full_content: query
    };
    setEvents([userEvent]);

    try {
      await apiStreamingService.streamQuery(
        {
          prompt: query,
          model: 'claude-sonnet-4-20250514',
          max_turns: 30
        },
        (event: StreamEvent) => {
          setEvents(prev => [...prev, event]);
        },
        (finalResponse?: string) => {
          setIsStreaming(false);
          if (finalResponse) {
            setFinalResponse(finalResponse);
            setShowFinalResponse(true);
          }
        },
        (error: Error) => {
          setIsStreaming(false);
          const errorEvent: StreamEvent = {
            id: Date.now().toString(),
            type: 'log',
            timestamp: new Date().toISOString(),
            display: `❌ Erreur: ${error.message}`,
            data: { error: error.message }
          };
          setEvents(prev => [...prev, errorEvent]);
        }
      );
    } catch (error) {
      setIsStreaming(false);
      console.error('Streaming error:', error);
    }

    inputRef.current?.focus();
  };

  const getEventIcon = (type: StreamEvent['type']) => {
    switch (type) {
      case 'connection':
        return <Zap className="h-3 w-3" />;
      case 'message':
        return <MessageSquare className="h-3 w-3" />;
      case 'log':
        return <Activity className="h-3 w-3" />;
      case 'final_response':
        return <Bot className="h-3 w-3" />;
      default:
        return <div className="h-3 w-3 rounded-full bg-muted" />;
    }
  };

  const getEventBadgeVariant = (type: StreamEvent['type']) => {
    switch (type) {
      case 'connection':
        return 'default';
      case 'message':
        return 'secondary';
      case 'log':
        return 'outline';
      case 'final_response':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  return (
    <div className={`flex flex-col h-full bg-background ${className}`}>
      {/* Header */}
      <div className="flex-shrink-0 p-4 border-b">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">Conversation en Streaming</h2>
          {isStreaming && (
            <Badge variant="outline" className="animate-pulse">
              <Activity className="h-3 w-3 mr-1" />
              En cours...
            </Badge>
          )}
        </div>
      </div>

      {/* Messages et événements */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {events.map((event, index) => (
            <div key={event.id} className="space-y-2">
              {/* Événement */}
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-1">
                  {getEventIcon(event.type)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant={getEventBadgeVariant(event.type)} className="text-xs">
                      {event.type}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-sm break-words">
                    {event.display}
                  </div>
                  {event.full_content && event.type === 'message' && event.data.role !== 'user' && (
                    <div className="mt-2 p-3 bg-muted/50 rounded-lg border-l-2 border-primary">
                      <div className="text-sm text-muted-foreground mb-1">Contenu complet:</div>
                      <div className="text-sm whitespace-pre-wrap">{event.full_content}</div>
                    </div>
                  )}
                </div>
              </div>
              
              {index < events.length - 1 && <Separator className="my-2" />}
            </div>
          ))}

          {/* Réponse finale avec effet TypewriterText */}
          {showFinalResponse && finalResponse && (
            <div className="space-y-2">
              <Separator className="my-4" />
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-1">
                  <Bot className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-3">
                    <Badge variant="default" className="text-xs">
                      Réponse finale
                    </Badge>
                  </div>
                  <div className="bg-muted/30 rounded-lg p-4 border-l-4 border-primary">
                    <TypewriterText 
                      text={finalResponse}
                      className="text-sm leading-relaxed"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </ScrollArea>

      {/* Input */}
      <div className="flex-shrink-0 p-4 border-t">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Tapez votre question..."
            disabled={isStreaming}
            className="flex-1"
          />
          <Button 
            type="submit" 
            disabled={!input.trim() || isStreaming}
            size="icon"
          >
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
};

export default StreamingConversation;