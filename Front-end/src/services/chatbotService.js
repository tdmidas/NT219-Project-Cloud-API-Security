import axios from "axios";

const API_URL = import.meta.env.VITE_APP_API_URL;

// Send message to chatbot
export const sendMessage = async (message) => {
	try {
		const response = await axios.post(
			`${API_URL}/chatbot/`,
			{
				message: message,
			},
			{
				headers: {
					"Content-Type": "application/json",
				},
				timeout: 30000, // 30 second timeout for AI responses
			}
		);
		return response.data;
	} catch (error) {
		console.error("Error sending message to chatbot:", error);
		throw error;
	}
};
