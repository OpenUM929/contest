import axios from "axios";

const API_BASE = process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000";

export async function triggerWelfareContact(userId: string): Promise<void> {
  await axios.post(`${API_BASE}/safety/alert`, {
    user_id: userId,
    reason: "user_request",
  });
}
