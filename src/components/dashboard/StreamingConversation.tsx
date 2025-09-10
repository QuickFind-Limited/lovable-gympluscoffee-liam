import MarkdownRenderer from "@/components/MarkdownRenderer";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StreamEvent, apiStreamingService } from "@/services/apiStreaming";
import { Activity, Bot, User, Paperclip, FileText } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import SearchBar from "./SearchBar";
import FilePreviewSheet from "@/components/FilePreviewSheet";

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
  const [filePreview, setFilePreview] = useState<{
    sessionId: string;
    filename: string;
    displayName: string;
  } | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const openFilePreview = (
    sessionId: string | undefined,
    pathOrName: string
  ) => {
    const id = sessionId || apiStreamingService.getCurrentSessionId() || undefined;
    if (!id) return;
    const name = pathOrName.split("/").pop() || pathOrName;
    setFilePreview({ sessionId: id, filename: name, displayName: name });
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
                        You • {message.timestamp.toLocaleTimeString()}
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
                        Source • {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

          {/* Simple Thinking indicator - only shown during streaming */}
          {isStreaming && events.filter(
            (event) => event.type === "connection" || event.type === "message"
          ).length > 0 && (
            <div className="rounded-lg p-4 border animate-fade-in bg-muted/20">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">
                  Thinking...
                </span>
                <div className="flex space-x-1 ml-2">
                  <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="h-2 w-2 bg-primary rounded-full animate-bounce"></div>
                </div>
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

                      {(Array.isArray(finalEvent.data.attachments) && finalEvent.data.attachments.length > 0) ||
                      (Array.isArray(finalEvent.data.new_files) && finalEvent.data.new_files.length > 0) ||
                      (Array.isArray(finalEvent.data.updated_files) && finalEvent.data.updated_files.length > 0) ? (
                        <div className="mt-4 pt-3 border-t">
                          <div className="flex items-center gap-2 mb-2 text-sm font-medium text-muted-foreground">
                            <Paperclip className="h-4 w-4" />
                            <span>Generated files</span>
                            {finalEvent.data.file_changes_summary && (
                              <span className="text-xs text-muted-foreground">
                                • {finalEvent.data.file_changes_summary.new_count ?? 0} new(s), {finalEvent.data.file_changes_summary.updated_count ?? 0} updated(s)
                              </span>
                            )}
                          </div>

                          {/* Pièces jointes */}
                          {Array.isArray(finalEvent.data.attachments) && finalEvent.data.attachments.length > 0 && (
                            <div className="mb-3">
                              <div className="text-xs text-muted-foreground mb-1">Pièces jointes</div>
                              <ul className="space-y-1">
                                {finalEvent.data.attachments.map((att: any, idx: number) => {
                                  const name = (att.path || att.absolute_path || "").toString().split("/").pop() || att.path || att.absolute_path || `attachment-${idx+1}`;
                                  return (
                                    <li key={`${name}-${idx}`} className="flex items-center gap-2 text-sm">
                                      <FileText className="h-3.5 w-3.5 text-primary/80" />
                                      <button
                                        type="button"
                                        onClick={() => openFilePreview(finalEvent.data.session_id as string | undefined, name)}
                                        className="text-left text-primary hover:underline disabled:opacity-50"
                                        disabled={!finalEvent.data.session_id}
                                        title={finalEvent.data.session_id ? "Ouvrir l'aperçu" : "Aucune session disponible"}
                                      >
                                        {name}
                                      </button>
                                      {typeof att.size === "number" && (
                                        <span className="text-xs text-muted-foreground">• {(att.size/1024).toFixed(1)} KB</span>
                                      )}
                                      {att.is_new && (
                                        <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">New</span>
                                      )}
                                      {att.is_updated && !att.is_new && (
                                        <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">Updated</span>
                                      )}
                                    </li>
                                  );
                                })}
                              </ul>
                            </div>
                          )}

                          {Array.isArray(finalEvent.data.new_files) && finalEvent.data.new_files.length > 0 && (
                            <div className="mb-3">
                              <div className="text-xs text-muted-foreground mb-1">New files</div>
                              <ul className="space-y-1">
                                {finalEvent.data.new_files.map((path: unknown, idx: number) => {
                                  const p = String(path);
                                  const name = p.split("/").pop() || p;
                                  return (
                                    <li key={`new-${idx}`} className="flex items-center gap-2 text-sm">
                                      <FileText className="h-3.5 w-3.5 text-primary/80" />
                                      <button
                                        type="button"
                                        onClick={() => openFilePreview(finalEvent.data.session_id as string | undefined, name)}
                                        className="text-left text-primary hover:underline disabled:opacity-50"
                                        disabled={!finalEvent.data.session_id}
                                        title={finalEvent.data.session_id ? "Open preview" : "No session available"}
                                      >
                                        {name}
                                      </button>
                                    </li>
                                  );
                                })}
                              </ul>
                            </div>
                          )}

                          {/* updated files */}
                          {Array.isArray(finalEvent.data.updated_files) && finalEvent.data.updated_files.length > 0 && (
                            <div>
                              <div className="text-xs text-muted-foreground mb-1">Updated files</div>
                              <ul className="space-y-1">
                                {finalEvent.data.updated_files.map((path: unknown, idx: number) => {
                                  const p = String(path);
                                  const name = p.split("/").pop() || p;
                                  return (
                                    <li key={`upd-${idx}`} className="flex items-center gap-2 text-sm">
                                      <FileText className="h-3.5 w-3.5 text-primary/80" />
                                      <button
                                        type="button"
                                        onClick={() => openFilePreview(finalEvent.data.session_id as string | undefined, name)}
                                        className="text-left text-primary hover:underline disabled:opacity-50"
                                        disabled={!finalEvent.data.session_id}
                                        title={finalEvent.data.session_id ? "Open preview" : "No session available"}
                                      >
                                        {name}
                                      </button>
                                    </li>
                                  );
                                })}
                              </ul>
                            </div>
                          )}
                        </div>
                      ) : null}
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
      {filePreview && (
        <FilePreviewSheet
          open={!!filePreview}
          onOpenChange={(open) => !open && setFilePreview(null)}
          conversationId={filePreview.sessionId}
          filename={filePreview.filename}
          displayName={filePreview.displayName}
        />
      )}
    </div>
  );
};

export default StreamingConversation;
