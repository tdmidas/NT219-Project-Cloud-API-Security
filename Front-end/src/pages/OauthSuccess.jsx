import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import SuccessModal from "../components/LoginModal"; 

function OauthSuccess() {
    const navigate = useNavigate();
    const [modalData, setModalData] = useState({
      show: false,
      success: true,
      message: "",
    });
  
    useEffect(() => {
      const params = new URLSearchParams(window.location.search);
      const accessToken = params.get("token");
      const username = params.get("username");
  
      if (accessToken) {
        sessionStorage.setItem("accessToken", accessToken);
        sessionStorage.setItem("username", username);
        setModalData({
          show: true,
          success: true,
          message: "🎉 Đăng nhập thành công!",
        });
      } else {
        setModalData({
          show: true,
          success: false,
          message: "❌ Đăng nhập thất bại!",
        });
      }
    }, []);
  
    const handleCloseModal = () => {
      setModalData((prev) => ({ ...prev, show: false }));
      if (modalData.success) {
        navigate("/");
      } else {
        navigate("/login"); // Chuyển hướng về trang đăng nhập nếu thất bại
      }
    };
  
    return (
      <div>
        {modalData.show && (
          <SuccessModal
            message={modalData.message}
            onClose={handleCloseModal}
            success={modalData.success}
          />
        )}
      </div>
    );
  }
  
  export default OauthSuccess;