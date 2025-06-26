import React, { useState, useEffect, useRef } from "react";
import { getAllVouchers } from "../services/voucherService";
import VoucherCard from "./VoucherCard";
import "../styles/Voucherlist.css";

// Thêm prop vouchersData để có thể sử dụng lại component
function VoucherList({ vouchersData = null, isCartDisplay = false, setToast }) {
  const [vouchers, setVouchers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [visibleCount, setVisibleCount] = useState(10);
  const [expandedIdx, setExpandedIdx] = useState(null);
  const [cardPos, setCardPos] = useState({ top: 0, left: 0, width: 0 });
  const containerRef = useRef(null);

  console.log("VoucherList render - State:", {
    vouchersLength: vouchers.length,
    loading,
    error,
    vouchersData: !!vouchersData
  });

  useEffect(() => {
    // Nếu có dữ liệu truyền vào, sử dụng luôn
    if (vouchersData) {
      setVouchers(vouchersData);
      setLoading(false);
      return;
    }

    // Nếu không có dữ liệu, fetch từ API
    const fetchVouchers = async () => {
      try {
        // getAllVouchers đã được sửa để trả về array vouchers trực tiếp
        const vouchers = await getAllVouchers();
        console.log("✅ Fetched vouchers:", vouchers);
        console.log("📊 Voucher count:", vouchers?.length || 0);

        if (Array.isArray(vouchers)) {
          console.log("✅ Setting vouchers from array, length:", vouchers.length);
          if (vouchers.length > 0) {
            console.log("📄 First voucher sample:", vouchers[0]);
          }
          setVouchers(vouchers);
        } else {
          console.error("❌ Invalid data structure - not an array:", vouchers);
          setError("Dữ liệu không hợp lệ - không phải là mảng");
        }
      } catch (err) {
        console.error("❌ Error fetching vouchers:", err);
        setError(err.message || "Không thể tải voucher");
      } finally {
        setLoading(false);
      }
    };

    fetchVouchers();
  }, [vouchersData]);

  useEffect(() => {
    setVisibleCount(10);
  }, [vouchersData]);

  if (loading) {
    console.log("Showing loading state");
    return <div className="loading">Đang tải voucher...</div>;
  }

  if (error) {
    console.log("Showing error state:", error);
    return <div className="error">Lỗi: {error}</div>;
  }

  if (!vouchers || vouchers.length === 0) {
    console.log("No vouchers to display. Vouchers:", vouchers, "Length:", vouchers?.length);
    return <div className="no-vouchers">
      {isCartDisplay ? "Giỏ hàng của bạn đang trống." : "Không có voucher nào"}
    </div>;
  }

  // Giới hạn số lượng voucher hiển thị tùy theo trang
  let vouchersToShow = vouchers;
  if (!isCartDisplay) {
    if (window.location.pathname === '/' || window.location.pathname === '/home') {
      vouchersToShow = vouchers.slice(0, 15);
    } else if (window.location.pathname.startsWith('/deals')) {
      vouchersToShow = vouchers.slice(0, visibleCount);
    }
  }

  console.log("Vouchers to show:", vouchersToShow.length, "from total:", vouchers.length);
  console.log("Current pathname:", window.location.pathname);

  const handleCardClick = (event, idx) => {
    const rect = event.currentTarget.getBoundingClientRect();
    const containerRect = containerRef.current.getBoundingClientRect();
    setCardPos({
      top: rect.top - containerRect.top,
      left: rect.left - containerRect.left,
      width: rect.width
    });
    setExpandedIdx(idx === expandedIdx ? null : idx);
  };

  return (
    <div className="voucher-list-container" ref={containerRef} style={{ position: "relative" }}>
      <div className={`voucher-list${vouchersToShow.length === 1 || vouchersToShow.length === 2 ? " single-voucher" : ""}`}>
        {vouchersToShow.map((voucher, idx) => {
          // Xử lý trường hợp voucher có thể khác nhau khi là từ giỏ hàng
          const voucherData = isCartDisplay && voucher.voucherId ? voucher.voucherId : voucher;

          console.log(`Voucher ${idx}:`, {
            hasId: !!voucherData.id,
            has_id: !!voucherData._id,
            title: voucherData.title,
            voucherData
          });

          // Kiểm tra dữ liệu hợp lệ
          if (!voucherData || (!voucherData.id && !voucherData._id)) {
            console.warn("Invalid voucher data:", voucherData);
            return (
              <div className="cart-item" key={idx}>
                <p>Voucher không hợp lệ hoặc đã bị xóa.</p>
              </div>
            );
          }

          return (
            <VoucherCard
              key={voucherData.id || voucherData._id || idx}
              id={voucherData.id}
              _id={voucherData._id}
              title={voucherData.title || ""}
              voucherType={voucherData.voucherType || ""}
              voucherAmount={voucherData.voucherAmount || ""}
              maxDiscount={voucherData.maxDiscount || ""}
              minSpend={voucherData.minSpend || 0}
              voucherCode={voucherData.voucherCode || ""}
              startAt={voucherData.startAt || ""}
              expiredAt={voucherData.expiredAt || ""}
              affLink={voucherData.affLink || ""}
              note={voucherData.note || ""}
              totalClick={voucherData.totalClick || 0}
              supplier={voucherData.supplier || {}}
              voucherCategory={voucherData.voucherCategory || {}}
              isInCart={isCartDisplay}
              setToast={setToast}
              isExpanded={expandedIdx === idx}
              handleCardClick={e => handleCardClick(e, idx)}
              cardPos={cardPos}
              style={
                expandedIdx === idx
                  ? {
                    position: "absolute",
                    top: cardPos.top,
                    left: cardPos.left,
                    width: cardPos.width,
                    zIndex: 1000
                  }
                  : {}
              }
            />
          );
        })}
      </div>
      {/* Nút xem thêm */}
      {!isCartDisplay && window.location.pathname.startsWith('/deals') && vouchersToShow.length < vouchers.length && (
        <div style={{ textAlign: "center", margin: "24px 0" }}>
          <button
            className="show-more-home-btn"
            onClick={() => setVisibleCount(visibleCount + 10)}
          >
            Xem thêm Voucher
          </button>
        </div>
      )}
    </div>
  );
}

export default VoucherList;