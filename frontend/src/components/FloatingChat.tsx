import React, { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Loader2 } from "lucide-react";
import { sendChatMessage } from "../api/client";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  sources?: Array<{
    meeting_id: string;
    segment_type: string;
    text: string;
    similarity?: number;
  }>;
  used_rag?: boolean;
}

interface FloatingChatProps {
  context?: string; // Optional context about the current page/view
  projectId?: string; // Optional project ID for project-scoped RAG search
}

export function FloatingChat({ context, projectId }: FloatingChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Hello! I'm your AI assistant. How can I help you with your meetings today?",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (isOpen) {
      scrollToBottom();
      // Focus input when chat opens
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, messages]);

  const handleSend = async () => {
    const message = inputValue.trim();
    if (!message || isLoading) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: message,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      // Send to API with project context for RAG
      const response = await sendChatMessage(message, context, projectId);
      
      // Add assistant response with sources if available
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.response,
        timestamp: new Date(),
        sources: response.sources,
        used_rag: response.used_rag,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Sorry, I encountered an error: ${error?.message || "Unknown error"}. Please try again.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <style>{`
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes slideDown {
          from {
            opacity: 1;
            transform: translateY(0);
          }
          to {
            opacity: 0;
            transform: translateY(20px);
          }
        }
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        @keyframes pulse {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.7;
          }
        }
        .chat-container {
          animation: slideUp 0.3s ease-out;
        }
        .chat-container.closing {
          animation: slideDown 0.3s ease-out;
        }
      `}</style>

      {/* Floating Chat Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: "fixed",
          bottom: "1.5rem",
          right: "1.5rem",
          width: "3.5rem",
          height: "3.5rem",
          borderRadius: "50%",
          background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
          border: "none",
          boxShadow: "0 4px 20px rgba(59, 130, 246, 0.4), 0 2px 8px rgba(0, 0, 0, 0.1)",
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1000,
          transition: "transform 0.2s ease, box-shadow 0.2s ease",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "scale(1.1)";
          e.currentTarget.style.boxShadow = "0 6px 24px rgba(59, 130, 246, 0.5), 0 4px 12px rgba(0, 0, 0, 0.15)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "scale(1)";
          e.currentTarget.style.boxShadow = "0 4px 20px rgba(59, 130, 246, 0.4), 0 2px 8px rgba(0, 0, 0, 0.1)";
        }}
        aria-label={isOpen ? "Close chat" : "Open chat"}
      >
        {isOpen ? (
          <X style={{ width: "1.5rem", height: "1.5rem", color: "white" }} />
        ) : (
          <MessageCircle style={{ width: "1.5rem", height: "1.5rem", color: "white" }} />
        )}
      </button>

      {/* Chat Modal */}
      {isOpen && (
        <div
          className="chat-container"
          style={{
            position: "fixed",
            bottom: "6rem",
            right: "1.5rem",
            width: "24rem",
            maxWidth: "calc(100vw - 3rem)",
            height: "32rem",
            maxHeight: "calc(100vh - 8rem)",
            background: "white",
            borderRadius: "16px",
            boxShadow: "0 20px 60px rgba(0, 0, 0, 0.15), 0 8px 24px rgba(0, 0, 0, 0.1)",
            display: "flex",
            flexDirection: "column",
            zIndex: 999,
            border: "1px solid #e5e7eb",
            overflow: "hidden",
          }}
        >
          {/* Header */}
          <div
            style={{
              padding: "1rem 1.25rem",
              background: "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)",
              color: "white",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <div
                style={{
                  width: "2rem",
                  height: "2rem",
                  background: "rgba(255, 255, 255, 0.2)",
                  borderRadius: "8px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                <MessageCircle style={{ width: "1.25rem", height: "1.25rem", color: "white" }} />
              </div>
              <div>
                <div style={{ fontSize: "0.95rem", fontWeight: 600 }}>AI Assistant</div>
                <div style={{ fontSize: "0.75rem", opacity: 0.9 }}>
                  {projectId ? "Project-scoped RAG enabled" : "Ask me anything"}
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: "rgba(255, 255, 255, 0.2)",
                border: "none",
                borderRadius: "6px",
                width: "2rem",
                height: "2rem",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                transition: "background 0.2s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.3)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)";
              }}
            >
              <X style={{ width: "1rem", height: "1rem", color: "white" }} />
            </button>
          </div>

          {/* Messages */}
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "1rem",
              display: "flex",
              flexDirection: "column",
              gap: "0.75rem",
              background: "#fafafa",
            }}
          >
            {messages.map((message) => (
              <div
                key={message.id}
                style={{
                  display: "flex",
                  justifyContent: message.role === "user" ? "flex-end" : "flex-start",
                  animation: "slideUp 0.3s ease-out",
                }}
              >
                <div
                  style={{
                    maxWidth: "80%",
                    padding: "0.75rem 1rem",
                    borderRadius: "12px",
                    background: message.role === "user"
                      ? "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
                      : "white",
                    color: message.role === "user" ? "white" : "#111827",
                    fontSize: "0.875rem",
                    lineHeight: 1.5,
                    boxShadow: message.role === "user"
                      ? "0 2px 8px rgba(59, 130, 246, 0.3)"
                      : "0 1px 3px rgba(0, 0, 0, 0.1)",
                    border: message.role === "assistant" ? "1px solid #e5e7eb" : "none",
                  }}
                >
                  {message.content}
                  {message.sources && message.sources.length > 0 && (
                    <div style={{
                      marginTop: '0.75rem',
                      paddingTop: '0.75rem',
                      borderTop: message.role === 'assistant' ? '1px solid rgba(0, 0, 0, 0.1)' : '1px solid rgba(255, 255, 255, 0.2)',
                      fontSize: '0.75rem',
                      opacity: 0.8,
                    }}>
                      <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>
                        📚 Sources ({message.sources.length}):
                      </div>
                      {message.sources.map((source, idx) => (
                        <div
                          key={idx}
                          style={{
                            marginBottom: '0.5rem',
                            padding: '0.5rem',
                            background: message.role === 'assistant' ? 'rgba(0, 0, 0, 0.05)' : 'rgba(255, 255, 255, 0.1)',
                            borderRadius: '6px',
                            fontSize: '0.7rem',
                          }}
                        >
                          <div style={{ fontWeight: 500, marginBottom: '0.25rem' }}>
                            {source.segment_type.replace('_', ' ').toUpperCase()} • Meeting: {source.meeting_id.split('_')[0].replace(/-/g, ' ')}
                            {source.similarity && (
                              <span style={{ marginLeft: '0.5rem', opacity: 0.7 }}>
                                ({Math.round(source.similarity * 100)}% match)
                              </span>
                            )}
                          </div>
                          <div style={{ opacity: 0.8, fontStyle: 'italic' }}>
                            "{source.text}..."
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "flex-start",
                  animation: "slideUp 0.3s ease-out",
                }}
              >
                <div
                  style={{
                    padding: "0.75rem 1rem",
                    borderRadius: "12px",
                    background: "white",
                    border: "1px solid #e5e7eb",
                    display: "flex",
                    alignItems: "center",
                    gap: "0.5rem",
                  }}
                >
                  <Loader2
                    style={{
                      width: "1rem",
                      height: "1rem",
                      animation: "spin 1s linear infinite",
                      color: "#6b7280",
                    }}
                  />
                  <span style={{ fontSize: "0.875rem", color: "#6b7280" }}>Thinking...</span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div
            style={{
              padding: "1rem",
              background: "white",
              borderTop: "1px solid #e5e7eb",
            }}
          >
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                alignItems: "flex-end",
              }}
            >
              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                disabled={isLoading}
                style={{
                  flex: 1,
                  padding: "0.75rem",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  fontSize: "0.875rem",
                  fontFamily: "inherit",
                  resize: "none",
                  minHeight: "2.5rem",
                  maxHeight: "6rem",
                  outline: "none",
                  transition: "border-color 0.2s ease",
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = "#3b82f6";
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = "#e5e7eb";
                }}
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isLoading}
                style={{
                  padding: "0.75rem",
                  background: inputValue.trim() && !isLoading
                    ? "linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)"
                    : "#e5e7eb",
                  border: "none",
                  borderRadius: "8px",
                  cursor: inputValue.trim() && !isLoading ? "pointer" : "not-allowed",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "all 0.2s ease",
                  width: "2.5rem",
                  height: "2.5rem",
                }}
                onMouseEnter={(e) => {
                  if (inputValue.trim() && !isLoading) {
                    e.currentTarget.style.transform = "scale(1.05)";
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = "scale(1)";
                }}
              >
                {isLoading ? (
                  <Loader2
                    style={{
                      width: "1.25rem",
                      height: "1.25rem",
                      animation: "spin 1s linear infinite",
                      color: "#9ca3af",
                    }}
                  />
                ) : (
                  <Send
                    style={{
                      width: "1.25rem",
                      height: "1.25rem",
                      color: inputValue.trim() ? "white" : "#9ca3af",
                    }}
                  />
                )}
              </button>
            </div>
            <div
              style={{
                fontSize: "0.75rem",
                color: "#9ca3af",
                marginTop: "0.5rem",
                textAlign: "center",
              }}
            >
              Press Enter to send, Shift+Enter for new line
            </div>
          </div>
        </div>
      )}
    </>
  );
}

