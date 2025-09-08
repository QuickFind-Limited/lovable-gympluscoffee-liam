import MarkdownRenderer from "@/components/MarkdownRenderer";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StreamEvent } from "@/services/apiStreaming";
import { Activity, Bot, MessageSquare, User, Zap } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import SearchBar from "./SearchBar";

interface ConversationMessage {
  id: string;
  content: string;
  role: "user" | "assistant";
  timestamp: Date;
}

interface StreamingConversationProps {
  className?: string;
  events?: StreamEvent[];
  isStreaming?: boolean;
  conversationMessages?: ConversationMessage[];
  onStreamingEvent?: (event: StreamEvent) => void;
  onStreamingStart?: () => void;
  onStreamingEnd?: (finalResponse?: string) => void;
  onStreamingError?: (error: Error) => void;
}

const StreamingConversation: React.FC<StreamingConversationProps> = ({
  className = "",
  events: propEvents = [],
  isStreaming: propIsStreaming = false,
  conversationMessages: propConversationMessages = [],
  onStreamingEvent,
  onStreamingStart,
  onStreamingEnd,
  onStreamingError,
}) => {
  const [events, setEvents] = useState<StreamEvent[]>(propEvents);
  const [isStreaming, setIsStreaming] = useState(propIsStreaming);
  const [searchQuery, setSearchQuery] = useState("");
  const [conversationMessages, setConversationMessages] = useState<
    ConversationMessage[]
  >(propConversationMessages);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    setEvents(propEvents);
  }, [propEvents]);

  useEffect(() => {
    setConversationMessages(propConversationMessages);
  }, [propConversationMessages]);

  useEffect(() => {
    setIsStreaming(propIsStreaming);
  }, [propIsStreaming]);

  useEffect(() => {
    scrollToBottom();
  }, [events, conversationMessages]);

  const handleSubmit = (query: string) => {
    // Cette fonction n'est plus utilisée car on utilise le store de conversation
    // mais on la garde pour compatibilité avec SearchBar
    if (onStreamingStart) {
      onStreamingStart();
    }
  };

  const getEventIcon = (type: StreamEvent["type"]) => {
    switch (type) {
      case "connection":
        return <Zap className="h-3 w-3" />;
      case "message":
        return <MessageSquare className="h-3 w-3" />;
      case "log":
        return <Activity className="h-3 w-3" />;
      case "final_response":
        return <Bot className="h-3 w-3" />;
      default:
        return <Activity className="h-3 w-3" />;
    }
  };

  const getEventBadgeVariant = (type: StreamEvent["type"]) => {
    switch (type) {
      case "connection":
        return "default";
      case "message":
        return "secondary";
      case "log":
        return "outline";
      case "final_response":
        return "destructive";
      default:
        return "outline";
    }
  };

  return (
    <div className={`flex flex-col h-full bg-background ${className}`}>
      {/* En-tête */}
      <div className="flex-shrink-0 p-4 border-b bg-background">
        <div className="flex items-center gap-2">
          <Bot className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">Conversation</h2>
          {isStreaming && (
            <Badge variant="outline" className="animate-pulse">
              <Activity className="h-3 w-3 mr-1" />
              Thinking...
            </Badge>
          )}
        </div>
      </div>

      {/* Messages et événements */}
      <ScrollArea className="flex-1 p-4">
        <div className="space-y-6">
          {/* Messages de conversation */}
          {conversationMessages
            .filter((message, index) => {
              // Ne pas afficher les messages assistant si il y a des événements final_response
              // car ils seront affichés via les événements
              if (
                message.role === "assistant" &&
                events.some((event) => event.type === "final_response")
              ) {
                // Pendant le streaming, ne pas afficher le dernier message assistant
                if (isStreaming) {
                  const isLastAssistantMessage =
                    index === conversationMessages.length - 1 ||
                    conversationMessages
                      .slice(index + 1)
                      .every((m) => m.role === "user");
                  return !isLastAssistantMessage;
                }
                // Après le streaming, ne pas afficher le dernier message assistant si on a des final_response
                const isLastAssistantMessage =
                  index === conversationMessages.length - 1 ||
                  conversationMessages
                    .slice(index + 1)
                    .every((m) => m.role === "user");
                return !isLastAssistantMessage;
              }
              return true;
            })
            .map((message, index) => (
              <div key={message.id} className="animate-fade-in">
                {message.role === "user" ? (
                  <div className="flex items-start gap-3 justify-end">
                    <div className="flex-1 min-w-0 max-w-[85%]">
                      <div className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-2xl p-4 ml-auto shadow-sm">
                        <div className="text-sm leading-relaxed">
                          {message.content}
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground mt-1 mr-2 text-right">
                        Vous • {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                    <div className="flex-shrink-0 mt-1">
                      <User className="h-8 w-8 text-primary bg-primary/10 rounded-full p-1.5" />
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 mt-1">
                      <Bot className="h-8 w-8 text-muted-foreground bg-muted/20 rounded-full p-1.5" />
                    </div>
                    <div className="flex-1 min-w-0 max-w-[85%]">
                      <div className="bg-background border rounded-2xl p-4 shadow-sm">
                        <MarkdownRenderer content={message.content} />
                      </div>
                      <div className="text-xs text-muted-foreground mt-1 ml-2">
                        Assistant • {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

          {/* Bloc Thinking - affiché pendant et après le streaming */}
          {events.filter(
            (event) => event.type === "connection" || event.type === "message"
          ).length > 0 && (
            <div
              className={`rounded-lg p-4 border animate-fade-in ${
                isStreaming ? "bg-muted/20" : "bg-muted/10 opacity-75"
              }`}
            >
              <div className="flex items-center gap-2 mb-3">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">
                  {isStreaming ? "Thinking..." : "Processus de réflexion"}
                </span>
                {isStreaming && (
                  <div className="flex space-x-1 ml-2">
                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="h-2 w-2 bg-primary rounded-full animate-bounce"></div>
                  </div>
                )}
              </div>
              <div className="space-y-4">
                {events
                  .filter(
                    (event) =>
                      event.type === "connection" || event.type === "message"
                  )
                  .map((event, index) => (
                    <div key={event.id} className="animate-fade-in">
                      {event.type === "connection" ? (
                        <div className="flex items-center gap-3">
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
                      ) : (
                        <div className="space-y-2">
                          <div className="flex items-center gap-3">
                            <div className="flex-shrink-0">
                              {getEventIcon(event.type)}
                            </div>
                            <div className="flex items-center gap-2">
                              <Badge
                                variant={getEventBadgeVariant(event.type)}
                                className="text-xs"
                              >
                                {event.type}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {new Date(event.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                          </div>
                          {event.full_content && event.data.role !== "user" && (
                            <div className="ml-6 p-3 bg-background rounded-lg border-l-2 border-primary">
                              <div className="text-sm whitespace-pre-wrap">
                                {event.full_content}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Réponse finale - affichée après le bloc events */}
          {events
            .filter((event) => event.type === "final_response")
            .map((finalEvent) => (
              <div key={finalEvent.id} className="animate-fade-in">
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0 mt-1">
                    <Bot className="h-8 w-8 text-muted-foreground bg-muted/20 rounded-full p-1.5" />
                  </div>
                  <div className="flex-1 min-w-0 max-w-[85%]">
                    <div className="bg-background border rounded-2xl p-4 shadow-sm">
                      <MarkdownRenderer
                        content={
                          finalEvent.full_content ||
                          finalEvent.data.response ||
                          ""
                        }
                      />
                    </div>
                    <div className="text-xs text-muted-foreground mt-1 ml-2">
                      Assistant •{" "}
                      {new Date(finalEvent.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
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
