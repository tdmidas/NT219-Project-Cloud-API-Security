import axios from "axios";

const API_URL = import.meta.env.VITE_APP_API_URL || "https://api.voux-platform.shop/api";

// Get all users (public)
export const getAllUsers = async () => {
	try {
		const response = await axios.get(`${API_URL}/users/`);
		return response.data;
	} catch (error) {
		console.error("Error fetching users:", error);
		throw error;
	}
};

// Get user by ID (public)
export const getUserById = async (userId) => {
	try {
		const response = await axios.get(`${API_URL}/users/${userId}`);
		return response.data;
	} catch (error) {
		console.error("Error fetching user by ID:", error);
		throw error;
	}
};

// ========== AUTHENTICATED USER OPERATIONS ==========

// Get user profile (requires auth)
export const getUserProfile = async (token) => {
	try {
		const response = await axios.get(`${API_URL}/users/profile/me`, {
			headers: {
				Authorization: `Bearer ${token}`,
			},
			withCredentials: true,
		});
		return response.data;
	} catch (error) {
		console.error("Error fetching user profile:", error);
		throw error;
	}
};

// Update user profile (requires auth)
export const updateUserProfile = async (userData, token) => {
	try {
		const response = await axios.put(`${API_URL}/users/profile/me`, userData, {
			headers: {
				Authorization: `Bearer ${token}`,
			},
			withCredentials: true,
		});
		return response.data;
	} catch (error) {
		console.error("Error updating user profile:", error);
		throw error;
	}
};

// Delete user (requires auth and admin permissions)
export const deleteUser = async (userId, token) => {
	try {
		const response = await axios.delete(`${API_URL}/users/${userId}`, {
			headers: {
				Authorization: `Bearer ${token}`,
			},
			withCredentials: true,
		});
		return response.data;
	} catch (error) {
		console.error("Error deleting user:", error);
		throw error;
	}
};
