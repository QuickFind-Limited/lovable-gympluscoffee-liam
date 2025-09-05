import React, { useState, useRef, useEffect } from 'react';
import { Bot, Activity, MessageSquare, Zap } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { StreamEvent } from '@/services/apiStreaming';
import TypewriterText from './TypewriterText';
import SearchBar from './SearchBar';

interface StreamingConversationProps {
  className?: string;
  events?: StreamEvent[];
  finalResponse?: string;
  isStreaming?: boolean;
  onStreamingEvent?: (event: StreamEvent) => void;
  onStreamingStart?: () => void;
  onStreamingEnd?: (finalResponse?: string) => void;
  onStreamingError?: (error: Error) => void;
}

const StreamingConversation: React.FC<StreamingConversationProps> = ({ 
  className = '', 
  events: propEvents = [], 
  finalResponse: propFinalResponse = '', 
  isStreaming: propIsStreaming = false,
  onStreamingEvent,
  onStreamingStart,
  onStreamingEnd,
  onStreamingError
}) => {
  const [events, setEvents] = useState<StreamEvent[]>(propEvents);
  const [finalResponse, setFinalResponse] = useState<string>(propFinalResponse);
  const [showFinalResponse, setShowFinalResponse] = useState(false);
  const [isStreaming, setIsStreaming] = useState(propIsStreaming);
  const [searchQuery, setSearchQuery] = useState('');
  const [userMessages, setUserMessages] = useState<string[]>([]);
  const [conversationHistory, setConversationHistory] = useState<Array<{
    userMessage?: string;
    events: StreamEvent[];
    finalResponse?: string;
  }>>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    setEvents(propEvents);
  }, [propEvents]);

  useEffect(() => {
    setFinalResponse(propFinalResponse);
    setShowFinalResponse(!!propFinalResponse);
  }, [propFinalResponse]);

  useEffect(() => {
    setIsStreaming(propIsStreaming);
  }, [propIsStreaming]);

  useEffect(() => {
    scrollToBottom();
  }, [events, finalResponse, userMessages, conversationHistory]);

  const handleSubmit = (query: string) => {
    // Ajouter à l'historique de conversation si on a des événements ou une réponse finale en cours
    if (events.length > 0 || finalResponse) {
      setConversationHistory(prev => [...prev, {
        events: [...events],
        finalResponse: finalResponse || undefined
      }]);
      
      // Réinitialiser les événements et réponse actuelle pour la nouvelle conversation
      setEvents([]);
      setFinalResponse('');
      setShowFinalResponse(false);
    }
    
    setUserMessages(prev => [...prev, query]);
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
        <div className="space-y-6">
          {/* Historique des conversations précédentes */}
          {conversationHistory.map((conversation, conversationIndex) => (
            <div key={`conversation-${conversationIndex}`} className="space-y-6">
              {/* Étapes de progression */}
              {conversation.events.filter(event => event.type === 'connection').length > 0 && (
                <div className="bg-muted/20 rounded-lg p-4 border">
                  <div className="flex items-center gap-2 mb-3">
                    <Activity className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium text-muted-foreground">Connexion</span>
                  </div>
                  <div className="space-y-2">
                    {conversation.events.filter(event => event.type === 'connection').map((event, index) => (
                      <div key={`${conversationIndex}-${event.id}`} className="flex items-center gap-3 animate-fade-in">
                        <div className="flex-shrink-0">
                          {getEventIcon(event.type)}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {event.display}
                        </div>
                        <div className="text-xs text-muted-foreground ml-auto">
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Messages complets */}
              {conversation.events.filter(event => event.type === 'message').map((event, index) => (
                <div key={`${conversationIndex}-${event.id}`} className="space-y-2 animate-fade-in">
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
                      {event.full_content && event.data.role !== 'user' && (
                        <div className="mt-2 p-3 bg-muted/50 rounded-lg border-l-2 border-primary">
                          <div className="text-sm text-muted-foreground mb-1">Contenu complet:</div>
                          <div className="text-sm whitespace-pre-wrap">{event.full_content}</div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {/* Réponse finale comme bulle de chat */}
              {conversation.finalResponse && (
                <div className="flex items-start gap-3 animate-fade-in">
                  <div className="flex-shrink-0 mt-1">
                    <Bot className="h-8 w-8 text-primary bg-primary/10 rounded-full p-1.5" />
                  </div>
                  <div className="flex-1 min-w-0 max-w-[85%]">
                    <div className="bg-background border rounded-2xl p-4 shadow-sm">
                      <div className="text-sm leading-relaxed whitespace-pre-wrap">
                        {conversation.finalResponse}
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground mt-1 ml-2">
                      Assistant
                    </div>
                  </div>
                </div>
              )}
              
              {conversationIndex < conversationHistory.length - 1 && <Separator className="my-8" />}
            </div>
          ))}

          {/* Messages utilisateur */}
          {userMessages.map((message, index) => (
            <div key={`user-${index}`} className="flex items-start gap-3 justify-end animate-fade-in">
              <div className="flex-1 min-w-0 max-w-[85%]">
                <div className="bg-primary text-primary-foreground rounded-2xl p-4 ml-auto shadow-sm">
                  <div className="text-sm leading-relaxed">
                    {message}
                  </div>
                </div>
                <div className="text-xs text-muted-foreground mt-1 mr-2 text-right">
                  Vous
                </div>
              </div>
              <div className="flex-shrink-0 mt-1">
                <MessageSquare className="h-8 w-8 text-primary bg-primary/10 rounded-full p-1.5" />
              </div>
            </div>
          ))}

          {/* Étapes de progression actuelles */}
          {events.filter(event => event.type === 'connection').length > 0 && (
            <div className="bg-muted/20 rounded-lg p-4 border animate-fade-in">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">Connexion</span>
                {isStreaming && (
                  <div className="flex space-x-1 ml-2">
                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce"></div>
                  </div>
                )}
              </div>
              <div className="space-y-2">
                {events.filter(event => event.type === 'connection').map((event, index) => (
                  <div key={event.id} className="flex items-center gap-3 animate-fade-in">
                    <div className="flex-shrink-0">
                      {getEventIcon(event.type)}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {event.display}
                    </div>
                    <div className="text-xs text-muted-foreground ml-auto">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Messages actuels complets */}
          {events.filter(event => event.type === 'message').map((event, index) => (
            <div key={event.id} className="space-y-2 animate-fade-in">
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
                  {event.full_content && event.data.role !== 'user' && (
                    <div className="mt-2 p-3 bg-muted/50 rounded-lg border-l-2 border-primary">
                      <div className="text-sm text-muted-foreground mb-1">Contenu complet:</div>
                      <div className="text-sm whitespace-pre-wrap">{event.full_content}</div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {/* Réponse finale actuelle comme bulle de chat */}
          {showFinalResponse && finalResponse && (
            <div className="flex items-start gap-3 animate-fade-in">
              <div className="flex-shrink-0 mt-1">
                <Bot className="h-8 w-8 text-primary bg-primary/10 rounded-full p-1.5" />
              </div>
              <div className="flex-1 min-w-0 max-w-[85%]">
                <div className="bg-background border rounded-2xl p-4 shadow-sm">
                  <TypewriterText 
                    text={finalResponse}
                    className="text-sm leading-relaxed"
                  />
                </div>
                <div className="text-xs text-muted-foreground mt-1 ml-2">
                  Assistant
                </div>
              </div>
            </div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </ScrollArea>

      {/* Input de conversation en bas */}
      <div className="flex-shrink-0 p-4 border-t bg-background">
        <SearchBar
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          onSubmit={handleSubmit}
          onStreamingEvent={onStreamingEvent}
          onStreamingStart={onStreamingStart}
          onStreamingEnd={onStreamingEnd}
          onStreamingError={onStreamingError}
        />
      </div>
    </div>
  );
};

export default StreamingConversation;