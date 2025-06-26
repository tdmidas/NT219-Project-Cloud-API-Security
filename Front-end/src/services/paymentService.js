import axios from "axios";

const API_URL = import.meta.env.VITE_APP_API_URL;
// Create payment
export const createPayment = async (paymentData) => {
	try {
		const response = await axios.post(`${API_URL}/payment/create`, paymentData, {
			headers: {
				"Content-Type": "application/json",
			},
			withCredentials: true,
		});
		return response.data;
	} catch (error) {
		console.error("Error creating payment:", error);
		throw error;
	}
};

// Get payment status
export const getPaymentStatus = async (orderId) => {
	try {
		const response = await axios.get(`${API_URL}/payment/status/${orderId}`, {
			withCredentials: true,
		});
		return response.data;
	} catch (error) {
		console.error("Error getting payment status:", error);
		throw error;
	}
};

// Cancel payment
export const cancelPayment = async (orderId) => {
	try {
		const response = await axios.put(
			`${API_URL}/payment/cancel/${orderId}`,
			{},
			{
				withCredentials: true,
			}
		);
		return response.data;
	} catch (error) {
		console.error("Error canceling payment:", error);
		throw error;
	}
};
