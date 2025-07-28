# Frontend Directory

This directory is prepared for you to add your own frontend application. The backend is already configured to work with any frontend framework through its REST API.

## Supported Frontend Frameworks

You can add any frontend framework here. Popular options include:

- **Next.js** (React-based)
- **Vue.js** with Nuxt
- **Angular**
- **Svelte/SvelteKit**
- **Vanilla JavaScript**
- **React** (Create React App or Vite)

## Frontend Integration Guide

This directory is prepared for frontend integration with the Ollama LLM API backend.

### Architecture Overview

The backend provides a clean REST API that can be consumed by any frontend framework:
- **React** - Modern component-based UI
- **Vue.js** - Progressive framework
- **Svelte** - Compile-time optimized
- **Next.js** - Full-stack React framework
- **Vanilla JS** - Simple HTML/CSS/JS

### API Contract

The backend exposes the following endpoints:

#### Core Endpoints
- `GET /` - API information and available endpoints
- `GET /health` - Health check status
- `POST /generate` - Generate text (supports streaming)
- `POST /ask` - Ask conversational questions
- `GET /models` - List available models

#### Request/Response Types
All types are defined in `/shared/types.py` and can be converted to TypeScript:

```typescript
// Example TypeScript interfaces (convert from Python types)
interface GenerateRequest {
  prompt: string;
  model?: string;
  temperature?: number;
  stream?: boolean;
}

interface GenerateResponse {
  response: string;
  model: string;
  done: boolean;
}
```

### Frontend Implementation Examples

#### React Example
```jsx
import { useState } from 'react';

function ChatInterface() {
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const res = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: message,
        temperature: 0.7
      })
    });
    
    const data = await res.json();
    setResponse(data.answer);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input 
        value={message} 
        onChange={(e) => setMessage(e.target.value)}
        placeholder="Ask a question..."
      />
      <button type="submit">Send</button>
      {response && <div>{response}</div>}
    </form>
  );
}
```

#### Vanilla JavaScript Example
```javascript
// Simple chat interface
async function askQuestion(question) {
  const response = await fetch('http://localhost:8000/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question: question,
      temperature: 0.7
    })
  });
  
  const data = await response.json();
  return data.answer;
}

// Streaming example
async function generateWithStreaming(prompt) {
  const response = await fetch('http://localhost:8000/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt: prompt,
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.chunk) {
          console.log(data.chunk); // Handle streaming chunk
        }
      }
    }
  }
}
```

### Environment Configuration

Create a `.env` file in your frontend project:

```env
REACT_APP_API_URL=http://localhost:8000
# or
VITE_API_URL=http://localhost:8000
# or
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### CORS Configuration

The backend is configured to allow CORS from all origins by default. For production, update the `CORS_ORIGINS` environment variable in the backend.

### Database Integration (Future)

When database functionality is implemented, additional endpoints will be available:

- `GET /chat/history` - Retrieve chat history
- `POST /documents/search` - Vector similarity search

### Getting Started

1. **Choose your frontend framework**
2. **Install dependencies** (axios, fetch, etc.)
3. **Configure API base URL** in environment variables
4. **Import shared types** (convert from Python to TypeScript if needed)
5. **Implement API calls** using the examples above
6. **Handle errors** and loading states appropriately

### Best Practices

- **Error Handling**: Always handle API errors gracefully
- **Loading States**: Show loading indicators for async operations
- **Streaming**: Use Server-Sent Events for streaming responses
- **Type Safety**: Use TypeScript for better development experience
- **Environment Variables**: Never hardcode API URLs

### Example Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.jsx
│   │   ├── ModelSelector.jsx
│   │   └── StreamingText.jsx
│   ├── services/
│   │   └── api.js
│   ├── types/
│   │   └── api.ts
│   └── App.jsx
├── public/
├── package.json
└── .env
```

## Getting Started

### 1. Choose Your Framework

Create your frontend application in this directory:

```bash
# Example with Next.js
npx create-next-app@latest . --typescript --tailwind --eslint

# Example with Vue/Nuxt
npx nuxi@latest init .

# Example with React + Vite
npm create vite@latest . -- --template react-ts

# Example with Angular
ng new . --routing --style=css
```

### 2. Configure API Connection

The backend API is available at:
- **Development**: `http://localhost:8080`
- **Docker**: `http://backend:8000` (internal network)

### 3. Available API Endpoints

Your frontend can interact with these backend endpoints:

```typescript
// Health check
GET /health

// List available models
GET /models

// Simple chat interface
POST /ask
{
  "message": "Your question here",
  "model": "llama3.2:1b" // optional
}

// Advanced text generation
POST /generate
{
  "prompt": "Your prompt here",
  "model": "llama3.2:1b", // optional
  "stream": false, // optional
  "options": {
    "temperature": 0.7,
    "max_tokens": 100
  }
}
```

### 4. TypeScript Types

Use the shared types from `../shared/types.ts`:

```typescript
import { AskRequest, AskResponse, GenerateRequest, GenerateResponse } from '../shared/types';

// Example API call
const response = await fetch('/api/backend/ask', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    message: "Hello, AI!"
  } as AskRequest)
});

const data: AskResponse = await response.json();
```

### 5. Docker Integration

Once you've created your frontend, update the `frontend.yml` Docker Compose configuration:

```yaml
services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    environment:
      - BACKEND_URL=${BACKEND_URL:-http://backend:8000}
    depends_on:
      - backend
    networks:
      - llm-network
```

### 6. Example Frontend Implementation

Here's a simple HTML example to get you started:

```html
<!DOCTYPE html>
<html>
<head>
    <title>LLM Chat</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        #chat { border: 1px solid #ccc; height: 400px; overflow-y: scroll; padding: 10px; margin: 10px 0; }
        input[type="text"] { width: 70%; padding: 10px; }
        button { padding: 10px 20px; }
    </style>
</head>
<body>
    <h1>LLM Chat Interface</h1>
    <div id="chat"></div>
    <input type="text" id="messageInput" placeholder="Type your message...">
    <button onclick="sendMessage()">Send</button>

    <script>
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const chat = document.getElementById('chat');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            chat.innerHTML += `<div><strong>You:</strong> ${message}</div>`;
            input.value = '';
            
            try {
                const response = await fetch('/api/backend/ask', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message })
                });
                
                const data = await response.json();
                chat.innerHTML += `<div><strong>AI:</strong> ${data.response}</div>`;
                chat.scrollTop = chat.scrollHeight;
            } catch (error) {
                chat.innerHTML += `<div style="color: red;"><strong>Error:</strong> ${error.message}</div>`;
            }
        }
        
        // Allow Enter key to send message
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
```

## Environment Variables

Configure these in your `.env` file:

```bash
# Frontend configuration
FRONTEND_PORT=3000
FRONTEND_DEV_PORT=3001
BACKEND_URL=http://backend:8000
NODE_ENV=production
```

## Next Steps

1. Choose and implement your preferred frontend framework
2. Create appropriate Dockerfile(s) for your frontend
3. Update `frontend.yml` with your specific build configuration
4. Test the integration with `docker-compose up`

The backend is ready to serve your frontend - just build what works best for your use case!
