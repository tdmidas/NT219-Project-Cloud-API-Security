const API_URL = import.meta.env.VITE_APP_API_URL;
export const getChatResponse = async (message) => {
	try {
		const response = await fetch(`${API_URL}/chatbot`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({ message }),
		});

		if (!response.ok) {
			throw new Error(`Error: ${response.statusText}`);
		}

		const data = await response.json();
		return data.reply;
	} catch (error) {
		console.error("Error fetching chat response:", error);
		return "Xin lỗi, tôi không thể hiểu yêu cầu của bạn.";
	}
};
