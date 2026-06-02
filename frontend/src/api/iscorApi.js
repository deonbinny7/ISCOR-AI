export const API_URL = "http://127.0.0.1:8000";

const getAuthHeaders = () => {
  const token = localStorage.getItem("iscor_session_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
};

const handleResponse = async (response, errorMsg) => {
  if (response.status === 401) {
    localStorage.removeItem("iscor_session_token");
    window.location.reload();
    throw new Error("Session expired. Please start a new session.");
  }
  if (!response.ok) throw new Error(errorMsg);
  return await response.json();
};

export const createSession = async () => {
  const response = await fetch(`${API_URL}/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ consent: true, consent_version: "demo-v1", region: "IN" })
  });
  if (!response.ok) throw new Error("Failed to create session");
  const data = await response.json();
  localStorage.setItem("iscor_session_token", data.session_token);
  return data;
};

export const submitScreening = async (payload) => {
  const response = await fetch(`${API_URL}/screen`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify(payload)
  });
  return await handleResponse(response, "Failed to submit screening");
};

export const getHistory = async (limit = 10) => {
  const response = await fetch(`${API_URL}/history?limit=${limit}`, {
    headers: getAuthHeaders()
  });
  const data = await handleResponse(response, "Failed to fetch history");
  return data.history || [];
};

export const getTrendSummary = async () => {
  const response = await fetch(`${API_URL}/trend-summary`, {
    headers: getAuthHeaders()
  });
  return await handleResponse(response, "Failed to fetch trend summary");
};

export const getReport = async (screeningId) => {
  const response = await fetch(`${API_URL}/get-report/${screeningId}`, {
    headers: getAuthHeaders()
  });
  return await handleResponse(response, "Failed to fetch report");
};

export const sendChat = async (screeningId, question) => {
  const response = await fetch(`${API_URL}/chat?screening_id=${screeningId}&question=${encodeURIComponent(question)}`, {
    method: "POST",
    headers: getAuthHeaders()
  });
  return await handleResponse(response, "Failed to send chat");
};

export const submitAssessment = async (scores) => {
  const response = await fetch(`${API_URL}/assessment/big-five`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify(scores)
  });
  return await handleResponse(response, "Failed to submit assessment");
};

export const getLatestAssessment = async () => {
  const response = await fetch(`${API_URL}/assessment/latest`, {
    headers: getAuthHeaders()
  });
  return await handleResponse(response, "Failed to fetch latest assessment");
};

export const sendCompanionChat = async (message) => {
  const response = await fetch(`${API_URL}/companion/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({ message })
  });
  return await handleResponse(response, "Failed to send companion chat");
};

export const getCompanionHistory = async () => {
  const response = await fetch(`${API_URL}/companion/history`, {
    headers: getAuthHeaders()
  });
  return await handleResponse(response, "Failed to fetch companion history");
};

export const submitMoodCheckin = async (mood_score, note = null) => {
  const response = await fetch(`${API_URL}/checkin/mood`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders()
    },
    body: JSON.stringify({ mood_score, note })
  });
  return await handleResponse(response, "Failed to submit mood check-in");
};

export const getRecentMoods = async () => {
  const response = await fetch(`${API_URL}/checkin/history`, {
    headers: getAuthHeaders()
  });
  return await handleResponse(response, "Failed to fetch mood history");
};
