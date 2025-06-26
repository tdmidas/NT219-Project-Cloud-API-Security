// src/components/Footer.jsx
import React from "react";
import "../styles/Footer.css";

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container">
        {/* Logo và mô tả */}
        <div className="footer-about">
          <h2 className="footer-logo">VouX</h2>
          <p className="footer-description">
            Nền tảng chia sẻ và trao đổi voucher hàng đầu Việt Nam.
            Hỗ trợ bạn tìm kiếm ưu đãi tốt nhất mỗi ngày!
          </p>
        </div>

        {/* Các link hữu ích */}
        <div className="footer-links">
          <h3>Liên kết nhanh</h3>
          <ul>
            <li><a href="/contact">Liên hệ</a></li>
            <li><a href="/policy">Chính sách</a></li>
            <li><a href="/guide">Hướng dẫn sử dụng</a></li>
            <li><a href="/faq">Câu hỏi thường gặp</a></li>
          </ul>
        </div>

        {/* Mạng xã hội */}
        <div className="footer-social">
          <h3>Kết nối với chúng tôi</h3>
          <div className="social-icons">
            <a href="https://facebook.com/voux" aria-label="Facebook" target="_blank" rel="noopener noreferrer">
              <i className="fab fa-facebook-f"></i>
            </a>
            <a href="https://twitter.com/voux" aria-label="Twitter" target="_blank" rel="noopener noreferrer">
              <i className="fab fa-twitter"></i>
            </a>
            <a href="https://instagram.com/voux" aria-label="Instagram" target="_blank" rel="noopener noreferrer">
              <i className="fab fa-instagram"></i>
            </a>
            <a href="https://linkedin.com/company/voux" aria-label="LinkedIn" target="_blank" rel="noopener noreferrer">
              <i className="fab fa-linkedin-in"></i>
            </a>
          </div>
        </div>
      </div>

      <div className="footer-bottom">
        <p>© 2025 VouX. Bản quyền thuộc về VouX.</p>
      </div>
    </footer>
  );
}

export default Footer;
