import axios from "axios";

// Use API Gateway URL instead of direct service URLs
const API_URL = import.meta.env.VITE_APP_API_URL || "https://api.voux-platform.shop/api";

// Helper function to extract user data from API response
export const extractUserData = (apiResponse) => {
	if (!apiResponse || !apiResponse.user) {
		console.error("❌ No user data in API response:", apiResponse);
		return null;
	}

	const userData = {
		id: apiResponse.user.id,
		username: apiResponse.user.username,
		email: apiResponse.user.email || "",
		bio: apiResponse.user.bio || "",
		theme: apiResponse.user.theme || "light",
		vouchersPosted: apiResponse.user.vouchers_posted || 0,
		vouchersSold: apiResponse.user.vouchers_sold || 0,
		avatar_url: apiResponse.user.avatar_url || "/default-avatar.png",
	};

	console.log("✅ Extracted user data:", userData);
	return userData;
};

// Các hàm xử lý đăng nhập và đăng ký đã có
export const login = async (username, password, rememberMe = false) => {
	try {
		console.log("🔄 Attempting login with:", { username, rememberMe, apiUrl: API_URL });
		const response = await axios.post(
			`${API_URL}/auth/login`,
			{
				username,
				password,
				remember_me: rememberMe,
			},
			{
				withCredentials: true, // Quan trọng: cho phép nhận HTTP-only cookies
			}
		);
		console.log("✅ Login API response:", response.data);
		return response.data;
	} catch (error) {
		console.error("❌ Login API error:", error);
		// Nếu server trả về lỗi và có response kèm thông điệp
		if (error.response && error.response.data) {
			return error.response.data; // vẫn trả về { success: false, message: "..."}
		}

		// Nếu lỗi không kết nối được đến server hoặc không có phản hồi
		return {
			success: false,
			message: "⚠️ Lỗi kết nối đến server!",
		};
	}
};

export const register = async (username, email, password) => {
	try {
		const response = await axios.post(
			`${API_URL}/auth/register`,
			{ username, email, password },
			{
				headers: {
					"Content-Type": "application/json",
				},
			}
		);
		return response.data;
	} catch (error) {
		console.error("Registration error:", error);

		// If request timed out
		if (error.code === "ECONNABORTED") {
			return {
				success: false,
				message: "Đăng ký mất quá nhiều thời gian. Vui lòng thử lại sau.",
			};
		}

		// If server returns an error with a specific message
		if (error.response && error.response.data) {
			return error.response.data; // Return error data from server
		}

		// Network error
		if (error.request) {
			return {
				success: false,
				message: "Không thể kết nối đến máy chủ. Vui lòng kiểm tra kết nối mạng.",
			};
		}

		// Generic error handling
		return {
			success: false,
			message: "⚠️ Lỗi kết nối đến server!",
		};
	}
};

export const logout = async () => {
	try {
		// Gọi API logout để vô hiệu hóa refresh token trong cookie
		await axios.post(
			`${API_URL}/auth/logout`,
			{
				logout_all: false, // Có thể customize thành true để logout tất cả thiết bị
			},
			{
				headers: {
					Authorization: `Bearer ${localStorage.getItem("accessToken")}`,
				},
				withCredentials: true, // Quan trọng: cho phép gửi/nhận cookie
			}
		);

		localStorage.removeItem("accessToken");
		return true;
	} catch (error) {
		console.error("Logout error:", error);
		localStorage.removeItem("accessToken");
		return false;
	}
};

// ========== TRADITIONAL AUTH FUNCTIONS ==========

// Hàm chuyển hướng người dùng đến Google OAuth
export const handleGoogleLogin = () => {
	window.location.href = `${API_URL}/auth/google`; // Chuyển hướng đến Google OAuth
};

export const getToken = () => {
	return localStorage.getItem("accessToken");
};

export const handleFacebookLogin = () => {
	window.location.href = `${API_URL}/auth/facebook`; // Chuyển hướng đến Facebook OAuth
};

// Hàm gọi API có tự động refresh token nếu accessToken hết hạn
export const authRequest = async (config) => {
	try {
		// For traditional auth, use Bearer token
		const token = getToken();
		if (token) {
			config.headers = {
				...config.headers,
				Authorization: `Bearer ${token}`,
			};
		}
		// Gọi API through API Gateway
		return await axios({ ...config, baseURL: API_URL, withCredentials: true });
	} catch (error) {
		// Traditional auth token refresh logic
		if (error.response && (error.response.status === 401 || error.response.status === 403) && !config._retry) {
			config._retry = true;
			try {
				console.log("🔄 Access token expired, attempting refresh...");

				// SỬA: Python backend expects empty body for refresh, refresh_token comes from HTTP-only cookie
				const res = await axios.post(
					`${API_URL}/auth/refresh`,
					{}, // Empty body - refresh_token sẽ được lấy từ HTTP-only cookie
					{
						headers: { "Content-Type": "application/json" },
						withCredentials: true, // Quan trọng: để gửi HTTP-only cookie
					}
				);

				if (res.status === 200 && res.data.access_token) {
					localStorage.setItem("accessToken", res.data.access_token);
					console.log("✅ Access token refreshed successfully");

					config.headers = {
						...config.headers,
						Authorization: `Bearer ${res.data.access_token}`,
					};
					return await axios({ ...config, baseURL: API_URL, withCredentials: true });
				}
			} catch (refreshError) {
				console.error("❌ Token refresh failed:", refreshError);
				// Traditional token refresh failed
				localStorage.removeItem("accessToken");
				window.location.href = "/login";
			}
		}

		// Các lỗi khác (400, 422, 500...) chỉ throw error, KHÔNG đăng xuất
		throw error;
	}
};

// ========== SECURE AUTH STATUS CHECKING ==========

// Check authentication status securely via API
export const checkAuthStatus = async () => {
	try {
		console.log("🔍 Checking authentication status...");

		// Try traditional auth
		console.log("🔄 Checking traditional authentication...");
		const token = localStorage.getItem("accessToken");
		if (token) {
			console.log("🎫 Found access token, verifying...");
			const response = await axios.get(`${API_URL}/auth/profile`, {
				headers: {
					Authorization: `Bearer ${token}`,
					"Content-Type": "application/json",
				},
				withCredentials: true,
			});

			if (response.status === 200 && response.data.success) {
				console.log("✅ Traditional authentication successful");

				// Use helper function to extract user data
				const userData = extractUserData(response.data);

				return {
					authenticated: true,
					user: userData,
				};
			}
		} else {
			console.log("❌ No access token found in localStorage");
		}

		// Not authenticated
		console.log("❌ No valid authentication found");
		return {
			authenticated: false,
			user: null,
		};
	} catch (error) {
		console.error("❌ Auth status check failed:", error);
		return {
			authenticated: false,
			user: null,
		};
	}
};

// Secure logout
export const secureLogout = async () => {
	try {
		await logout();
		// Clear the access token
		localStorage.removeItem("accessToken");
		return { success: true };
	} catch (error) {
		console.error("Logout error:", error);
		// Force clear access token
		localStorage.removeItem("accessToken");
		return { success: false, message: error.message };
	}
};
