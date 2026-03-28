import api from './api';

export const authService = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
  me: () => api.get('/auth/me/'),
};

export const rfqService = {
  list: (params) => api.get('/rfq/', { params }),
  get: (id) => api.get(`/rfq/${id}/`),
  create: (data) => api.post('/rfq/', data),
};

export const bidService = {
  submit: (data) => api.post('/bids/', data),
  listByRfq: (rfqId, params) => api.get(`/bids/${rfqId}/`, { params }),
};

export const auctionService = {
  status: (rfqId) => api.get(`/auction/${rfqId}/status/`),
  ranking: (rfqId) => api.get(`/auction/${rfqId}/ranking/`),
};

export const logService = {
  list: (rfqId, params) => api.get(`/logs/${rfqId}/`, { params }),
};
