import React, { useState, useEffect } from 'react';
import { Activity, Car, MessageSquare, Wrench, Bell, Settings, LogOut } from 'lucide-react';

// Import components
import Dashboard from './components/Dashboard';
import Diagnostics from './components/Diagnostics';
import Chatbot from './components/Chatbot';
import MaintenanceHistory from './components/MaintenanceHistory';
import Navbar from './components/Navbar';

// Import API service
import api from './services/api';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [selectedVehicle, setSelectedVehicle] = useState('EV-00001');
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);

  // Load vehicles on mount
  useEffect(() => {
    loadVehicles();
  }, []);

  const loadVehicles = async () => {
    try {
      const data = await api.getVehicles();
      setVehicles(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load vehicles:', error);
      setLoading(false);
    }
  };

  const pages = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity, component: Dashboard },
    { id: 'diagnostics', label: 'Diagnostics', icon: Activity, component: Diagnostics },
    { id: 'chatbot', label: 'Assistant', icon: MessageSquare, component: Chatbot },
    { id: 'maintenance', label: 'Maintenance', icon: Wrench, component: MaintenanceHistory },
  ];

  const CurrentComponent = pages.find(p => p.id === currentPage)?.component || Dashboard;

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-white text-lg">Loading TorqCare...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      <Navbar
        currentPage={currentPage}
        setCurrentPage={setCurrentPage}
        selectedVehicle={selectedVehicle}
        setSelectedVehicle={setSelectedVehicle}
        vehicles={vehicles}
        pages={pages}
        notifications={notifications}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <CurrentComponent
          vehicleId={selectedVehicle}
          onNavigate={setCurrentPage}
        />
      </main>

      {/* Footer */}
      <footer className="bg-black/30 backdrop-blur-lg border-t border-white/10 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="text-gray-400 text-sm">
              © 2025 TorqCare. Powered by Multi-Agent AI.
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-400">
              <a href="#" className="hover:text-white transition-colors">Privacy</a>
              <a href="#" className="hover:text-white transition-colors">Terms</a>
              <a href="#" className="hover:text-white transition-colors">Support</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;