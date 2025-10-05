import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface SignupData {
  email: string;
  username: string;
  password: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  username: string;
}

export interface AnalysisResponse {
  sport: string;
  analysis: string;
}

export const authAPI = {
  signup: (data: SignupData) => api.post<AuthResponse>('/api/signup', data),
  login: (data: LoginData) => api.post<AuthResponse>('/api/login', data),
  getMe: () => api.get<User>('/api/me'),
};

export const videoAPI = {
  analyzeVideo: (sport: string, videoFile: File) => {
    const formData = new FormData();
    formData.append('user_video', videoFile);
    return api.post<AnalysisResponse>(`/api/analyze-video/${sport}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  getSports: () => api.get<{ sports: string[] }>('/api/sports'),
};

export default api;
