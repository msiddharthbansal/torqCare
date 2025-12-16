import React, { useState } from 'react';
import { Car, Bell, ChevronDown } from 'lucide-react';

const Navbar = ({ currentPage, setCurrentPage, selectedVehicle, setSelectedVehicle, vehicles, pages, notifications }) => {
  const [showVehicleDropdown, setShowVehicleDropdown] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  return (
    <nav className="bg-black/30 backdrop-blur-lg border-b border-white/10 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setCurrentPage('dashboard')}>
            <div className="bg-blue-500/20 p-2 rounded-lg">
              <Car className="text-blue-400" size={28} />
            </div>
            <div>
              <div className="text-xl font-bold text-white">TorqCare</div>
              <div className="text-xs text-gray-400">Multi-Agent Network</div>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-2">
            {pages.map(page => {
              const Icon = page.icon;
              const isActive = currentPage === page.id;
              
              return (
                <button
                  key={page.id}
                  onClick={() => setCurrentPage(page.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                    isActive
                      ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/50'
                      : 'bg-white/10 text-gray-300 hover:bg-white/20'
                  }`}
                >
                  <Icon size={18} />
                  <span className="font-medium">{page.label}</span>
                </button>
              );
            })}
          </div>

          {/* Right Side - Vehicle Selector & Notifications */}
          <div className="flex items-center gap-4">
            {/* Vehicle Selector */}
            <div className="relative">
              <button
                onClick={() => setShowVehicleDropdown(!showVehicleDropdown)}
                className="flex items-center gap-2 bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg transition-all border border-white/20"
              >
                <Car size={18} className="text-blue-400" />
                <span className="text-white font-medium">{selectedVehicle}</span>
                <ChevronDown size={16} className="text-gray-400" />
              </button>

              {showVehicleDropdown && (
                <div className="absolute right-0 mt-2 w-56 bg-slate-800 border border-white/20 rounded-lg shadow-xl overflow-hidden z-50">
                  <div className="py-1 max-h-64 overflow-y-auto">
                    {vehicles.slice(0, 10).map(vehicle => (
                      <button
                        key={vehicle.vehicle_id}
                        onClick={() => {
                          setSelectedVehicle(vehicle.vehicle_id);
                          setShowVehicleDropdown(false);
                        }}
                        className={`w-full text-left px-4 py-2 hover:bg-white/10 transition-colors ${
                          selectedVehicle === vehicle.vehicle_id ? 'bg-blue-500/20 text-blue-300' : 'text-gray-300'
                        }`}
                      >
                        <div className="font-medium">{vehicle.vehicle_id}</div>
                        <div className="text-xs text-gray-400">{vehicle.model || 'Tesla Model 3'}</div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Notifications */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative bg-white/10 hover:bg-white/20 p-2 rounded-lg transition-all border border-white/20"
              >
                <Bell size={20} className="text-gray-300" />
                {notifications.length > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {notifications.length}
                  </span>
                )}
              </button>

              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-slate-800 border border-white/20 rounded-lg shadow-xl overflow-hidden z-50">
                  <div className="p-4 border-b border-white/10">
                    <h3 className="font-semibold text-white">Notifications</h3>
                  </div>
                  <div className="py-2 max-h-96 overflow-y-auto">
                    {notifications.length === 0 ? (
                      <div className="px-4 py-8 text-center text-gray-400">
                        No new notifications
                      </div>
                    ) : (
                      notifications.map((notif, idx) => (
                        <div key={idx} className="px-4 py-3 hover:bg-white/5 border-b border-white/5">
                          <div className="text-sm text-white">{notif.message}</div>
                          <div className="text-xs text-gray-400 mt-1">{notif.time}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      <div className="md:hidden border-t border-white/10">
        <div className="flex justify-around py-2">
          {pages.map(page => {
            const Icon = page.icon;
            const isActive = currentPage === page.id;
            
            return (
              <button
                key={page.id}
                onClick={() => setCurrentPage(page.id)}
                className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg ${
                  isActive ? 'text-blue-400' : 'text-gray-400'
                }`}
              >
                <Icon size={20} />
                <span className="text-xs">{page.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;