import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StreamEvent } from "@/services/apiStreaming";
import { Activity, Bot, MessageSquare, User, Zap } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
  finalResponse?: string;
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
  finalResponse: propFinalResponse = "",
  isStreaming: propIsStreaming = false,
  conversationMessages: propConversationMessages = [],
  onStreamingEvent,
  onStreamingStart,
  onStreamingEnd,
  onStreamingError,
}) => {
  const [events, setEvents] = useState<StreamEvent[]>(propEvents);
  const [finalResponse, setFinalResponse] = useState<string>(propFinalResponse);
  const [showFinalResponse, setShowFinalResponse] = useState(false);
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
    setFinalResponse(propFinalResponse);
    setShowFinalResponse(!!propFinalResponse);
  }, [propFinalResponse]);

  useEffect(() => {
    setIsStreaming(propIsStreaming);
  }, [propIsStreaming]);

  useEffect(() => {
    scrollToBottom();
  }, [events, finalResponse, conversationMessages]);

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
          {conversationMessages.map((message, index) => (
            <div key={message.id} className="animate-fade-in">
              {message.role === "user" ? (
                <div className="flex items-start gap-3 justify-end">
                  <div className="flex-1 min-w-0 max-w-[85%]">
                    <div className="bg-primary text-primary-foreground rounded-2xl p-4 ml-auto shadow-sm">
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
                      <div className="text-sm leading-relaxed prose prose-sm max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          components={{
                            // Personnaliser les composants pour s'adapter au design
                            p: ({ children }) => (
                              <p className="mb-2 last:mb-0">{children}</p>
                            ),
                            h1: ({ children }) => (
                              <h1 className="text-lg font-bold mb-2">
                                {children}
                              </h1>
                            ),
                            h2: ({ children }) => (
                              <h2 className="text-base font-bold mb-2">
                                {children}
                              </h2>
                            ),
                            h3: ({ children }) => (
                              <h3 className="text-sm font-bold mb-1">
                                {children}
                              </h3>
                            ),
                            ul: ({ children }) => (
                              <ul className="list-disc pl-4 mb-2">
                                {children}
                              </ul>
                            ),
                            ol: ({ children }) => (
                              <ol className="list-decimal pl-4 mb-2">
                                {children}
                              </ol>
                            ),
                            li: ({ children }) => (
                              <li className="mb-1">{children}</li>
                            ),
                            code: ({ children, ...props }) =>
                              (props as any).inline ? (
                                <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">
                                  {children}
                                </code>
                              ) : (
                                <code className="block bg-muted p-2 rounded text-xs font-mono overflow-x-auto">
                                  {children}
                                </code>
                              ),
                            pre: ({ children }) => (
                              <pre className="bg-muted p-2 rounded overflow-x-auto mb-2">
                                {children}
                              </pre>
                            ),
                            blockquote: ({ children }) => (
                              <blockquote className="border-l-4 border-primary pl-4 italic mb-2">
                                {children}
                              </blockquote>
                            ),
                            strong: ({ children }) => (
                              <strong className="font-semibold">
                                {children}
                              </strong>
                            ),
                            em: ({ children }) => (
                              <em className="italic">{children}</em>
                            ),
                          }}
                        >
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground mt-1 ml-2">
                      Assistant • {message.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {events.filter(
            (event) => event.type === "connection" || event.type === "message"
          ).length > 0 && (
            <div className="bg-muted/20 rounded-lg p-4 border animate-fade-in">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">
                  Thinking...
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

          {/* Réponse finale en streaming */}
          {showFinalResponse && finalResponse && (
            <div className="flex items-start gap-3 animate-fade-in">
              <div className="flex-shrink-0 mt-1">
                <Bot className="h-8 w-8 text-muted-foreground bg-muted/20 rounded-full p-1.5" />
              </div>
              <div className="flex-1 min-w-0 max-w-[85%]">
                <div className="bg-background border rounded-2xl p-4 shadow-sm">
                  <div className="text-sm leading-relaxed prose prose-sm max-w-none">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        // Personnaliser les composants pour s'adapter au design
                        p: ({ children }) => (
                          <p className="mb-2 last:mb-0">{children}</p>
                        ),
                        h1: ({ children }) => (
                          <h1 className="text-lg font-bold mb-2">{children}</h1>
                        ),
                        h2: ({ children }) => (
                          <h2 className="text-base font-bold mb-2">
                            {children}
                          </h2>
                        ),
                        h3: ({ children }) => (
                          <h3 className="text-sm font-bold mb-1">{children}</h3>
                        ),
                        ul: ({ children }) => (
                          <ul className="list-disc pl-4 mb-2">{children}</ul>
                        ),
                        ol: ({ children }) => (
                          <ol className="list-decimal pl-4 mb-2">{children}</ol>
                        ),
                        li: ({ children }) => (
                          <li className="mb-1">{children}</li>
                        ),
                        code: ({ children, ...props }) =>
                          (props as any).inline ? (
                            <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">
                              {children}
                            </code>
                          ) : (
                            <code className="block bg-muted p-2 rounded text-xs font-mono overflow-x-auto">
                              {children}
                            </code>
                          ),
                        pre: ({ children }) => (
                          <pre className="bg-muted p-2 rounded overflow-x-auto mb-2">
                            {children}
                          </pre>
                        ),
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-4 border-primary pl-4 italic mb-2">
                            {children}
                          </blockquote>
                        ),
                        strong: ({ children }) => (
                          <strong className="font-semibold">{children}</strong>
                        ),
                        em: ({ children }) => (
                          <em className="italic">{children}</em>
                        ),
                      }}
                    >
                      {finalResponse}
                    </ReactMarkdown>
                  </div>
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
