import axios from 'axios';

export const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_URL || (
    process.env.NODE_ENV === 'production' 
      ? 'https://your-app.koyeb.app' 
      : 'http://localhost:8000'
  ),
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API service functions
export const contactsApi = {
  getAll: (params = {}) => apiClient.get('/api/v1/contacts', { params }),
  getById: (id) => apiClient.get(`/api/v1/contacts/${id}`),
  create: (data) => apiClient.post('/api/v1/contacts', data),
  update: (id, data) => apiClient.patch(`/api/v1/contacts/${id}`, data),
  delete: (id) => apiClient.delete(`/api/v1/contacts/${id}`),
  search: (query) => apiClient.get(`/api/v1/contacts/search?q=${encodeURIComponent(query)}`),
};

export const activitiesApi = {
  getAll: (params = {}) => apiClient.get('/api/v1/activities', { params }),
  getByContact: (contactId) => apiClient.get(`/api/v1/contacts/${contactId}/activities`),
  create: (data) => apiClient.post('/api/v1/activities', data),
};

export const callsApi = {
  initiate: (data) => apiClient.post('/api/v1/calls', data),
  getById: (id) => apiClient.get(`/api/v1/calls/${id}`),
};

export const monitoringApi = {
  health: () => apiClient.get('/api/v1/monitoring/health'),
  metrics: () => apiClient.get('/api/v1/monitoring/metrics/summary'),
};