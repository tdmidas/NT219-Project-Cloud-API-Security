import React, { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import '../styles/PaymentStatus.css';

const PaymentStatus = () => {
  const [status, setStatus] = useState('loading');
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  useEffect(() => {
    const pathStatus = window.location.pathname.split('/')[2]; // Lấy status từ URL
    if (pathStatus === 'pending') {
      setStatus('pending');
    } else if (pathStatus === 'success') { // Sửa từ 'completed' thành 'success'
      setStatus('completed');
      setTimeout(() => navigate('/cart'), 3000);
    } else if (pathStatus === 'canceled') {
      setStatus('canceled');
    } else if (pathStatus === 'timeout') {
      setStatus('timeout');
    } else {
      setStatus('failed');
    }
  }, [searchParams, navigate]);

  const getStatusContent = () => {
    switch(status) {
      case 'loading':
        return {
          icon: '⌛',
          title: 'Đang xử lý thanh toán...',
          message: 'Vui lòng đợi trong giây lát'
        };
      case 'completed':
        return {
          icon: '✅',
          title: 'Thanh toán thành công!',
          message: 'Voucher đã được thêm vào tài khoản của bạn. Bạn sẽ được chuyển về trang chủ trong 3 giây.'
        };
      case 'canceled':
        return {
          icon: '❌',
          title: 'Đã hủy thanh toán',
          message: 'Bạn đã hủy giao dịch này'
        };
      case 'timeout':
        return {
          icon: '⏰',
          title: 'Giao dịch hết hạn',
          message: 'Đã quá thời gian thanh toán'
        };
      case 'pending':
        return {
          icon: '⌛',
          title: 'Đang chờ thanh toán',
          message: 'Vui lòng hoàn tất thanh toán trong cửa sổ MoMo'
        };
    }
  };

  const content = getStatusContent();

  return (
    <div className="payment-status-container">
      <div className="status-card">
        <div className={`status-icon ${status}`}>{content.icon}</div>
        <h2 className="status-title">{content.title}</h2>
        <p className="status-message">{content.message}</p>
        {status !== 'loading' && status !== 'success' && status !== 'pending' && (
          <button className="status-button" onClick={() => navigate('/')}>
            Về trang chủ
          </button>
        )}
      </div>
    </div>
  );
};

export default PaymentStatus;
