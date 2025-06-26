import axios from "axios";
import { getToken, authRequest } from "./authService";

const API_URL = import.meta.env.VITE_APP_API_URL || "https://api.voux-platform.shop/api";
// tao voucher

export const createVoucher = async (voucherData) => {
	try {
		const token = sessionStorage.getItem("accessToken");
		if (!token) {
			throw new Error("Vui lòng đăng nhập để tạo voucher!");
		}

		const response = await authRequest({
			url: "/vouchers/createVoucher",
			method: "POST",
			data: voucherData,
			headers: {
				Authorization: `Bearer ${token}`,
				"Content-Type": "application/json",
			},
		});
		return response.data;
	} catch (error) {
		console.error("Lỗi tạo voucher:", error);
		throw error;
	}
};

// lấy voucher của người dùng - SỬA ĐỂ KHỚP PYTHON BACKEND
export const getUserVouchers = async (userId) => {
	try {
		// Sử dụng endpoint có trong Python backend
		const response = await authRequest({
			url: `/vouchers/user/${userId}/vouchers`,
			method: "GET",
		});
		if (response.data.success) {
			return response.data.vouchers; // Python backend trả về .vouchers, không phải .data
		} else {
			throw new Error("Không thể tải danh sách voucher!");
		}
	} catch (error) {
		console.error(error);
		throw new Error("Lỗi kết nối đến server!");
	}
};

// lấy tất cả voucher - SỬA RESPONSE FORMAT CHO PYTHON BACKEND
export const getAllVouchers = async () => {
	try {
		const response = await axios.get(`${API_URL}/vouchers/getAllVoucher`);
		console.log("🔍 getAllVouchers response:", response.data);

		if (response.data.success) {
			// Python API Gateway trả về response.data.data, không phải response.data.vouchers
			const vouchers = response.data.data || [];
			console.log("✅ Parsed vouchers:", vouchers.length, "items");
			return vouchers;
		} else {
			console.error("❌ API returned success=false:", response.data.message);
			throw new Error(response.data.message || "Không thể tải danh sách voucher!");
		}
	} catch (error) {
		console.error("❌ getAllVouchers error:", error);
		if (error.response) {
			console.error("Response status:", error.response.status);
			console.error("Response data:", error.response.data);
		}
		throw new Error(error.response?.data?.message || "Lỗi kết nối đến server!");
	}
};

// Lấy voucher theo platform - SỬA CHO PYTHON BACKEND
export const getVouchersByPlatform = async (platform) => {
	try {
		// Sử dụng getAllVoucher và filter ở frontend
		const response = await axios.get(`${API_URL}/vouchers/getAllVoucher`);
		console.log("🔍 getVouchersByPlatform response:", response.data);

		if (response.data.success) {
			// Python API Gateway trả về response.data.data
			const allVouchers = response.data.data || [];
			console.log("✅ All vouchers:", allVouchers.length, "items");

			// Filter theo platform ở frontend (tạm thời)
			const filteredVouchers =
				platform === "all"
					? allVouchers
					: allVouchers.filter((v) => v.category === platform || v.voucherCategory?.title === platform);

			console.log("✅ Filtered vouchers for", platform, ":", filteredVouchers.length, "items");
			return filteredVouchers;
		} else {
			console.error("❌ API returned success=false:", response.data.message);
			throw new Error(response.data.message || "Không thể tải danh sách voucher!");
		}
	} catch (error) {
		console.error("❌ getVouchersByPlatform error:", error);
		if (error.response) {
			console.error("Response status:", error.response.status);
			console.error("Response data:", error.response.data);
		}
		throw new Error(error.response?.data?.message || "Lỗi kết nối đến server!");
	}
};

export const addToCart = async (voucherId, token) => {
	// Thêm kiểm tra
	if (!voucherId) {
		throw new Error("Voucher ID không được để trống!");
	}

	try {
		const response = await authRequest({
			url: "/cart/add",
			method: "POST",
			data: { voucher_id: voucherId.toString() }, // SỬA: Python backend mong đợi voucher_id (snake_case)
		});
		return response.data;
	} catch (error) {
		console.error("Lỗi khi thêm vào giỏ hàng:", error);
		throw new Error(error.response?.data?.message || "Lỗi kết nối khi thêm vào giỏ hàng!");
	}
};

// Lấy số lượng voucher theo platform - SỬA CHO PYTHON BACKEND
export const getVoucherCountByPlatform = async (platform) => {
	try {
		// Sử dụng getAllVouchers (đã sửa) và count ở frontend
		const vouchers = await getAllVouchers();
		console.log("🔍 getVoucherCountByPlatform - All vouchers:", vouchers.length);

		const count =
			platform === "all"
				? vouchers.length
				: vouchers.filter((v) => v.category === platform || v.voucherCategory?.title === platform).length;

		console.log("✅ Voucher count for", platform, ":", count);
		return count;
	} catch (error) {
		console.error("❌ getVoucherCountByPlatform error:", error);
		throw new Error("Lỗi kết nối đến server!");
	}
};

// Lấy tất cả uservoucher không lọc theo gì cả - SỬA ĐỂ KHỚP ENDPOINT
export const getUserVouchersByUsername = async () => {
	try {
		// Sử dụng getUserVouchers với current user ID
		const token = sessionStorage.getItem("accessToken");
		if (!token) {
			throw new Error("Vui lòng đăng nhập!");
		}

		// Lấy thông tin user hiện tại trước
		const profileResponse = await authRequest({
			url: "/auth/profile",
			method: "GET",
		});

		if (profileResponse.data.success) {
			const userId = profileResponse.data.user.id;
			return await getUserVouchers(userId);
		} else {
			throw new Error("Không thể tải thông tin người dùng!");
		}
	} catch (error) {
		console.error(error);
		throw new Error("Lỗi kết nối đến server!");
	}
};
