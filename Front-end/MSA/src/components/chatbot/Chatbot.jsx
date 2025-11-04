import { useState, useRef, useEffect } from 'react';
import './Chatbot.css';

const Chatbot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Hello! I'm your Mine Safety AI Assistant. I can help you analyze previous accidents, detect patterns, and provide safety insights. How can I assist you today?",
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  const quickActions = [
    { id: 1, text: "Recent accident patterns", icon: "📊" },
    { id: 2, text: "Safety recommendations", icon: "⚠️" },
    { id: 3, text: "Risk assessment", icon: "🔍" },
    { id: 4, text: "Equipment status", icon: "⚙️" }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (messageText = inputValue) => {
    if (!messageText.trim()) return;

    const userMessage = {
      id: messages.length + 1,
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response (replace with actual API call)
    setTimeout(() => {
      const botResponse = {
        id: messages.length + 2,
        text: generateResponse(messageText),
        sender: 'bot',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const generateResponse = (query) => {
    // This is a placeholder. Replace with actual API integration
    const responses = {
      pattern: "Based on analysis of 150+ incidents, the most common patterns include: equipment failure during shift changes (23%), inadequate ventilation (18%), and human error during high-pressure operations (15%).",
      safety: "Key safety recommendations: 1) Implement real-time monitoring systems, 2) Conduct bi-weekly safety drills, 3) Upgrade ventilation in sectors B and C, 4) Mandatory equipment checks before each shift.",
      risk: "Current risk assessment shows: High risk in Zone A-3 (ventilation concerns), Medium risk in Zone B-1 (aging equipment), Low risk in Zone C-2. Immediate action recommended for Zone A-3.",
      equipment: "Equipment status overview: 87% operational, 8% under maintenance, 5% flagged for replacement. Critical alerts: Drill #4 requires immediate inspection, Ventilation system #2 showing irregular patterns."
    };

    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('pattern') || lowerQuery.includes('accident')) {
      return responses.pattern;
    } else if (lowerQuery.includes('safety') || lowerQuery.includes('recommend')) {
      return responses.safety;
    } else if (lowerQuery.includes('risk') || lowerQuery.includes('assess')) {
      return responses.risk;
    } else if (lowerQuery.includes('equipment') || lowerQuery.includes('status')) {
      return responses.equipment;
    }
    return "I'm analyzing your query using our AI-powered safety intelligence system. Could you please provide more specific details about incidents, safety concerns, or risk assessments you'd like to explore?";
  };

  const handleQuickAction = (text) => {
    handleSendMessage(text);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <>
      {/* Chatbot Toggle Button */}
      <button 
        className={`chatbot-toggle ${isOpen ? 'open' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle chatbot"
      >
        {isOpen ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
        )}
      </button>

      {/* Chatbot Window */}
      <div className={`chatbot-container ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div className="chatbot-header">
          <div className="header-content">
            <div className="header-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
              </svg>
            </div>
            <div className="header-info">
              <h3>Mine Safety AI</h3>
              <span className="status">
                <span className="status-dot"></span>
                Online & Monitoring
              </span>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="chatbot-messages">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message ${message.sender === 'user' ? 'user-message' : 'bot-message'}`}
            >
              {message.sender === 'bot' && (
                <div className="message-avatar bot-avatar">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M12 16v-4"></path>
                    <path d="M12 8h.01"></path>
                  </svg>
                </div>
              )}
              <div className="message-content">
                <p>{message.text}</p>
                <span className="message-time">
                  {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
              {message.sender === 'user' && (
                <div className="message-avatar user-avatar">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                    <circle cx="12" cy="7" r="4"></circle>
                  </svg>
                </div>
              )}
            </div>
          ))}
          
          {isTyping && (
            <div className="message bot-message">
              <div className="message-avatar bot-avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M12 16v-4"></path>
                  <path d="M12 8h.01"></path>
                </svg>
              </div>
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          {quickActions.map((action) => (
            <button
              key={action.id}
              className="quick-action-btn"
              onClick={() => handleQuickAction(action.text)}
            >
              <span className="action-icon">{action.icon}</span>
              <span className="action-text">{action.text}</span>
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div className="chatbot-input">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about safety insights, patterns, or recommendations..."
            rows="1"
          />
          <button 
            className="send-btn"
            onClick={() => handleSendMessage()}
            disabled={!inputValue.trim()}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </>
  );
};

export default Chatbot;
