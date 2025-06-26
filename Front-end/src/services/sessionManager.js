import { authRequest, secureLogout } from "./authService";

class SessionManager {
	constructor() {
		this.sessionExpiryTimer = null;
		this.onSessionExpiry = null;
		this.onSessionWarning = null;
		this.isModalShown = false;
		this.tokenExpiryTime = null;
		this.sessionDuration = 30; // 30 seconds
	}

	// Khởi tạo session manager sau khi login
	initializeSession(expiresIn, onSessionWarning, onSessionExpiry) {
		console.log("🔧 SessionManager.initializeSession called with:", {
			expiresIn,
			hasWarningCallback: !!onSessionWarning,
			hasExpiryCallback: !!onSessionExpiry,
		});

		this.onSessionWarning = onSessionWarning;
		this.onSessionExpiry = onSessionExpiry;
		this.isModalShown = false;
		this.sessionDuration = expiresIn || 30;

		// Lưu thời gian bắt đầu session
		this.tokenExpiryTime = Date.now() + this.sessionDuration * 1000;

		console.log(`🕐 Session initialized: will ask user after ${this.sessionDuration} seconds`);
		console.log(`⏰ Modal will appear at: ${new Date(this.tokenExpiryTime).toLocaleTimeString()}`);

		// Clear any existing timers
		this.clearAllTimers();

		// Hiển thị modal đúng sau thời gian session (30s)
		this.sessionExpiryTimer = setTimeout(() => {
			console.log("⏰ Timer triggered - showing continue modal");
			this.showContinueModal();
		}, this.sessionDuration * 1000);

		console.log(`✅ Timer set for ${this.sessionDuration} seconds`);
	}

	// Hiển thị modal hỏi có muốn tiếp tục session không
	showContinueModal() {
		console.log("🔔 showContinueModal called");
		console.log("📊 Current state:", {
			isModalShown: this.isModalShown,
			hasWarningCallback: !!this.onSessionWarning,
			sessionDuration: this.sessionDuration,
		});

		if (this.isModalShown) {
			console.log("⚠️ Modal already shown, skipping");
			return;
		}

		this.isModalShown = true;
		console.log(`❓ Asking user if they want to continue session after ${this.sessionDuration} seconds`);

		if (this.onSessionWarning) {
			console.log("📢 Calling onSessionWarning callback");
			this.onSessionWarning({
				timeLeft: 10, // Cho user 10 giây quyết định
				message: "Phiên đăng nhập đã hết thời gian quy định. Bạn có muốn tiếp tục không?",
				isSessionExpired: true,
			});
			console.log("✅ onSessionWarning callback called successfully");
		} else {
			console.error("❌ onSessionWarning callback is null!");
		}

		// Nếu user không quyết định trong 10 giây, tự động logout
		setTimeout(() => {
			if (this.isModalShown) {
				console.log("⏰ User didn't respond in 10 seconds - auto logout");
				this.handleSessionExpired();
			} else {
				console.log("✅ User already responded, no auto logout needed");
			}
		}, 10000); // 10 giây để user quyết định
	}

	// Gia hạn session (refresh token)
	async extendSession() {
		try {
			console.log("🔄 User chose to continue - extending session...");

			console.log("📤 Sending refresh token request...");
			// SỬA: Không cần gửi refresh_token trong body, server sẽ lấy từ HTTP-only cookie
			const response = await authRequest({
				method: "POST",
				url: "/auth/refresh",
				data: {}, // Empty body - refresh_token sẽ được lấy từ HTTP-only cookie
			});

			console.log("📥 Refresh response:", response.data);

			if (response.data.success && response.data.access_token) {
				// Lưu token mới vào localStorage
				localStorage.setItem("accessToken", response.data.access_token);
				console.log("💾 New access token saved to localStorage");

				// Ẩn modal TRƯỚC khi khởi tạo lại session
				this.hideModal();
				console.log("🙈 Modal hidden");

				// Khởi tạo lại session với thời gian mới
				const expiresIn = response.data.expires_in || 30;
				console.log(`🔄 Reinitializing session with ${expiresIn} seconds`);

				// Đợi một chút để UI update
				setTimeout(() => {
					this.initializeSession(expiresIn, this.onSessionWarning, this.onSessionExpiry);
					console.log("✅ Session reinitialized successfully");
				}, 100);

				console.log("✅ Session extended successfully");
				return true;
			} else {
				console.error("❌ Invalid response from refresh endpoint:", response.data);
				throw new Error("Invalid refresh response");
			}
		} catch (error) {
			console.error("❌ Failed to extend session:", error);

			// Xử lý chi tiết các loại lỗi
			if (error.response) {
				const status = error.response.status;
				const errorData = error.response.data;

				console.error(`❌ HTTP ${status} Error:`, errorData);

				if (status === 401) {
					console.error("🔐 Refresh token expired or invalid - forcing logout");
					// Xóa refresh token cookie không hợp lệ bằng cách gọi logout
					try {
						await authRequest({
							method: "POST",
							url: "/auth/logout",
							data: { logout_all: false },
						});
					} catch (logoutError) {
						console.warn("⚠️ Logout request failed (continuing anyway):", logoutError);
					}
				} else if (status === 403) {
					console.error("🚫 Insufficient permissions for refresh");
				} else if (status >= 500) {
					console.error("🔥 Server error during refresh");
				}
			} else if (error.request) {
				console.error("🌐 Network error - no response received:", error.request);
			} else {
				console.error("⚙️ Request setup error:", error.message);
			}

			// Trong mọi trường hợp lỗi, đều chuyển về handleSessionExpired
			this.handleSessionExpired();
			return false;
		}
	}

	// Ẩn modal
	hideModal() {
		this.isModalShown = false;
		if (this.onSessionExpiry) {
			this.onSessionExpiry(null); // Ẩn modal
		}
	}

	// Xử lý khi user chọn logout hoặc tự động logout
	async handleSessionExpired(userChose = false) {
		console.log(`🚨 Session ending - ${userChose ? "user chose logout" : "automatic logout"}`);

		// Clear timer ngay lập tức để tránh duplicate calls
		this.clearAllTimers();

		// Reset modal state ngay lập tức
		this.isModalShown = false;

		try {
			// Chỉ gọi secureLogout nếu có tokens
			const hasTokens = localStorage.getItem("accessToken");
			if (hasTokens) {
				console.log("🔐 Calling secure logout...");
				await secureLogout();
				console.log("✅ Secure logout completed");
			} else {
				console.log("ℹ️ No tokens found, skipping logout API call");
			}
		} catch (error) {
			console.error("⚠️ Logout API error (continuing anyway):", error);
		}

		// Xóa tất cả token ngay lập tức từ localStorage
		localStorage.removeItem("accessToken");
		console.log("🗑️ Tokens cleared from localStorage");

		// Hiển thị thông báo logout
		if (this.onSessionExpiry) {
			this.onSessionExpiry({
				expired: true,
				message: userChose
					? "Bạn đã chọn đăng xuất. Cảm ơn bạn đã sử dụng dịch vụ!"
					: "Phiên đăng nhập đã kết thúc do không có phản hồi. Bạn sẽ được chuyển về trang đăng nhập.",
			});
		}

		// Chuyển về trang login nhanh hơn
		setTimeout(
			() => {
				console.log("🔄 Redirecting to login page...");
				window.location.href = "/login";
			},
			userChose ? 1000 : 1500
		); // User chọn = 1s, auto = 1.5s
	}

	// Xóa tất cả timer
	clearAllTimers() {
		if (this.sessionExpiryTimer) {
			clearTimeout(this.sessionExpiryTimer);
			this.sessionExpiryTimer = null;
		}
	}

	// Dọn dẹp khi logout hoặc unmount
	cleanup() {
		console.log("🧹 Cleaning up session manager");
		this.clearAllTimers();
		this.onSessionExpiry = null;
		this.onSessionWarning = null;
		this.isModalShown = false;
		this.tokenExpiryTime = null;

		// Đừng cleanup ngay khi navigate - chỉ cleanup khi thực sự logout
		console.log("⚠️  Session manager cleaned up");
	}

	// Method riêng cho việc force cleanup
	forceCleanup() {
		console.log("🚨 Force cleaning up session manager");
		this.cleanup();
	}

	// Kiểm tra xem có đang hiển thị modal không
	isShowingModal() {
		return this.isModalShown;
	}

	// Lấy thời gian đã trôi qua (giây)
	getElapsedTime() {
		if (!this.tokenExpiryTime) return 0;
		const elapsed = Math.floor((Date.now() - (this.tokenExpiryTime - this.sessionDuration * 1000)) / 1000);
		return Math.max(0, elapsed);
	}
}

// Tạo singleton instance
const sessionManager = new SessionManager();

export default sessionManager;

// Helper functions
export const initializeSessionAfterLogin = (loginResponse, onSessionWarning, onSessionExpiry) => {
	const expiresIn = loginResponse.expires_in || 30;
	sessionManager.initializeSession(expiresIn, onSessionWarning, onSessionExpiry);
};

export const extendSession = () => {
	return sessionManager.extendSession();
};

export const logoutByChoice = () => {
	return sessionManager.handleSessionExpired(true);
};

export const cleanupSession = () => {
	sessionManager.forceCleanup();
};
