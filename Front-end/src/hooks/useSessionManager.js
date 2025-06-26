import { useState, useEffect, useCallback } from "react";
import sessionManager, {
	initializeSessionAfterLogin,
	extendSession,
	logoutByChoice,
	cleanupSession,
} from "../services/sessionManager";

export const useSessionManager = () => {
	const [sessionModal, setSessionModal] = useState({
		isVisible: false,
		timeLeft: 10,
		message: "",
		isExpired: false,
		isSessionExpired: false,
		isProcessing: false,
	});

	// Xử lý cảnh báo session (giờ là hỏi có muốn tiếp tục không)
	const handleSessionWarning = useCallback((warningData) => {
		console.log("🔔 useSessionManager.handleSessionWarning called with:", warningData);

		if (!warningData) {
			// Ẩn modal
			console.log("🙈 Hiding session modal");
			setSessionModal((prev) => ({
				...prev,
				isVisible: false,
			}));
			return;
		}

		console.log("📱 Showing session modal with data:", warningData);
		setSessionModal({
			isVisible: true,
			timeLeft: warningData.timeLeft,
			message: warningData.message,
			isExpired: false,
			isSessionExpired: warningData.isSessionExpired || false,
		});
		console.log("✅ Session modal state updated");
	}, []);

	// Xử lý session hết hạn
	const handleSessionExpiry = useCallback((expiryData) => {
		if (!expiryData) {
			// Ẩn modal
			setSessionModal((prev) => ({
				...prev,
				isVisible: false,
			}));
			return;
		}

		if (expiryData.expired) {
			setSessionModal({
				isVisible: true,
				timeLeft: 0,
				message: expiryData.message,
				isExpired: true,
				isSessionExpired: false,
			});
		}
	}, []);

	// Khởi tạo session sau login
	const initializeSession = useCallback(
		(loginResponse) => {
			console.log("🚀 useSessionManager.initializeSession called with:", loginResponse);

			// Lưu tokens - SỬA: Sử dụng localStorage thay vì sessionStorage để nhất quán
			if (loginResponse.access_token) {
				localStorage.setItem("accessToken", loginResponse.access_token);
				console.log("💾 Access token saved to localStorage");
			}
			if (loginResponse.refresh_token) {
				localStorage.setItem("refreshToken", loginResponse.refresh_token);
				console.log("💾 Refresh token saved to localStorage");
			}

			// Khởi tạo session manager
			console.log("🔧 Calling sessionManager.initializeSessionAfterLogin");
			initializeSessionAfterLogin(loginResponse, handleSessionWarning, handleSessionExpiry);
			console.log("✅ Session manager initialization completed");
		},
		[handleSessionWarning, handleSessionExpiry]
	);

	// Gia hạn session (user chọn "Có, tiếp tục")
	const handleExtendSession = useCallback(async () => {
		console.log("🔄 User clicked extend session");

		// Ngăn duplicate calls
		if (sessionModal.isProcessing) {
			console.log("⚠️ Already processing extend request, ignoring");
			return false;
		}

		// Set processing state
		setSessionModal((prev) => ({ ...prev, isProcessing: true }));

		try {
			const success = await extendSession();
			if (success) {
				console.log("✅ User chose to continue - session extended");
				// Modal sẽ được ẩn bởi sessionManager.hideModal()
			} else {
				console.log("❌ Failed to extend session");
				setSessionModal((prev) => ({ ...prev, isProcessing: false }));
			}
			return success;
		} catch (error) {
			console.error("❌ Error in handleExtendSession:", error);
			setSessionModal((prev) => ({ ...prev, isProcessing: false }));
			return false;
		}
	}, [sessionModal.isProcessing]);

	// Đăng xuất (user chọn "Không, đăng xuất" hoặc tự động)
	const handleLogoutNow = useCallback(async () => {
		console.log("🚪 User clicked logout or auto logout triggered");

		// Ngăn duplicate calls
		if (sessionModal.isProcessing) {
			console.log("⚠️ Already processing logout request, ignoring");
			return;
		}

		// Set processing state
		setSessionModal((prev) => ({ ...prev, isProcessing: true }));

		// Ẩn modal ngay lập tức để tránh user click nhiều lần
		setSessionModal((prev) => ({
			...prev,
			isVisible: false,
			isProcessing: true,
		}));

		try {
			// Sử dụng logoutByChoice để phân biệt user chọn logout
			const isUserChoice = sessionModal.isSessionExpired;
			console.log(`🚪 Logout type: ${isUserChoice ? "user choice" : "auto logout"}`);

			if (isUserChoice) {
				await logoutByChoice();
			} else {
				// Auto logout - cleanup và redirect
				cleanupSession();

				// Xóa tokens
				localStorage.removeItem("accessToken");
				localStorage.removeItem("refreshToken");

				// Chuyển về login ngay
				setTimeout(() => {
					window.location.href = "/login";
				}, 500);
			}
		} catch (error) {
			console.error("❌ Error in handleLogoutNow:", error);
			// Force redirect even if error
			setTimeout(() => {
				window.location.href = "/login";
			}, 1000);
		}
	}, [sessionModal.isSessionExpired, sessionModal.isProcessing]);

	// Cleanup khi component unmount - KHÔNG tự động cleanup session manager
	useEffect(() => {
		// Chỉ cleanup khi thực sự cần thiết (như logout manual)
		// KHÔNG cleanup tự động khi component unmount vì có thể gây mất session khi navigate

		return () => {
			// Chỉ log, không cleanup
			console.log("🔄 useSessionManager component unmounting (session manager continues)");
		};
	}, []);

	return {
		sessionModal,
		initializeSession,
		handleExtendSession,
		handleLogoutNow,
		hideModal: () => setSessionModal((prev) => ({ ...prev, isVisible: false })),
	};
};
