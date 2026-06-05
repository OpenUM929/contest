// src/api/survey.ts
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const fetchCurrentSurveys = () => axios.get(`${API}/welfare/surveys/current`);
export const fetchSurveyHistory = (weeks = 4) => axios.get(`${API}/welfare/surveys/history?weeks=${weeks}`);
export const cloneSurvey = (topicId: string) => axios.post(`${API}/welfare/surveys/${topicId}/clone`);
export const stopSurvey = (topicId: string) => axios.patch(`${API}/welfare/surveys/${topicId}/stop`);
export const fetchSurveyForEdit = (topicId: string) => axios.get(`${API}/welfare/surveys/${topicId}/edit`);
export const updateSurvey = (topicId: string, data: any) => axios.put(`${API}/welfare/surveys/${topicId}/edit`, data);
export const fetchAnalytics = (topicId: string) => axios.get(`${API}/welfare/surveys/${topicId}/analytics`);
export const fetchResponses = (topicId: string, page = 1, pageSize = 50) =>
  axios.get(`${API}/welfare/surveys/${topicId}/responses?page=${page}&page_size=${pageSize}`);

export const generateQuestions = (data: any) => axios.post(`${API}/welfare/topics/generate-questions`, data);
export const refineQuestions = (data: any) => axios.post(`${API}/welfare/topics/refine-questions`, data);
export const validateQuestions = (data: any) => axios.post(`${API}/welfare/topics/validate-questions`, data);
export const saveDraft = (data: any) => axios.post(`${API}/welfare/topics/save-draft`, data);

export const saveTemplate = (data: any) => axios.post(`${API}/welfare/survey-templates`, data);
export const fetchTemplates = (welfareId: string) => axios.get(`${API}/welfare/survey-templates?welfare_id=${welfareId}`);
