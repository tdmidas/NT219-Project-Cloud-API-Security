import React, { useEffect, useState } from 'react';
import '../styles/Notification.css';

const SuccessModal = ({ success, message, onClose }) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setTimeout(() => setVisible(true), 10);
    if (success) {
      const timer = setTimeout(() => {
        setVisible(false);
        setTimeout(onClose, 300); // Gọi hàm onClose sau khi animation kết thúc
      }, 800); // 3 giây

      return () => clearTimeout(timer); // Dọn dẹp timer khi component unmount
    }
  }, [success, onClose]);

  const handleClick = () => {
    setVisible(false);
    setTimeout(onClose, 300);
  };

  return (
    <div className="modal-wrapper">
      <div className={`modal-box modal-${success ? 'success' : 'error'} ${visible ? 'show' : ''}`}>
        <div className="modal-icon-container">
          <div className="modal-icon-background"></div>
          <div className="modal-icon">{success ? '✓' : '✕'}</div>
        </div>
        <div className="modal-message">{message}</div>
        {!success && (
          <button className="modal-btn" onClick={handleClick}>
            THỬ LẠI
          </button>
        )}
      </div>
    </div>
  );
};

export default SuccessModal;
