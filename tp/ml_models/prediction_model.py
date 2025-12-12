"""
TorqCare ML Prediction Models
Predictive Analytics for Vehicle Failure Detection
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

class VehicleFailurePredictionModel:
    """
    Multi-class prediction model for various vehicle system failures
    """
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_names = []
        self.failure_types = [
            'engine_overheating',
            'battery_failure',
            'brake_system',
            'transmission_issue',
            'tire_failure',
            'oil_system',
            'electrical_system'
        ]
        
        # Initialize models for each failure type
        for failure_type in self.failure_types:
            self.models[failure_type] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.scalers[failure_type] = StandardScaler()
    
    def prepare_features(self, sensor_data: Dict) -> np.ndarray:
        """
        Prepare features from raw sensor data
        """
        features = [
            sensor_data.get('engine_temp', 0),
            sensor_data.get('rpm', 0),
            sensor_data.get('fuel_level', 0),
            sensor_data.get('tire_pressure_fl', 0),
            sensor_data.get('tire_pressure_fr', 0),
            sensor_data.get('tire_pressure_rl', 0),
            sensor_data.get('tire_pressure_rr', 0),
            sensor_data.get('battery_voltage', 0),
            sensor_data.get('oil_pressure', 0),
            sensor_data.get('brake_fluid_level', 0),
            sensor_data.get('speed', 0),
            # Derived features
            abs(sensor_data.get('tire_pressure_fl', 32) - 32),  # Deviation from optimal
            sensor_data.get('engine_temp', 75) - 75,  # Temperature deviation
            sensor_data.get('battery_voltage', 12.6) - 12.6,  # Battery deviation
        ]
        
        self.feature_names = [
            'engine_temp', 'rpm', 'fuel_level',
            'tire_pressure_fl', 'tire_pressure_fr', 'tire_pressure_rl', 'tire_pressure_rr',
            'battery_voltage', 'oil_pressure', 'brake_fluid_level', 'speed',
            'tire_pressure_deviation', 'engine_temp_deviation', 'battery_deviation'
        ]
        
        return np.array(features).reshape(1, -1)
    
    def train_models(self, historical_data: pd.DataFrame):
        """
        Train models using historical maintenance and failure data
        """
        print("Training ML models for failure prediction...")
        
        for failure_type in self.failure_types:
            # Prepare training data
            X = historical_data[self.feature_names]
            y = historical_data[failure_type]  # Binary: 0 = no failure, 1 = failure
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scalers[failure_type].fit_transform(X_train)
            X_test_scaled = self.scalers[failure_type].transform(X_test)
            
            # Train model
            self.models[failure_type].fit(X_train_scaled, y_train)
            
            # Evaluate
            train_score = self.models[failure_type].score(X_train_scaled, y_train)
            test_score = self.models[failure_type].score(X_test_scaled, y_test)
            
            print(f"{failure_type}: Train={train_score:.3f}, Test={test_score:.3f}")
        
        print("Training complete!")
    
    def predict(self, features: np.ndarray) -> List[Dict]:
        """
        Predict potential failures across all systems
        """
        predictions = []
        
        for failure_type in self.failure_types:
            # Scale features
            features_scaled = self.scalers[failure_type].transform(features)
            
            # Get prediction probability
            prob = self.models[failure_type].predict_proba(features_scaled)[0][1]
            
            # Only include if probability is significant
            if prob > 0.3:
                severity = self._calculate_severity(prob)
                time_to_failure = self._estimate_time_to_failure(prob, failure_type)
                
                predictions.append({
                    'failure_type': failure_type,
                    'probability': float(prob),
                    'severity': severity,
                    'estimated_days_to_failure': time_to_failure,
                    'recommended_action': self._get_recommendation(failure_type, severity),
                    'estimated_cost': self._estimate_repair_cost(failure_type),
                    'confidence': 'high' if prob > 0.7 else 'medium' if prob > 0.5 else 'low'
                })
        
        # Sort by probability
        predictions.sort(key=lambda x: x['probability'], reverse=True)
        
        return predictions
    
    def _calculate_severity(self, probability: float) -> str:
        """Calculate severity based on failure probability"""
        if probability >= 0.8:
            return 'critical'
        elif probability >= 0.6:
            return 'high'
        elif probability >= 0.4:
            return 'medium'
        else:
            return 'low'
    
    def _estimate_time_to_failure(self, probability: float, failure_type: str) -> int:
        """
        Estimate days until failure based on probability and failure type
        """
        base_days = {
            'engine_overheating': 7,
            'battery_failure': 14,
            'brake_system': 21,
            'transmission_issue': 30,
            'tire_failure': 10,
            'oil_system': 14,
            'electrical_system': 20
        }
        
        # Higher probability = shorter time to failure
        days = int(base_days[failure_type] * (1 - probability))
        return max(1, days)
    
    def _get_recommendation(self, failure_type: str, severity: str) -> str:
        """Get maintenance recommendation"""
        recommendations = {
            'engine_overheating': {
                'critical': 'IMMEDIATE: Stop vehicle safely. Check coolant level. Tow to service center.',
                'high': 'Schedule service within 48 hours. Check coolant and radiator.',
                'medium': 'Monitor temperature. Schedule service within 1 week.',
                'low': 'Include in next routine maintenance.'
            },
            'battery_failure': {
                'critical': 'Battery replacement needed immediately. Risk of vehicle not starting.',
                'high': 'Battery test recommended within 3 days. Replacement likely needed.',
                'medium': 'Battery health declining. Test within 2 weeks.',
                'low': 'Monitor battery voltage. Test at next service.'
            },
            'brake_system': {
                'critical': 'URGENT: Brake inspection required immediately. Safety risk.',
                'high': 'Brake service needed within 3 days. Do not delay.',
                'medium': 'Schedule brake inspection within 1 week.',
                'low': 'Brake pads wearing normally. Check at next service.'
            },
            'transmission_issue': {
                'critical': 'Transmission service required urgently. Avoid highway driving.',
                'high': 'Transmission diagnosis needed within 1 week.',
                'medium': 'Monitor shifting behavior. Service within 2 weeks.',
                'low': 'Transmission fluid check at next service.'
            },
            'tire_failure': {
                'critical': 'IMMEDIATE: Check tire pressure and tread. Replace if needed.',
                'high': 'Tire inspection needed within 2 days.',
                'medium': 'Adjust tire pressure. Inspect within 1 week.',
                'low': 'Regular tire rotation recommended.'
            },
            'oil_system': {
                'critical': 'URGENT: Check oil level immediately. Do not drive if low.',
                'high': 'Oil change and system check needed within 3 days.',
                'medium': 'Schedule oil change within 1 week.',
                'low': 'Oil change due soon. Normal schedule.'
            },
            'electrical_system': {
                'critical': 'Electrical system diagnosis required immediately.',
                'high': 'Electrical inspection needed within 1 week.',
                'medium': 'Monitor electrical issues. Service if worsens.',
                'low': 'Electrical system functioning normally.'
            }
        }
        
        return recommendations.get(failure_type, {}).get(severity, 'Service recommended')
    
    def _estimate_repair_cost(self, failure_type: str) -> Tuple[float, float]:
        """Estimate repair cost range"""
        costs = {
            'engine_overheating': (200, 800),
            'battery_failure': (150, 300),
            'brake_system': (300, 1000),
            'transmission_issue': (1000, 3500),
            'tire_failure': (400, 1200),
            'oil_system': (100, 400),
            'electrical_system': (200, 1500)
        }
        
        return costs.get(failure_type, (100, 500))
    
    def save_models(self, path: str = 'models/'):
        """Save trained models to disk"""
        for failure_type in self.failure_types:
            joblib.dump(
                self.models[failure_type],
                f'{path}{failure_type}_model.pkl'
            )
            joblib.dump(
                self.scalers[failure_type],
                f'{path}{failure_type}_scaler.pkl'
            )
        
        print(f"Models saved to {path}")
    
    def load_models(self, path: str = 'models/'):
        """Load trained models from disk"""
        for failure_type in self.failure_types:
            self.models[failure_type] = joblib.load(
                f'{path}{failure_type}_model.pkl'
            )
            self.scalers[failure_type] = joblib.load(
                f'{path}{failure_type}_scaler.pkl'
            )
        
        print(f"Models loaded from {path}")


class AnomalyDetectionModel:
    """
    Real-time anomaly detection for sensor data
    """
    
    def __init__(self):
        self.baseline_stats = {}
        self.anomaly_threshold = 2.5  # Standard deviations
    
    def establish_baseline(self, historical_data: pd.DataFrame):
        """
        Establish normal operating ranges from historical data
        """
        sensors = [
            'engine_temp', 'rpm', 'battery_voltage', 'oil_pressure',
            'tire_pressure_fl', 'tire_pressure_fr', 'tire_pressure_rl', 'tire_pressure_rr'
        ]
        
        for sensor in sensors:
            self.baseline_stats[sensor] = {
                'mean': historical_data[sensor].mean(),
                'std': historical_data[sensor].std(),
                'min': historical_data[sensor].quantile(0.01),
                'max': historical_data[sensor].quantile(0.99)
            }
    
    def detect_anomalies(self, sensor_data: Dict) -> List[Dict]:
        """
        Detect anomalies in real-time sensor readings
        """
        anomalies = []
        
        for sensor, value in sensor_data.items():
            if sensor not in self.baseline_stats:
                continue
            
            stats = self.baseline_stats[sensor]
            
            # Calculate z-score
            z_score = abs(value - stats['mean']) / stats['std']
            
            # Check if anomaly
            if z_score > self.anomaly_threshold:
                severity = 'critical' if z_score > 3.5 else 'warning'
                
                anomalies.append({
                    'sensor': sensor,
                    'value': value,
                    'expected_range': (stats['min'], stats['max']),
                    'z_score': z_score,
                    'severity': severity,
                    'message': self._get_anomaly_message(sensor, value, stats)
                })
        
        return anomalies
    
    def _get_anomaly_message(self, sensor: str, value: float, stats: Dict) -> str:
        """Generate human-readable anomaly message"""
        messages = {
            'engine_temp': f"Engine temperature {value:.1f}°C is abnormal (normal: {stats['min']:.1f}-{stats['max']:.1f}°C)",
            'battery_voltage': f"Battery voltage {value:.1f}V is out of range (normal: {stats['min']:.1f}-{stats['max']:.1f}V)",
            'oil_pressure': f"Oil pressure {value:.1f} PSI is abnormal (normal: {stats['min']:.1f}-{stats['max']:.1f} PSI)",
            'tire_pressure_fl': f"Front-left tire pressure {value:.1f} PSI is abnormal",
            'tire_pressure_fr': f"Front-right tire pressure {value:.1f} PSI is abnormal",
            'tire_pressure_rl': f"Rear-left tire pressure {value:.1f} PSI is abnormal",
            'tire_pressure_rr': f"Rear-right tire pressure {value:.1f} PSI is abnormal"
        }
        
        return messages.get(sensor, f"{sensor} reading is abnormal")


class MaintenanceSchedulePredictor:
    """
    Predict optimal maintenance schedule based on vehicle usage patterns
    """
    
    def __init__(self):
        self.service_intervals = {
            'oil_change': {'miles': 5000, 'days': 180},
            'tire_rotation': {'miles': 7500, 'days': 180},
            'brake_inspection': {'miles': 12000, 'days': 365},
            'battery_test': {'miles': None, 'days': 365},
            'coolant_flush': {'miles': 30000, 'days': 730},
            'transmission_service': {'miles': 60000, 'days': 1825}
        }
    
    def predict_next_services(self, vehicle_data: Dict) -> List[Dict]:
        """
        Predict when each service will be due
        """
        current_mileage = vehicle_data.get('current_mileage', 0)
        last_service_date = vehicle_data.get('last_service_date', datetime.now())
        avg_miles_per_day = vehicle_data.get('avg_miles_per_day', 30)
        
        upcoming_services = []
        
        for service_type, interval in self.service_intervals.items():
            # Calculate based on mileage
            if interval['miles']:
                miles_until_due = interval['miles'] - (current_mileage % interval['miles'])
                days_until_due_miles = int(miles_until_due / avg_miles_per_day)
            else:
                days_until_due_miles = float('inf')
            
            # Calculate based on time
            days_since_last = (datetime.now() - last_service_date).days
            days_until_due_time = interval['days'] - days_since_last
            
            # Use whichever comes first
            days_until_due = min(days_until_due_miles, days_until_due_time)
            
            if days_until_due < 60:  # Next 60 days
                upcoming_services.append({
                    'service_type': service_type,
                    'days_until_due': max(0, days_until_due),
                    'due_date': (datetime.now() + timedelta(days=days_until_due)).strftime('%Y-%m-%d'),
                    'priority': 'high' if days_until_due < 7 else 'medium' if days_until_due < 30 else 'low'
                })
        
        return sorted(upcoming_services, key=lambda x: x['days_until_due'])


# Example usage and testing
if __name__ == "__main__":
    # Initialize model
    model = VehicleFailurePredictionModel()
    
    # Simulate sensor data
    test_data = {
        'engine_temp': 98.5,  # High temperature
        'rpm': 2500,
        'fuel_level': 45,
        'tire_pressure_fl': 28,  # Low pressure
        'tire_pressure_fr': 32,
        'tire_pressure_rl': 32,
        'tire_pressure_rr': 32,
        'battery_voltage': 11.8,  # Low voltage
        'oil_pressure': 35,
        'brake_fluid_level': 75,
        'speed': 60
    }
    
    # Prepare features
    features = model.prepare_features(test_data)
    
    # Make predictions (note: models need to be trained first)
    # predictions = model.predict(features)
    # print(json.dumps(predictions, indent=2))
    
    print("ML Models initialized and ready for training!")
    print(f"Feature vector shape: {features.shape}")
    print(f"Number of failure types: {len(model.failure_types)}")