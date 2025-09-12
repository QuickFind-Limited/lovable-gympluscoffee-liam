import { useConversation } from "@/contexts/ConversationContext";
import { apiStreamingService, StreamEvent } from "@/services/apiStreaming";
import { ArrowRight, Loader2 } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface SearchBarProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onSubmit: (query: string) => void;
  onNavigateToConversation?: (message: string) => void;
  onOrderGeneration?: (query: string) => void;
  onStreamingEvent?: (event: StreamEvent) => void;
  onStreamingStart?: () => void;
  onStreamingEnd?: (finalResponse?: string) => void;
  onStreamingError?: (error: Error) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({
  searchQuery,
  setSearchQuery,
  onSubmit,
  onNavigateToConversation,
  onOrderGeneration,
  onStreamingEvent,
  onStreamingStart,
  onStreamingEnd,
  onStreamingError,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const navigate = useNavigate();
  const conversation = useConversation();
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, 200) + "px";
    }
  }, [searchQuery]);

  // Auto-open advanced options if a system prompt already exists
  useEffect(() => {
    if (conversation.systemPrompt && conversation.systemPrompt.trim()) {
      setIsAdvancedOpen(true);
    }
    // We only want this to run on mount and when the prompt first appears
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const queryToUse = searchQuery.trim();

    if (!queryToUse) return;

    // Vider le champ de texte immédiatement
    setSearchQuery("");

    // Ajouter le message utilisateur au store
    conversation.addUserMessage(queryToUse);
    conversation.setIsStreaming(true);

    // Naviguer vers la page de conversation
    navigate("/dashboard");

    setIsProcessing(true);

    try {
      // Démarrer le streaming
      const options = {
        prompt: queryToUse,
        model: "claude-sonnet-4-20250514",
        max_turns: 30,
        session_id: conversation.sessionId || undefined, // Inclure le session_id s'il existe
        ...(conversation.systemPrompt.trim()
          ? { system_prompt: conversation.systemPrompt.trim() }
          : {}),
      } as const;

      await apiStreamingService.streamQuery(
        options,
        (event: StreamEvent) => {
          conversation.addStreamingEvent(event);
        },
        (finalResponse?: string, sessionId?: string) => {
          setIsProcessing(false);
          conversation.setIsStreaming(false);

          // Conserver le session_id reçu pour les prochaines requêtes
          if (sessionId) {
            conversation.setSessionId(sessionId);
            console.log("Session ID conservé dans le contexte:", sessionId);
          }

          if (finalResponse) {
            conversation.setFinalResponse(finalResponse);
            // Ajouter la réponse de l'assistant aux messages
            conversation.addAssistantMessage(finalResponse);
          }
        },
        (error: Error) => {
          setIsProcessing(false);
          conversation.setIsStreaming(false);

          // Ajouter l'erreur comme événement
          const errorEvent: StreamEvent = {
            id: Date.now().toString(),
            type: "log",
            timestamp: new Date().toISOString(),
            display: `❌ Erreur: ${error.message}`,
            data: { error: error.message },
          };
          conversation.addStreamingEvent(errorEvent);
        }
      );
    } catch (error) {
      setIsProcessing(false);
      conversation.setIsStreaming(false);

      const errorEvent: StreamEvent = {
        id: Date.now().toString(),
        type: "log",
        timestamp: new Date().toISOString(),
        display: `❌ Erreur: ${
          error instanceof Error ? error.message : "Erreur inconnue"
        }`,
        data: {
          error: error instanceof Error ? error.message : "Erreur inconnue",
        },
      };
      conversation.addStreamingEvent(errorEvent);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative mb-3">
      <div className={`relative transition-all duration-300`}>
        <textarea
          ref={textareaRef}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          placeholder='"What do I need to know about today across my data?"'
          className="w-full min-h-[3rem] max-h-[12.5rem] pl-4 pr-12 pt-3 pb-3 text-base bg-white dark:bg-[#303030] border-2 border-gray-200 dark:border-gray-700 rounded-2xl focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all duration-300 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white shadow-lg resize-none overflow-hidden"
          disabled={isProcessing}
          rows={1}
        />
        <button
          type="submit"
          className="absolute bottom-2 right-2 p-2 flex items-center group"
          disabled={isProcessing}
        >
          <div className="p-1.5 rounded-lg bg-primary text-white group-hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
            {isProcessing ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <ArrowRight className="h-4 w-4" />
            )}
          </div>
        </button>
      </div>

      {/* Collapsible advanced options: systemPrompt input */}
      <Collapsible
        open={isAdvancedOpen}
        onOpenChange={setIsAdvancedOpen}
        className="mt-2"
     >
        <CollapsibleTrigger
          type="button"
          className="text-sm text-gray-600 dark:text-gray-300 underline decoration-dotted hover:decoration-solid"
          disabled={isProcessing}
        >
          {isAdvancedOpen ? "Masquer les options avancées" : "Options avancées"}
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-2">
          <div className="rounded-xl border-2 border-gray-200 dark:border-gray-700 p-3 bg-white dark:bg-[#303030] shadow-sm">
            <Label htmlFor="system-prompt" className="text-gray-700 dark:text-gray-200">
              System Prompt (optionnel)
            </Label>
            <Input
              id="system-prompt"
              placeholder="Ajouter un system prompt pour guider l'assistant"
              value={conversation.systemPrompt}
              onChange={(e) => conversation.setSystemPrompt(e.target.value)}
              disabled={isProcessing}
              className="mt-2"
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Si laissé vide, le comportement reste inchangé. Si rempli, la clé
              "system_prompt" est envoyée dans le corps de la requête.
            </p>
          </div>
        </CollapsibleContent>
      </Collapsible>
      {isProcessing && (
        <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 text-center animate-pulse">
          Processing your request...
        </div>
      )}
    </form>
  );
};

export default SearchBar;
