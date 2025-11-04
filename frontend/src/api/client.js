/**
 * API Client for TraderBot Backend
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================
// Bot Control API
// ============================================

export const botAPI = {
  /**
   * Start the trading bot
   * @param {Object} params - Start parameters
   * @param {string} params.symbol - Trading symbol (optional)
   * @param {number} params.trade_interval - Trade interval in seconds (optional)
   */
  start: async (params = {}) => {
    const response = await apiClient.post('/bot/start', params);
    return response.data;
  },

  /**
   * Stop the trading bot
   */
  stop: async () => {
    const response = await apiClient.post('/bot/stop');
    return response.data;
  },

  /**
   * Get bot status
   */
  getStatus: async () => {
    const response = await apiClient.get('/bot/status');
    return response.data;
  },
};

// ============================================
// Statistics API
// ============================================

export const statsAPI = {
  /**
   * Get account statistics
   */
  getAccount: async () => {
    const response = await apiClient.get('/stats/account');
    return response.data;
  },

  /**
   * Get open positions
   */
  getPositions: async () => {
    const response = await apiClient.get('/stats/positions');
    return response.data;
  },

  /**
   * Get strategy statistics
   */
  getStrategies: async () => {
    const response = await apiClient.get('/stats/strategies');
    return response.data;
  },
};

// ============================================
// History API
// ============================================

export const historyAPI = {
  /**
   * Get trade history
   * @param {Object} params - Query parameters
   * @param {number} params.page - Page number
   * @param {number} params.page_size - Items per page
   * @param {string} params.status - Filter by status
   * @param {string} params.symbol - Filter by symbol
   */
  getTrades: async (params = {}) => {
    const response = await apiClient.get('/history/trades', { params });
    return response.data;
  },
};

// ============================================
// System API
// ============================================

export const systemAPI = {
  /**
   * Health check
   */
  health: async () => {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default apiClient;

