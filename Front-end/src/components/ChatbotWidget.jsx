import { useState } from 'react';
import './ChatbotWidget.css'; 

const ChatbotWidget = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="chatbot-widget">
      {isOpen && (
        <div className="chatbot-popup">
          <div className="chatbot-header">
            <span>Chatbot AI 🤖</span>
            <button onClick={() => setIsOpen(false)}>✖</button>
          </div>
          {/* Gọi component chatbot của bạn ở đây */}
          <iframe src="/chatbot" title="Chatbot" className="chatbot-frame" />
        </div>
      )}

      {/* Nút mở chatbot */}
      {!isOpen && (
        <button className="chatbot-button" onClick={() => setIsOpen(true)}>
          💬
        </button>
      )}
    </div>
  );
};

export default ChatbotWidget;
