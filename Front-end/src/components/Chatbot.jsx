import React, { useState } from 'react';
import { getChatResponse } from '../services/chatService'; 
import '../styles/aiChatbot.css';

const Chatbot = () => {
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false); // Trạng thái loading

  const handleMessageChange = (event) => {
    setMessage(event.target.value);
  };

  const handleSendMessage = async () => {
    if (!message) return;

    // Cập nhật lịch sử chat của người dùng
    setChatHistory(prev => [
      ...prev,
      { role: 'user', content: message }
    ]);
    setMessage('');
    setLoading(true); // Bật trạng thái loading

    try {
      // Gọi API để nhận phản hồi từ chatbot
      const reply = await getChatResponse(message);
  
      // Cập nhật kết quả mới lên màn hình
      setChatHistory(prev => [
        ...prev,
        { role: 'assistant', content: reply }
      ]);
    } catch (error) {
      console.error('Error:', error);
      setChatHistory(prev => [
        ...prev,
        { role: 'assistant', content: 'Xin lỗi, tôi không thể hiểu yêu cầu của bạn.' }
      ]);
    } finally {
      setLoading(false); // Tắt trạng thái loading khi có phản hồi
    }
  };

  return (
    <div className="chatbot-container">
      <div className="chatbot-header">Chatbot AI</div>

      <div className="chatbot-messages">
        {chatHistory.map((msg, index) => (
          <div key={index} className={`message ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {loading && <div className="message assistant">Đang xử lý...</div>} {/* Hiển thị khi loading */}
      </div>

      <div className="chatbot-input">
        <input
          type="text"
          value={message}
          onChange={handleMessageChange}
          placeholder="Nhập tin nhắn..."
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
        />
        <button onClick={handleSendMessage}>Gửi</button>
      </div>
    </div>
  );
};

export default Chatbot;
