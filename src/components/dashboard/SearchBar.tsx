
import React, { useState, useRef, useEffect } from 'react';
import { Search, ArrowRight, Loader2 } from 'lucide-react';

interface SearchBarProps {
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onSubmit: (query: string) => void;
  onOrderGeneration?: (query: string) => void;
}

const SearchBar = ({
  searchQuery,
  setSearchQuery,
  onSubmit,
  onOrderGeneration
}: SearchBarProps) => {
  const [isFocused, setIsFocused] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [searchQuery]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const queryToUse = searchQuery.trim() || "How can I help you today?";
    
    setIsProcessing(true);
    
    // Check if the query contains "order" keyword
    const containsOrder = queryToUse.toLowerCase().includes('order');
    
    // Simulate brief processing
    setTimeout(() => {
      setIsProcessing(false);
      
      if (containsOrder && onOrderGeneration) {
        onOrderGeneration(queryToUse);
      } else {
        onSubmit(queryToUse);
      }
    }, 800);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative mb-3">
      <div className={`relative transition-all duration-300 ${isFocused ? 'transform scale-105' : ''}`}>
        <textarea
          ref={textareaRef}
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
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
      {isProcessing && (
        <div className="mt-2 text-sm text-gray-600 dark:text-gray-400 text-center animate-pulse">
          Processing your request...
        </div>
      )}
    </form>
  );
};

export default SearchBar;
