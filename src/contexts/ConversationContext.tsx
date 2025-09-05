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
  addUserMessage: (userMessage: string) => void;
  addAssistantMessage: (content: string) => void;
  addStreamingEvent: (event: StreamEvent) => void;
  setIsStreaming: (streaming: boolean) => void;
  setFinalResponse: (response: string) => void;
  clearConversation: () => void;
}

const ConversationContext = createContext<ConversationContextType | undefined>(undefined);

export const useConversation = () => {
  const context = useContext(ConversationContext);
  if (!context) {
    throw new Error('useConversation must be used within a ConversationProvider');
  }
  return context;
};

interface ConversationProviderProps {
  children: ReactNode;
}

export const ConversationProvider: React.FC<ConversationProviderProps> = ({ children }) => {
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [streamingEvents, setStreamingEvents] = useState<StreamEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [finalResponse, setFinalResponse] = useState('');

  const addUserMessage = (userMessage: string) => {
    const userMsg: ConversationMessage = {
      id: Date.now().toString(),
      content: userMessage,
      role: 'user',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMsg]);
    // Ne pas réinitialiser les événements de streaming, juste les vider pour la nouvelle réponse
    setStreamingEvents([]);
    setFinalResponse('');
  };

  const addAssistantMessage = (content: string) => {
    const assistantMsg: ConversationMessage = {
      id: Date.now().toString(),
      content: content,
      role: 'assistant',
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, assistantMsg]);
  };

  const addStreamingEvent = (event: StreamEvent) => {
    setStreamingEvents(prev => [...prev, event]);
  };

  const clearConversation = () => {
    setMessages([]);
    setStreamingEvents([]);
    setFinalResponse('');
    setIsStreaming(false);
  };

  const value: ConversationContextType = {
    messages,
    streamingEvents,
    isStreaming,
    finalResponse,
    addUserMessage,
    addAssistantMessage,
    addStreamingEvent,
    setIsStreaming,
    setFinalResponse,
    clearConversation
  };

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
};
