// src/api/survey.ts
import axios from "axios";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const fetchCurrentSurveys = (welfareId?: string) =>
  axios.get(`${API}/api/welfare/surveys/current`, { params: welfareId ? { welfare_id: welfareId } : {} });
export const fetchSurveyHistory = (weeks = 4, welfareId?: string) =>
  axios.get(`${API}/api/welfare/surveys/history`, { params: { weeks, ...(welfareId ? { welfare_id: welfareId } : {}) } });
export const cloneSurvey = (topicId: string) => axios.post(`${API}/api/welfare/surveys/${topicId}/clone`);
export const stopSurvey = (topicId: string) => axios.patch(`${API}/api/welfare/surveys/${topicId}/stop`);
export const fetchSurveyForEdit = (topicId: string) => axios.get(`${API}/api/welfare/surveys/${topicId}/edit`);
export const updateSurvey = (topicId: string, data: any) => axios.put(`${API}/api/welfare/surveys/${topicId}/edit`, data);
export const fetchAnalytics = (topicId: string, welfareId?: string) =>
  axios.get(`${API}/api/welfare/surveys/${topicId}/analytics`, { params: welfareId ? { welfare_id: welfareId } : {} });
export const fetchResponses = (topicId: string, page = 1, pageSize = 50) =>
  axios.get(`${API}/api/welfare/surveys/${topicId}/responses?page=${page}&page_size=${pageSize}`);

export const generateQuestions = (data: any) => axios.post(`${API}/api/welfare/topics/generate-questions`, data);
export const refineQuestions = (data: any) => axios.post(`${API}/api/welfare/topics/refine-questions`, data);
export const validateQuestions = (data: any) => axios.post(`${API}/api/welfare/topics/validate-questions`, data);
export const saveDraft = (data: any) => axios.post(`${API}/api/welfare/topics/save-draft`, data);

export const saveTemplate = (data: any) => axios.post(`${API}/api/welfare/survey-templates`, data);
export const fetchTemplates = (welfareId: string) => axios.get(`${API}/api/welfare/survey-templates?welfare_id=${welfareId}`);

export const fetchUserMbti = (userId: string) =>
  axios.get(`${API}/api/welfare/users/${userId}/mbti`);

export const generateArtwork = (
  topicId: string,
  contentType: string,
  promptVersion: string,
  referenceTitles?: string,
) =>
  axios.post(
    `${API}/api/essay/generate`,
    { reference_titles: referenceTitles?.trim() || null },
    { params: { topic_id: topicId, content_type: contentType, prompt_version: promptVersion } },
  );
