import React, { useState, useEffect } from 'react';
import { Activity, AlertCircle, Battery, Gauge, Wrench, RefreshCw, TrendingUp, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import api from '../services/api';

const Diagnostics = ({ vehicleId }) => {
  const [sensorData, setSensorData] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [diagnosis, setDiagnosis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    loadDiagnostics();
    const interval = setInterval(loadDiagnostics, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [vehicleId]);

  const loadDiagnostics = async () => {
    try {
      const [sensor, analyze, diagnosisData, historyData] = await Promise.all([
        api.getLatestSensorData(vehicleId),
        api.analyzeSensorData(vehicleId),
        api.diagnoseVehicle(vehicleId),
        api.getSensorHistory(vehicleId, 1) // Last 1 hour
      ]);
      
      setSensorData(sensor);
      setAnalysis(analyze);
      setDiagnosis(diagnosisData);
      setHistory(historyData.slice(0, 20)); // Last 20 readings
      setLoading(false);
    } catch (error) {
      console.error('Diagnostics error:', error);
      setLoading(false);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      Critical: 'text-red-400 bg-red-500/20 border-red-500/30',
      High: 'text-orange-400 bg-orange-500/20 border-orange-500/30',
      Medium: 'text-yellow-400 bg-yellow-500/20 border-yellow-500/30',
      Low: 'text-blue-400 bg-blue-500/20 border-blue-500/30',
      Normal: 'text-green-400 bg-green-500/20 border-green-500/30'
    };
    return colors[severity] || colors.Normal;
  };

  const metrics = sensorData ? [
    { label: 'Battery SoC', value: `${sensorData.soc?.toFixed(1)}%`, icon: Battery, color: 'text-green-400' },
    { label: 'Battery SoH', value: `${sensorData.soh?.toFixed(1)}%`, icon: TrendingUp, color: 'text-blue-400' },
    { label: 'Battery Temp', value: `${sensorData.battery_temp?.toFixed(1)}°C`, icon: Activity, color: 'text-orange-400' },
    { label: 'Motor Temp', value: `${sensorData.motor_temp?.toFixed(1)}°C`, icon: Gauge, color: 'text-red-400' },
    { label: 'Motor Vibration', value: sensorData.motor_vibration?.toFixed(2), icon: Activity, color: 'text-purple-400' },
    { label: 'Brake Pad Wear', value: `${sensorData.brake_pad_wear?.toFixed(1)}mm`, icon: Wrench, color: 'text-yellow-400' },
    { label: 'Motor Torque', value: `${sensorData.motor_torque?.toFixed(0)}Nm`, icon: Zap, color: 'text-cyan-400' },
    { label: 'Power Consumption', value: `${sensorData.power_consumption?.toFixed(1)}kW`, icon: Battery, color: 'text-pink-400' },
  ] : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-300">Loading diagnostics...</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const chartData = history.map((reading, idx) => ({
    time: idx,
    batteryTemp: reading.battery_temp,
    motorTemp: reading.motor_temp,
    soc: reading.soc,
    vibration: reading.motor_vibration * 10 // Scale for visibility
  })).reverse();

  return (
    <div className="space-y-6 animate-slideIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Real-Time Diagnostics</h1>
          <p className="text-gray-300">Continuous monitoring of vehicle telemetry</p>
        </div>
        <button
          onClick={loadDiagnostics}
          className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors"
        >
          <RefreshCw size={20} />
          Refresh
        </button>
      </div>

      {/* Status Banner */}
      {analysis && (
        <div className={`rounded-xl p-6 border ${getSeverityColor(analysis.severity)}`}>
          <div className="flex items-center gap-4">
            <AlertCircle size={40} />
            <div className="flex-1">
              <div className="font-bold text-2xl mb-1">{analysis.status}</div>
              <div className="text-sm opacity-90">
                {analysis.anomalies?.length || 0} anomalies detected • 
                Health Score: {(analysis.health_score * 100).toFixed(1)}% • 
                Failure Probability: {(analysis.failure_probability * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        {metrics.map((metric, idx) => {
          const Icon = metric.icon;
          return (
            <div key={idx} className="bg-white/10 rounded-xl p-4 border border-white/20 hover:bg-white/15 transition-all">
              <div className="flex items-center justify-between mb-2">
                <Icon className={metric.color} size={24} />
              </div>
              <div className="text-2xl font-bold text-white mb-1">{metric.value}</div>
              <div className="text-xs text-gray-300">{metric.label}</div>
            </div>
          );
        })}
      </div>

      {/* Sensor Trends Chart */}
      {chartData.length > 0 && (
        <div className="bg-white/10 rounded-xl p-6 border border-white/20">
          <h3 className="text-xl font-bold text-white mb-4">Sensor Trends (Last Hour)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="time" stroke="rgba(255,255,255,0.5)" />
              <YAxis stroke="rgba(255,255,255,0.5)" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(15, 23, 42, 0.9)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                  color: '#fff'
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="batteryTemp" stroke="#f97316" name="Battery Temp (°C)" />
              <Line type="monotone" dataKey="motorTemp" stroke="#ef4444" name="Motor Temp (°C)" />
              <Line type="monotone" dataKey="soc" stroke="#22c55e" name="SoC (%)" />
              <Line type="monotone" dataKey="vibration" stroke="#a855f7" name="Vibration (×10)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Anomalies */}
      {analysis?.anomalies && analysis.anomalies.length > 0 && (
        <div className="bg-white/10 rounded-xl p-6 border border-white/20">
          <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
            <AlertCircle className="text-orange-400" />
            Detected Anomalies
          </h3>
          <div className="space-y-3">
            {analysis.anomalies.map((anomaly, idx) => (
              <div key={idx} className="bg-white/5 rounded-lg p-4 border border-white/10">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-white">
                    {anomaly.system} - {anomaly.metric}
                  </span>
                  <span className={`px-3 py-1 rounded-full text-sm ${getSeverityColor(anomaly.severity)}`}>
                    {anomaly.severity}
                  </span>
                </div>
                <div className="text-gray-300 text-sm">
                  Current Value: <span className="font-mono text-yellow-400">{typeof anomaly.value === 'number' ? anomaly.value.toFixed(2) : anomaly.value}</span> | 
                  Threshold: <span className="font-mono text-blue-400">{typeof anomaly.threshold === 'number' ? anomaly.threshold.toFixed(2) : anomaly.threshold}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI Diagnosis Report */}
      {diagnosis?.report && (
        <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6">
          <h3 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
            <Activity className="text-blue-400" />
            AI Diagnosis Report
          </h3>
          <p className="text-gray-200 leading-relaxed">{diagnosis.report}</p>
          
          {diagnosis.issues && diagnosis.issues.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/20">
              <h4 className="text-lg font-semibold text-white mb-2">Identified Issues:</h4>
              <ul className="list-disc list-inside space-y-1 text-gray-300">
                {diagnosis.issues.map((issue, idx) => (
                  <li key={idx}>
                    {issue.component} ({issue.severity}) - 
                    {issue.rul_days && ` RUL: ${issue.rul_days.toFixed(1)} days`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Additional Sensor Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Tire Pressures */}
        <div className="bg-white/10 rounded-xl p-6 border border-white/20">
          <h3 className="text-lg font-bold text-white mb-4">Tire Pressures</h3>
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Front Left', value: sensorData?.tire_pressure_fl },
              { label: 'Front Right', value: sensorData?.tire_pressure_fr },
              { label: 'Rear Left', value: sensorData?.tire_pressure_rl },
              { label: 'Rear Right', value: sensorData?.tire_pressure_rr },
            ].map((tire, idx) => (
              <div key={idx} className="bg-white/5 p-3 rounded-lg">
                <div className="text-sm text-gray-400">{tire.label}</div>
                <div className="text-xl font-bold text-white">{tire.value?.toFixed(1)} PSI</div>
              </div>
            ))}
          </div>
        </div>

        {/* Environmental Conditions */}
        <div className="bg-white/10 rounded-xl p-6 border border-white/20">
          <h3 className="text-lg font-bold text-white mb-4">Environmental Conditions</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Ambient Temperature</span>
              <span className="text-white font-semibold">{sensorData?.ambient_temp?.toFixed(1)}°C</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Humidity</span>
              <span className="text-white font-semibold">{sensorData?.ambient_humidity?.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Driving Speed</span>
              <span className="text-white font-semibold">{sensorData?.driving_speed?.toFixed(1)} km/h</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-300">Route Condition</span>
              <span className="text-white font-semibold">
                {['Smooth', 'Fair', 'Rough', 'Very Rough'][sensorData?.route_roughness || 0]}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Diagnostics;