/**
 * Enhanced API Service Layer for TorqCare Frontend
 * Handles all communication with FastAPI backend with robust error handling
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';

class APIService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.wsBaseURL = WS_BASE_URL;
    this.wsConnections = new Map();
  }

  /**
   * Generic fetch wrapper with comprehensive error handling
   */
  async fetch(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      console.log(`API Request: ${options.method || 'GET'} ${url}`);
      
      const response = await fetch(url, defaultOptions);

      // Handle different response status codes
      if (response.status === 404) {
        throw new Error('Resource not found');
      }
      
      if (response.status === 500) {
        throw new Error('Server error occurred');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log(`API Response: Success`, data);
      return data;

    } catch (error) {
      console.error('API Request failed:', error);
      
      // Network errors
      if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
        throw new Error('Cannot connect to server. Please check if the backend is running.');
      }
      
      throw error;
    }
  }

  /**
   * GET request helper
   */
  async get(endpoint) {
    return this.fetch(endpoint, { method: 'GET' });
  }

  /**
   * POST request helper
   */
  async post(endpoint, data) {
    return this.fetch(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  /**
   * PUT request helper
   */
  async put(endpoint, data) {
    return this.fetch(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  /**
   * DELETE request helper
   */
  async delete(endpoint) {
    return this.fetch(endpoint, { method: 'DELETE' });
  }

  // ==================== VEHICLES ====================
  
  /**
   * Get all vehicles
   */
  async getVehicles() {
    return this.get('/vehicles');
  }

  /**
   * Get specific vehicle details
   */
  async getVehicle(vehicleId) {
    return this.get(`/vehicles/${vehicleId}`);
  }

  /**
   * Get vehicle health summary
   */
  async getVehicleHealth(vehicleId) {
    return this.get(`/vehicles/${vehicleId}/health`);
  }

  // ==================== SENSOR DATA ====================
  
  /**
   * Get latest sensor reading for a vehicle
   */
  async getLatestSensorData(vehicleId) {
    return this.get(`/sensor/${vehicleId}/latest`);
  }

  /**
   * Get historical sensor data
   * @param {string} vehicleId - Vehicle identifier
   * @param {number} hours - Number of hours of history (default: 24)
   */
  async getSensorHistory(vehicleId, hours = 24) {
    return this.get(`/sensor/${vehicleId}/history?hours=${hours}`);
  }

  /**
   * Analyze sensor data for anomalies
   */
  async analyzeSensorData(vehicleId) {
    return this.get(`/sensor/${vehicleId}/analyze`);
  }

  // ==================== DIAGNOSIS ====================
  
  /**
   * Run comprehensive vehicle diagnosis
   */
  async diagnoseVehicle(vehicleId) {
    return this.post(`/diagnosis/${vehicleId}`);
  }

  // ==================== CHATBOT ====================
  
  /**
   * Send message to chatbot
   * @param {string} vehicleId - Vehicle identifier
   * @param {string} message - User message
   */
  async sendChatMessage(vehicleId, message) {
    return this.post(`/chat/${vehicleId}?message=${encodeURIComponent(message)}`);
  }

  // ==================== APPOINTMENTS ====================
  
  /**
   * Get all available workshops
   */
  async getWorkshops() {
    return this.get('/workshops');
  }

  /**
   * Propose appointment based on vehicle diagnosis
   */
  async proposeAppointment(vehicleId) {
    return this.post(`/appointments/propose/${vehicleId}`);
  }

  /**
   * Confirm and book an appointment
   * @param {string} vehicleId - Vehicle identifier
   * @param {Object} appointmentData - Appointment details
   */
  async confirmAppointment(vehicleId, appointmentData) {
    return this.post(
      `/appointments/confirm?vehicle_id=${vehicleId}`,
      appointmentData
    );
  }

  /**
   * Get appointments for a vehicle
   */
  async getAppointments(vehicleId) {
    return this.get(`/appointments/${vehicleId}`);
  }

  // ==================== MAINTENANCE ====================
  
  /**
   * Get maintenance history for a vehicle
   */
  async getMaintenanceHistory(vehicleId) {
    return this.get(`/maintenance/${vehicleId}`);
  }

  // ==================== FEEDBACK ====================
  
  /**
   * Submit feedback on a repair/service
   * @param {Object} feedbackData - Feedback details
   */
  async submitFeedback(feedbackData) {
    return this.post('/feedback', feedbackData);
  }

  // ==================== QUALITY INSIGHTS ====================
  
  /**
   * Get quality insights for manufacturer
   */
  async getQualityInsights() {
    return this.get('/insights');
  }

  // ==================== HEALTH CHECK ====================
  
  /**
   * Check API health status
   */
  async healthCheck() {
    try {
      const response = await fetch(`${this.baseURL.replace('/api', '')}/health`);
      return await response.json();
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'unhealthy', error: error.message };
    }
  }

  // ==================== WEBSOCKET ====================
  
  /**
   * Create WebSocket connection for real-time updates
   * @param {string} vehicleId - Vehicle identifier
   * @param {Function} onMessage - Callback for received messages
   * @param {Function} onError - Callback for errors (optional)
   * @param {Function} onClose - Callback for connection close (optional)
   */
  createWebSocket(vehicleId, onMessage, onError = null, onClose = null) {
    // Close existing connection if any
    if (this.wsConnections.has(vehicleId)) {
      this.closeWebSocket(vehicleId);
    }

    const wsURL = `${this.wsBaseURL}/${vehicleId}`;
    console.log(`WebSocket connecting to: ${wsURL}`);
    
    try {
      const ws = new WebSocket(wsURL);

      ws.onopen = () => {
        console.log(`WebSocket connected: ${vehicleId}`);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket message received:', data);
          if (onMessage) {
            onMessage(data);
          }
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) {
          onError(error);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.wsConnections.delete(vehicleId);
        if (onClose) {
          onClose(event);
        }
      };

      // Store connection
      this.wsConnections.set(vehicleId, ws);

      return ws;

    } catch (error) {
      console.error('WebSocket creation error:', error);
      if (onError) {
        onError(error);
      }
      return null;
    }
  }

  /**
   * Close WebSocket connection
   * @param {string} vehicleId - Vehicle identifier
   */
  closeWebSocket(vehicleId) {
    const ws = this.wsConnections.get(vehicleId);
    if (ws) {
      ws.close();
      this.wsConnections.delete(vehicleId);
      console.log(`WebSocket closed: ${vehicleId}`);
    }
  }

  /**
   * Close all WebSocket connections
   */
  closeAllWebSockets() {
    this.wsConnections.forEach((ws, vehicleId) => {
      ws.close();
      console.log(`WebSocket closed: ${vehicleId}`);
    });
    this.wsConnections.clear();
  }

  /**
   * Check if WebSocket is connected
   */
  isWebSocketConnected(vehicleId) {
    const ws = this.wsConnections.get(vehicleId);
    return ws && ws.readyState === WebSocket.OPEN;
  }
}

// Export singleton instance
const apiService = new APIService();

// Health check on initialization
apiService.healthCheck().then(health => {
  console.log('🏥 API Health Check:', health);
  if (health.status !== 'healthy') {
    console.warn('⚠️ Backend may not be fully operational');
  }
}).catch(error => {
  console.error('❌ Cannot connect to backend:', error.message);
  console.log('💡 Make sure the backend server is running on http://localhost:8000');
});

export default apiService;
