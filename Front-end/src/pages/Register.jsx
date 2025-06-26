import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom"; // Import useNavigate
import "../styles/Login.css"; // Sử dụng chung CSS với Login
import { register } from "../services/authService";
import SuccessModal from "../components/LoginModal";

function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [modalData, setModalData] = useState({
    show: false,
    success: true,
    message: "",
  });

  const navigate = useNavigate(); // Khởi tạo useNavigate

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Kiểm tra độ dài username
    if (username.length < 6) {
      setModalData({
        show: true,
        success: false,
        message: "Tên người dùng phải có ít nhất 6 ký tự! ❌",
      });
      setUsername(""); // Xóa dữ liệu trong ô nhập username
      return;
    }

    // Kiểm tra mật khẩu
    const passwordRegex = /^(?=.*[0-9])(?=.*[!@#$%^&*])(?=.*[a-zA-Z])[a-zA-Z0-9!@#$%^&*]{8,}$/;
    if (!passwordRegex.test(password)) {
      setModalData({
        show: true,
        success: false,
        message: "Mật khẩu phải có ít nhất 8 ký tự, bao gồm số và ký tự đặc biệt! ❌",
      });
      setPassword(""); // Xóa dữ liệu trong ô nhập mật khẩu
      setConfirmPassword("");
      return;
    }

    if (password !== confirmPassword) {
      setModalData({
        show: true,
        success: false,
        message: "Mật khẩu không khớp! ❌",
      });
      setPassword("");
      setConfirmPassword("");
      return;
    }

    setLoading(true);

    // Set a timeout to handle hanging requests
    const timeoutId = setTimeout(() => {
      if (loading) {
        setLoading(false);
        setModalData({
          show: true,
          success: false,
          message: "Đăng ký mất quá nhiều thời gian. Vui lòng thử lại sau.",
        });
      }
    }, 15000); // 15 second timeout

    try {
      console.log("Sending registration request...");
      const data = await register(username, email, password);
      clearTimeout(timeoutId);

      if (data.success) {
        setModalData({
          show: true,
          success: true,
          message: data.message,
        });
      } else {
        setModalData({
          show: true,
          success: false,
          message: data.message || "Đăng ký thất bại. Vui lòng thử lại.",
        });
        setUsername("");
        setEmail("");
        setPassword("");
        setConfirmPassword("");
      }
    } catch (error) {
      clearTimeout(timeoutId);
      console.error("Registration error:", error);

      if (error.response && error.response.data) {
        setModalData({
          show: true,
          success: false,
          message: error.response.data.message || "Lỗi từ máy chủ.",
        });
      } else if (error.request) {
        // Request was made but no response received (network error)
        setModalData({
          show: true,
          success: false,
          message: "Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối mạng.",
        });
      } else {
        // Error setting up the request
        setModalData({
          show: true,
          success: false,
          message: "Đã xảy ra lỗi. Vui lòng thử lại sau.",
        });
      }

      setUsername("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  const handleCloseModal = () => {
    setModalData((prev) => ({ ...prev, show: false }));
    if (modalData.success) {
      navigate("/login");
    }
  };

  return (
    <div className="login-page">
      {modalData.show && (
        <SuccessModal
          success={modalData.success}
          message={modalData.message}
          onClose={handleCloseModal}
        />
      )}

      <div className="login-box">
        <h1>Register</h1>

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
              <i className="fas fa-envelope"></i>
            </span>
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="input-wrapper">
            <span className="icon">
              <i className="fas fa-lock"></i>
            </span>
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="input-wrapper">
            <span className="icon">
              <i className="fas fa-lock"></i>
            </span>
            <input
              type="password"
              placeholder="Confirm Password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <button
            type="submit"
            className={`login-btn ${loading ? "loading" : ""}`}
          >
            {loading ? "Processing..." : "Register"}
          </button>
        </form>
        <br></br>
        <div className="register-link">
          Already have an account? <Link to="/login">Login here</Link>
        </div>
      </div>
    </div>
  );
}

export default Register;