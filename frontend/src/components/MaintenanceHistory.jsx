import React, { useState, useEffect } from 'react';
import { Calendar, Clock, DollarSign, Wrench, CheckCircle, AlertCircle, MapPin, Star } from 'lucide-react';
import api from '../services/api';

const MaintenanceHistory = ({ vehicleId }) => {
  const [history, setHistory] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('upcoming'); // 'upcoming' or 'history'
  const [showBooking, setShowBooking] = useState(false);
  const [proposal, setProposal] = useState(null);

  useEffect(() => {
    loadData();
  }, [vehicleId]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [histData, apptData] = await Promise.all([
        api.getMaintenanceHistory(vehicleId),
        api.getAppointments(vehicleId)
      ]);
      setHistory(histData);
      setAppointments(apptData);
    } catch (error) {
      console.error('Maintenance data error:', error);
    } finally {
      setLoading(false);
    }
  };

  const requestAppointment = async () => {
    try {
      setLoading(true);
      const proposalData = await api.proposeAppointment(vehicleId);
      setProposal(proposalData);
      setShowBooking(true);
    } catch (error) {
      console.error('Appointment proposal error:', error);
      alert('Failed to create appointment proposal');
    } finally {
      setLoading(false);
    }
  };

  const confirmBooking = async (option) => {
    try {
      await api.confirmAppointment(vehicleId, option);
      alert('Appointment confirmed successfully!');
      setShowBooking(false);
      loadData();
    } catch (error) {
      console.error('Booking confirmation error:', error);
      alert('Failed to confirm appointment');
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      Critical: 'text-red-400 bg-red-500/20',
      High: 'text-orange-400 bg-orange-500/20',
      Medium: 'text-yellow-400 bg-yellow-500/20',
      Low: 'text-blue-400 bg-blue-500/20'
    };
    return colors[severity] || colors.Low;
  };

  const getStatusColor = (status) => {
    const colors = {
      Scheduled: 'text-blue-400 bg-blue-500/20',
      Confirmed: 'text-green-400 bg-green-500/20',
      Completed: 'text-gray-400 bg-gray-500/20',
      Cancelled: 'text-red-400 bg-red-500/20'
    };
    return colors[status] || colors.Scheduled;
  };

  if (loading && !history.length && !appointments.length) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="spinner mx-auto mb-4"></div>
          <p className="text-gray-300">Loading maintenance data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-slideIn">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Maintenance & Service</h1>
          <p className="text-gray-300">Track your vehicle's service history and appointments</p>
        </div>
        <button
          onClick={requestAppointment}
          className="flex items-center gap-2 bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg transition-colors"
        >
          <Calendar size={20} />
          Book Service
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-white/20">
        <button
          onClick={() => setActiveTab('upcoming')}
          className={`px-6 py-3 font-semibold transition-all ${
            activeTab === 'upcoming'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Upcoming Appointments ({appointments.filter(a => a.status !== 'Completed').length})
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-6 py-3 font-semibold transition-all ${
            activeTab === 'history'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          Service History ({history.length})
        </button>
      </div>

      {/* Appointment Proposal Modal */}
      {showBooking && proposal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-white/20">
            <div className="p-6 border-b border-white/20">
              <h2 className="text-2xl font-bold text-white">Book Service Appointment</h2>
              <p className="text-gray-300 mt-1">{proposal.proposal_text || 'Select your preferred time slot'}</p>
            </div>

            {proposal.status === 'proposal_ready' && (
              <div className="p-6 space-y-4">
                {/* Recommended Option */}
                <div className="bg-blue-500/10 border-2 border-blue-500/30 rounded-xl p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Star className="text-yellow-400 fill-yellow-400" size={24} />
                    <span className="text-lg font-bold text-white">Recommended</span>
                  </div>
                  <AppointmentOption
                    option={proposal.recommended_option}
                    onConfirm={confirmBooking}
                    isRecommended
                  />
                </div>

                {/* Alternative Options */}
                {proposal.alternative_options && proposal.alternative_options.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-3">Alternative Times</h3>
                    <div className="space-y-3">
                      {proposal.alternative_options.map((option, idx) => (
                        <AppointmentOption
                          key={idx}
                          option={option}
                          onConfirm={confirmBooking}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="p-6 border-t border-white/20 flex justify-end gap-3">
              <button
                onClick={() => setShowBooking(false)}
                className="px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upcoming Appointments */}
      {activeTab === 'upcoming' && (
        <div className="space-y-4">
          {appointments.filter(a => a.status !== 'Completed').length === 0 ? (
            <div className="bg-white/10 rounded-xl p-12 text-center border border-white/20">
              <Calendar className="text-gray-400 mx-auto mb-4" size={48} />
              <h3 className="text-xl font-semibold text-white mb-2">No Upcoming Appointments</h3>
              <p className="text-gray-300 mb-6">Book a service appointment to keep your vehicle in top condition</p>
              <button
                onClick={requestAppointment}
                className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-lg transition-colors"
              >
                Book Service Now
              </button>
            </div>
          ) : (
            appointments
              .filter(a => a.status !== 'Completed')
              .map(apt => (
                <div key={apt.appointment_id} className="bg-white/10 rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-semibold text-white mb-1">{apt.service_type}</h3>
                      <p className="text-gray-300 text-sm">Appointment ID: {apt.appointment_id}</p>
                    </div>
                    <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getStatusColor(apt.status)}`}>
                      {apt.status}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="flex items-center gap-2 text-gray-300">
                      <Calendar size={18} className="text-blue-400" />
                      <div>
                        <div className="text-xs text-gray-400">Date</div>
                        <div className="font-semibold">{new Date(apt.scheduled_date).toLocaleDateString()}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-gray-300">
                      <Clock size={18} className="text-purple-400" />
                      <div>
                        <div className="text-xs text-gray-400">Time</div>
                        <div className="font-semibold">{new Date(apt.scheduled_date).toLocaleTimeString()}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-gray-300">
                      <Clock size={18} className="text-orange-400" />
                      <div>
                        <div className="text-xs text-gray-400">Duration</div>
                        <div className="font-semibold">{apt.estimated_duration_hours}h</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-gray-300">
                      <DollarSign size={18} className="text-green-400" />
                      <div>
                        <div className="text-xs text-gray-400">Est. Cost</div>
                        <div className="font-semibold">${apt.estimated_cost}</div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
          )}
        </div>
      )}

      {/* Service History */}
      {activeTab === 'history' && (
        <div className="space-y-4">
          {history.length === 0 ? (
            <div className="bg-white/10 rounded-xl p-12 text-center border border-white/20">
              <Wrench className="text-gray-400 mx-auto mb-4" size={48} />
              <h3 className="text-xl font-semibold text-white mb-2">No Service History</h3>
              <p className="text-gray-300">Your maintenance records will appear here</p>
            </div>
          ) : (
            history.map(record => (
              <div key={record.maintenance_id} className="bg-white/10 rounded-xl p-6 border border-white/20">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-xl font-semibold text-white">{record.issue_detected}</h3>
                      <span className={`px-3 py-1 rounded-full text-sm ${getSeverityColor(record.severity)}`}>
                        {record.severity}
                      </span>
                    </div>
                    <p className="text-gray-300 text-sm mb-2">{record.component} • {record.maintenance_type}</p>
                    <p className="text-gray-400 text-sm">{record.description}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">${record.cost_usd}</div>
                    <div className="text-sm text-gray-400">{new Date(record.maintenance_date).toLocaleDateString()}</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-white/20">
                  <div className="text-sm">
                    <div className="text-gray-400">Duration</div>
                    <div className="text-white font-semibold">{record.repair_duration_hours}h</div>
                  </div>
                  <div className="text-sm">
                    <div className="text-gray-400">Downtime</div>
                    <div className="text-white font-semibold">{record.downtime_hours}h</div>
                  </div>
                  <div className="text-sm">
                    <div className="text-gray-400">Workshop</div>
                    <div className="text-white font-semibold">{record.workshop_id}</div>
                  </div>
                  <div className="text-sm">
                    <div className="text-gray-400">Parts Replaced</div>
                    <div className="text-white font-semibold">{record.parts_replaced ? 'Yes' : 'No'}</div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

// Appointment Option Component
const AppointmentOption = ({ option, onConfirm, isRecommended }) => (
  <div className={`bg-white/5 rounded-lg p-4 ${!isRecommended && 'border border-white/10'}`}>
    <div className="flex items-start justify-between mb-3">
      <div>
        <h4 className="font-semibold text-white mb-1">{option.workshop_name}</h4>
        <div className="flex items-center gap-2 text-sm text-gray-300">
          <MapPin size={14} />
          <span>{option.city}</span>
          <span>•</span>
          <div className="flex items-center gap-1">
            <Star size={14} className="text-yellow-400 fill-yellow-400" />
            <span>{option.rating}/5.0</span>
          </div>
        </div>
      </div>
    </div>

    <div className="grid grid-cols-2 gap-3 mb-4">
      <div className="flex items-center gap-2 text-sm text-gray-300">
        <Calendar size={16} className="text-blue-400" />
        <span>{option.date} at {option.time}</span>
      </div>
      <div className="flex items-center gap-2 text-sm text-gray-300">
        <Clock size={16} className="text-purple-400" />
        <span>~{option.estimated_duration}h</span>
      </div>
      <div className="flex items-center gap-2 text-sm text-gray-300">
        <DollarSign size={16} className="text-green-400" />
        <span>${option.estimated_cost_min}-${option.estimated_cost_max}</span>
      </div>
      <div className="flex items-center gap-2 text-sm text-gray-300">
        <Wrench size={16} className="text-orange-400" />
        <span>{option.specialties?.split(',')[0] || 'General'}</span>
      </div>
    </div>

    <button
      onClick={() => onConfirm(option)}
      className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 rounded-lg transition-colors flex items-center justify-center gap-2"
    >
      <CheckCircle size={18} />
      Confirm Appointment
    </button>
  </div>
);

export default MaintenanceHistory;