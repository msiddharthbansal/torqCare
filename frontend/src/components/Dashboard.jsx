import React, { useState, useEffect } from 'react';
import { Activity, AlertCircle, Calendar, MessageSquare, TrendingUp, Wrench, CheckCircle, Battery, Gauge } from 'lucide-react';
import api from '../services/api';

const Dashboard = ({ vehicleId, onNavigate }) => {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [vehicleId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const health = await api.getVehicleHealth(vehicleId);
      setHealthData(health);
      setError(null);
    } catch (err) {
      setError('Failed to load vehicle data');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-300">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
          <AlertCircle className="text-red-400 mx-auto mb-2" size={48} />
          <p className="text-red-300 text-lg">{error}</p>
          <button
            onClick={loadDashboardData}
            className="mt-4 bg-red-500 hover:bg-red-600 text-white px-6 py-2 rounded-lg transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const getHealthColor = (score) => {
    if (score >= 90) return 'from-green-500 to-emerald-600';
    if (score >= 75) return 'from-blue-500 to-cyan-600';
    if (score >= 60) return 'from-yellow-500 to-orange-600';
    return 'from-red-500 to-pink-600';
  };

  const getHealthStatus = (score) => {
    if (score >= 90) return { text: 'Excellent', color: 'text-green-400' };
    if (score >= 75) return { text: 'Good', color: 'text-blue-400' };
    if (score >= 60) return { text: 'Fair', color: 'text-yellow-400' };
    return { text: 'Poor', color: 'text-red-400' };
  };

  const componentIcons = {
    battery: Battery,
    motor: Gauge,
    brake: Wrench,
    tire: Activity
  };

  const healthStatus = getHealthStatus(healthData?.overall_health || 0);

  return (
    <div className="space-y-6 animate-slideIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Vehicle Dashboard</h1>
          <p className="text-gray-300">Real-time health monitoring and insights</p>
        </div>
        <div className="flex items-center gap-2 bg-white/10 border border-white/20 rounded-xl px-6 py-3">
          <Activity className="text-blue-400" size={24} />
          <div>
            <div className="text-xs text-gray-400">Vehicle ID</div>
            <div className="text-xl font-semibold text-white">{vehicleId}</div>
          </div>
        </div>
      </div>

      {/* Overall Health Score */}
      <div className={`bg-gradient-to-br ${getHealthColor(healthData?.overall_health || 0)} rounded-2xl p-8 shadow-2xl`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-white">Overall Health Score</h2>
          <Activity className="text-white" size={40} />
        </div>
        <div className="flex items-center gap-6">
          <div className="text-7xl font-bold text-white">
            {healthData?.overall_health?.toFixed(1) || 0}%
          </div>
          <div className="flex-1">
            <div className="bg-white/20 rounded-full h-6 overflow-hidden mb-3">
              <div
                className="bg-white h-full rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${healthData?.overall_health || 0}%` }}
              ></div>
            </div>
            <div className="flex items-center justify-between text-white/90">
              <span className={`text-lg font-semibold ${healthStatus.color}`}>
                {healthStatus.text}
              </span>
              <span className="text-sm">
                Last updated: {new Date().toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Component Health Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {healthData?.component_health && Object.entries(healthData.component_health).map(([component, score]) => {
          const Icon = componentIcons[component] || Wrench;
          const colorClass = getHealthColor(score);
          
          return (
            <div
              key={component}
              className={`bg-gradient-to-br ${colorClass} rounded-xl p-6 shadow-lg hover:scale-105 transition-transform cursor-pointer`}
              onClick={() => onNavigate('diagnostics')}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-white/80 capitalize font-medium">{component}</span>
                <Icon className="text-white" size={28} />
              </div>
              <div className="text-4xl font-bold text-white mb-2">
                {score?.toFixed(1)}%
              </div>
              <div className="w-full bg-white/20 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-white h-full rounded-full transition-all duration-500"
                  style={{ width: `${score}%` }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => onNavigate('diagnostics')}
          className="bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl p-6 transition-all flex items-center gap-4 group"
        >
          <div className="bg-blue-500/20 p-3 rounded-lg group-hover:scale-110 transition-transform">
            <Activity className="text-blue-400" size={32} />
          </div>
          <div className="text-left">
            <div className="text-white font-semibold text-lg">View Diagnostics</div>
            <div className="text-gray-300 text-sm">Real-time sensor monitoring</div>
          </div>
        </button>

        <button
          onClick={() => onNavigate('chatbot')}
          className="bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl p-6 transition-all flex items-center gap-4 group"
        >
          <div className="bg-green-500/20 p-3 rounded-lg group-hover:scale-110 transition-transform">
            <MessageSquare className="text-green-400" size={32} />
          </div>
          <div className="text-left">
            <div className="text-white font-semibold text-lg">Ask Assistant</div>
            <div className="text-gray-300 text-sm">Get instant AI support</div>
          </div>
        </button>

        <button
          onClick={() => onNavigate('maintenance')}
          className="bg-white/10 hover:bg-white/20 border border-white/20 rounded-xl p-6 transition-all flex items-center gap-4 group"
        >
          <div className="bg-purple-500/20 p-3 rounded-lg group-hover:scale-110 transition-transform">
            <Calendar className="text-purple-400" size={32} />
          </div>
          <div className="text-left">
            <div className="text-white font-semibold text-lg">Maintenance</div>
            <div className="text-gray-300 text-sm">Schedule & history</div>
          </div>
        </button>
      </div>

      {/* Recent Activity */}
      <div className="bg-white/10 rounded-xl p-6 border border-white/20">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <TrendingUp size={24} className="text-blue-400" />
          Recent Activity
        </h3>
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-gray-300 bg-white/5 p-3 rounded-lg">
            <CheckCircle className="text-green-400" size={20} />
            <span>System health check completed</span>
            <span className="ml-auto text-sm text-gray-400">2 hours ago</span>
          </div>
          <div className="flex items-center gap-3 text-gray-300 bg-white/5 p-3 rounded-lg">
            <TrendingUp className="text-blue-400" size={20} />
            <span>Distance traveled: {healthData?.distance_traveled?.toFixed(1) || 0} km</span>
            <span className="ml-auto text-sm text-gray-400">Today</span>
          </div>
          <div className="flex items-center gap-3 text-gray-300 bg-white/5 p-3 rounded-lg">
            <Activity className="text-purple-400" size={20} />
            <span>All systems operating normally</span>
            <span className="ml-auto text-sm text-gray-400">Current</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;