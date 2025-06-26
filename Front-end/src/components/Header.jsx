import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import logo from "../assets/logo.png";
import "../styles/Header.css";
import UserMenu from "./Usermenu";
import { secureLogout } from "../services/authService";
import { useAuth } from "../contexts/AuthContext";

function Header() {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  // Use authentication context
  const { isAuthenticated, user, loading, logout: authLogout } = useAuth();

  // Handle login button click
  const handleLoginClick = () => {
    navigate("/login");
  };

  // Handle register button click
  const handleRegisterClick = () => {
    navigate("/register");
  };

  // Secure logout function
  const handleLogout = async () => {
    try {
      console.log('Logging out user...');

      await secureLogout();

      // Clear auth context
      authLogout();

      // Navigate to home
      navigate("/");
    } catch (error) {
      console.error("Logout error:", error);
      // Force clear state even if logout fails
      authLogout();
      navigate("/");
    }
  };

  return (
    <header className="header">
      <div className="logo">
        <img
          src={logo}
          alt="VouX Logo"
          className="logo-img"
          style={{ cursor: "pointer" }}
          onClick={() => {
            window.location.href = "/";
          }}
        />
      </div>
      <div className="hamburger" onClick={() => setMenuOpen(!menuOpen)}>
        ☰
      </div>
      <nav className={`nav-menu ${menuOpen ? "open" : ""}`}>
        <Link to="/userVoucher" className="menu-btn">Mua bán</Link>
        <Link to="/deals" className="discount-btn">Ưu đãi hot</Link>
        <Link to="/chatbot" className="chatbot-btn">Chatbot</Link>
        <Link to="/create-voucher" className="create-voucher-btn">Tạo voucher</Link>
        <Link to="/cart" className="cart-btn">🛒 Giỏ hàng</Link>
        {!loading && !isAuthenticated && (
          <>
            <button
              onClick={handleLoginClick}
              className="login-btn"
            >
              🔐 Đăng nhập
            </button>
            <button
              onClick={handleRegisterClick}
              className="register-btn"
            >
              📝 Đăng ký
            </button>
          </>
        )}
      </nav>

      {!loading && isAuthenticated && user && (
        <div className="header-user-menu">
          <UserMenu
            name={user.username}
            onLogout={handleLogout}
            authType="Traditional"
          />
        </div>
      )}
    </header>
  );
}

export default Header;