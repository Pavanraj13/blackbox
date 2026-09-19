import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

let keySyncPromise = null;
export const ensureApiKey = async () => {
  const existing = localStorage.getItem('blackbox_api_key');
  if (existing) return existing;
  if (!keySyncPromise) {
    keySyncPromise = axios.get('http://localhost:8000/api/key-info')
      .then((res) => {
        if (res.data && res.data.api_key) {
          localStorage.setItem('blackbox_api_key', res.data.api_key);
          return res.data.api_key;
        }
        return '';
      })
      .catch(() => '')
      .finally(() => {
        keySyncPromise = null;
      });
  }
  return keySyncPromise;
};

// Auto-sync on client load
if (typeof window !== 'undefined') {
  ensureApiKey();
}

// Intercept requests to attach API Key from storage if present
api.interceptors.request.use(async (config) => {
  let storedKey = localStorage.getItem('blackbox_api_key');
  if (!storedKey) {
    storedKey = await ensureApiKey();
  }
  if (storedKey) {
    config.headers['X-API-Key'] = storedKey;
  }
  return config;
});

export const setStoredApiKey = (key) => {
  if (key) {
    localStorage.setItem('blackbox_api_key', key.trim());
  } else {
    localStorage.removeItem('blackbox_api_key');
  }
};

export const getStoredApiKey = () => {
  return localStorage.getItem('blackbox_api_key') || '';
};

export const getKeyInfo = async () => {
  const res = await api.get('/key-info');
  return res.data;
};

export const getModels = async () => {
  const res = await api.get('/models');
  return res.data;
};

export const startRun = async (goal, targetUrl, mode = 'FOCUSED', model = 'qwen3.6:35b') => {
  const res = await api.post('/runs', {
    goal,
    target_url: targetUrl,
    mode: mode.toUpperCase(),
    model: model || 'qwen3.6:35b'
  });
  return res.data;
};

export const stopRun = async (runId) => {
  const res = await api.post(`/runs/${runId}/stop`);
  return res.data;
};

export const deleteRun = async (runId) => {
  const res = await api.delete(`/runs/${runId}`);
  return res.data;
};

export const deleteAllRuns = async () => {
  const res = await api.delete('/runs');
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

export const getRunSummary = async (runId) => {
  const res = await api.get(`/runs/${runId}/summary`);
  return res.data;
};

export const getHealth = async () => {
  const res = await api.get('/health');
  return res.data;
};

export default api;
