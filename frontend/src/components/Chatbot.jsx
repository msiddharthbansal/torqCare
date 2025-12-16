import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader } from 'lucide-react';
import api from '../services/api';

const Chatbot = ({ vehicleId }) => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I'm your TorqCare assistant for vehicle ${vehicleId}. I can help you with questions about your vehicle's health, maintenance, and any concerns you might have. How can I assist you today?`,
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Reset conversation when vehicle changes
  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content: `Hello! I'm your TorqCare assistant for vehicle ${vehicleId}. How can I help you today?`,
        timestamp: new Date()
      }
    ]);
  }, [vehicleId]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.sendChatMessage(vehicleId, input);
      
      const assistantMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      
      const errorMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again in a moment.',
        timestamp: new Date(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const quickQuestions = [
    "What's my current battery health?",
    "When is my next maintenance due?",
    "Are there any issues I should know about?",
    "How's my tire pressure?",
    "Explain my health score"
  ];

  const handleQuickQuestion = (question) => {
    setInput(question);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] animate-slideIn">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">TorqCare Assistant</h1>
        <p className="text-gray-300">Ask me anything about your vehicle {vehicleId}</p>
      </div>

      {/* Quick Questions */}
      {messages.length <= 1 && (
        <div className="mb-4">
          <p className="text-sm text-gray-400 mb-2">Quick questions:</p>
          <div className="flex flex-wrap gap-2">
            {quickQuestions.map((question, idx) => (
              <button
                key={idx}
                onClick={() => handleQuickQuestion(question)}
                className="text-sm bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 text-blue-300 px-3 py-2 rounded-lg transition-colors"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 bg-white/5 rounded-xl p-6 overflow-y-auto space-y-4 border border-white/20">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slideIn`}
          >
            {msg.role === 'assistant' && (
              <div className="bg-blue-500/20 rounded-full p-2 h-fit">
                <Bot className="text-blue-400" size={24} />
              </div>
            )}
            
            <div
              className={`max-w-[70%] rounded-2xl p-4 ${
                msg.role === 'user'
                  ? 'bg-blue-500 text-white'
                  : msg.isError
                  ? 'bg-red-500/20 text-red-200 border border-red-500/30'
                  : 'bg-white/10 text-gray-200 border border-white/20'
              }`}
            >
              <div className="whitespace-pre-wrap break-words">{msg.content}</div>
              <div className={`text-xs mt-2 ${msg.role === 'user' ? 'text-blue-100' : 'text-gray-400'}`}>
                {msg.timestamp.toLocaleTimeString()}
              </div>
            </div>

            {msg.role === 'user' && (
              <div className="bg-white/10 rounded-full p-2 h-fit">
                <User className="text-gray-300" size={24} />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start animate-slideIn">
            <div className="bg-blue-500/20 rounded-full p-2 h-fit">
              <Bot className="text-blue-400" size={24} />
            </div>
            <div className="bg-white/10 rounded-2xl p-4 border border-white/20">
              <div className="flex gap-2 items-center">
                <Loader className="animate-spin text-blue-400" size={16} />
                <span className="text-gray-300">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="mt-4 flex gap-3">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask me anything about your vehicle..."
          rows={1}
          className="flex-1 bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-blue-400 resize-none"
          style={{ minHeight: '52px', maxHeight: '150px' }}
        />
        <button
          onClick={sendMessage}
          disabled={!input.trim() || loading}
          className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-xl font-semibold transition-colors flex items-center gap-2"
        >
          <Send size={20} />
          Send
        </button>
      </div>

      {/* Tips */}
      <div className="mt-4 text-sm text-gray-400 text-center">
        💡 Tip: Ask about battery health, maintenance schedules, or any warning signs
      </div>
    </div>
  );
};

export default Chatbot;