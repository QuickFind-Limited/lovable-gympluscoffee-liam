import { StreamEvent } from '@/services/apiStreaming';
import React, { createContext, ReactNode, useContext, useState } from 'react';

interface ConversationMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

interface ConversationContextType {
  messages: ConversationMessage[];
  streamingEvents: StreamEvent[];
  isStreaming: boolean;
  finalResponse: string;
  sessionId: string | null;
  addUserMessage: (userMessage: string) => void;
  addAssistantMessage: (content: string) => void;
  addStreamingEvent: (event: StreamEvent) => void;
  setIsStreaming: (streaming: boolean) => void;
  setFinalResponse: (response: string) => void;
  setSessionId: (sessionId: string | null) => void;
  clearConversation: () => void;
}

const ConversationContext = createContext<ConversationContextType | undefined>(
  undefined
);

export const useConversation = () => {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error(
      "useConversation must be used within a ConversationProvider"
    );
  }
  return context;
};

interface ConversationProviderProps {
  children: ReactNode;
}

export const ConversationProvider: React.FC<ConversationProviderProps> = ({
  children,
}) => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [streamingEvents, setStreamingEvents] = useState<StreamEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [finalResponse, setFinalResponse] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);

  const addUserMessage = (userMessage: string) => {
    const userMsg: ConversationMessage = {
      id: Date.now().toString(),
      content: userMessage,
      role: "user",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    // Conserver les événements et fichiers précédents; ne pas vider
    // Garder également la dernière finalResponse pour référence
  };

  const addAssistantMessage = (content: string) => {
    const assistantMsg: ConversationMessage = {
      id: Date.now().toString(),
      content: content,
      role: "assistant",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMsg]);
  };

  const addStreamingEvent = (event: StreamEvent) => {
    setStreamingEvents((prev) => [...prev, event]);
  };

  const clearConversation = () => {
    setMessages([]);
    setStreamingEvents([]);
    setFinalResponse("");
    setIsStreaming(false);
    // Note: on ne remet pas le sessionId à null lors du clear pour le conserver entre les conversations
  };

  const value: ConversationContextType = {
    messages,
    streamingEvents,
    isStreaming,
    finalResponse,
    sessionId,
    addUserMessage,
    addAssistantMessage,
    addStreamingEvent,
    setIsStreaming,
    setFinalResponse,
    setSessionId,
    clearConversation,
  };

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
};
