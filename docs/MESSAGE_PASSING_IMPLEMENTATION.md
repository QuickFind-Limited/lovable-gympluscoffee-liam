# Message Passing Implementation

This document describes the implementation for passing messages from the homepage to the conversation interface.

## Overview

The solution enables users to enter a message on the homepage that will appear as the first message in the conversation interface. The implementation uses URL parameters to pass the message between pages while maintaining clean state management.

## Implementation Details

### 1. URL Parameter Approach

Messages are passed using the `message` URL parameter:
```
/dashboard?message=How%20can%20I%20improve%20inventory%20turnover
```

### 2. Components Modified

#### Dashboard Component (`src/pages/Dashboard.tsx`)
- Added URL parameter handling with `useSearchParams`
- Extracts and validates the `message` parameter on mount
- Automatically shows the ChatInterface when a message is present
- Clears the URL parameter after processing to prevent re-triggering

#### App Component (`src/App.tsx`)
- Added navigation utilities import
- Created `handleNavigateToConversation` function
- Passes the navigation handler to Dashboard component

#### ChatInterface Component (`src/components/dashboard/ChatInterface.tsx`)
- Enhanced to handle initial messages passed via props
- Modified localStorage loading to avoid conflicts with initial messages
- Automatically processes initial messages and generates appropriate responses
- Shows the message as the first user message in the conversation

### 3. Navigation Utilities (`src/utils/navigationUtils.ts`)

Created utility functions for consistent navigation:

- `navigateToConversation(navigate, message)`: Navigates to dashboard with message
- `navigateToOrderSummary(navigate, query)`: Navigates to order summary
- `extractMessageFromParams(searchParams)`: Safely extracts message from URL params

### 4. Error Handling

- Input validation (message length ≤ 1000 characters)
- URL decoding error handling
- Toast notifications for invalid parameters
- Graceful fallback when message parameter is malformed

## Usage Examples

### From Any Component
```typescript
import { useNavigate } from 'react-router-dom';
import { navigateToConversation } from '@/utils/navigationUtils';

const MyComponent = () => {
  const navigate = useNavigate();
  
  const handleSuggestionClick = (message: string) => {
    navigateToConversation(navigate, message);
  };
  
  return (
    <button onClick={() => handleSuggestionClick("Show me inventory status")}>
      Check Inventory
    </button>
  );
};
```

### Direct Navigation
```typescript
// Navigate with a message
navigate('/dashboard?message=' + encodeURIComponent('Help me create a forecast'));
```

## Flow Diagram

1. User enters message on homepage
2. `navigateToConversation()` called with message
3. User navigated to `/dashboard?message=encoded_message`
4. Dashboard component loads and detects URL parameter
5. Message extracted, validated, and passed to ChatInterface
6. URL parameter cleared to prevent re-triggering
7. ChatInterface displays message as first user message
8. Assistant response is generated based on message content

## Benefits

- **Clean separation of concerns**: Navigation logic separated from component logic
- **Type-safe**: Full TypeScript support with proper typing
- **Error resilient**: Handles malformed URLs and invalid parameters gracefully
- **Reusable**: Navigation utilities can be used throughout the application
- **User-friendly**: Natural flow from homepage prompt to conversation
- **No state pollution**: URL parameters are cleaned up after processing

## Security Considerations

- Message length validation (max 1000 characters)
- URL encoding/decoding handled safely
- Input sanitization before processing
- Error boundaries for malformed parameters

## Future Enhancements

- Support for initial message types (forecast, analysis, action)
- Pre-populate conversation context from homepage selections
- Integration with user preferences for default message handling
- Analytics tracking for homepage-to-conversation conversion rates