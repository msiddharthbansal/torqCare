import React, { useState, useEffect } from 'react';
import { AlertCircle, Activity, Calendar, MessageSquare, BarChart3, Settings, Car, Bell, CheckCircle, XCircle, Clock, Wrench, TrendingUp } from 'lucide-react';

// Main App Component
const TorqCare = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [sensorData, setSensorData] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [notifications, setNotifications] = useState([]);

  // Simulate real-time sensor data
  useEffect(() => {
    const interval = setInterval(() => {
      const hasIssue = Math.random() > 0.7;
      const newData = {
        timestamp: new Date().toISOString(),
        engineTemp: hasIssue ? 95 + Math.random() * 10 : 75 + Math.random() * 15,
        rpm: 800 + Math.random() * 3000,
        fuelLevel: 20 + Math.random() * 80,
        tirePressure: {
          fl: hasIssue ? 25 + Math.random() * 5 : 32 + Math.random() * 3,
          fr: 32 + Math.random() * 3,
          rl: 32 + Math.random() * 3,
          rr: 32 + Math.random() * 3
        },
        batteryVoltage: hasIssue ? 11 + Math.random() * 1 : 12.5 + Math.random() * 1.5,
        oilPressure: hasIssue ? 15 + Math.random() * 10 : 35 + Math.random() * 15,
        brakeFluidLevel: 70 + Math.random() * 30,
        speed: Math.random() * 120
      };
      
      setSensorData(newData);

      // Generate alerts for anomalies
      if (newData.engineTemp > 95) {
        addAlert('critical', 'Engine temperature critical', 'Engine');
      }
      if (newData.batteryVoltage < 12) {
        addAlert('warning', 'Low battery voltage detected', 'Battery');
      }
      if (newData.tirePressure.fl < 28) {
        addAlert('warning', 'Low tire pressure - Front Left', 'Tires');
      }
      if (newData.oilPressure < 20) {
        addAlert('critical', 'Low oil pressure', 'Engine');
      }
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const addAlert = (severity, message, system) => {
    const newAlert = {
      id: Date.now(),
      severity,
      message,
      system,
      timestamp: new Date().toISOString()
    };
    setAlerts(prev => [newAlert, ...prev.slice(0, 9)]);
    
    if (severity === 'critical') {
      addNotification('Critical Issue Detected', message, 'error');
    }
  };

  const addNotification = (title, message, type) => {
    const newNotif = {
      id: Date.now(),
      title,
      message,
      type,
      timestamp: new Date().toISOString()
    };
    setNotifications(prev => [newNotif, ...prev.slice(0, 4)]);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar currentPage={currentPage} setCurrentPage={setCurrentPage} notifications={notifications} />
      <div className="flex">
        <Sidebar currentPage={currentPage} setCurrentPage={setCurrentPage} />
        <main className="flex-1 p-6">
          {currentPage === 'dashboard' && <Dashboard sensorData={sensorData} alerts={alerts} predictions={predictions} />}
          {currentPage === 'monitoring' && <Monitoring sensorData={sensorData} alerts={alerts} />}
          {currentPage === 'chatbot' && <Chatbot sensorData={sensorData} />}
          {currentPage === 'appointments' && <Appointments appointments={appointments} setAppointments={setAppointments} addNotification={addNotification} />}
          {currentPage === 'feedback' && <Feedback addNotification={addNotification} />}
          {currentPage === 'admin' && <AdminPanel />}
        </main>
      </div>
    </div>
  );
};

// Navbar Component
const Navbar = ({ currentPage, setCurrentPage, notifications }) => {
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <nav className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Car className="w-8 h-8" />
          <div>
            <h1 className="text-2xl font-bold">TorqCare</h1>
            <p className="text-xs text-blue-100">Autonomous Vehicle Care Network</p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-right text-sm">
            <p className="font-semibold">Tesla Model 3</p>
            <p className="text-blue-100">VIN: 5YJ3E1EA7KF123456</p>
          </div>
          <div className="relative">
            <button 
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2 hover:bg-blue-700 rounded-full transition"
            >
              <Bell className="w-6 h-6" />
              {notifications.length > 0 && (
                <span className="absolute top-0 right-0 bg-red-500 text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {notifications.length}
                </span>
              )}
            </button>
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl z-50 text-gray-800">
                <div className="p-4 border-b">
                  <h3 className="font-semibold">Notifications</h3>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <p className="p-4 text-gray-500 text-sm">No notifications</p>
                  ) : (
                    notifications.map(notif => (
                      <div key={notif.id} className="p-4 border-b hover:bg-gray-50">
                        <div className="flex items-start space-x-2">
                          {notif.type === 'error' && <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />}
                          {notif.type === 'success' && <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />}
                          {notif.type === 'info' && <Bell className="w-5 h-5 text-blue-500 mt-0.5" />}
                          <div className="flex-1">
                            <p className="font-semibold text-sm">{notif.title}</p>
                            <p className="text-xs text-gray-600">{notif.message}</p>
                            <p className="text-xs text-gray-400 mt-1">
                              {new Date(notif.timestamp).toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

// Sidebar Component
const Sidebar = ({ currentPage, setCurrentPage }) => {
  const menuItems = [
    { id: 'dashboard', icon: Activity, label: 'Dashboard' },
    { id: 'monitoring', icon: TrendingUp, label: 'Live Monitoring' },
    { id: 'chatbot', icon: MessageSquare, label: 'AI Assistant' },
    { id: 'appointments', icon: Calendar, label: 'Appointments' },
    { id: 'feedback', icon: BarChart3, label: 'Feedback' },
    { id: 'admin', icon: Settings, label: 'Admin Panel' }
  ];

  return (
    <aside className="w-64 bg-white shadow-lg min-h-screen">
      <div className="p-4">
        {menuItems.map(item => (
          <button
            key={item.id}
            onClick={() => setCurrentPage(item.id)}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg mb-2 transition ${
              currentPage === item.id 
                ? 'bg-blue-500 text-white' 
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </button>
        ))}
      </div>
    </aside>
  );
};

// Dashboard Component
const Dashboard = ({ sensorData, alerts, predictions }) => {
  const criticalAlerts = alerts.filter(a => a.severity === 'critical').length;
  const warningAlerts = alerts.filter(a => a.severity === 'warning').length;

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-800">Vehicle Health Dashboard</h2>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <MetricCard 
          title="Vehicle Status" 
          value={criticalAlerts > 0 ? "Critical" : warningAlerts > 0 ? "Warning" : "Healthy"}
          icon={Activity}
          color={criticalAlerts > 0 ? "red" : warningAlerts > 0 ? "yellow" : "green"}
        />
        <MetricCard 
          title="Critical Alerts" 
          value={criticalAlerts}
          icon={AlertCircle}
          color="red"
        />
        <MetricCard 
          title="Warnings" 
          value={warningAlerts}
          icon={Bell}
          color="yellow"
        />
        <MetricCard 
          title="Predictions" 
          value={predictions.length}
          icon={TrendingUp}
          color="blue"
        />
      </div>

      {/* Live Sensor Data */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Live Telemetry</h3>
        {sensorData ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <SensorDisplay label="Engine Temp" value={`${sensorData.engineTemp.toFixed(1)}°C`} critical={sensorData.engineTemp > 95} />
            <SensorDisplay label="RPM" value={sensorData.rpm.toFixed(0)} />
            <SensorDisplay label="Fuel Level" value={`${sensorData.fuelLevel.toFixed(1)}%`} />
            <SensorDisplay label="Battery" value={`${sensorData.batteryVoltage.toFixed(1)}V`} critical={sensorData.batteryVoltage < 12} />
            <SensorDisplay label="Speed" value={`${sensorData.speed.toFixed(0)} km/h`} />
            <SensorDisplay label="Oil Pressure" value={`${sensorData.oilPressure.toFixed(0)} PSI`} critical={sensorData.oilPressure < 20} />
            <SensorDisplay label="Brake Fluid" value={`${sensorData.brakeFluidLevel.toFixed(0)}%`} />
            <SensorDisplay label="Tire FL" value={`${sensorData.tirePressure.fl.toFixed(1)} PSI`} critical={sensorData.tirePressure.fl < 28} />
          </div>
        ) : (
          <p className="text-gray-500">Loading sensor data...</p>
        )}
      </div>

      {/* Recent Alerts */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Recent Alerts</h3>
        <div className="space-y-2">
          {alerts.slice(0, 5).map(alert => (
            <div key={alert.id} className={`p-3 rounded border-l-4 ${
              alert.severity === 'critical' ? 'bg-red-50 border-red-500' : 'bg-yellow-50 border-yellow-500'
            }`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AlertCircle className={`w-5 h-5 ${alert.severity === 'critical' ? 'text-red-500' : 'text-yellow-500'}`} />
                  <div>
                    <p className="font-semibold text-sm">{alert.message}</p>
                    <p className="text-xs text-gray-600">{alert.system} • {new Date(alert.timestamp).toLocaleTimeString()}</p>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  alert.severity === 'critical' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {alert.severity.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Monitoring Component
const Monitoring = ({ sensorData, alerts }) => {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-800">Real-Time Monitoring</h2>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Detailed Telemetry Stream</h3>
        {sensorData && (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <TelemetryChart label="Engine Temperature" value={sensorData.engineTemp} unit="°C" max={120} warning={90} critical={95} />
              <TelemetryChart label="Battery Voltage" value={sensorData.batteryVoltage} unit="V" max={15} warning={12.5} critical={12} />
              <TelemetryChart label="Oil Pressure" value={sensorData.oilPressure} unit="PSI" max={60} warning={25} critical={20} />
              <TelemetryChart label="RPM" value={sensorData.rpm} unit="" max={7000} />
            </div>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Alert History</h3>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {alerts.map(alert => (
            <div key={alert.id} className="p-3 border rounded hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-sm">{alert.message}</p>
                  <p className="text-xs text-gray-500">{new Date(alert.timestamp).toLocaleString()}</p>
                </div>
                <span className={`px-2 py-1 rounded text-xs ${
                  alert.severity === 'critical' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'
                }`}>
                  {alert.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Chatbot Component
const Chatbot = ({ sensorData }) => {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I\'m your TorqCare AI assistant. I can help you with vehicle diagnostics, maintenance questions, and real-time telemetry analysis. How can I assist you today?' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      let response = '';
      
      if (input.toLowerCase().includes('temperature') || input.toLowerCase().includes('engine')) {
        response = `Based on current telemetry, your engine temperature is ${sensorData?.engineTemp.toFixed(1)}°C. ${sensorData?.engineTemp > 95 ? 'This is above normal operating range. I recommend pulling over safely and letting the engine cool down. This could indicate a coolant leak or thermostat issue.' : 'This is within normal operating range.'}`;
      } else if (input.toLowerCase().includes('battery')) {
        response = `Your battery voltage is currently ${sensorData?.batteryVoltage.toFixed(1)}V. ${sensorData?.batteryVoltage < 12 ? 'This is below optimal levels. You may need a battery replacement soon or have an alternator issue.' : 'Battery health is good.'}`;
      } else if (input.toLowerCase().includes('maintenance') || input.toLowerCase().includes('service')) {
        response = 'Based on your vehicle\'s mileage and maintenance history, your next service is recommended in 2,500 km or 2 months. This includes oil change, filter replacement, and brake inspection. Would you like me to schedule an appointment?';
      } else if (input.toLowerCase().includes('tire')) {
        response = `Current tire pressures: FL: ${sensorData?.tirePressure.fl.toFixed(1)} PSI, FR: ${sensorData?.tirePressure.fr.toFixed(1)} PSI, RL: ${sensorData?.tirePressure.rl.toFixed(1)} PSI, RR: ${sensorData?.tirePressure.rr.toFixed(1)} PSI. ${sensorData?.tirePressure.fl < 28 ? 'Front left tire is underinflated. Please inflate to 32 PSI.' : 'All tires are properly inflated.'}`;
      } else {
        response = 'I can help you with vehicle diagnostics, maintenance scheduling, real-time telemetry analysis, and answer questions about your vehicle. What specific information would you like to know?';
      }

      setMessages(prev => [...prev, { role: 'assistant', content: response }]);
      setIsTyping(false);
    }, 1500);
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-800">AI Assistant</h2>
      
      <div className="bg-white rounded-lg shadow h-[600px] flex flex-col">
        <div className="p-4 border-b bg-gradient-to-r from-blue-50 to-blue-100">
          <div className="flex items-center space-x-2">
            <MessageSquare className="w-6 h-6 text-blue-600" />
            <div>
              <h3 className="font-semibold">TorqCare AI Assistant</h3>
              <p className="text-xs text-gray-600">Powered by Multi-Agent Network</p>
            </div>
          </div>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] p-3 rounded-lg ${
                msg.role === 'user' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                <p className="text-sm">{msg.content}</p>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-gray-100 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Analyzing...</p>
              </div>
            </div>
          )}
        </div>
        
        <div className="p-4 border-t">
          <div className="flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask about your vehicle..."
              className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleSend}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Appointments Component
const Appointments = ({ appointments, setAppointments, addNotification }) => {
  const [showBooking, setShowBooking] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [urgency, setUrgency] = useState('routine');

  const workshops = [
    { id: 1, name: 'AutoCare Center', location: 'Downtown', rating: 4.8, distance: '2.5 km' },
    { id: 2, name: 'Premium Motors', location: 'Westside', rating: 4.6, distance: '5.1 km' },
    { id: 3, name: 'QuickFix Garage', location: 'Eastside', rating: 4.9, distance: '3.8 km' }
  ];

  const generateTimeSlots = () => {
    const slots = [];
    const today = new Date();
    for (let day = 0; day < 5; day++) {
      const date = new Date(today);
      date.setDate(date.getDate() + day);
      const times = urgency === 'critical' 
        ? ['09:00 AM', '11:00 AM', '02:00 PM'] 
        : ['09:00 AM', '11:00 AM', '02:00 PM', '04:00 PM'];
      
      times.forEach(time => {
        slots.push({
          date: date.toLocaleDateString(),
          time,
          available: Math.random() > 0.3
        });
      });
    }
    return slots;
  };

  const handleBooking = () => {
    if (selectedSlot) {
      const newAppointment = {
        id: Date.now(),
        workshop: workshops[0],
        slot: selectedSlot,
        urgency,
        status: 'pending',
        createdAt: new Date().toISOString()
      };
      setAppointments(prev => [...prev, newAppointment]);
      addNotification('Appointment Requested', `Your ${urgency} maintenance appointment has been requested for ${selectedSlot.date} at ${selectedSlot.time}`, 'success');
      setShowBooking(false);
      setSelectedSlot(null);
    }
  };

  const handleAccept = (id) => {
    setAppointments(prev => prev.map(apt => 
      apt.id === id ? { ...apt, status: 'confirmed' } : apt
    ));
    addNotification('Appointment Confirmed', 'Your appointment has been confirmed!', 'success');
  };

  const handleReject = (id) => {
    setAppointments(prev => prev.filter(apt => apt.id !== id));
    addNotification('Appointment Cancelled', 'Your appointment has been cancelled', 'info');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold text-gray-800">Appointments</h2>
        <button
          onClick={() => setShowBooking(true)}
          className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition flex items-center space-x-2"
        >
          <Calendar className="w-5 h-5" />
          <span>Book Appointment</span>
        </button>
      </div>

      {/* Upcoming Appointments */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Your Appointments</h3>
        <div className="space-y-4">
          {appointments.length === 0 ? (
            <p className="text-gray-500 text-center py-8">No appointments scheduled</p>
          ) : (
            appointments.map(apt => (
              <div key={apt.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h4 className="font-semibold">{apt.workshop.name}</h4>
                    <p className="text-sm text-gray-600">{apt.workshop.location} • {apt.workshop.distance}</p>
                  </div>
                  <span className={`px-3 py-1 rounded text-sm font-semibold ${
                    apt.status === 'confirmed' ? 'bg-green-100 text-green-700' :
                    apt.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {apt.status.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center space-x-4 text-sm text-gray-700 mb-3">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-4 h-4" />
                    <span>{apt.slot.date}</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <Clock className="w-4 h-4" />
                    <span>{apt.slot.time}</span>
                  </span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    apt.urgency === 'critical' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {apt.urgency}
                  </span>
                </div>
                {apt.status === 'pending' && (
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleAccept(apt.id)}
                      className="flex-1 px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 transition flex items-center justify-center space-x-1"
                    >
                      <CheckCircle className="w-4 h-4" />
                      <span>Accept</span>
                    </button>
                    <button
                      onClick={() => handleReject(apt.id)}
                      className="flex-1 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 transition flex items-center justify-center space-x-1"
                    >
                      <XCircle className="w-4 h-4" />
                      <span>Reject</span>
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Booking Modal */}
      {showBooking && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-2xl font-bold">Book Appointment</h3>
                <button onClick={() => setShowBooking(false)} className="text-gray-500 hover:text-gray-700">
                  <XCircle className="w-6 h-6" />
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Urgency Selection */}
              <div>
                <label className="block text-sm font-semibold mb-2">Appointment Type</label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setUrgency('routine')}
                    className={`p-4 border-2 rounded-lg ${urgency === 'routine' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}
                  >
                    <p className="font-semibold">Routine Maintenance</p>
                    <p className="text-sm text-gray-600">Scheduled service</p>
                  </button>
                  <button
                    onClick={() => setUrgency('critical')}
                    className={`p-4 border-2 rounded-lg ${urgency === 'critical' ? 'border-red-500 bg-red-50' : 'border-gray-200'}`}
                  >
                    <p className="font-semibold">Critical Issue</p>
                    <p className="text-sm text-gray-600">Urgent repair needed</p>
                  </button>
                </div>
              </div>

              {/* Workshop Selection */}
              <div>
                <label className="block text-sm font-semibold mb-2">Select Workshop</label>
                <div className="space-y-3">
                  {workshops.map(shop => (
                    <div key={shop.id} className="p-4 border rounded-lg hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold">{shop.name}</h4>
                          <p className="text-sm text-gray-600">{shop.location} • {shop.distance}</p>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-semibold">⭐ {shop.rating}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Time Slots */}
              <div>
                <label className="block text-sm font-semibold mb-2">Available Time Slots</label>
                <div className="grid grid-cols-3 gap-3">
                  {generateTimeSlots().map((slot, idx) => (
                    <button
                      key={idx}
                      onClick={() => slot.available && setSelectedSlot(slot)}
                      disabled={!slot.available}
                      className={`p-3 border rounded-lg text-sm ${
                        selectedSlot === slot ? 'border-blue-500 bg-blue-50' :
                        slot.available ? 'border-gray-200 hover:border-blue-300' :
                        'border-gray-200 bg-gray-100 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      <p className="font-semibold">{slot.date}</p>
                      <p className="text-xs">{slot.time}</p>
                    </button>
                  ))}
                </div>
              </div>

              <button
                onClick={handleBooking}
                disabled={!selectedSlot}
                className={`w-full py-3 rounded-lg font-semibold ${
                  selectedSlot 
                    ? 'bg-blue-500 text-white hover:bg-blue-600' 
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Confirm Booking
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Feedback Component
const Feedback = ({ addNotification }) => {
  const [feedbackType, setFeedbackType] = useState('repair');
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState('');

  const handleSubmit = () => {
    if (rating > 0 && comment) {
      addNotification('Feedback Submitted', 'Thank you for your feedback! It has been shared with the manufacturer and service center.', 'success');
      setRating(0);
      setComment('');
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-800">Feedback & Quality Insights</h2>
      
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Submit Feedback</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold mb-2">Feedback Type</label>
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => setFeedbackType('repair')}
                className={`p-3 border-2 rounded-lg ${feedbackType === 'repair' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}
              >
                <Wrench className="w-6 h-6 mx-auto mb-1 text-blue-500" />
                <p className="font-semibold text-sm">Repair Experience</p>
              </button>
              <button
                onClick={() => setFeedbackType('vehicle')}
                className={`p-3 border-2 rounded-lg ${feedbackType === 'vehicle' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`}
              >
                <Car className="w-6 h-6 mx-auto mb-1 text-blue-500" />
                <p className="font-semibold text-sm">Vehicle Performance</p>
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2">Rating</label>
            <div className="flex space-x-2">
              {[1, 2, 3, 4, 5].map(star => (
                <button
                  key={star}
                  onClick={() => setRating(star)}
                  className="text-3xl"
                >
                  {star <= rating ? '⭐' : '☆'}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold mb-2">Comments</label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="Share your experience..."
              className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={5}
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={rating === 0 || !comment}
            className={`w-full py-3 rounded-lg font-semibold ${
              rating > 0 && comment
                ? 'bg-blue-500 text-white hover:bg-blue-600'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            Submit Feedback
          </button>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Quality Insights Dashboard</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-600">Average Repair Satisfaction</p>
            <p className="text-3xl font-bold text-blue-600">4.7/5</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg">
            <p className="text-sm text-gray-600">Vehicle Reliability Score</p>
            <p className="text-3xl font-bold text-green-600">92%</p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg">
            <p className="text-sm text-gray-600">Feedback Submitted</p>
            <p className="text-3xl font-bold text-purple-600">43</p>
          </div>
          <div className="p-4 bg-orange-50 rounded-lg">
            <p className="text-sm text-gray-600">Issues Resolved</p>
            <p className="text-3xl font-bold text-orange-600">38/43</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Admin Panel Component
const AdminPanel = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-800">Admin Panel</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4">Multi-Agent Status</h3>
          <div className="space-y-3">
            <AgentStatus name="Data Analysis Agent" status="active" tasks={156} />
            <AgentStatus name="Diagnosis Agent" status="active" tasks={23} />
            <AgentStatus name="Customer Engagement Agent" status="active" tasks={89} />
            <AgentStatus name="Scheduling Agent" status="active" tasks={45} />
            <AgentStatus name="Quality Insights Agent" status="active" tasks={67} />
            <AgentStatus name="Feedback Agent" status="active" tasks={34} />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-xl font-semibold mb-4">System Metrics</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b">
              <span className="text-gray-600">Active Vehicles</span>
              <span className="font-bold">1,247</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b">
              <span className="text-gray-600">Real-time Connections</span>
              <span className="font-bold">943</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b">
              <span className="text-gray-600">Predictions Today</span>
              <span className="font-bold">178</span>
            </div>
            <div className="flex items-center justify-between pb-2 border-b">
              <span className="text-gray-600">Appointments Scheduled</span>
              <span className="font-bold">89</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Feedback Collected</span>
              <span className="font-bold">234</span>
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-xl font-semibold mb-4">Database Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 bg-blue-50 rounded-lg text-center">
            <p className="text-sm text-gray-600 mb-1">Sensor Data</p>
            <p className="text-2xl font-bold text-blue-600">2.3M</p>
            <p className="text-xs text-gray-500">records</p>
          </div>
          <div className="p-4 bg-green-50 rounded-lg text-center">
            <p className="text-sm text-gray-600 mb-1">Maintenance History</p>
            <p className="text-2xl font-bold text-green-600">45K</p>
            <p className="text-xs text-gray-500">records</p>
          </div>
          <div className="p-4 bg-purple-50 rounded-lg text-center">
            <p className="text-sm text-gray-600 mb-1">Appointments</p>
            <p className="text-2xl font-bold text-purple-600">12K</p>
            <p className="text-xs text-gray-500">records</p>
          </div>
          <div className="p-4 bg-orange-50 rounded-lg text-center">
            <p className="text-sm text-gray-600 mb-1">Feedback</p>
            <p className="text-2xl font-bold text-orange-600">8.9K</p>
            <p className="text-xs text-gray-500">records</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper Components
const MetricCard = ({ title, value, icon: Icon, color }) => {
  const colors = {
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    blue: 'bg-blue-50 text-blue-600'
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-2">
        <p className="text-gray-600 text-sm">{title}</p>
        <Icon className={`w-8 h-8 ${colors[color]}`} />
      </div>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  );
};

const SensorDisplay = ({ label, value, critical }) => (
  <div className={`p-3 rounded-lg ${critical ? 'bg-red-50 border border-red-200' : 'bg-gray-50'}`}>
    <p className="text-xs text-gray-600 mb-1">{label}</p>
    <p className={`text-lg font-bold ${critical ? 'text-red-600' : 'text-gray-800'}`}>{value}</p>
  </div>
);

const TelemetryChart = ({ label, value, unit, max, warning, critical }) => {
  const percentage = (value / max) * 100;
  let barColor = 'bg-green-500';
  if (critical && value >= critical) barColor = 'bg-red-500';
  else if (warning && value >= warning) barColor = 'bg-yellow-500';

  return (
    <div className="p-4 border rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <p className="font-semibold">{label}</p>
        <p className="text-lg font-bold">{value.toFixed(1)} {unit}</p>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div className={`${barColor} h-3 rounded-full transition-all duration-300`} style={{ width: `${Math.min(percentage, 100)}%` }} />
      </div>
    </div>
  );
};

const AgentStatus = ({ name, status, tasks }) => (
  <div className="flex items-center justify-between p-3 border rounded">
    <div className="flex items-center space-x-3">
      <div className={`w-3 h-3 rounded-full ${status === 'active' ? 'bg-green-500' : 'bg-gray-400'}`} />
      <span className="font-medium">{name}</span>
    </div>
    <span className="text-sm text-gray-600">{tasks} tasks processed</span>
  </div>
);

export default TorqCare;