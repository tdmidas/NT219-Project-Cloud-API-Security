import axios from "axios";

const API_URL = import.meta.env.VITE_APP_API_URL || "https://api.voux-platform.shop/api";

// Add voucher to cart (requires auth)
export const addToCart = async (voucherId, token) => {
	try {
		const response = await axios.post(
			`${API_URL}/cart/add`,
			{ voucher_id: voucherId },
			{
				headers: {
					Authorization: `Bearer ${token}`,
				},
				withCredentials: true,
			}
		);
		return response.data;
	} catch (error) {
		console.error("Error adding to cart:", error);
		throw error;
	}
};

// Get user's cart (requires auth)
export const getCart = async (token) => {
	try {
		const response = await axios.get(`${API_URL}/cart/`, {
			headers: {
				Authorization: `Bearer ${token}`,
			},
			withCredentials: true,
		});
		return response.data;
	} catch (error) {
		console.error("Error fetching cart:", error);
		throw error;
	}
};

// Remove voucher from cart (requires auth)
export const removeFromCart = async (voucherId, token) => {
	try {
		const response = await axios.post(
			`${API_URL}/cart/remove`,
			{ voucher_id: voucherId },
			{
				headers: {
					Authorization: `Bearer ${token}`,
				},
				withCredentials: true,
			}
		);
		return response.data;
	} catch (error) {
		console.error("Error removing from cart:", error);
		throw error;
	}
};

// Update cart item quantity (new function for Python backend)
export const updateCartItem = async (voucherId, quantity, token) => {
	try {
		const response = await axios.put(
			`${API_URL}/cart/update/${voucherId}`,
			{ quantity: quantity },
			{
				headers: {
					Authorization: `Bearer ${token}`,
				},
				withCredentials: true,
			}
		);
		return response.data;
	} catch (error) {
		console.error("Error updating cart item:", error);
		throw error;
	}
};

// Clear entire cart (new function for Python backend)
export const clearCart = async (token) => {
	try {
		const response = await axios.delete(`${API_URL}/cart/clear`, {
			headers: {
				Authorization: `Bearer ${token}`,
			},
			withCredentials: true,
		});
		return response.data;
	} catch (error) {
		console.error("Error clearing cart:", error);
		throw error;
	}
};

// Get cart summary (new function for Python backend)
export const getCartSummary = async (token) => {
	try {
		const response = await axios.get(`${API_URL}/cart/summary`, {
			headers: {
				Authorization: `Bearer ${token}`,
			},
			withCredentials: true,
		});
		return response.data;
	} catch (error) {
		console.error("Error fetching cart summary:", error);
		throw error;
	}
};
