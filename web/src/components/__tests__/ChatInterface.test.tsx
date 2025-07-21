import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { describe, test, expect, beforeEach, vi } from 'vitest';
import ChatInterface from '../ChatInterface';

// Mock WebSocket
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  readyState = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(public url: string) {
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      if (this.onopen) {
        this.onopen(new Event('open'));
      }
    }, 100);
  }

  send(data: string) {
    // Mock sending data
    console.log('Mock WebSocket send:', data);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent('close'));
    }
  }
}

// Mock global WebSocket
(global as any).WebSocket = MockWebSocket;

describe('ChatInterface', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Mock scrollIntoView
    Element.prototype.scrollIntoView = vi.fn();
  });

  test('renders chat interface with initial elements', () => {
    render(<ChatInterface />);
    
    expect(screen.getByText('🤖 Personality Chat Assistant')).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Connecting/)).toBeInTheDocument();
    expect(screen.getByText('Send')).toBeInTheDocument();
    expect(screen.getByText('Clear Chat')).toBeInTheDocument();
  });

  test('shows connection status', async () => {
    render(<ChatInterface />);
    
    // Initially disconnected
    expect(screen.getByText('🔴 Disconnected')).toBeInTheDocument();
    
    // Should connect after a short delay
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });
  });

  test('disables input when disconnected', () => {
    render(<ChatInterface />);
    
    const input = screen.getByPlaceholderText(/Connecting/) as HTMLInputElement;
    const sendButton = screen.getByText('Send') as HTMLButtonElement;
    
    expect(input.disabled).toBe(true);
    expect(sendButton.disabled).toBe(true);
  });

  test('enables input when connected', async () => {
    render(<ChatInterface />);
    
    await waitFor(() => {
      const input = screen.getByPlaceholderText(/Type your message/) as HTMLInputElement;
      const sendButton = screen.getByText('Send') as HTMLButtonElement;
      
      expect(input.disabled).toBe(false);
      expect(sendButton.disabled).toBe(true); // Still disabled because input is empty
    }, { timeout: 200 });
  });

  test('enables send button when input has text', async () => {
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    const input = screen.getByPlaceholderText(/Type your message/);
    const sendButton = screen.getByText('Send') as HTMLButtonElement;
    
    fireEvent.change(input, { target: { value: 'Hello' } });
    
    expect(sendButton.disabled).toBe(false);
  });

  test('sends message when form is submitted', async () => {
    const mockSend = vi.fn();
    MockWebSocket.prototype.send = mockSend;
    
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    const input = screen.getByPlaceholderText(/Type your message/);
    const sendButton = screen.getByText('Send');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    expect(mockSend).toHaveBeenCalledWith(
      JSON.stringify({ message: 'Test message' })
    );
  });

  test('adds user message to chat when sent', async () => {
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    const input = screen.getByPlaceholderText(/Type your message/);
    
    fireEvent.change(input, { target: { value: 'Hello there' } });
    fireEvent.submit(input.closest('form')!);
    
    expect(screen.getByText('Hello there')).toBeInTheDocument();
  });

  test('clears input after sending message', async () => {
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    const input = screen.getByPlaceholderText(/Type your message/) as HTMLInputElement;
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.submit(input.closest('form')!);
    
    expect(input.value).toBe('');
  });

  test('handles incoming WebSocket messages', async () => {
    let mockWebSocket: MockWebSocket;
    const originalWebSocket = (global as any).WebSocket;
    
    (global as any).WebSocket = function(url: string) {
      mockWebSocket = new MockWebSocket(url);
      return mockWebSocket;
    };
    
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    // Simulate receiving a message
    const mockMessage = {
      type: 'assistant',
      message: 'Hello! How can I help you?',
      timestamp: new Date().toISOString(),
      suggestions: ['Option 1', 'Option 2']
    };

    if (mockWebSocket!.onmessage) {
      mockWebSocket!.onmessage(new MessageEvent('message', {
        data: JSON.stringify(mockMessage)
      }));
    }

    await waitFor(() => {
      expect(screen.getByText('Hello! How can I help you?')).toBeInTheDocument();
      expect(screen.getByText('Option 1')).toBeInTheDocument();
      expect(screen.getByText('Option 2')).toBeInTheDocument();
    });

    // Restore original WebSocket
    (global as any).WebSocket = originalWebSocket;
  });

  test('shows typing indicator', async () => {
    let mockWebSocket: MockWebSocket;
    const originalWebSocket = (global as any).WebSocket;
    
    (global as any).WebSocket = function(url: string) {
      mockWebSocket = new MockWebSocket(url);
      return mockWebSocket;
    };
    
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    // Simulate typing indicator
    const typingMessage = {
      type: 'typing',
      message: 'Processing your request...',
      timestamp: new Date().toISOString()
    };

    if (mockWebSocket!.onmessage) {
      mockWebSocket!.onmessage(new MessageEvent('message', {
        data: JSON.stringify(typingMessage)
      }));
    }

    await waitFor(() => {
      expect(screen.getByText('Assistant is typing...')).toBeInTheDocument();
    });

    // Restore original WebSocket
    (global as any).WebSocket = originalWebSocket;
  });

  test('handles suggestion button clicks', async () => {
    const mockSend = vi.fn();
    let mockWebSocket: MockWebSocket;
    const originalWebSocket = (global as any).WebSocket;
    
    (global as any).WebSocket = function(url: string) {
      mockWebSocket = new MockWebSocket(url);
      mockWebSocket.send = mockSend;
      return mockWebSocket;
    };
    
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    // Add a message with suggestions
    const mockMessage = {
      type: 'assistant',
      message: 'What would you like?',
      timestamp: new Date().toISOString(),
      suggestions: ['Option A', 'Option B']
    };

    if (mockWebSocket!.onmessage) {
      mockWebSocket!.onmessage(new MessageEvent('message', {
        data: JSON.stringify(mockMessage)
      }));
    }

    await waitFor(() => {
      expect(screen.getByText('Option A')).toBeInTheDocument();
    });

    // Click suggestion
    fireEvent.click(screen.getByText('Option A'));

    expect(mockSend).toHaveBeenCalledWith(
      JSON.stringify({ message: 'Option A' })
    );

    // Restore original WebSocket
    (global as any).WebSocket = originalWebSocket;
  });

  test('calls onPersonalityConfigured when personality is configured', async () => {
    const mockCallback = vi.fn();
    let mockWebSocket: MockWebSocket;
    const originalWebSocket = (global as any).WebSocket;
    
    (global as any).WebSocket = function(url: string) {
      mockWebSocket = new MockWebSocket(url);
      return mockWebSocket;
    };
    
    render(<ChatInterface onPersonalityConfigured={mockCallback} />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    // Simulate success message
    const successMessage = {
      type: 'success',
      message: 'Personality configured!',
      timestamp: new Date().toISOString(),
      config_id: 'test-config-123',
      profile: { name: 'Test Personality', type: 'fictional' }
    };

    if (mockWebSocket!.onmessage) {
      mockWebSocket!.onmessage(new MessageEvent('message', {
        data: JSON.stringify(successMessage)
      }));
    }

    await waitFor(() => {
      expect(mockCallback).toHaveBeenCalledWith({
        id: 'test-config-123',
        profile: { name: 'Test Personality', type: 'fictional' }
      });
    });

    // Restore original WebSocket
    (global as any).WebSocket = originalWebSocket;
  });

  test('clears chat when clear button is clicked', async () => {
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    // Add a message first
    const input = screen.getByPlaceholderText(/Type your message/);
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.submit(input.closest('form')!);
    
    expect(screen.getByText('Test message')).toBeInTheDocument();
    
    // Clear chat
    fireEvent.click(screen.getByText('Clear Chat'));
    
    // Message should be gone
    expect(screen.queryByText('Test message')).not.toBeInTheDocument();
  });

  test('handles Enter key to send message', async () => {
    const mockSend = vi.fn();
    MockWebSocket.prototype.send = mockSend;
    
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    const input = screen.getByPlaceholderText(/Type your message/);
    
    fireEvent.change(input, { target: { value: 'Enter key test' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter' });
    
    expect(mockSend).toHaveBeenCalledWith(
      JSON.stringify({ message: 'Enter key test' })
    );
  });

  test('does not send message on Shift+Enter', async () => {
    const mockSend = vi.fn();
    MockWebSocket.prototype.send = mockSend;
    
    render(<ChatInterface />);
    
    await waitFor(() => {
      expect(screen.getByText('🟢 Connected')).toBeInTheDocument();
    }, { timeout: 200 });

    const input = screen.getByPlaceholderText(/Type your message/);
    
    fireEvent.change(input, { target: { value: 'Shift enter test' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', shiftKey: true });
    
    expect(mockSend).not.toHaveBeenCalled();
  });
});