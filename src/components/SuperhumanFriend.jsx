import { useState, useRef, useEffect } from 'react';
import { FiSend } from 'react-icons/fi';
import { FaRobot } from 'react-icons/fa';
import { BsPersonCircle } from 'react-icons/bs';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function SuperhumanFriend() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hello! How can I help you today?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const endOfMessagesRef = useRef(null);
  const abortControllerRef = useRef(null);
  const inputRef = useRef(null);  // Add input ref

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  useEffect(() => {
    // Keep focus on input field
    if (!isTyping) {
      inputRef.current?.focus();
    }
  }, [isTyping, messages]); // Re-run when typing status or messages change

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    // Add user message to chat
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    setStreamingMessage('');

    try {
      // Get conversation history excluding the initial greeting
      const conversationHistory = messages.slice(1);
      
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: input,
          history: [...conversationHistory, userMessage]
        }),
        signal: abortControllerRef.current.signal
      });

      const reader = res.body.getReader();
      let result = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = new TextDecoder().decode(value);
        result += chunk;
        setStreamingMessage(prev => prev + chunk);
      }

      setMessages(prev => [...prev, { role: 'assistant', content: result }]);
      setStreamingMessage('');
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Error: Could not connect to the AI API.'
      }]);
      setStreamingMessage('');
    } finally {
      setIsTyping(false);
      abortControllerRef.current = null;
      // Ensure input is focused after response
      setTimeout(() => {
        inputRef.current?.focus();
      }, 0);
    }
  };

  return (
    <div className="flex flex-col min-h-[calc(100vh-5rem)] bg-black pt-20">
      {/* Chat Container */}
      <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4 max-w-5xl mx-auto w-full">
        <div className="flex items-center space-x-2 mb-4">
          <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          <div className="bg-zinc-900/60 backdrop-blur-sm px-4 py-2 rounded-full">
            <span className="text-gray-400 text-sm">AI Assistant</span>
          </div>
        </div>
        
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex items-start space-x-3 ${
              message.role === 'user' ? 'flex-row-reverse space-x-reverse' : 'flex-row'
            } opacity-0 animate-slideIn`}
            style={{ animationDelay: `${index * 100}ms`, animationFillMode: 'forwards' }}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-6 py-4 ${
                message.role === 'user'
                  ? 'bg-green-600 text-white rounded-tr-none'
                  : 'bg-zinc-900/60 backdrop-blur-sm text-white rounded-tl-none'
              }`}
            >
              {message.role === 'assistant' ? (
                <div className="markdown-body prose prose-invert">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {message.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <p className="text-[15px] leading-relaxed">{message.content}</p>
              )}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex items-start space-x-3">
            <div className="max-w-[85%] rounded-2xl px-6 py-4 bg-zinc-900/60 backdrop-blur-sm text-white rounded-tl-none">
              {streamingMessage ? (
                <>
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {streamingMessage}
                  </ReactMarkdown>
                  <span className="inline-block w-2 h-4 ml-1 bg-green-400 animate-cursor"/>
                </>
              ) : (
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}/>
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}/>
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-bounce" style={{ animationDelay: '400ms' }}/>
                </div>
              )}
            </div>
          </div>
        )}
        <div ref={endOfMessagesRef} />
      </div>

      {/* Input Form */}
      <div className="border-t border-zinc-800/50">
        <form onSubmit={handleSubmit} className="max-w-5xl mx-auto px-6 py-4 flex space-x-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            ref={inputRef}  // Add ref to input
            autoFocus  // Add autoFocus
            placeholder="Type your message..."
            className="flex-1 bg-zinc-900/60 backdrop-blur-sm text-white rounded-lg px-4 py-3 focus:outline-none placeholder-gray-500 cursor-default"
            disabled={isTyping}
          />
          <button
            type="submit"
            className={`bg-green-600 text-white rounded-lg px-6 py-3 flex items-center justify-center transition-colors ${
              isTyping ? 'opacity-50 cursor-not-allowed' : 'hover:bg-green-500'
            }`}
            disabled={isTyping}
          >
            Send
            <FiSend className="ml-2" />
          </button>
        </form>
      </div>
    </div>
  );
}

export default SuperhumanFriend;