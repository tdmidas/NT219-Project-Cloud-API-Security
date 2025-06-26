import React, { useEffect, useState } from "react";
import { authRequest } from "../services/authService";
import { getUserVouchers } from "../services/voucherService";
import "../styles/Cart.css";
import UserCard from "../components/Uservoucher";
import VoucherList from "../components/Voucherlist";
import { getUserVouchersByUsername } from "../services/voucherService";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

const API_URL = import.meta.env.VITE_APP_API_URL || "http://localhost:8060/api";

function Cart(props) {
  const [cartItems, setCartItems] = useState([]);
  const [ownedVouchers, setOwnedVouchers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('owned');
  const [columns, setColumns] = useState(3); // Số cột mặc định
  const navigate = useNavigate();
  useEffect(() => {
    const fetchCart = async () => {
      try {
        const response = await authRequest({
          url: "/cart",
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        });
        setCartItems(response.data.cart.vouchers || []);
      } catch (error) {
        console.error("Lỗi khi tải giỏ hàng:", error);
        if (error.response?.status === 401) {
          // Token hết hạn, thử refresh token
          try {
            const refreshToken = sessionStorage.getItem('refreshToken');
            if (!refreshToken) {
              throw new Error('No refresh token');
            }

            // Gọi API refresh token
            const response = await axios.post(`${API_URL}/auth/refresh`,
              { refreshToken },
              {
                headers: { 'Content-Type': 'application/json' }
              }
            );

            if (response.data.accessToken) {
              // Lưu token mới
              sessionStorage.setItem('accessToken', response.data.accessToken);
              if (response.data.refreshToken) {
                sessionStorage.setItem('refreshToken', response.data.refreshToken);
              }

              // Thử fetch lại giỏ hàng
              const cartResponse = await authRequest({
                url: "/cart",
                method: "GET"
              });

              setCartItems(cartResponse.data.cart.vouchers || []);

              // Thông báo cho user
              toast.success("Phiên đăng nhập đã được làm mới");
            }
          } catch (refreshError) {
            console.error("Lỗi khi làm mới token:", refreshError);
            // Xóa token cũ
            sessionStorage.clear();
            // Thông báo cho user
            toast.error("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại!");
            // Chuyển về trang login
            navigate('/login');
          }
        }
      }
    };

    const fetchOwnedVouchers = async () => {
      try {
        const response = await getUserVouchersByUsername();
        setOwnedVouchers(response.data || []);
      } catch (error) {
        console.error("Lỗi khi tải voucher sở hữu:", error);
        if (error.response?.status === 401) {
          // Xử lý tương tự như fetchCart
          try {
            const refreshToken = sessionStorage.getItem('refreshToken');
            if (!refreshToken) {
              throw new Error('No refresh token');
            }
            const response = await axios.post(`${API_URL}/auth/refresh`, {
              refreshToken
            });
            if (response.data.accessToken) {
              sessionStorage.setItem('accessToken', response.data.accessToken);
              // Thử fetch lại vouchers
              const vouchersResponse = await getUserVouchersByUsername();
              setOwnedVouchers(vouchersResponse.data || []);
            }
          } catch (refreshError) {
            sessionStorage.clear();
            navigate('/login');
          }
        }
      } finally {
        setLoading(false);
      }
    };

    fetchCart();
    fetchOwnedVouchers();
  }, []);

  useEffect(() => {
    const updateColumns = () => {
      if (window.innerWidth <= 768) {
        setColumns(1);
      } else {
        setColumns(3);
      }
    };

    updateColumns();
    window.addEventListener("resize", updateColumns);

    return () => window.removeEventListener("resize", updateColumns);
  }, []);

  if (loading) return <p>Đang tải giỏ hàng...</p>;

  // Phân loại voucher
  const savedFreeVouchers = cartItems.filter(v => !v.isFree);

  return (
    <div className="cart-page">
      <h2>Giỏ hàng của tôi</h2>

      <div className="cart-tabs" style={{ margin: '20px 0' }}>
        <button
          onClick={() => setActiveTab('owned')}
          style={{
            padding: '10px 20px',
            marginRight: '10px',
            backgroundColor: activeTab === 'owned' ? '#4CAF50' : '#f1f1f1',
            border: 'none',
            borderRadius: '4px',
            color: activeTab === 'owned' ? 'white' : 'black',
            cursor: 'pointer'
          }}
        >
          Voucher sở hữu
        </button>
        <button
          onClick={() => setActiveTab('free')}
          style={{
            padding: '10px 10px',
            backgroundColor: activeTab === 'free' ? '#4CAF50' : '#f1f1f1',
            border: 'none',
            borderRadius: '4px',
            color: activeTab === 'free' ? 'white' : 'black',
            cursor: 'pointer'
          }}
        >
          Voucher miễn phí đã lưu
        </button>
      </div>

      <div className="cart-content">
        {activeTab === 'owned' ? (
          <div className="voucher-grid" style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${columns}, 1fr)`,
            gap: '20px'
          }}>
            {ownedVouchers.map((voucher) => (
              <UserCard
                key={voucher._id || voucher.id}
                voucher={voucher}
              />
            ))}
          </div>
        ) : (
          <div>
            <VoucherList
              vouchersData={savedFreeVouchers}
              isCartDisplay={true}
              setToast={props.setToast}
            />
          </div>
        )}
      </div>
    </div>
  );
}

export default Cart;
