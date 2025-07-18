import { useState, useRef, useEffect } from 'react';
import { FiSend, FiUpload, FiFile, FiX } from 'react-icons/fi';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function RagAI() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const endOfMessagesRef = useRef(null);
  const abortControllerRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Add cleanup on unmount only, not on window unload
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      // Only cleanup when component unmounts
      if (sessionId) {
        fetch(`http://localhost:8000/api/rag/cleanup/${sessionId}`, {
          method: 'DELETE'
        }).catch(console.error);
      }
    };
  }, [sessionId]);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = Array.from(e.dataTransfer.files);
    handleFiles(files);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    handleFiles(files);
  };

  const handleFiles = async (files) => {
    if (files.length === 0) return;

    // Only accept PDF files
    const pdfFile = files[0];
    if (!pdfFile.type.includes('pdf') && !pdfFile.name.endsWith('.pdf')) {
      alert('Please upload PDF files only');
      return;
    }

    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append('file', pdfFile);
      if (sessionId) {
        formData.append('session_id', sessionId);
      }

      const response = await fetch('http://localhost:8000/api/rag/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText);
      }

      const data = await response.json();
      console.log('Upload response:', data);
      
      // Store session and file IDs
      setSessionId(data.session_id);
      setFileId(data.file_id);
      setUploadedFiles([{ name: pdfFile.name, id: data.file_id }]);
      
      // Add initial message
      setMessages([{
        role: 'assistant',
        content: 'I\'ve processed your document. What would you like to know about it?'
      }]);
    } catch (error) {
      console.error('Upload error:', error);
      alert('Failed to upload file. Please try again.');
      // Clear state on error
      setSessionId(null);
      setFileId(null);
      setUploadedFiles([]);
      setMessages([]);
    } finally {
      setIsProcessing(false);
    }
  };

  const removeFile = async () => {
    // Clear all state
    setUploadedFiles([]);
    setMessages([]);
    setFileId(null);
    setSessionId(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isTyping || !fileId || !sessionId) {
      console.error('Missing required data:', { fileId, sessionId });
      return;
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    setStreamingMessage('');

    try {
      console.log('Sending request with:', { sessionId, fileId }); // Debug log
      const res = await fetch('http://localhost:8000/api/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: input,
          session_id: sessionId,
          file_id: fileId,
          history: messages.slice(1)
        }),
        signal: abortControllerRef.current.signal
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(errorText);
      }

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
      console.error('Query error:', err);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.message}`
      }]);
      setStreamingMessage('');
    } finally {
      setIsTyping(false);
      abortControllerRef.current = null;
    }
  };

  return (
    <div className="flex flex-col min-h-[calc(100vh-5rem)] bg-black pt-20">
      {uploadedFiles.length === 0 ? (
        // File Upload Interface
        <div className="flex-1 flex items-center justify-center p-6">
          <div
            className={`w-full max-w-2xl border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
              isDragging 
                ? 'border-green-500 bg-green-500/10' 
                : 'border-zinc-700 hover:border-zinc-500'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              className="hidden"
              accept=".pdf"
            />
            {isProcessing ? (
              <div className="space-y-4">
                <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto"/>
                <p className="text-white">Processing document...</p>
              </div>
            ) : (
              <>
                <FiUpload className="w-12 h-12 mx-auto mb-4 text-zinc-500" />
                <h3 className="text-xl font-medium text-white mb-2">
                  Drop your PDF here
                </h3>
                <p className="text-zinc-400 mb-6">
                  Upload a PDF document to start analyzing
                </p>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="px-6 py-3 bg-zinc-800 rounded-lg text-white hover:bg-zinc-700 transition-colors"
                >
                  Select File
                </button>
              </>
            )}
          </div>
        </div>
      ) : (
        // Chat Interface
        <>
          <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4 max-w-5xl mx-auto w-full">
            {/* File List */}
            <div className="bg-zinc-900/40 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-white text-sm font-medium">Current Document:</h3>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="text-xs text-green-400 hover:text-green-300"
                >
                  Change Document
                </button>
              </div>
              <ul className="space-y-2">
                {uploadedFiles.map((file, index) => (
                  <li key={file.id} className="flex items-center justify-between bg-zinc-800/50 rounded-lg px-3 py-2">
                    <div className="flex items-center space-x-2">
                      <FiFile className="text-zinc-400" />
                      <span className="text-gray-300 text-sm truncate">{file.name}</span>
                    </div>
                    <button
                      onClick={() => removeFile()}
                      className="text-zinc-500 hover:text-zinc-300"
                    >
                      <FiX />
                    </button>
                  </li>
                ))}
              </ul>
            </div>

            {/* Messages */}
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
                placeholder="Ask about your document..."
                className="flex-1 bg-zinc-900/60 backdrop-blur-sm text-white rounded-lg px-4 py-3 focus:outline-none placeholder-gray-500"
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
        </>
      )}
    </div>
  );
}

export default RagAI; 