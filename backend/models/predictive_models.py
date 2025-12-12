"""
Machine Learning Models for Predictive Maintenance
- Failure Prediction (Binary Classification)
- Component Classification (Multi-class)
- RUL Estimation (Regression)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import xgboost as xgb
import joblib
import os
from datetime import datetime

class VehicleFailurePredictor:
    """Predicts vehicle failures and identifies failing components"""
    
    def __init__(self):
        self.failure_classifier = None
        self.component_classifier = None
        self.rul_regressor = None
        self.scaler = StandardScaler()
        self.component_encoder = LabelEncoder()
        
        # Feature columns for prediction
        self.feature_cols = [
            'soc', 'soh', 'battery_voltage', 'battery_current', 'battery_temp',
            'charge_cycles', 'motor_temp', 'motor_vibration', 'motor_torque',
            'motor_rpm', 'power_consumption', 'brake_pad_wear', 'brake_pressure',
            'regen_efficiency', 'tire_pressure_fl', 'tire_pressure_fr',
            'tire_pressure_rl', 'tire_pressure_rr', 'tire_temp_avg',
            'suspension_load', 'ambient_temp', 'ambient_humidity',
            'load_weight', 'driving_speed', 'route_roughness'
        ]
        
        # Component failure signatures (rules-based + ML)
        self.component_rules = {
            'Battery': {
                'conditions': [
                    ('soh', '<', 75),
                    ('battery_temp', '>', 50),
                    ('battery_voltage', 'range', (350, 450))
                ],
                'weight': 0.3
            },
            'Motor': {
                'conditions': [
                    ('motor_temp', '>', 90),
                    ('motor_vibration', '>', 1.5),
                    ('motor_torque', 'std', 50)
                ],
                'weight': 0.25
            },
            'Brake': {
                'conditions': [
                    ('brake_pad_wear', '<', 3),
                    ('brake_pressure', '<', 70),
                    ('regen_efficiency', '<', 60)
                ],
                'weight': 0.2
            },
            'Tire': {
                'conditions': [
                    ('tire_pressure_fl', '<', 28),
                    ('tire_temp_avg', '>', 45)
                ],
                'weight': 0.15
            },
            'Suspension': {
                'conditions': [
                    ('suspension_load', '>', 700),
                    ('route_roughness', '>=', 2)
                ],
                'weight': 0.1
            }
        }
    
    def prepare_data(self, sensor_df, maintenance_df=None):
        """Prepare data for training"""
        # Extract features
        X = sensor_df[self.feature_cols].copy()
        
        # Handle missing values
        X = X.fillna(X.mean())
        
        # Create labels from sensor data
        y_failure = sensor_df['failure_probability'].values
        
        # Create component labels from maintenance data if available
        if maintenance_df is not None:
            # Map vehicle failures to components
            failure_map = {}
            for _, row in maintenance_df.iterrows():
                failure_map[row['vehicle_id']] = row['component']
            
            # Create synthetic component labels based on sensor patterns
            y_component = []
            for idx, row in sensor_df.iterrows():
                vehicle_id = row['vehicle_id']
                if vehicle_id in failure_map:
                    y_component.append(failure_map[vehicle_id])
                else:
                    # Use rule-based classification
                    y_component.append(self._rule_based_component(row))
            
            y_component = np.array(y_component)
        else:
            y_component = None
        
        # RUL target
        y_rul = sensor_df['estimated_rul_hours'].values
        
        return X, y_failure, y_component, y_rul
    
    def _rule_based_component(self, reading):
        """Rule-based component identification"""
        scores = {}
        
        for component, rules in self.component_rules.items():
            score = 0
            for condition in rules['conditions']:
                if len(condition) == 3:
                    col, op, threshold = condition
                    value = reading[col]
                    
                    if op == '<' and value < threshold:
                        score += 1
                    elif op == '>' and value > threshold:
                        score += 1
                    elif op == '>=' and value >= threshold:
                        score += 1
                    elif op == 'range':
                        if not (threshold[0] <= value <= threshold[1]):
                            score += 1
            
            scores[component] = score * rules['weight']
        
        # Return component with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        return 'Normal'
    
    def train(self, sensor_df, maintenance_df=None):
        """Train all models"""
        print("Preparing training data...")
        X, y_failure, y_component, y_rul = self.prepare_data(sensor_df, maintenance_df)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_fail_train, y_fail_test = train_test_split(
            X_scaled, y_failure, test_size=0.2, random_state=42
        )
        
        # 1. Train Failure Classifier (XGBoost)
        print("Training failure prediction model...")
        self.failure_classifier = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        self.failure_classifier.fit(X_train, y_fail_train)
        fail_score = self.failure_classifier.score(X_test, y_fail_test)
        print(f"✓ Failure Classifier Accuracy: {fail_score:.4f}")
        
        # 2. Train Component Classifier (Random Forest)
        if y_component is not None:
            print("Training component classification model...")
            y_comp_encoded = self.component_encoder.fit_transform(y_component)
            X_train_c, X_test_c, y_comp_train, y_comp_test = train_test_split(
                X_scaled, y_comp_encoded, test_size=0.2, random_state=42
            )
            
            self.component_classifier = RandomForestClassifier(
                n_estimators=200,
                max_depth=10,
                random_state=42
            )
            self.component_classifier.fit(X_train_c, y_comp_train)
            comp_score = self.component_classifier.score(X_test_c, y_comp_test)
            print(f"✓ Component Classifier Accuracy: {comp_score:.4f}")
        
        # 3. Train RUL Regressor (Gradient Boosting)
        print("Training RUL estimation model...")
        X_train_r, X_test_r, y_rul_train, y_rul_test = train_test_split(
            X_scaled, y_rul, test_size=0.2, random_state=42
        )
        
        self.rul_regressor = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        self.rul_regressor.fit(X_train_r, y_rul_train)
        rul_score = self.rul_regressor.score(X_test_r, y_rul_test)
        print(f"✓ RUL Regressor R² Score: {rul_score:.4f}")
        
        return {
            'failure_accuracy': fail_score,
            'component_accuracy': comp_score if y_component is not None else None,
            'rul_r2': rul_score
        }
    
    def predict_failure(self, sensor_reading):
        """Predict if vehicle will fail"""
        if self.failure_classifier is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Prepare features
        features = np.array([[sensor_reading[col] for col in self.feature_cols]])
        features_scaled = self.scaler.transform(features)
        
        # Predict
        failure_prob = self.failure_classifier.predict_proba(features_scaled)[0][1]
        will_fail = failure_prob > 0.5
        
        return {
            'will_fail': bool(will_fail),
            'failure_probability': float(failure_prob),
            'confidence': float(max(failure_prob, 1 - failure_prob))
        }
    
    def identify_component(self, sensor_reading):
        """Identify which component is likely to fail"""
        if self.component_classifier is None:
            # Fall back to rule-based
            component = self._rule_based_component(sensor_reading)
            return {
                'component': component,
                'confidence': 0.7,
                'method': 'rule-based'
            }
        
        # Prepare features
        features = np.array([[sensor_reading[col] for col in self.feature_cols]])
        features_scaled = self.scaler.transform(features)
        
        # Predict
        component_encoded = self.component_classifier.predict(features_scaled)[0]
        component_probs = self.component_classifier.predict_proba(features_scaled)[0]
        
        component = self.component_encoder.inverse_transform([component_encoded])[0]
        confidence = float(max(component_probs))
        
        return {
            'component': component,
            'confidence': confidence,
            'method': 'ml-model',
            'all_probabilities': {
                self.component_encoder.inverse_transform([i])[0]: float(prob)
                for i, prob in enumerate(component_probs)
            }
        }
    
    def estimate_rul(self, sensor_reading):
        """Estimate Remaining Useful Life in hours"""
        if self.rul_regressor is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Prepare features
        features = np.array([[sensor_reading[col] for col in self.feature_cols]])
        features_scaled = self.scaler.transform(features)
        
        # Predict
        rul_hours = self.rul_regressor.predict(features_scaled)[0]
        
        return {
            'rul_hours': float(max(0, rul_hours)),
            'rul_days': float(max(0, rul_hours / 24)),
            'recommended_action': 'immediate' if rul_hours < 48 else 'schedule_soon' if rul_hours < 168 else 'monitor'
        }
    
    def comprehensive_diagnosis(self, sensor_reading):
        """Complete vehicle health assessment"""
        failure_pred = self.predict_failure(sensor_reading)
        
        if failure_pred['will_fail']:
            component_pred = self.identify_component(sensor_reading)
            rul_pred = self.estimate_rul(sensor_reading)
            
            return {
                'status': 'at_risk',
                'failure_prediction': failure_pred,
                'component_diagnosis': component_pred,
                'rul_estimation': rul_pred,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'status': 'healthy',
                'failure_prediction': failure_pred,
                'timestamp': datetime.now().isoformat()
            }
    
    def save_models(self, path='ml_models/trained_models'):
        """Save trained models"""
        os.makedirs(path, exist_ok=True)
        
        joblib.dump(self.failure_classifier, f'{path}/failure_classifier.pkl')
        joblib.dump(self.component_classifier, f'{path}/component_classifier.pkl')
        joblib.dump(self.rul_regressor, f'{path}/rul_regressor.pkl')
        joblib.dump(self.scaler, f'{path}/scaler.pkl')
        joblib.dump(self.component_encoder, f'{path}/component_encoder.pkl')
        
        print(f"✓ Models saved to {path}/")
    
    def load_models(self, path='ml_models/trained_models'):
        """Load trained models"""
        self.failure_classifier = joblib.load(f'{path}/failure_classifier.pkl')
        self.component_classifier = joblib.load(f'{path}/component_classifier.pkl')
        self.rul_regressor = joblib.load(f'{path}/rul_regressor.pkl')
        self.scaler = joblib.load(f'{path}/scaler.pkl')
        self.component_encoder = joblib.load(f'{path}/component_encoder.pkl')
        
        print(f"✓ Models loaded from {path}/")

if __name__ == "__main__":
    # Train models
    print("Loading data...")
    sensor_df = pd.read_csv("backend/data/sensor_data.csv")
    maintenance_df = pd.read_csv("backend/data/maintenance_history.csv")
    
    print(f"Loaded {len(sensor_df)} sensor readings and {len(maintenance_df)} maintenance records")
    
    predictor = VehicleFailurePredictor()
    metrics = predictor.train(sensor_df, maintenance_df)
    
    print("\n" + "="*50)
    print("Training Complete!")
    print("="*50)
    print(f"Failure Prediction Accuracy: {metrics['failure_accuracy']:.2%}")
    print(f"Component Classification Accuracy: {metrics['component_accuracy']:.2%}" if metrics['component_accuracy'] else "Component Classification: Rule-based")
    print(f"RUL Estimation R² Score: {metrics['rul_r2']:.4f}")
    
    predictor.save_models()
    print("\n✅ All models trained and saved successfully!")
