"""
TorqCare Testing Utilities and Sample Data Generation
Run this script to generate realistic test data and perform system tests
"""

import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import asyncio
import httpx

class SensorDataGenerator:
    """Generate realistic sensor data with configurable anomaly rates"""
    
    def __init__(self, anomaly_rate: float = 0.1):
        self.anomaly_rate = anomaly_rate
        self.baseline = {
            'engine_temp': {'min': 70, 'max': 90, 'mean': 80, 'std': 5},
            'rpm': {'min': 800, 'max': 4000, 'mean': 2000, 'std': 500},
            'fuel_level': {'min': 10, 'max': 100, 'mean': 55, 'std': 25},
            'tire_pressure': {'min': 30, 'max': 35, 'mean': 32, 'std': 1},
            'battery_voltage': {'min': 12.4, 'max': 14.5, 'mean': 13.0, 'std': 0.5},
            'oil_pressure': {'min': 25, 'max': 55, 'mean': 40, 'std': 8},
            'brake_fluid': {'min': 70, 'max': 100, 'mean': 90, 'std': 10},
            'speed': {'min': 0, 'max': 120, 'mean': 50, 'std': 30}
        }
    
    def generate_normal_reading(self, vehicle_id: str = "VEH001") -> Dict:
        """Generate normal sensor reading"""
        return {
            'vehicle_id': vehicle_id,
            'engine_temp': random.gauss(
                self.baseline['engine_temp']['mean'],
                self.baseline['engine_temp']['std']
            ),
            'rpm': max(800, random.gauss(
                self.baseline['rpm']['mean'],
                self.baseline['rpm']['std']
            )),
            'fuel_level': max(0, min(100, random.gauss(
                self.baseline['fuel_level']['mean'],
                self.baseline['fuel_level']['std']
            ))),
            'tire_pressure_fl': random.gauss(
                self.baseline['tire_pressure']['mean'],
                self.baseline['tire_pressure']['std']
            ),
            'tire_pressure_fr': random.gauss(
                self.baseline['tire_pressure']['mean'],
                self.baseline['tire_pressure']['std']
            ),
            'tire_pressure_rl': random.gauss(
                self.baseline['tire_pressure']['mean'],
                self.baseline['tire_pressure']['std']
            ),
            'tire_pressure_rr': random.gauss(
                self.baseline['tire_pressure']['mean'],
                self.baseline['tire_pressure']['std']
            ),
            'battery_voltage': random.gauss(
                self.baseline['battery_voltage']['mean'],
                self.baseline['battery_voltage']['std']
            ),
            'oil_pressure': random.gauss(
                self.baseline['oil_pressure']['mean'],
                self.baseline['oil_pressure']['std']
            ),
            'brake_fluid_level': random.gauss(
                self.baseline['brake_fluid']['mean'],
                self.baseline['brake_fluid']['std']
            ),
            'speed': max(0, random.gauss(
                self.baseline['speed']['mean'],
                self.baseline['speed']['std']
            ))
        }
    
    def generate_anomalous_reading(self, vehicle_id: str = "VEH001", anomaly_type: str = None) -> Dict:
        """Generate sensor reading with specific anomaly"""
        data = self.generate_normal_reading(vehicle_id)
        
        if not anomaly_type:
            anomaly_type = random.choice([
                'engine_overheating',
                'battery_failure',
                'oil_pressure_low',
                'tire_pressure_low'
            ])
        
        if anomaly_type == 'engine_overheating':
            data['engine_temp'] = random.uniform(95, 110)
        elif anomaly_type == 'battery_failure':
            data['battery_voltage'] = random.uniform(10.5, 11.8)
        elif anomaly_type == 'oil_pressure_low':
            data['oil_pressure'] = random.uniform(10, 19)
        elif anomaly_type == 'tire_pressure_low':
            tire = random.choice(['fl', 'fr', 'rl', 'rr'])
            data[f'tire_pressure_{tire}'] = random.uniform(20, 27)
        
        return data
    
    def generate_dataset(self, num_samples: int = 1000, vehicle_ids: List[str] = None) -> List[Dict]:
        """Generate dataset with mix of normal and anomalous readings"""
        if not vehicle_ids:
            vehicle_ids = [f"VEH{str(i).zfill(3)}" for i in range(1, 11)]
        
        dataset = []
        for _ in range(num_samples):
            vehicle_id = random.choice(vehicle_ids)
            
            if random.random() < self.anomaly_rate:
                data = self.generate_anomalous_reading(vehicle_id)
            else:
                data = self.generate_normal_reading(vehicle_id)
            
            data['timestamp'] = (
                datetime.now() - timedelta(seconds=random.randint(0, 86400))
            ).isoformat()
            
            dataset.append(data)
        
        return dataset


class MaintenanceDataGenerator:
    """Generate realistic maintenance history data"""
    
    def __init__(self):
        self.service_types = [
            'Oil Change',
            'Tire Rotation',
            'Brake Service',
            'Battery Replacement',
            'Transmission Service',
            'Engine Diagnostic',
            'Air Filter Replacement',
            'Coolant Flush',
            'Spark Plug Replacement',
            'Wheel Alignment'
        ]
        
        self.common_issues = [
            'Unusual engine noise',
            'Brake squealing',
            'Check engine light',
            'Tire wear uneven',
            'Battery not holding charge',
            'Transmission slipping',
            'Oil leak detected',
            'Coolant leak',
            'Rough idling',
            'Poor fuel economy'
        ]
    
    def generate_record(self, vehicle_id: str, service_date: datetime = None) -> Dict:
        """Generate a maintenance record"""
        if not service_date:
            service_date = datetime.now() - timedelta(days=random.randint(0, 730))
        
        service_type = random.choice(self.service_types)
        parts_cost = random.uniform(50, 500)
        labor_hours = random.uniform(0.5, 4.0)
        labor_cost = labor_hours * random.uniform(80, 150)
        
        return {
            'vehicle_id': vehicle_id,
            'service_date': service_date.isoformat(),
            'service_type': service_type,
            'mileage_at_service': random.uniform(5000, 100000),
            'parts_cost': round(parts_cost, 2),
            'labor_hours': round(labor_hours, 2),
            'labor_cost': round(labor_cost, 2),
            'total_cost': round(parts_cost + labor_cost, 2),
            'issue_reported': random.choice(self.common_issues) if random.random() > 0.3 else None,
            'issue_resolved': random.random() > 0.1,
            'customer_rating': random.randint(3, 5)
        }
    
    def generate_history(self, vehicle_id: str, num_records: int = 10) -> List[Dict]:
        """Generate maintenance history for a vehicle"""
        history = []
        start_date = datetime.now() - timedelta(days=730)
        
        for i in range(num_records):
            service_date = start_date + timedelta(days=random.randint(0, 730))
            history.append(self.generate_record(vehicle_id, service_date))
        
        return sorted(history, key=lambda x: x['service_date'])


class FeedbackDataGenerator:
    """Generate realistic customer feedback data"""
    
    def __init__(self):
        self.positive_comments = [
            "Excellent service! Very professional and quick.",
            "The mechanic explained everything clearly.",
            "Great experience, will definitely come back.",
            "Fixed my issue on the first visit.",
            "Reasonable prices and quality work."
        ]
        
        self.negative_comments = [
            "Issue came back after just a week.",
            "Took longer than expected.",
            "Price was higher than quoted.",
            "Not satisfied with the communication.",
            "Had to bring the car back twice."
        ]
        
        self.neutral_comments = [
            "Service was okay, nothing special.",
            "Got the job done.",
            "Average experience.",
            "Met my basic expectations.",
            "Typical service, nothing to complain about."
        ]
    
    def generate_feedback(self, vehicle_id: str, appointment_id: int = None) -> Dict:
        """Generate a feedback entry"""
        rating = random.randint(1, 5)
        
        if rating >= 4:
            comment = random.choice(self.positive_comments)
        elif rating <= 2:
            comment = random.choice(self.negative_comments)
        else:
            comment = random.choice(self.neutral_comments)
        
        return {
            'vehicle_id': vehicle_id,
            'appointment_id': appointment_id or random.randint(1, 1000),
            'feedback_type': random.choice(['repair', 'vehicle', 'service']),
            'rating': rating,
            'comment': comment,
            'repair_quality_rating': max(1, min(5, rating + random.randint(-1, 1))),
            'service_speed_rating': max(1, min(5, rating + random.randint(-1, 1))),
            'cost_satisfaction_rating': max(1, min(5, rating + random.randint(-1, 1))),
            'issue_recurring': random.random() < 0.15,
            'issue_fully_resolved': rating >= 4
        }


class SystemTester:
    """Test the complete TorqCare system"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def test_health_check(self) -> bool:
        """Test if API is responding"""
        try:
            response = await self.client.get(f"{self.api_url}/")
            print(f"✅ Health Check: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health Check Failed: {e}")
            return False
    
    async def test_sensor_data_ingestion(self, sensor_data: Dict) -> bool:
        """Test sensor data ingestion"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/sensor-data",
                json=sensor_data
            )
            print(f"✅ Sensor Data Ingestion: {response.status_code}")
            result = response.json()
            print(f"   Analysis: {result.get('analysis', {}).get('status', 'unknown')}")
            if result.get('analysis', {}).get('anomalies'):
                print(f"   Anomalies Detected: {len(result['analysis']['anomalies'])}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Sensor Data Ingestion Failed: {e}")
            return False
    
    async def test_prediction_api(self, sensor_data: Dict) -> bool:
        """Test failure prediction API"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/predict-failures",
                json=sensor_data
            )
            print(f"✅ Prediction API: {response.status_code}")
            result = response.json()
            predictions = result.get('predictions', [])
            print(f"   Predictions: {len(predictions)}")
            for pred in predictions[:3]:
                print(f"   - {pred.get('failure_type')}: {pred.get('probability'):.2%} confidence")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Prediction API Failed: {e}")
            return False
    
    async def test_chatbot(self, message: str, vehicle_id: str = "VEH001") -> bool:
        """Test chatbot API"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/chat",
                json={
                    'vehicle_id': vehicle_id,
                    'message': message
                }
            )
            print(f"✅ Chatbot API: {response.status_code}")
            result = response.json()
            print(f"   Response: {result.get('response', 'No response')[:100]}...")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Chatbot API Failed: {e}")
            return False
    
    async def test_appointment_creation(self, vehicle_id: str = "VEH001") -> bool:
        """Test appointment creation"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/appointments",
                json={
                    'vehicle_id': vehicle_id,
                    'issue_type': 'diagnostic',
                    'urgency': 'routine'
                }
            )
            print(f"✅ Appointment Creation: {response.status_code}")
            result = response.json()
            print(f"   Available Slots: {len(result.get('available_slots', []))}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Appointment Creation Failed: {e}")
            return False
    
    async def test_feedback_submission(self, feedback_data: Dict) -> bool:
        """Test feedback submission"""
        try:
            response = await self.client.post(
                f"{self.api_url}/api/feedback",
                json=feedback_data
            )
            print(f"✅ Feedback Submission: {response.status_code}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Feedback Submission Failed: {e}")
            return False
    
    async def test_agent_status(self) -> bool:
        """Test agent status endpoint"""
        try:
            response = await self.client.get(f"{self.api_url}/api/agents/status")
            print(f"✅ Agent Status: {response.status_code}")
            result = response.json()
            print(f"   Active Agents: {len(result)}")
            for agent_id, info in result.items():
                print(f"   - {info['name']}: {info['tasks_processed']} tasks")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Agent Status Failed: {e}")
            return False
    
    async def run_comprehensive_test(self):
        """Run all tests"""
        print("\n" + "="*60)
        print("🧪 TorqCare Comprehensive System Test")
        print("="*60 + "\n")
        
        # Test 1: Health Check
        print("Test 1: Health Check")
        await self.test_health_check()
        print()
        
        # Test 2: Sensor Data with Normal Reading
        print("Test 2: Normal Sensor Data")
        generator = SensorDataGenerator()
        normal_data = generator.generate_normal_reading()
        await self.test_sensor_data_ingestion(normal_data)
        print()
        
        # Test 3: Sensor Data with Anomaly
        print("Test 3: Anomalous Sensor Data")
        anomaly_data = generator.generate_anomalous_reading(anomaly_type='engine_overheating')
        await self.test_sensor_data_ingestion(anomaly_data)
        print()
        
        # Test 4: Prediction API
        print("Test 4: Failure Prediction")
        await self.test_prediction_api(anomaly_data)
        print()
        
        # Test 5: Chatbot
        print("Test 5: Chatbot Query")
        await self.test_chatbot("What is my current engine temperature?")
        print()
        
        # Test 6: Appointment Creation
        print("Test 6: Appointment Scheduling")
        await self.test_appointment_creation()
        print()
        
        # Test 7: Feedback
        print("Test 7: Feedback Submission")
        feedback_gen = FeedbackDataGenerator()
        feedback = feedback_gen.generate_feedback("VEH001")
        await self.test_feedback_submission(feedback)
        print()
        
        # Test 8: Agent Status
        print("Test 8: Agent Status")
        await self.test_agent_status()
        print()
        
        print("="*60)
        print("✅ Comprehensive Test Complete!")
        print("="*60)
        
        await self.client.aclose()


# Main execution
if __name__ == "__main__":
    import sys
    
    print("TorqCare Testing & Data Generation Utility")
    print("=" * 60)
    print("\nOptions:")
    print("1. Generate sample sensor data")
    print("2. Generate maintenance history")
    print("3. Generate feedback data")
    print("4. Run comprehensive system test")
    print("5. Generate all sample data and export to JSON")
    
    choice = input("\nSelect option (1-5): ").strip()
    
    if choice == "1":
        generator = SensorDataGenerator(anomaly_rate=0.2)
        dataset = generator.generate_dataset(num_samples=100)
        
        with open('sample_sensor_data.json', 'w') as f:
            json.dump(dataset, f, indent=2)
        
        print(f"✅ Generated {len(dataset)} sensor readings")
        print("   Saved to: sample_sensor_data.json")
        print(f"   Anomalies: ~{int(len(dataset) * 0.2)}")
    
    elif choice == "2":
        generator = MaintenanceDataGenerator()
        vehicle_ids = [f"VEH{str(i).zfill(3)}" for i in range(1, 11)]
        
        all_history = {}
        for vehicle_id in vehicle_ids:
            all_history[vehicle_id] = generator.generate_history(vehicle_id, num_records=15)
        
        with open('sample_maintenance_history.json', 'w') as f:
            json.dump(all_history, f, indent=2)
        
        print(f"✅ Generated maintenance history for {len(vehicle_ids)} vehicles")
        print("   Saved to: sample_maintenance_history.json")
    
    elif choice == "3":
        generator = FeedbackDataGenerator()
        feedback_list = [generator.generate_feedback(f"VEH{str(i).zfill(3)}") for i in range(1, 51)]
        
        with open('sample_feedback.json', 'w') as f:
            json.dump(feedback_list, f, indent=2)
        
        print(f"✅ Generated {len(feedback_list)} feedback entries")
        print("   Saved to: sample_feedback.json")
    
    elif choice == "4":
        print("\nStarting comprehensive system test...")
        print("Make sure the backend is running at http://localhost:8000\n")
        
        tester = SystemTester()
        asyncio.run(tester.run_comprehensive_test())
    
    elif choice == "5":
        print("\nGenerating all sample data...")
        
        # Sensor data
        sensor_gen = SensorDataGenerator(anomaly_rate=0.15)
        sensor_data = sensor_gen.generate_dataset(num_samples=1000)
        
        # Maintenance history
        maint_gen = MaintenanceDataGenerator()
        vehicle_ids = [f"VEH{str(i).zfill(3)}" for i in range(1, 21)]
        maintenance_data = {vid: maint_gen.generate_history(vid, 20) for vid in vehicle_ids}
        
        # Feedback
        feedback_gen = FeedbackDataGenerator()
        feedback_data = [feedback_gen.generate_feedback(random.choice(vehicle_ids)) for _ in range(200)]
        
        # Save all
        with open('all_sample_data.json', 'w') as f:
            json.dump({
                'sensor_data': sensor_data,
                'maintenance_history': maintenance_data,
                'feedback': feedback_data
            }, f, indent=2)
        
        print("✅ All sample data generated!")
        print(f"   Sensor readings: {len(sensor_data)}")
        print(f"   Vehicles with history: {len(maintenance_data)}")
        print(f"   Feedback entries: {len(feedback_data)}")
        print("   Saved to: all_sample_data.json")
    
    else:
        print("Invalid option selected.")