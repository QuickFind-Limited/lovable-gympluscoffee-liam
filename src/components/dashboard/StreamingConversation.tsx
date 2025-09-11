import MarkdownRenderer from "@/components/MarkdownRenderer";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StreamEvent, apiStreamingService } from "@/services/apiStreaming";
import {
  Activity,
  Bot,
  User,
  Paperclip,
  FileText,
  MessageSquare,
  Zap,
} from "lucide-react";
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

  // Calculer l'index et le timestamp du dernier message utilisateur
  const lastUserMessageIndex = (() => {
    for (let i = conversationMessages.length - 1; i >= 0; i--) {
      if (conversationMessages[i].role === "user") return i;
    }
    return -1;
  })();
  const lastUserMessage = lastUserMessageIndex >= 0 ? conversationMessages[lastUserMessageIndex] : null;
  const lastUserMessageId = lastUserMessage ? lastUserMessage.id : null;
  const lastUserMessageTimestamp: Date | null = lastUserMessage ? lastUserMessage.timestamp : null;

  // Limiter l'affichage des événements au tour courant (ceux postérieurs au dernier message utilisateur)
  const currentTurnEvents: StreamEvent[] = React.useMemo(() => {
    if (!lastUserMessageTimestamp) return events;
    const cutoff = lastUserMessageTimestamp.getTime();
    return events.filter((e) => {
      const t = new Date(e.timestamp).getTime();
      return !isNaN(t) && t >= cutoff;
    });
  }, [events, lastUserMessageTimestamp]);

  // Identifier un potentiel assistant_message d'événements à masquer quand la réponse finale arrive (tour courant)
  const latestFinalResponseIndex = (() => {
    for (let i = currentTurnEvents.length - 1; i >= 0; i--) {
      if (currentTurnEvents[i].type === "final_response") return i;
    }
    return -1;
  })();
  const assistantMessageToHideId = (() => {
    if (latestFinalResponseIndex < 0) return undefined;
    for (let i = latestFinalResponseIndex; i >= 0; i--) {
      const e = currentTurnEvents[i];
      if (
        e.type === "message" &&
        e.data?.type === "assistant_message" &&
        !!e.full_content
      ) {
        return e.id;
      }
    }
    return undefined;
  })();

  // Regrouper toutes les réponses finales par tour (ancrées au dernier message utilisateur précédent leur timestamp)
  const finalResponsesByUserId = React.useMemo(() => {
    const map = new Map<string, StreamEvent[]>();
    const userMessages = conversationMessages.filter((m) => m.role === "user");
    for (const e of events) {
      if (e.type !== "final_response") continue;
      const et = new Date(e.timestamp).getTime();
      if (isNaN(et)) continue;
      let anchorId: string | null = null;
      for (let i = 0; i < userMessages.length; i++) {
        const m = userMessages[i];
        const mt = m.timestamp.getTime();
        if (!isNaN(mt) && mt <= et) {
          anchorId = m.id;
        } else if (!isNaN(mt) && mt > et) {
          break;
        }
      }
      if (anchorId) {
        const arr = map.get(anchorId) || [];
        arr.push(e);
        map.set(anchorId, arr);
      }
    }
    return map;
  }, [events, conversationMessages]);

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
        return <div className="h-3 w-3 rounded-full bg-muted" />;
    }
  };

  const getEventBadgeVariant = (type: StreamEvent["type"]) => {
    switch (type) {
      case "connection":
        return "default" as const;
      case "message":
        return "secondary" as const;
      case "log":
        return "outline" as const;
      case "final_response":
        return "destructive" as const;
      default:
        return "outline" as const;
    }
  };

  const formatEventDisplay = (event: StreamEvent) => {
    const raw = event.display || "";
    if (event.data?.type === "tool_use" && typeof raw === "string") {
      return raw.replace(/mcp__netsuite_mcp__/g, "Request NetSuite: ");
    }
    return raw;
  };

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
              if (message.role !== "assistant") return true;

              // Détecter le tour auquel appartient ce message assistant
              let prevUserIdx = -1;
              for (let i = index - 1; i >= 0; i--) {
                if (conversationMessages[i].role === "user") { prevUserIdx = i; break; }
              }
              if (prevUserIdx < 0) return true;

              // Y a-t-il une réponse finale pour ce tour ?
              const hasFinalForTurn = (() => {
                // cas du tour courant
                if (prevUserIdx === lastUserMessageIndex) {
                  return currentTurnEvents.some((e) => e.type === "final_response");
                }
                // cas des tours précédents
                const prevUserId = conversationMessages[prevUserIdx]?.id;
                if (!prevUserId) return false;
                return (finalResponsesByUserId.get(prevUserId)?.length ?? 0) > 0;
              })();
              if (!hasFinalForTurn) return true;

              // Est-ce le DERNIER message assistant avant le prochain message utilisateur ?
              let nextUserIdx = conversationMessages.length;
              for (let i = index + 1; i < conversationMessages.length; i++) {
                if (conversationMessages[i].role === "user") { nextUserIdx = i; break; }
              }
              const hasAssistantAfterInTurn = conversationMessages
                .slice(index + 1, nextUserIdx)
                .some((m) => m.role === "assistant");
              const isLastAssistantInTurn = !hasAssistantAfterInTurn;
              return !isLastAssistantInTurn; // masquer uniquement le dernier assistant du tour
            })
            .map((message, index) => (
              <React.Fragment key={message.id}>
                <div className="animate-fade-in">
                  {message.role === "user" ? (
                    <div className="flex items-start gap-3 justify-end">
                      <div className="flex-1 min-w-0 max-w-[85%]">
                        <div className="bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-2xl p-4 ml-auto shadow-sm">
                          <div className="text-sm leading-relaxed">{message.content}</div>
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

                {/* Insérer le bloc d'événements du tour courant juste après le dernier message utilisateur */}
                {lastUserMessageId && message.id === lastUserMessageId && (isStreaming || currentTurnEvents.length > 0) && (
                  <div className="bg-muted/20 rounded-lg p-4 border animate-fade-in">
                    <div className="flex items-center gap-2 mb-3">
                      <Activity className="h-4 w-4 text-muted-foreground" />
                      <span className="text-sm font-medium text-muted-foreground">Thinking...</span>
                      {isStreaming && (
                        <div className="flex space-x-1 ml-2">
                          <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                          <div className="h-2 w-2 bg-primary rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                          <div className="h-2 w-2 bg-primary rounded-full animate-bounce"></div>
                        </div>
                      )}
                    </div>
                    <div className="space-y-4">
                      {currentTurnEvents
                        .filter((e) => {
                          const isAssistantNoText =
                            e.type === "log" &&
                            e.data?.type === "assistant_message" &&
                            e.data?.details &&
                            typeof e.data.details === "object" &&
                            (e.data.details as any).has_text === false;
                          const passesBaseFilter =
                            e.type === "connection" ||
                            ((e.type === "log" && e.data?.type !== "user_message" && e.data?.type !== "completed" && !e.data?.user_message) && !isAssistantNoText) ||
                            (e.type === "message" && e.data?.type === "assistant_message" && !!e.full_content);

                          if (!passesBaseFilter) return false;
                          if (
                            e.type === "message" &&
                            e.data?.type === "assistant_message" &&
                            assistantMessageToHideId &&
                            e.id === assistantMessageToHideId
                          ) {
                            return false;
                          }
                          return true;
                        })
                        .map((event) => (
                          <div key={event.id} className="animate-fade-in">
                            {event.type === "connection" ? (
                              <div className="flex items-center gap-3">
                                <div className="flex-shrink-0">{getEventIcon(event.type)}</div>
                                <div className="text-sm text-muted-foreground">{event.display}</div>
                                <div className="text-xs text-muted-foreground ml-auto">
                                  {new Date(event.timestamp).toLocaleTimeString()}
                                </div>
                              </div>
                            ) : (
                              <div className="space-y-2">
                                <div className="flex items-center gap-3">
                                  <div className="flex-shrink-0">{getEventIcon(event.type)}</div>
                                  <div className="flex items-center gap-2">
                                    <Badge variant={getEventBadgeVariant(event.type)} className="text-xs">{event.type}</Badge>
                                    <span className="text-xs text-muted-foreground">
                                      {new Date(event.timestamp).toLocaleTimeString()}
                                    </span>
                                  </div>
                                </div>
                                <div className="text-sm break-words ml-6">
                                  {event.type === "message" ? "💬 Assistant" : formatEventDisplay(event)}
                                </div>
                                {event.type === "log" && event.data?.type === "tool_use" && event.data?.details && (
                                  <div className="ml-6 mt-2 p-3 bg-background rounded-lg border-l-2 border-primary">
                                    <div className="text-sm text-muted-foreground mb-1">Details</div>
                                    <div className="text-sm">
                                      <MarkdownRenderer
                                        content={
                                          typeof event.data.details === "string"
                                            ? (event.data.details as string)
                                            : "```json\n" + JSON.stringify(event.data.details, null, 2) + "\n```"
                                        }
                                      />
                                    </div>
                                  </div>
                                )}
                                {event.type === "message" && event.full_content && (
                                  <div className="ml-6 mt-2 p-3 bg-background rounded-lg border-l-2 border-primary">
                                    <div className="text-sm text-muted-foreground mb-1">Content</div>
                                    <div className="text-sm">
                                      <MarkdownRenderer content={event.full_content || ""} />
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

                {/* Réponse finale du tour courant */}
                {lastUserMessageId && message.id === lastUserMessageId && currentTurnEvents
                  .filter((event) => event.type === "final_response")
                  .map((finalEvent, idx) => (
                    <div key={finalEvent.id} className="animate-fade-in">
                      {idx > 0 && <hr className="my-4 border-t border-border/60" />}
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-1">
                          <Bot className="h-8 w-8 text-muted-foreground bg-muted/20 rounded-full p-1.5" />
                        </div>
                        <div className="flex-1 min-w-0 max-w-[85%]">
                          <div className="bg-background border rounded-2xl p-4 shadow-sm">
                            <MarkdownRenderer content={finalEvent.full_content || finalEvent.data.response || ""} />

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
                                    <div className="text-xs text-muted-foreground mb-1">Attachments</div>
                                    <ul className="space-y-1">
                                      {finalEvent.data.attachments.map((att, idx) => {
                                        const name = att.path.split("/").pop() || att.path;
                                        return (
                                          <li key={`att-${idx}`} className="flex items-center gap-2 text-sm">
                                            <Paperclip className="h-3.5 w-3.5 text-primary/80" />
                                            <button
                                              type="button"
                                              onClick={() => openFilePreview(finalEvent.data.session_id as string | undefined, name)}
                                              className="text-left text-primary hover:underline disabled:opacity-50"
                                              disabled={!finalEvent.data.session_id}
                                              title={finalEvent.data.session_id ? "Open preview" : "No session available"}
                                            >
                                              {name}
                                            </button>
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

                                {/* new files */}
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
                            Assistant • {new Date(finalEvent.timestamp).toLocaleTimeString()}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                {/* Réponses finales des tours précédents (toujours visibles) */}
                {lastUserMessageId && message.id !== lastUserMessageId && finalResponsesByUserId.get(message.id)?.map((finalEvent, idx) => (
                  <div key={`${finalEvent.id}-past`} className="animate-fade-in">
                    {idx > 0 && <hr className="my-4 border-t border-border/60" />}
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 mt-1">
                        <Bot className="h-8 w-8 text-muted-foreground bg-muted/20 rounded-full p-1.5" />
                      </div>
                      <div className="flex-1 min-w-0 max-w-[85%]">
                        <div className="bg-background border rounded-2xl p-4 shadow-sm">
                          <MarkdownRenderer content={finalEvent.full_content || finalEvent.data.response || ""} />

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
                                  <div className="text-xs text-muted-foreground mb-1">Attachments</div>
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
                                            title={finalEvent.data.session_id ? "Open preview" : "No session available"}
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
                          Assistant • {new Date(finalEvent.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </React.Fragment>
            ))}

          {/* Étapes de progression actuelles */}
          {false && events
            .filter((e) => {
              const isAssistantNoText =
                e.type === "log" &&
                e.data?.type === "assistant_message" &&
                e.data?.details &&
                typeof e.data.details === "object" &&
                (e.data.details as any).has_text === false;

              const passesBaseFilter = (
                e.type === "connection" ||
                ((e.type === "log" && e.data?.type !== "user_message" && e.data?.type !== "completed" && !e.data?.user_message) && !isAssistantNoText) ||
                (e.type === "message" && e.data?.type === "assistant_message" && !!e.full_content)
              );

              if (!passesBaseFilter) return false;

              // Cacher le dernier assistant_message quand la réponse finale est affichée
              if (
                e.type === "message" &&
                e.data?.type === "assistant_message" &&
                assistantMessageToHideId &&
                e.id === assistantMessageToHideId
              ) {
                return false;
              }
              return true;
            })
            .length > 0 && (
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
                  .filter((event) => {
                    const isAssistantNoText =
                      event.type === "log" &&
                      event.data?.type === "assistant_message" &&
                      event.data?.details &&
                      typeof event.data.details === "object" &&
                      (event.data.details as any).has_text === false;

                    const passesBaseFilter = (
                      event.type === "connection" ||
                      ((event.type === "log" && event.data?.type !== "user_message" && event.data?.type !== "completed" && !event.data?.user_message) && !isAssistantNoText) ||
                      (event.type === "message" && event.data?.type === "assistant_message" && !!event.full_content)
                    );

                    if (!passesBaseFilter) return false;

                    if (
                      event.type === "message" &&
                      event.data?.type === "assistant_message" &&
                      assistantMessageToHideId &&
                      event.id === assistantMessageToHideId
                    ) {
                      return false;
                    }

                    return true;
                  })
                  .map((event) => (
                    <div key={event.id} className="animate-fade-in">
                      {event.type === "connection" ? (
                        <div className="flex items-center gap-3">
                          <div className="flex-shrink-0">{getEventIcon(event.type)}</div>
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
                            <div className="flex-shrink-0">{getEventIcon(event.type)}</div>
                            <div className="flex items-center gap-2">
                              <Badge variant={getEventBadgeVariant(event.type)} className="text-xs">
                                {event.type}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {new Date(event.timestamp).toLocaleTimeString()}
                              </span>
                            </div>
                          </div>
                          <div className="text-sm break-words ml-6">
                            {event.type === "message" ? "💬 Assistant" : formatEventDisplay(event)}
                          </div>
                          {event.type === "log" && event.data?.type === "tool_use" && event.data?.details && (
                            <div className="ml-6 mt-2 p-3 bg-background rounded-lg border-l-2 border-primary">
                              <div className="text-sm text-muted-foreground mb-1">Details</div>
                              <div className="text-sm">
                                <MarkdownRenderer
                                  content={
                                    typeof event.data.details === "string"
                                      ? (event.data.details as string)
                                      : "```json\n" + JSON.stringify(event.data.details, null, 2) + "\n```"
                                  }
                                />
                              </div>
                            </div>
                          )}
                          {event.type === "message" && event.full_content && (
                            <div className="ml-6 mt-2 p-3 bg-background rounded-lg border-l-2 border-primary">
                              <div className="text-sm text-muted-foreground mb-1">Content</div>
                              <div className="text-sm">
                                <MarkdownRenderer content={event.full_content || ""} />
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
          {false && events
            .filter((event) => event.type === "final_response")
            .map((finalEvent, idx) => (
              <div key={finalEvent.id} className="animate-fade-in">
                {idx > 0 && <hr className="my-4 border-t border-border/60" />}
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
