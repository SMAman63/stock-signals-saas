import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
client.interceptors.request.use(
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

// Handle token expiration
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  signup: (email, password) => client.post('/auth/signup', { email, password }),
  login: (email, password) => client.post('/auth/login', { email, password }),
  getMe: () => client.get('/auth/me'),
};

// Billing API
export const billingAPI = {
  // Unified checkout (uses backend's configured gateway)
  createCheckout: (gateway = null) =>
    client.post('/billing/create-checkout', null, {
      params: gateway ? { gateway } : {}
    }),

  // Gateway-specific endpoints
  createStripeCheckout: () => client.post('/billing/stripe/create-checkout'),
  createRazorpayOrder: () => client.post('/billing/razorpay/create-order'),
  verifyRazorpayPayment: (paymentData) =>
    client.post('/billing/razorpay/verify-payment', paymentData),

  // Status and info
  getStatus: () => client.get('/billing/status'),
  getGatewayInfo: () => client.get('/billing/gateway-info'),
};

// Signals API
export const signalsAPI = {
  getSignals: () => client.get('/signals'),
};

export default client;
