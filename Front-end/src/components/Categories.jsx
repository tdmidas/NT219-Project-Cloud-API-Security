import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getAllVouchers } from "../services/voucherService";
import { useAuth } from "../context/AuthContext";
import { FaShoppingCart } from "react-icons/fa";
import { addToCart } from "../services/voucherService";

const Categories = () => {
  const [vouchers, setVouchers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { user } = useAuth();

  useEffect(() => {
    const fetchVouchers = async () => {
      try {
        const data = await getAllVouchers();
        setVouchers(data);
        setLoading(false);
      } catch (err) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchVouchers();
  }, []);

  const handleAddToCart = async (voucherId) => {
    try {
      await addToCart(voucherId);
      alert("Đã thêm vào giỏ hàng!");
    } catch (error) {
      alert(error.message);
    }
  };

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Danh sách Voucher</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {vouchers.map((voucher) => (
          <div
            key={voucher._id}
            className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300"
          >
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-2">{voucher.name}</h2>
              <p className="text-gray-600 mb-4">{voucher.description}</p>
              <div className="flex justify-between items-center mb-4">
                <span className="text-lg font-bold text-blue-600">
                  {voucher.price.toLocaleString("vi-VN")} VNĐ
                </span>
                <span className="text-sm text-gray-500">
                  Còn lại: {voucher.quantity}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <Link
                  to={`/voucher/${voucher._id}`}
                  className="text-blue-600 hover:text-blue-800"
                >
                  Xem chi tiết
                </Link>
                {user && (
                  <button
                    onClick={() => handleAddToCart(voucher._id)}
                    className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors duration-300"
                  >
                    <FaShoppingCart />
                    Mua ngay
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Categories; 