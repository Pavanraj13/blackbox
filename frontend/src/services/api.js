import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const startRun = async (goal, targetUrl) => {
  const res = await api.post('/runs', { goal, target_url: targetUrl });
  return res.data;
};

export const stopRun = async (runId) => {
  const res = await api.post(`/runs/${runId}/stop`);
  return res.data;
};

export const getRuns = async () => {
  const res = await api.get('/runs');
  return res.data;
};

export const getRun = async (runId) => {
  const res = await api.get(`/runs/${runId}`);
  return res.data;
};

export const getRunSteps = async (runId) => {
  const res = await api.get(`/runs/${runId}/steps`);
  return res.data;
};

export const getRunIssues = async (runId) => {
  const res = await api.get(`/runs/${runId}/issues`);
  return res.data;
};

export const getHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export default api;
