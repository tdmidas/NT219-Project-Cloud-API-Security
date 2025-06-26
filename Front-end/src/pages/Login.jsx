import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  login,
  handleGoogleLogin,
  handleFacebookLogin,
  extractUserData,
} from "../services/authService";
import SuccessModal from "../components/LoginModal"; // Import modal
import "../styles/Login.css";
import { useAuth } from "../contexts/AuthContext";

function Login({ initializeSession, setToast }) {
  const [loading, setLoading] = useState(false);
  const [fadeIn, setFadeIn] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [modalData, setModalData] = useState({
    show: false,
    success: true,
    message: "",
  });

  const navigate = useNavigate();
  const { login: authLogin } = useAuth();

  useEffect(() => {
    setFadeIn(true);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const data = await login(username, password, rememberMe);
      setLoading(false);

      if (data.success) {
        // Lưu access token vào localStorage (thay vì sessionStorage)
        localStorage.setItem("accessToken", data.access_token);

        console.log("🚀 Login successful, initializing session...", data);
        console.log("💾 Access token saved to localStorage");
        console.log("🍪 Refresh token should be set as HTTP-only cookie by server");

        // Update global auth state FIRST using helper function
        const userData = extractUserData(data);

        if (userData) {
          authLogin(userData);
          console.log("✅ Auth context updated with user data");
        } else {
          console.error("❌ Failed to extract user data from login response");
        }

        // Khởi tạo session management TRƯỚC khi hiển thị modal
        if (initializeSession) {
          try {
            initializeSession(data);
            console.log("✅ Session manager initialized successfully");
          } catch (error) {
            console.error("❌ Session manager initialization failed:", error);
          }
        } else {
          console.warn("⚠️ initializeSession function not provided");
        }

        // Hiển thị session warning nếu có
        let loginMessage = "🎉 Đăng nhập thành công!";
        if (data.session_warning) {
          loginMessage += `\n${data.session_warning}`;
        }

        // Hiển thị toast với thông tin session
        if (setToast) {
          setToast({
            message: `✅ Đăng nhập thành công! Phiên làm việc: ${data.expires_in || 30} giây`,
            type: "success"
          });
        }

        setModalData({
          show: true,
          success: true,
          message: loginMessage,
        });

      } else {
        setModalData({
          show: true,
          success: false,
          message: data.message,
        });
      }
    } catch (error) {
      setLoading(false);
      setModalData({
        show: true,
        success: false,
        message: "⚠️ Lỗi kết nối đến server!",
      });
      console.error(error);
    }
  };

  const handleCloseModal = () => {
    setModalData((prev) => ({ ...prev, show: false }));
    if (modalData.success) {
      // Delay navigation để đảm bảo auth context đã được update
      setTimeout(() => {
        navigate("/");
        // Không reload toàn bộ trang để auth context không bị mất
      }, 100);
    }
  };

  return (
    <div className={`login-page ${fadeIn ? "fade-in" : ""}`}>
      {modalData.show && (
        <SuccessModal
          success={modalData.success}
          message={modalData.message}
          onClose={handleCloseModal}
        />
      )}

      <div className="login-box">
        <h1>Login</h1>

        <form onSubmit={handleSubmit}>
          <div className="input-wrapper">
            <span className="icon">
              <i className="fas fa-user"></i>
            </span>
            <input
              type="text"
              placeholder="User name"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="input-wrapper">
            <span className="icon">
              <i className="fas fa-lock"></i>
            </span>
            <input
              type="password"
              placeholder="••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <div className="options">
            <label className="remember">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
              />
              Remember me
            </label>
            <Link to="#" className="forgot">Forgot Password?</Link>
          </div>

          <button type="submit" className={`login-btn ${loading ? "loading" : ""}`}>
            {loading ? "Processing..." : "Login"}
          </button>
        </form>

        <div className="or-divider">
          <span>or</span>
        </div>

        <div className="social-buttons">
          <button className="facebook-btn" onClick={handleFacebookLogin}>
            <i className="fab fa-facebook-f"></i> Facebook
          </button>
          <button className="google-btn" onClick={handleGoogleLogin}>
            <i className="fab fa-google"></i> Google
          </button>
        </div>

        <div className="register-link">
          Don't have an account? <Link to="/register">Register here</Link>
        </div>
      </div>
    </div>
  );
}

export default Login;
