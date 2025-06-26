import React from "react";
import { useNavigate } from "react-router-dom";
import { createVoucher } from "../services/voucherService";
import "../styles/CreateV.css";
import Toast from "./toast";

const CreateV = () => {
    const [toast, setToast] = React.useState({ message: "", type: "info" });

    const [formData, setFormData] = React.useState({
        title: "",
        voucherType: "", 
        category: "",
        validityStart: "",
        validityEnd: "",
        price: 0,
        quantity: 1,
        minSpend: 0,
    });

    const navigate = useNavigate();
    const [error, setError] = React.useState("");

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            if(formData.validityStart > formData.validityEnd){
                setToast({ message: "Ngày bắt đầu không thể lớn hơn ngày kết thúc!", type: "error" });
                return;
            } else if(new Date(formData.validityStart).getTime() < Date.now()){
                setToast({ message: "Ngày bắt đầu không thể nhỏ hơn ngày hiện tại!", type: "error" });
                return;
            }
            const response = await createVoucher(formData);
            if (response.success) {
                setToast({ message: "Tạo voucher thành công!", type: "success" });
            } else {
                setToast({ message: response.message || "Có lỗi xảy ra khi tạo voucher!", type: "error" });
            }
        } catch (error) {
            console.error("Lỗi khi tạo voucher:", error);
            if (error.response?.status === 403) {
                setToast({ message: "Đăng nhập để tạo voucher!", type: "error" });
            } else {
                setToast({ message: error.response?.data?.message || "Có lỗi xảy ra khi tạo voucher!", type: "error" });
            }
        }
    };


    return (
        <div>
        <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast({ message: "" })}
            duration={2000}
        />
        {error && <p style={{ color: "red" }}>{error}</p>}
        <form className="voucher-form" onSubmit={handleSubmit}>
            <h2 className="form-title">Tạo Voucher</h2>
            <div className="form-group">
                <input name="title" placeholder="Tên voucher" onChange={handleChange} required />
                <input name="voucherType" placeholder="Loại voucher" onChange={handleChange} required />
            </div>
            <div className="form-group">
                {/* <input name="category" placeholder="Danh mục" onChange={handleChange} /> */}
                <select name="category" placeholder="Danh mục" onChange={handleChange} required>
                    <option value="">--Chọn danh mục--</option>
                    <option value={"clothes"}>Thời trang</option>
                    <option value={"food"}>Thực phẩm</option>
                    <option value={"electronics"}>Điện tử</option>
                    <option value={"home"}>Nhà cửa</option>
                    <option value={"travel"}>Du lịch</option>
                    <option value={"health"}>Sức khỏe</option>
                    <option value={"sports"}>Thể thao</option>
                    <option value={"beauty"}>Làm đẹp</option>
                    <option value={"books"}>Sách</option>
                    <option value={"toys"}>Đồ chơi</option>
                    <option value={"gifts"}>Quà tặng</option>
                    <option value={"pets"}>Thú cưng</option>
                    <option value={"furniture"}>Nội thất</option>
                    <option value={"automotive"}>Ô tô</option>
                    <option value={"accessories"}>Phụ kiện</option>
                    <option value={"stationery"}>Văn phòng phẩm</option>
                    <option value={"baby"}>Trẻ em</option>
                    <option value={"garden"}>Vườn</option>
                    <option value={"music"}>Âm nhạc</option>
                    <option value={"movies"}>Phim ảnh</option>
                    <option value={"games"}>Trò chơi</option>
                    <option value={"software"}>Phần mềm</option>
                    <option value={"services"}>Dịch vụ</option>
                    <option value={"others"}>Khác</option>
                </select>
                <input type="number" name="price" placeholder="Giá" onChange={handleChange} />
            </div>
            <div className="form-group">
                <input type="date" name="validityStart" onChange={handleChange} required />
                <input type="date" name="validityEnd" onChange={handleChange} required />
            </div>
            <div className="form-group">
                <input type="number" name="quantity" placeholder="Số lượng" onChange={handleChange} />
                <input type="number" name="minSpend" placeholder="Số tiền tối thiểu" onChange={handleChange} />
            </div>
            <button className="submit-btn" type="submit">Tạo</button>
        </form>
        </div>
      );
};

export default CreateV;

