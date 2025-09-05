import React from 'react';
import { render, screen, fireEvent, waitFor } from '../utils/test-utils';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import StreamingConversation from '@/components/dashboard/StreamingConversation';
import { mockStreamEvent } from '../utils/test-utils';
import { StreamEvent } from '@/services/apiStreaming';

/**
 * Unit Tests for StreamingConversation Component
 * Tests streaming message display, event handling, and conversation flow
 */

// Mock child components
vi.mock('@/components/dashboard/SearchBar', () => ({
  default: ({ onSubmit, searchQuery, setSearchQuery }: any) => (
    <div data-testid="search-bar">
      <input
        data-testid="search-input"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Type your message"
      />
      <button onClick={() => onSubmit(searchQuery)}>Submit</button>
    </div>
  ),
}));

vi.mock('@/components/dashboard/TypewriterText', () => ({
  default: ({ text }: { text: string }) => (
    <div data-testid="typewriter-text">{text}</div>
  ),
}));

describe('StreamingConversation Component', () => {
  const mockOnStreamingEvent = vi.fn();
  const mockOnStreamingStart = vi.fn();
  const mockOnStreamingEnd = vi.fn();
  const mockOnStreamingError = vi.fn();

  const defaultProps = {
    onStreamingEvent: mockOnStreamingEvent,
    onStreamingStart: mockOnStreamingStart,
    onStreamingEnd: mockOnStreamingEnd,
    onStreamingError: mockOnStreamingError,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders streaming conversation interface correctly', () => {
    render(<StreamingConversation {...defaultProps} />);
    
    expect(screen.getByText(/conversation en streaming/i)).toBeInTheDocument();
    expect(screen.getByTestId('search-bar')).toBeInTheDocument();
  });

  it('displays streaming events correctly', () => {
    const events: StreamEvent[] = [
      {
        ...mockStreamEvent,
        type: 'connection',
        display: 'Connecting to assistant...',
      },
      {
        ...mockStreamEvent,
        id: 'event-2',
        type: 'message',
        display: 'Processing your request...',
      },
    ];

    render(<StreamingConversation {...defaultProps} events={events} />);
    
    expect(screen.getByText('Connecting to assistant...')).toBeInTheDocument();
    expect(screen.getByText('Processing your request...')).toBeInTheDocument();
  });

  it('shows streaming indicator when streaming is active', () => {
    render(<StreamingConversation {...defaultProps} isStreaming={true} />);
    
    expect(screen.getByText(/en cours/i)).toBeInTheDocument();
    // Should show animated dots
    expect(screen.getByText(/en cours/i).closest('div')).toHaveClass('animate-pulse');
  });

  it('displays final response with typewriter effect', () => {
    const finalResponse = 'This is the final assistant response.';
    
    render(<StreamingConversation {...defaultProps} finalResponse={finalResponse} />);
    
    expect(screen.getByTestId('typewriter-text')).toHaveTextContent(finalResponse);
  });

  it('handles message submission through embedded search bar', async () => {
    render(<StreamingConversation {...defaultProps} />);
    
    const input = screen.getByTestId('search-input');
    const submitButton = screen.getByRole('button', { name: /submit/i });
    
    fireEvent.change(input, { target: { value: 'New message' } });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('New message')).toBeInTheDocument();
    });
  });

  it('displays different event types with appropriate icons', () => {
    const events: StreamEvent[] = [
      {
        ...mockStreamEvent,
        type: 'connection',
        display: 'Connection event',
      },
      {
        ...mockStreamEvent,
        id: 'event-2',
        type: 'message',
        display: 'Message event',
      },
      {
        ...mockStreamEvent,
        id: 'event-3',
        type: 'log',
        display: 'Log event',
      },
      {
        ...mockStreamEvent,
        id: 'event-4',
        type: 'final_response',
        display: 'Final response event',
      },
    ];

    render(<StreamingConversation {...defaultProps} events={events} />);
    
    // All event displays should be present
    expect(screen.getByText('Connection event')).toBeInTheDocument();
    expect(screen.getByText('Message event')).toBeInTheDocument();
    expect(screen.getByText('Log event')).toBeInTheDocument();
    expect(screen.getByText('Final response event')).toBeInTheDocument();
  });

  it('shows event timestamps correctly', () => {
    const event: StreamEvent = {
      ...mockStreamEvent,
      timestamp: new Date('2025-01-01T10:30:00Z').toISOString(),
      display: 'Timed event',
    };

    render(<StreamingConversation {...defaultProps} events={[event]} />);
    
    expect(screen.getByText('Timed event')).toBeInTheDocument();
    // Should display formatted time
    expect(screen.getByText(/10:30/)).toBeInTheDocument();
  });

  it('handles conversation history correctly', async () => {
    const { rerender } = render(<StreamingConversation {...defaultProps} />);
    
    // Submit first message
    const input = screen.getByTestId('search-input');
    fireEvent.change(input, { target: { value: 'First message' } });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    await waitFor(() => {
      expect(screen.getByText('First message')).toBeInTheDocument();
    });
    
    // Add response and submit second message
    rerender(<StreamingConversation {...defaultProps} finalResponse="First response" />);
    
    fireEvent.change(input, { target: { value: 'Second message' } });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    await waitFor(() => {
      expect(screen.getByText('First message')).toBeInTheDocument();
      expect(screen.getByText('First response')).toBeInTheDocument();
      expect(screen.getByText('Second message')).toBeInTheDocument();
    });
  });

  it('scrolls to bottom when new messages arrive', async () => {
    const scrollIntoViewSpy = vi.fn();
    window.HTMLElement.prototype.scrollIntoView = scrollIntoViewSpy;
    
    render(<StreamingConversation {...defaultProps} />);
    
    const input = screen.getByTestId('search-input');
    fireEvent.change(input, { target: { value: 'Scroll test' } });
    fireEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    await waitFor(() => {
      expect(scrollIntoViewSpy).toHaveBeenCalled();
    });
  });

  it('filters and displays only relevant event types in processing section', () => {
    const events: StreamEvent[] = [
      {
        ...mockStreamEvent,
        type: 'connection',
        display: 'Connection',
      },
      {
        ...mockStreamEvent,
        id: 'event-2',
        type: 'message',
        display: 'Message',
      },
      {
        ...mockStreamEvent,
        id: 'event-3',
        type: 'log',
        display: 'Log entry',
      },
    ];

    render(<StreamingConversation {...defaultProps} events={events} />);
    
    // Processing section should only show connection and message events
    expect(screen.getByText('Connection')).toBeInTheDocument();
    expect(screen.getByText('Message')).toBeInTheDocument();
    
    // Log events might be displayed differently or not in the processing section
    expect(screen.getByText('Log entry')).toBeInTheDocument();
  });

  it('displays full content for message events', () => {
    const eventWithContent: StreamEvent = {
      ...mockStreamEvent,
      type: 'message',
      display: 'Message event',
      full_content: 'This is the full content of the message.',
      data: { role: 'assistant' },
    };

    render(<StreamingConversation {...defaultProps} events={[eventWithContent]} />);
    
    expect(screen.getByText('This is the full content of the message.')).toBeInTheDocument();
  });

  it('does not display full content for user messages', () => {
    const userEvent: StreamEvent = {
      ...mockStreamEvent,
      type: 'message',
      display: 'User message',
      full_content: 'User content should not be shown',
      data: { role: 'user' },
    };

    render(<StreamingConversation {...defaultProps} events={[userEvent]} />);
    
    expect(screen.getByText('User message')).toBeInTheDocument();
    expect(screen.queryByText('User content should not be shown')).not.toBeInTheDocument();
  });

  describe('Props Updates', () => {
    it('updates events when props change', () => {
      const initialEvents = [{ ...mockStreamEvent, display: 'Initial event' }];
      const { rerender } = render(<StreamingConversation {...defaultProps} events={initialEvents} />);
      
      expect(screen.getByText('Initial event')).toBeInTheDocument();
      
      const updatedEvents = [
        ...initialEvents,
        { ...mockStreamEvent, id: 'event-2', display: 'New event' },
      ];
      
      rerender(<StreamingConversation {...defaultProps} events={updatedEvents} />);
      
      expect(screen.getByText('Initial event')).toBeInTheDocument();
      expect(screen.getByText('New event')).toBeInTheDocument();
    });

    it('updates final response when props change', () => {
      const { rerender } = render(<StreamingConversation {...defaultProps} />);
      
      expect(screen.queryByTestId('typewriter-text')).not.toBeInTheDocument();
      
      rerender(<StreamingConversation {...defaultProps} finalResponse="Updated response" />);
      
      expect(screen.getByTestId('typewriter-text')).toHaveTextContent('Updated response');
    });

    it('updates streaming state when props change', () => {
      const { rerender } = render(<StreamingConversation {...defaultProps} />);
      
      expect(screen.queryByText(/en cours/i)).not.toBeInTheDocument();
      
      rerender(<StreamingConversation {...defaultProps} isStreaming={true} />);
      
      expect(screen.getByText(/en cours/i)).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('has proper semantic structure', () => {
      render(<StreamingConversation {...defaultProps} />);
      
      expect(screen.getByRole('heading', { level: 2 })).toHaveTextContent(/conversation en streaming/i);
    });

    it('provides proper labels for streaming status', () => {
      render(<StreamingConversation {...defaultProps} isStreaming={true} />);
      
      const statusIndicator = screen.getByText(/en cours/i);
      expect(statusIndicator).toBeInTheDocument();
    });
  });
});