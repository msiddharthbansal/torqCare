"""
Data Analysis Agent - Continuous monitoring of vehicle telemetry data
Analyzes real-time sensor data and detects anomalies
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional
import os

class DataAnalysisAgent:
    """
    Agent responsible for continuous monitoring and analysis of vehicle telemetry data
    """
    
    def __init__(self, groq_api_key: str = None):
        self.api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            temperature=0.1,
            model_name="llama-3.1-70b-versatile",
            groq_api_key=self.api_key
        )
        
        # Thresholds for anomaly detection
        self.thresholds = {
            'battery': {
                'soc_min': 20, 'soh_min': 75, 'temp_max': 50,
                'voltage_range': (350, 450), 'current_max': 150
            },
            'motor': {
                'temp_max': 90, 'vibration_max': 1.5,
                'torque_range': (100, 400), 'rpm_max': 5000
            },
            'brake': {
                'pad_wear_min': 2, 'pressure_min': 60,
                'regen_efficiency_min': 60
            },
            'tire': {
                'pressure_min': 28, 'pressure_max': 40,
                'temp_max': 45
            },
            'suspension': {
                'load_max': 750
            }
        }
    
    def analyze_sensor_reading(self, reading: Dict) -> Dict:
        """
        Analyze a single sensor reading for anomalies
        """
        anomalies = []
        severity = "Normal"
        
        # Battery Analysis
        if reading['soc'] < self.thresholds['battery']['soc_min']:
            anomalies.append({
                'system': 'Battery',
                'metric': 'State of Charge',
                'value': reading['soc'],
                'threshold': self.thresholds['battery']['soc_min'],
                'severity': 'High' if reading['soc'] < 10 else 'Medium'
            })
        
        if reading['soh'] < self.thresholds['battery']['soh_min']:
            anomalies.append({
                'system': 'Battery',
                'metric': 'State of Health',
                'value': reading['soh'],
                'threshold': self.thresholds['battery']['soh_min'],
                'severity': 'High'
            })
        
        if reading['battery_temp'] > self.thresholds['battery']['temp_max']:
            anomalies.append({
                'system': 'Battery',
                'metric': 'Temperature',
                'value': reading['battery_temp'],
                'threshold': self.thresholds['battery']['temp_max'],
                'severity': 'Critical' if reading['battery_temp'] > 60 else 'High'
            })
        
        # Motor Analysis
        if reading['motor_temp'] > self.thresholds['motor']['temp_max']:
            anomalies.append({
                'system': 'Motor',
                'metric': 'Temperature',
                'value': reading['motor_temp'],
                'threshold': self.thresholds['motor']['temp_max'],
                'severity': 'High'
            })
        
        if reading['motor_vibration'] > self.thresholds['motor']['vibration_max']:
            anomalies.append({
                'system': 'Motor',
                'metric': 'Vibration',
                'value': reading['motor_vibration'],
                'threshold': self.thresholds['motor']['vibration_max'],
                'severity': 'Medium'
            })
        
        # Brake Analysis
        if reading['brake_pad_wear'] < self.thresholds['brake']['pad_wear_min']:
            anomalies.append({
                'system': 'Brake',
                'metric': 'Pad Wear',
                'value': reading['brake_pad_wear'],
                'threshold': self.thresholds['brake']['pad_wear_min'],
                'severity': 'High'
            })
        
        if reading['brake_pressure'] < self.thresholds['brake']['pressure_min']:
            anomalies.append({
                'system': 'Brake',
                'metric': 'Hydraulic Pressure',
                'value': reading['brake_pressure'],
                'threshold': self.thresholds['brake']['pressure_min'],
                'severity': 'Critical'
            })
        
        # Tire Analysis
        tire_pressures = [
            reading['tire_pressure_fl'], reading['tire_pressure_fr'],
            reading['tire_pressure_rl'], reading['tire_pressure_rr']
        ]
        low_tire = min(tire_pressures)
        if low_tire < self.thresholds['tire']['pressure_min']:
            anomalies.append({
                'system': 'Tire',
                'metric': 'Pressure',
                'value': low_tire,
                'threshold': self.thresholds['tire']['pressure_min'],
                'severity': 'Medium'
            })
        
        # Determine overall severity
        if anomalies:
            severities = [a['severity'] for a in anomalies]
            if 'Critical' in severities:
                severity = 'Critical'
            elif 'High' in severities:
                severity = 'High'
            elif 'Medium' in severities:
                severity = 'Medium'
            else:
                severity = 'Low'
        
        return {
            'vehicle_id': reading['vehicle_id'],
            'timestamp': reading.get('timestamp', datetime.now().isoformat()),
            'status': 'Anomaly Detected' if anomalies else 'Normal',
            'severity': severity,
            'anomalies': anomalies,
            'health_score': reading.get('component_health_score', 1.0),
            'failure_probability': reading.get('failure_probability', 0.0)
        }
    
    def analyze_trend(self, readings: List[Dict], window_minutes: int = 30) -> Dict:
        """
        Analyze trends in sensor data over a time window
        """
        if not readings:
            return {'status': 'insufficient_data'}
        
        df = pd.DataFrame(readings)
        
        # Calculate trends
        trends = {}
        for col in ['soc', 'soh', 'battery_temp', 'motor_temp', 'motor_vibration']:
            if col in df.columns:
                values = df[col].values
                if len(values) > 1:
                    # Linear regression for trend
                    x = np.arange(len(values))
                    z = np.polyfit(x, values, 1)
                    slope = z[0]
                    
                    # Classify trend
                    if abs(slope) < 0.01:
                        trend = 'stable'
                    elif slope > 0:
                        trend = 'increasing'
                    else:
                        trend = 'decreasing'
                    
                    trends[col] = {
                        'direction': trend,
                        'rate': float(slope),
                        'current': float(values[-1]),
                        'avg': float(np.mean(values)),
                        'std': float(np.std(values))
                    }
        
        return {
            'vehicle_id': readings[0]['vehicle_id'],
            'analysis_window': f'{window_minutes} minutes',
            'readings_analyzed': len(readings),
            'trends': trends,
            'timestamp': datetime.now().isoformat()
        }
    
    async def generate_analysis_report(self, analysis: Dict) -> str:
        """
        Use LLM to generate human-readable analysis report
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert vehicle diagnostics analyst. 
            Analyze the provided telemetry data and provide a concise, professional report.
            Focus on actionable insights and severity of issues."""),
            HumanMessage(content=f"""
            Analyze this vehicle telemetry data:
            
            Vehicle: {analysis['vehicle_id']}
            Status: {analysis['status']}
            Severity: {analysis['severity']}
            Health Score: {analysis['health_score']:.2f}
            Failure Probability: {analysis['failure_probability']:.2%}
            
            Detected Anomalies:
            {analysis['anomalies']}
            
            Provide a brief analysis report (2-3 sentences) highlighting:
            1. Current vehicle health status
            2. Most critical issues if any
            3. Immediate recommendations
            """)
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            return response.content
        except Exception as e:
            return f"Analysis: Vehicle {analysis['vehicle_id']} - {analysis['status']}. {len(analysis['anomalies'])} anomalies detected."
    
    def get_vehicle_health_summary(self, readings: List[Dict]) -> Dict:
        """
        Generate comprehensive health summary for a vehicle
        """
        if not readings:
            return {'status': 'no_data'}
        
        latest = readings[-1]
        
        # Calculate component-wise health scores
        battery_health = min(100, (latest['soh'] + latest['soc']) / 2)
        motor_health = max(0, 100 - (latest['motor_temp'] / 100 * 50 + latest['motor_vibration'] * 20))
        brake_health = min(100, (latest['brake_pad_wear'] / 12 * 100 + latest['regen_efficiency']))  / 2
        tire_health = min(100, min([latest['tire_pressure_fl'], latest['tire_pressure_fr'], 
                                    latest['tire_pressure_rl'], latest['tire_pressure_rr']]) / 35 * 100)
        
        overall_health = (battery_health + motor_health + brake_health + tire_health) / 4
        
        return {
            'vehicle_id': latest['vehicle_id'],
            'overall_health': round(overall_health, 2),
            'component_health': {
                'battery': round(battery_health, 2),
                'motor': round(motor_health, 2),
                'brake': round(brake_health, 2),
                'tire': round(tire_health, 2)
            },
            'last_updated': latest.get('timestamp', datetime.now().isoformat()),
            'distance_traveled': latest.get('distance_traveled', 0),
            'status': 'Excellent' if overall_health > 90 else 
                     'Good' if overall_health > 75 else
                     'Fair' if overall_health > 60 else 'Poor'
        }
    
    def detect_pattern_anomalies(self, readings: List[Dict]) -> List[Dict]:
        """
        Detect unusual patterns in sensor data using statistical methods
        """
        if len(readings) < 10:
            return []
        
        df = pd.DataFrame(readings)
        anomalies = []
        
        # Z-score based anomaly detection
        for col in ['battery_temp', 'motor_temp', 'motor_vibration', 'power_consumption']:
            if col in df.columns:
                mean = df[col].mean()
                std = df[col].std()
                
                if std > 0:
                    z_scores = np.abs((df[col] - mean) / std)
                    outliers = df[z_scores > 3]
                    
                    if not outliers.empty:
                        anomalies.append({
                            'metric': col,
                            'type': 'statistical_outlier',
                            'occurrences': len(outliers),
                            'severity': 'Medium'
                        })
        
        return anomalies

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        agent = DataAnalysisAgent()
        
        # Test reading
        test_reading = {
            'vehicle_id': 'EV-00001',
            'timestamp': datetime.now().isoformat(),
            'soc': 15,  # Low
            'soh': 72,  # Low
            'battery_voltage': 395,
            'battery_current': 80,
            'battery_temp': 55,  # High
            'motor_temp': 95,  # High
            'motor_vibration': 1.8,  # High
            'motor_torque': 250,
            'motor_rpm': 3000,
            'brake_pad_wear': 1.5,  # Low
            'brake_pressure': 85,
            'regen_efficiency': 75,
            'tire_pressure_fl': 32,
            'tire_pressure_fr': 31,
            'tire_pressure_rl': 33,
            'tire_pressure_rr': 32,
            'component_health_score': 0.65,
            'failure_probability': 0.85
        }
        
        analysis = agent.analyze_sensor_reading(test_reading)
        print("Analysis Result:")
        print(f"Status: {analysis['status']}")
        print(f"Severity: {analysis['severity']}")
        print(f"Anomalies: {len(analysis['anomalies'])}")
        
        report = await agent.generate_analysis_report(analysis)
        print(f"\nLLM Report:\n{report}")
    
    asyncio.run(test_agent())
