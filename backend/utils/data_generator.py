"""
TorqCare Data Generator
Generates realistic mock data for 100 electric vehicles with 20 failure scenarios
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

class TorqCareDataGenerator:
    def __init__(self, num_vehicles=100, readings_per_vehicle=1000):
        self.num_vehicles = num_vehicles
        self.readings_per_vehicle = readings_per_vehicle
        self.vehicle_ids = [f"EV-{str(i).zfill(5)}" for i in range(1, num_vehicles + 1)]
        
        # Failure scenarios with component and symptoms
        self.failure_scenarios = [
            {"id": 1, "component": "Battery", "issue": "Rapid SoH Degradation", "symptoms": ["low_soh", "high_temp"]},
            {"id": 2, "component": "Battery", "issue": "Cell Imbalance", "symptoms": ["voltage_variance", "low_soc"]},
            {"id": 3, "component": "Battery", "issue": "Thermal Runaway Risk", "symptoms": ["critical_temp", "high_current"]},
            {"id": 4, "component": "Motor", "issue": "Bearing Wear", "symptoms": ["high_vibration", "high_temp"]},
            {"id": 5, "component": "Motor", "issue": "Winding Insulation Failure", "symptoms": ["high_temp", "power_drop"]},
            {"id": 6, "component": "Motor", "issue": "Rotor Imbalance", "symptoms": ["vibration_spike", "torque_fluctuation"]},
            {"id": 7, "component": "Brake", "issue": "Pad Wear Critical", "symptoms": ["low_pad_thickness", "high_pressure"]},
            {"id": 8, "component": "Brake", "issue": "Hydraulic Leak", "symptoms": ["pressure_drop", "inefficient_braking"]},
            {"id": 9, "component": "Brake", "issue": "Regenerative Braking Failure", "symptoms": ["low_regen_efficiency", "battery_not_charging"]},
            {"id": 10, "component": "Tire", "issue": "Low Pressure", "symptoms": ["pressure_below_threshold", "high_temp"]},
            {"id": 11, "component": "Tire", "issue": "Uneven Wear", "symptoms": ["temp_variance", "vibration"]},
            {"id": 12, "component": "Suspension", "issue": "Shock Absorber Failure", "symptoms": ["high_load_stress", "rough_ride"]},
            {"id": 13, "component": "Suspension", "issue": "Spring Fatigue", "symptoms": ["load_imbalance", "vibration"]},
            {"id": 14, "component": "Cooling", "issue": "Coolant Pump Failure", "symptoms": ["battery_temp_rise", "motor_temp_rise"]},
            {"id": 15, "component": "Cooling", "issue": "Radiator Blockage", "symptoms": ["sustained_high_temp", "power_reduction"]},
            {"id": 16, "component": "Power Electronics", "issue": "Inverter Overheating", "symptoms": ["high_power_consumption", "temp_spike"]},
            {"id": 17, "component": "Power Electronics", "issue": "DC-DC Converter Failure", "symptoms": ["voltage_instability", "power_loss"]},
            {"id": 18, "component": "Charging", "issue": "Onboard Charger Fault", "symptoms": ["slow_charging", "voltage_fluctuation"]},
            {"id": 19, "component": "BMS", "issue": "Communication Error", "symptoms": ["data_inconsistency", "delayed_response"]},
            {"id": 20, "component": "Drivetrain", "issue": "Gear Reduction Unit Wear", "symptoms": ["noise_increase", "efficiency_drop"]},
        ]
    
    def generate_sensor_data(self):
        """Generate sensor telemetry data with injected failures"""
        print("Generating sensor data...")
        data = []
        
        for vehicle_id in self.vehicle_ids:
            # Decide if this vehicle will have failures (30% chance)
            has_failure = random.random() < 0.3
            failure_scenario = random.choice(self.failure_scenarios) if has_failure else None
            failure_start_idx = random.randint(600, 900) if has_failure else None
            
            base_timestamp = datetime.now() - timedelta(days=30)
            
            for i in range(self.readings_per_vehicle):
                timestamp = base_timestamp + timedelta(seconds=i*10)
                
                # Base normal readings
                reading = {
                    "vehicle_id": vehicle_id,
                    "timestamp": timestamp,
                    "soc": np.clip(np.random.normal(75, 15), 20, 100),
                    "soh": np.clip(np.random.normal(95, 3), 70, 100),
                    "battery_voltage": np.random.normal(400, 10),
                    "battery_current": np.random.normal(50, 20),
                    "battery_temp": np.random.normal(25, 5),
                    "charge_cycles": random.randint(50, 500),
                    "motor_temp": np.random.normal(65, 10),
                    "motor_vibration": np.random.normal(0.5, 0.2),
                    "motor_torque": np.random.normal(250, 50),
                    "motor_rpm": np.random.normal(3000, 500),
                    "power_consumption": np.random.normal(45, 15),
                    "brake_pad_wear": np.clip(np.random.normal(8, 2), 1, 12),
                    "brake_pressure": np.random.normal(100, 20),
                    "regen_efficiency": np.clip(np.random.normal(85, 10), 50, 95),
                    "tire_pressure_fl": np.random.normal(35, 2),
                    "tire_pressure_fr": np.random.normal(35, 2),
                    "tire_pressure_rl": np.random.normal(35, 2),
                    "tire_pressure_rr": np.random.normal(35, 2),
                    "tire_temp_avg": np.random.normal(30, 5),
                    "suspension_load": np.random.normal(500, 100),
                    "ambient_temp": np.random.normal(22, 8),
                    "ambient_humidity": np.random.normal(60, 15),
                    "load_weight": np.random.normal(200, 100),
                    "driving_speed": np.clip(np.random.normal(60, 20), 0, 120),
                    "distance_traveled": i * 0.167,  # ~10 km per 100 readings
                    "idle_time": random.randint(0, 300),
                    "route_roughness": np.random.choice([0, 1, 2, 3], p=[0.5, 0.3, 0.15, 0.05])
                }
                
                # Inject failure symptoms
                if has_failure and i >= failure_start_idx:
                    intensity = min((i - failure_start_idx) / 100, 1.0)  # Gradual degradation
                    
                    if failure_scenario["id"] in [1, 2, 3]:  # Battery issues
                        if "low_soh" in failure_scenario["symptoms"]:
                            reading["soh"] = np.clip(reading["soh"] - intensity * 20, 65, 100)
                        if "high_temp" in failure_scenario["symptoms"]:
                            reading["battery_temp"] = reading["battery_temp"] + intensity * 30
                        if "voltage_variance" in failure_scenario["symptoms"]:
                            reading["battery_voltage"] = reading["battery_voltage"] + random.uniform(-50, 50) * intensity
                        if "critical_temp" in failure_scenario["symptoms"]:
                            reading["battery_temp"] = reading["battery_temp"] + intensity * 45
                    
                    elif failure_scenario["id"] in [4, 5, 6]:  # Motor issues
                        if "high_vibration" in failure_scenario["symptoms"]:
                            reading["motor_vibration"] = reading["motor_vibration"] + intensity * 2
                        if "high_temp" in failure_scenario["symptoms"]:
                            reading["motor_temp"] = reading["motor_temp"] + intensity * 40
                        if "vibration_spike" in failure_scenario["symptoms"]:
                            reading["motor_vibration"] = reading["motor_vibration"] + intensity * 3
                        if "torque_fluctuation" in failure_scenario["symptoms"]:
                            reading["motor_torque"] = reading["motor_torque"] * (1 + random.uniform(-0.3, 0.3) * intensity)
                    
                    elif failure_scenario["id"] in [7, 8, 9]:  # Brake issues
                        if "low_pad_thickness" in failure_scenario["symptoms"]:
                            reading["brake_pad_wear"] = max(reading["brake_pad_wear"] - intensity * 6, 0.5)
                        if "pressure_drop" in failure_scenario["symptoms"]:
                            reading["brake_pressure"] = reading["brake_pressure"] - intensity * 50
                        if "low_regen_efficiency" in failure_scenario["symptoms"]:
                            reading["regen_efficiency"] = max(reading["regen_efficiency"] - intensity * 40, 30)
                    
                    elif failure_scenario["id"] in [10, 11]:  # Tire issues
                        if "pressure_below_threshold" in failure_scenario["symptoms"]:
                            reading["tire_pressure_fl"] = max(reading["tire_pressure_fl"] - intensity * 10, 20)
                        if "temp_variance" in failure_scenario["symptoms"]:
                            reading["tire_temp_avg"] = reading["tire_temp_avg"] + intensity * 20
                    
                    elif failure_scenario["id"] in [12, 13]:  # Suspension issues
                        if "high_load_stress" in failure_scenario["symptoms"]:
                            reading["suspension_load"] = reading["suspension_load"] + intensity * 300
                    
                    elif failure_scenario["id"] in [14, 15]:  # Cooling issues
                        if "battery_temp_rise" in failure_scenario["symptoms"]:
                            reading["battery_temp"] = reading["battery_temp"] + intensity * 25
                        if "motor_temp_rise" in failure_scenario["symptoms"]:
                            reading["motor_temp"] = reading["motor_temp"] + intensity * 35
                
                # Calculate derived metrics
                reading["failure_probability"] = 1 if (has_failure and i >= failure_start_idx + 50) else 0
                reading["component_health_score"] = max(0.3, 1.0 - intensity) if has_failure and i >= failure_start_idx else random.uniform(0.85, 1.0)
                reading["estimated_rul_hours"] = max(10, 1000 - (intensity * 900)) if has_failure and i >= failure_start_idx else random.randint(500, 2000)
                
                data.append(reading)
        
        df = pd.DataFrame(data)
        return df
    
    def generate_maintenance_history(self):
        """Generate maintenance history for 200 past events"""
        print("Generating maintenance history...")
        data = []
        
        for i in range(200):
            vehicle_id = random.choice(self.vehicle_ids)
            scenario = random.choice(self.failure_scenarios)
            
            maintenance_date = datetime.now() - timedelta(days=random.randint(1, 365))
            detection_date = maintenance_date - timedelta(days=random.randint(1, 7))
            
            record = {
                "maintenance_id": f"MNT-{str(i+1).zfill(5)}",
                "vehicle_id": vehicle_id,
                "detection_date": detection_date,
                "maintenance_date": maintenance_date,
                "component": scenario["component"],
                "issue_detected": scenario["issue"],
                "maintenance_type": random.choice(["Preventive", "Corrective", "Predictive"]),
                "repair_duration_hours": random.randint(1, 24),
                "cost_usd": random.randint(100, 5000),
                "parts_replaced": random.choice([True, False]),
                "workshop_id": f"WS-{random.randint(1, 10):03d}",
                "technician_id": f"TECH-{random.randint(1, 50):03d}",
                "severity": random.choice(["Low", "Medium", "High", "Critical"]),
                "downtime_hours": random.randint(0, 48),
                "odometer_reading": random.randint(5000, 150000),
                "description": f"Resolved {scenario['issue']} in {scenario['component']} system"
            }
            data.append(record)
        
        df = pd.DataFrame(data)
        return df.sort_values("detection_date")
    
    def generate_appointments(self):
        """Generate appointment data"""
        print("Generating appointments...")
        data = []
        
        for i in range(50):
            vehicle_id = random.choice(self.vehicle_ids)
            appointment_date = datetime.now() + timedelta(days=random.randint(1, 7), hours=random.randint(8, 17))
            
            record = {
                "appointment_id": f"APT-{str(i+1).zfill(5)}",
                "vehicle_id": vehicle_id,
                "workshop_id": f"WS-{random.randint(1, 10):03d}",
                "scheduled_date": appointment_date,
                "estimated_duration_hours": random.choice([2, 4, 6, 8]),
                "service_type": random.choice(["Diagnostic", "Repair", "Preventive Maintenance", "Inspection"]),
                "status": random.choice(["Scheduled", "Confirmed", "Completed", "Cancelled"]),
                "created_date": datetime.now() - timedelta(days=random.randint(1, 30)),
                "priority": random.choice(["Low", "Medium", "High"]),
                "estimated_cost": random.randint(100, 3000)
            }
            data.append(record)
        
        df = pd.DataFrame(data)
        return df
    
    def generate_feedback(self):
        """Generate feedback data"""
        print("Generating feedback...")
        data = []
        
        sentiments = ["Positive", "Neutral", "Negative"]
        comments = {
            "Positive": [
                "Excellent service, issue resolved quickly",
                "Very satisfied with the repair quality",
                "Professional technicians, great experience",
                "Problem fixed on first visit"
            ],
            "Neutral": [
                "Service was okay, took longer than expected",
                "Average experience, issue resolved",
                "Standard service, no complaints"
            ],
            "Negative": [
                "Issue recurred after repair",
                "Long wait time, poor communication",
                "Expensive repair, not satisfied",
                "Problem not fully resolved"
            ]
        }
        
        for i in range(150):
            sentiment = random.choice(sentiments)
            
            record = {
                "feedback_id": f"FBK-{str(i+1).zfill(5)}",
                "maintenance_id": f"MNT-{random.randint(1, 200):05d}",
                "vehicle_id": random.choice(self.vehicle_ids),
                "feedback_date": datetime.now() - timedelta(days=random.randint(1, 180)),
                "rating": random.randint(3, 5) if sentiment == "Positive" else random.randint(1, 3),
                "sentiment": sentiment,
                "comment": random.choice(comments[sentiment]),
                "repair_effectiveness": random.randint(1, 5),
                "service_quality": random.randint(1, 5),
                "communication_rating": random.randint(1, 5),
                "would_recommend": sentiment == "Positive"
            }
            data.append(record)
        
        df = pd.DataFrame(data)
        return df
    
    def generate_workshops(self):
        """Generate workshop/service center data"""
        print("Generating workshop data...")
        data = []
        
        cities = ["San Francisco", "Los Angeles", "New York", "Chicago", "Houston", 
                  "Phoenix", "Philadelphia", "San Antonio", "San Diego", "Dallas"]
        
        for i in range(10):
            # Generate 7-day schedule with available slots
            schedule = {}
            for day in range(7):
                date = (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d")
                available_slots = []
                for hour in range(8, 18, 2):  # 8 AM to 6 PM, 2-hour slots
                    if random.random() > 0.3:  # 70% slots available
                        available_slots.append(f"{hour:02d}:00")
                schedule[date] = available_slots
            
            record = {
                "workshop_id": f"WS-{i+1:03d}",
                "name": f"TorqCare Service Center {cities[i]}",
                "city": cities[i],
                "address": f"{random.randint(100, 9999)} Main Street",
                "phone": f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                "specialties": ", ".join(random.sample(["Battery", "Motor", "Brake", "Suspension", "Diagnostics"], k=3)),
                "rating": round(random.uniform(3.5, 5.0), 1),
                "available_slots": str(schedule),
                "capacity_per_day": random.randint(5, 15),
                "average_wait_days": random.randint(1, 5)
            }
            data.append(record)
        
        df = pd.DataFrame(data)
        return df
    
    def save_all_data(self, output_dir="backend/data"):
        """Generate and save all datasets"""
        os.makedirs(output_dir, exist_ok=True)
        
        sensor_df = self.generate_sensor_data()
        sensor_df.to_csv(f"{output_dir}/sensor_data.csv", index=False)
        print(f"✓ Saved sensor_data.csv ({len(sensor_df)} records)")
        
        maintenance_df = self.generate_maintenance_history()
        maintenance_df.to_csv(f"{output_dir}/maintenance_history.csv", index=False)
        print(f"✓ Saved maintenance_history.csv ({len(maintenance_df)} records)")
        
        appointments_df = self.generate_appointments()
        appointments_df.to_csv(f"{output_dir}/appointments.csv", index=False)
        print(f"✓ Saved appointments.csv ({len(appointments_df)} records)")
        
        feedback_df = self.generate_feedback()
        feedback_df.to_csv(f"{output_dir}/feedback.csv", index=False)
        print(f"✓ Saved feedback.csv ({len(feedback_df)} records)")
        
        workshops_df = self.generate_workshops()
        workshops_df.to_csv(f"{output_dir}/workshops.csv", index=False)
        print(f"✓ Saved workshops.csv ({len(workshops_df)} records)")
        
        print(f"\n✅ All data generated successfully in {output_dir}/")
        return {
            "sensor": sensor_df,
            "maintenance": maintenance_df,
            "appointments": appointments_df,
            "feedback": feedback_df,
            "workshops": workshops_df
        }

if __name__ == "__main__":
    generator = TorqCareDataGenerator(num_vehicles=100, readings_per_vehicle=1000)
    generator.save_all_data()
