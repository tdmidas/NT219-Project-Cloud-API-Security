import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from 'react-toastify';
import "react-toastify/dist/ReactToastify.css";
import "../styles/Uservoucher.css";
import axios from "axios";

const API_URL = import.meta.env.VITE_APP_API_URL || "http://localhost:8060/api";

const UserCard = ({ voucher, onClick }) => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [quantity, setQuantity] = useState(1);
  const [totalPrice, setTotalPrice] = useState(voucher.price);
  const navigate = useNavigate();
  const ownerUsername = voucher.ownerUsername;

  useEffect(() => {
    setTotalPrice(quantity * voucher.price);
  }, [quantity, voucher.price]);

  const processPayment = async (paymentTotal) => { // Add paymentTotal parameter
    setIsProcessing(true);
    try {
      const token = sessionStorage.getItem('accessToken'); if (!token) {
        toast.error("Vui lòng đăng nhập để mua voucher!", {
          style: {
            background: '#2196F3',
            color: 'white'
          }
        });
        navigate('/login');
        return;
      }

      const decodedToken = JSON.parse(atob(token.split('.')[1]));
      const userId = decodedToken.id;

      const response = await axios.post(
        `${API_URL}/payment/create`,
        {
          voucherData: {
            _id: voucher._id,
            title: voucher.title,
            price: paymentTotal, // Use paymentTotal instead of finalAmount
            quantity: quantity,
            ownerId: voucher.ownerId
          },
          userInfo: {
            userId: userId
          }
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );

      if (response.data.payUrl) {
        // Chuyển trực tiếp đến trang thanh toán
        window.location.href = response.data.payUrl;
      } else {
        toast.error("Không thể tạo liên kết thanh toán!", {
          style: {
            background: '#2196F3',
            color: 'white'
          }
        });
      }
    } catch (error) {
      toast.error("Có lỗi xảy ra: " + error.message, {
        style: {
          background: '#2196F3',
          color: 'white'
        }
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const showConfirmToast = () => {
    let currentQuantity = quantity;
    let currentTotal = totalPrice;

    const updateToast = () => {
      toast.update(confirmToastId, {
        render: renderToastContent(),
      });
    };

    const increaseQuantity = () => {
      if (currentQuantity < voucher.quantity) {
        currentQuantity++;
        currentTotal = currentQuantity * voucher.price;
        setQuantity(currentQuantity);
        setTotalPrice(currentTotal);
        updateToast();
      }
    };

    const decreaseQuantity = () => {
      if (currentQuantity > 1) {
        currentQuantity--;
        currentTotal = currentQuantity * voucher.price;
        setQuantity(currentQuantity);
        setTotalPrice(currentTotal);
        updateToast();
      }
    };

    const renderToastContent = () => (
      <div
        style={{
          padding: '12px',
          width: '100%',
          maxWidth: '420px',
          boxSizing: 'border-box',
          fontSize: '14px',
          lineHeight: '1.4'
        }}
      >
        <h4
          style={{
            marginBottom: '10px',
            fontWeight: '600',
            borderBottom: '1px solid #ddd',
            paddingBottom: '6px',
            fontSize: '16px'
          }}
        >
          Xác nhận mua voucher
        </h4>

        <div style={{ marginBottom: '10px' }}>
          <p><b>Tên:</b> {voucher.title}</p>
          <p><b>Người tạo:</b> {ownerUsername}</p>
          <p><b>Loại:</b> {voucher.voucherType}</p>
          {voucher.category && <p><b>Danh mục:</b> {voucher.category}</p>}
          <p><b>Bắt đầu:</b> {new Date(voucher.validityStart).toLocaleDateString()}</p>
          <p><b>Hạn:</b> {new Date(voucher.validityEnd).toLocaleDateString()}</p>
          <p><b>Tối thiểu:</b> {voucher.minSpend.toLocaleString()}đ</p>
          <p><b>Giá:</b> {voucher.price.toLocaleString()}đ</p>
          <p><b>Còn lại:</b> {voucher.quantity}</p>
        </div>

        <div
          style={{
            margin: '10px 0',
            padding: '10px',
            backgroundColor: '#f5f5f5',
            borderRadius: '6px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '8px'
          }}
        >
          <label><b>Số lượng:</b></label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <button onClick={decreaseQuantity} disabled={currentQuantity <= 1}>-</button>
            <span style={{ minWidth: '32px', textAlign: 'center' }}>{currentQuantity}</span>
            <button onClick={increaseQuantity} disabled={currentQuantity >= voucher.quantity}>+</button>
          </div>
        </div>

        <div
          style={{
            marginTop: '10px',
            padding: '10px',
            backgroundColor: '#fff3f3',
            borderRadius: '6px',
            textAlign: 'center'
          }}
        >
          <p style={{ fontSize: '16px', fontWeight: 'bold', color: '#e53935' }}>
            Tổng tiền: {currentTotal.toLocaleString()}đ
          </p>
        </div>

        <button
          onClick={() => {
            toast.dismiss(confirmToastId);
            processPayment(currentTotal);
          }}
          style={{
            backgroundColor: '#4CAF50',
            color: '#fff',
            border: 'none',
            padding: '10px',
            borderRadius: '4px',
            cursor: 'pointer',
            marginTop: '12px',
            width: '100%',
            fontSize: '15px'
          }}
        >
          Xác nhận mua
        </button>
      </div>
    );


    const confirmToastId = toast(renderToastContent(), {
      position: "top-center",
      autoClose: false,
      closeOnClick: false,
      draggable: false,
      closeButton: true,
      className: 'voucher-confirmation-toast'
      // Xóa onClose để không gọi processPayment 2 lần
    });
  };

  const isOwner = () => {
    const token = sessionStorage.getItem('accessToken');
    if (!token) return false;
    const decodedToken = JSON.parse(atob(token.split('.')[1]));
    return decodedToken.id === voucher.ownerId;
  };

  const handleEdit = (e) => {
    e.preventDefault();
    e.stopPropagation();
    navigate(`/edit-voucher/${voucher._id}`);
  };
  const handleToggleSelling = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      setIsProcessing(true);
      const response = await axios.patch(
        `${API_URL}/vouchers/toggle-status/${voucher._id}`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${sessionStorage.getItem('accessToken')}`
          }
        }
      );
      if (response.data.success) {
        toast.info(response.data.message, {
          style: {
            background: '#2196F3',
            color: 'white'
          }
        });
        // Đợi toast hiển thị 1 chút rồi mới reload
        setTimeout(() => {
          window.location.reload();
        }, 1000);
      } else {
        toast.error(response.data.message || "Có lỗi xảy ra khi thay đổi trạng thái", {
          style: {
            background: '#2196F3',
            color: 'white'
          }
        });
      }
    } catch (error) {
      toast.error(error.response?.data?.message || "Có lỗi xảy ra khi thay đổi trạng thái");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="user-card" onClick={onClick}>
      <div className="user-card-left">
        <h3 className="voucher-title">{voucher.title}</h3>
        {/* <p className="voucher-info"><b>Người tạo:</b> {ownerUsername}</p> */}
        <p className="voucher-info">
          <b>Người tạo:</b>{" "}
          <span onClick={(e) => {
            e.stopPropagation();
            navigate(`/profile/${voucher.ownerId}`);
          }}
            style={{
              color: "#1e88e5",
              cursor: "pointer",
              textDecoration: "underline"
            }}>
            {ownerUsername}
          </span>
        </p>
        <div style={{ whitespace: "nowrap" }}>
          <p className="voucher-info"><strong>Loại:</strong> {voucher.voucherType}</p>
          {voucher.category && <p className="voucher-info"><strong>Danh mục:</strong> {voucher.category}</p>}
          {/* <p className="voucher-info">Bắt đầu: {new Date(voucher.validityStart).toLocaleDateString()}</p> */}
          <p className="voucher-info"><strong>HSD: </strong>{new Date(voucher.validityEnd).toLocaleDateString()}</p>
        </div>
      </div>
      {/* <div className="divider">|</div> */}
      <div className="user-card-right">
        <p className="discount">Giảm <span className="discount-amount">{voucher.price}đ</span></p>
        <p className="min-spend">Đơn hàng tối thiểu: {voucher.minSpend}đ</p>
        <p className="quantity">Số lượng: {voucher.quantity}</p>
        <div className="button-container">
          {isOwner() ? (
            <>
              <button
                className="edit-button"
                onClick={handleEdit}
                style={{
                  marginRight: '10px',
                  padding: '8px 15px',
                  backgroundColor: '#2196F3',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Chỉnh sửa
              </button>
              <button
                className="toggle-button"
                onClick={handleToggleSelling} style={{
                  padding: '8px 15px',
                  backgroundColor: voucher.isPublic ? '#f44336' : '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  transition: 'all 0.3s ease',
                  minWidth: '100px',
                  transform: isProcessing ? 'scale(0.95)' : 'scale(1)',
                  opacity: isProcessing ? '0.8' : '1'
                }}
                disabled={isProcessing}
              >
                {voucher.isPublic ? 'Gỡ bán' : 'Đăng bán'}
              </button>
            </>
          ) : (
            <button
              className="buy-button"
              style={{ minWidth: '120px' }} // Đặt độ dài cố định cho nút
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                showConfirmToast();
              }}
              disabled={isProcessing || voucher.quantity <= 0}
            >
              {isProcessing ? "Đang xử lý..." : "Mua ngay"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserCard;
