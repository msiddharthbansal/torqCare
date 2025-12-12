"""
Diagnosis Agent - Predicts potential mechanical issues using ML models
Identifies failing components and estimates time to failure
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import sys
sys.path.append('..')
from models.predictive_models import VehicleFailurePredictor
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os

class DiagnosisAgent:
    """
    Agent responsible for diagnosing vehicle issues and predicting failures
    """
    
    def __init__(self, groq_api_key: str = None, model_path: str = 'ml_models/trained_models'):
        self.api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            temperature=0.2,
            model_name="llama-3.1-70b-versatile",
            groq_api_key=self.api_key
        )
        
        # Load ML predictor
        self.predictor = VehicleFailurePredictor()
        try:
            self.predictor.load_models(model_path)
            print("✓ ML models loaded successfully")
        except Exception as e:
            print(f"⚠ Warning: Could not load ML models: {e}")
            print("  Models will be trained on first use")
            self.predictor = None
        
        # Issue severity mapping
        self.severity_map = {
            'Critical': {
                'priority': 1,
                'action': 'immediate_attention',
                'max_delay_hours': 24
            },
            'High': {
                'priority': 2,
                'action': 'schedule_soon',
                'max_delay_hours': 72
            },
            'Medium': {
                'priority': 3,
                'action': 'schedule_maintenance',
                'max_delay_hours': 168
            },
            'Low': {
                'priority': 4,
                'action': 'monitor',
                'max_delay_hours': 720
            }
        }
        
        # Component-specific recommendations
        self.repair_recommendations = {
            'Battery': {
                'common_fixes': [
                    'Battery cell balancing',
                    'Thermal management system check',
                    'Battery management system reset',
                    'Cell replacement if SoH < 70%'
                ],
                'avg_cost_range': (500, 3000),
                'avg_duration_hours': 4
            },
            'Motor': {
                'common_fixes': [
                    'Bearing replacement',
                    'Winding inspection and repair',
                    'Rotor balancing',
                    'Coolant system service'
                ],
                'avg_cost_range': (800, 4000),
                'avg_duration_hours': 6
            },
            'Brake': {
                'common_fixes': [
                    'Brake pad replacement',
                    'Hydraulic system inspection',
                    'Regenerative braking calibration',
                    'Brake fluid replacement'
                ],
                'avg_cost_range': (200, 1000),
                'avg_duration_hours': 2
            },
            'Tire': {
                'common_fixes': [
                    'Tire pressure adjustment',
                    'Tire rotation and balancing',
                    'Tire replacement',
                    'Alignment check'
                ],
                'avg_cost_range': (100, 800),
                'avg_duration_hours': 1
            },
            'Suspension': {
                'common_fixes': [
                    'Shock absorber replacement',
                    'Spring inspection',
                    'Bushing replacement',
                    'Alignment adjustment'
                ],
                'avg_cost_range': (400, 2000),
                'avg_duration_hours': 3
            },
            'Cooling': {
                'common_fixes': [
                    'Coolant pump replacement',
                    'Radiator cleaning/replacement',
                    'Coolant flush and refill',
                    'Thermostat replacement'
                ],
                'avg_cost_range': (300, 1500),
                'avg_duration_hours': 3
            },
            'Power Electronics': {
                'common_fixes': [
                    'Inverter inspection and repair',
                    'DC-DC converter replacement',
                    'Connector cleaning and tightening',
                    'Software update'
                ],
                'avg_cost_range': (600, 3500),
                'avg_duration_hours': 4
            }
        }
    
    def diagnose_vehicle(self, sensor_reading: Dict, anomalies: List[Dict] = None) -> Dict:
        """
        Comprehensive vehicle diagnosis using ML and rule-based analysis
        """
        diagnosis = {
            'vehicle_id': sensor_reading['vehicle_id'],
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': []
        }
        
        # ML-based prediction
        if self.predictor:
            try:
                ml_diagnosis = self.predictor.comprehensive_diagnosis(sensor_reading)
                diagnosis['ml_prediction'] = ml_diagnosis
                
                if ml_diagnosis['status'] == 'at_risk':
                    component_info = ml_diagnosis['component_diagnosis']
                    rul_info = ml_diagnosis['rul_estimation']
                    
                    # Determine severity based on RUL
                    if rul_info['rul_hours'] < 48:
                        severity = 'Critical'
                    elif rul_info['rul_hours'] < 168:
                        severity = 'High'
                    elif rul_info['rul_hours'] < 720:
                        severity = 'Medium'
                    else:
                        severity = 'Low'
                    
                    issue = {
                        'component': component_info['component'],
                        'confidence': component_info['confidence'],
                        'severity': severity,
                        'rul_hours': rul_info['rul_hours'],
                        'rul_days': rul_info['rul_days'],
                        'recommended_action': rul_info['recommended_action'],
                        'failure_probability': ml_diagnosis['failure_prediction']['failure_probability']
                    }
                    
                    # Add repair recommendations
                    if component_info['component'] in self.repair_recommendations:
                        issue['repair_info'] = self.repair_recommendations[component_info['component']]
                    
                    diagnosis['issues'].append(issue)
                    diagnosis['status'] = 'at_risk'
            except Exception as e:
                print(f"ML prediction error: {e}")
        
        # Incorporate anomaly-based diagnosis
        if anomalies:
            for anomaly in anomalies:
                # Check if not already diagnosed by ML
                component = anomaly['system']
                existing = [i for i in diagnosis['issues'] if i.get('component') == component]
                
                if not existing:
                    issue = {
                        'component': component,
                        'metric': anomaly['metric'],
                        'severity': anomaly['severity'],
                        'value': anomaly['value'],
                        'threshold': anomaly['threshold'],
                        'source': 'anomaly_detection'
                    }
                    
                    if component in self.repair_recommendations:
                        issue['repair_info'] = self.repair_recommendations[component]
                    
                    diagnosis['issues'].append(issue)
                    if diagnosis['status'] == 'healthy':
                        diagnosis['status'] = 'requires_attention'
        
        # Sort issues by severity
        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        diagnosis['issues'].sort(key=lambda x: severity_order.get(x['severity'], 4))
        
        return diagnosis
    
    async def generate_diagnosis_report(self, diagnosis: Dict) -> str:
        """
        Generate detailed diagnosis report using LLM
        """
        if diagnosis['status'] == 'healthy':
            return f"Vehicle {diagnosis['vehicle_id']} is operating normally. All systems are within acceptable parameters."
        
        issues_summary = "\n".join([
            f"- {i['component']}: {i['severity']} severity, "
            f"{'RUL: ' + str(round(i.get('rul_days', 0), 1)) + ' days' if 'rul_days' in i else 'Immediate attention needed'}"
            for i in diagnosis['issues'][:3]  # Top 3 issues
        ])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert automotive diagnostic technician specializing in electric vehicles.
            Provide clear, actionable diagnosis reports that prioritize safety and efficiency.
            Be specific about the issue and next steps."""),
            HumanMessage(content=f"""
            Generate a diagnosis report for:
            
            Vehicle: {diagnosis['vehicle_id']}
            Status: {diagnosis['status']}
            Number of Issues: {len(diagnosis['issues'])}
            
            Top Issues Identified:
            {issues_summary}
            
            Provide a concise diagnostic summary (3-4 sentences) that:
            1. Explains the primary concern
            2. States the urgency level
            3. Recommends immediate next steps
            4. Mentions any safety implications
            """)
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            return response.content
        except Exception as e:
            return f"Diagnostic Report: Vehicle {diagnosis['vehicle_id']} has {len(diagnosis['issues'])} issues requiring attention. Primary concern: {diagnosis['issues'][0]['component']} ({diagnosis['issues'][0]['severity']} severity)."
    
    def prioritize_repairs(self, issues: List[Dict]) -> List[Dict]:
        """
        Prioritize repair tasks based on severity, safety, and cost
        """
        prioritized = []
        
        for issue in issues:
            severity = issue.get('severity', 'Medium')
            component = issue.get('component', 'Unknown')
            
            priority_info = self.severity_map.get(severity, self.severity_map['Medium'])
            repair_info = self.repair_recommendations.get(component, {})
            
            prioritized.append({
                **issue,
                'priority_level': priority_info['priority'],
                'action_required': priority_info['action'],
                'max_delay_hours': priority_info['max_delay_hours'],
                'estimated_cost': repair_info.get('avg_cost_range', (0, 0))[0] if repair_info else 0,
                'estimated_duration': repair_info.get('avg_duration_hours', 0),
                'safety_critical': severity in ['Critical', 'High']
            })
        
        # Sort by priority level
        prioritized.sort(key=lambda x: (x['priority_level'], -x['estimated_cost']))
        
        return prioritized
    
    def generate_maintenance_plan(self, diagnosis: Dict) -> Dict:
        """
        Generate comprehensive maintenance plan
        """
        if not diagnosis['issues']:
            return {
                'vehicle_id': diagnosis['vehicle_id'],
                'plan_type': 'preventive',
                'total_cost_estimate': 0,
                'total_duration_hours': 0,
                'tasks': []
            }
        
        prioritized_issues = self.prioritize_repairs(diagnosis['issues'])
        
        # Calculate totals
        total_cost_min = sum([i.get('repair_info', {}).get('avg_cost_range', (0, 0))[0] for i in prioritized_issues])
        total_cost_max = sum([i.get('repair_info', {}).get('avg_cost_range', (0, 0))[1] for i in prioritized_issues])
        total_duration = sum([i.get('repair_info', {}).get('avg_duration_hours', 0) for i in prioritized_issues])
        
        # Determine plan type
        has_critical = any(i['severity'] == 'Critical' for i in prioritized_issues)
        plan_type = 'emergency' if has_critical else 'corrective'
        
        # Group tasks by urgency
        immediate_tasks = [i for i in prioritized_issues if i['severity'] in ['Critical', 'High']]
        scheduled_tasks = [i for i in prioritized_issues if i['severity'] in ['Medium', 'Low']]
        
        return {
            'vehicle_id': diagnosis['vehicle_id'],
            'plan_type': plan_type,
            'total_cost_estimate': (total_cost_min, total_cost_max),
            'total_duration_hours': total_duration,
            'immediate_tasks': immediate_tasks,
            'scheduled_tasks': scheduled_tasks,
            'tasks': prioritized_issues,
            'recommended_schedule': {
                'immediate': len(immediate_tasks),
                'within_week': len(scheduled_tasks)
            },
            'generated_at': datetime.now().isoformat()
        }
    
    def explain_technical_issue(self, component: str, issue_type: str) -> str:
        """
        Provide layman explanation of technical issues
        """
        explanations = {
            'Battery': {
                'SoH': "Battery health indicates how much of the original capacity remains. Lower values mean reduced range.",
                'Temperature': "High battery temperature can damage cells and reduce lifespan. Cooling system may need attention.",
                'Voltage': "Voltage irregularities suggest cell imbalance or failing battery management system."
            },
            'Motor': {
                'Vibration': "Excessive vibration often indicates worn bearings or rotor imbalance, which can lead to motor failure.",
                'Temperature': "Motor overheating may be caused by bearing wear, cooling issues, or electrical problems.",
                'Torque': "Irregular torque output suggests motor controller or winding issues."
            },
            'Brake': {
                'Pad Wear': "Brake pads wear naturally but need replacement when too thin to ensure safe stopping.",
                'Pressure': "Low brake pressure indicates possible fluid leak or pump failure - a safety critical issue.",
                'Regen': "Poor regenerative braking efficiency reduces range and increases brake pad wear."
            }
        }
        
        return explanations.get(component, {}).get(issue_type, "Technical issue detected requiring professional inspection.")

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_diagnosis():
        agent = DiagnosisAgent()
        
        test_reading = {
            'vehicle_id': 'EV-00001',
            'soc': 25, 'soh': 73, 'battery_temp': 52,
            'motor_temp': 92, 'motor_vibration': 1.7,
            'brake_pad_wear': 1.8, 'brake_pressure': 78,
            'tire_pressure_fl': 31, 'tire_pressure_fr': 32,
            'regen_efficiency': 68
        }
        
        diagnosis = agent.diagnose_vehicle(test_reading)
        print(f"Diagnosis: {diagnosis['status']}")
        print(f"Issues found: {len(diagnosis['issues'])}")
        
        if diagnosis['issues']:
            report = await agent.generate_diagnosis_report(diagnosis)
            print(f"\nReport:\n{report}")
            
            plan = agent.generate_maintenance_plan(diagnosis)
            print(f"\nMaintenance Plan: {plan['plan_type']}")
            print(f"Estimated cost: ${plan['total_cost_estimate'][0]}-${plan['total_cost_estimate'][1]}")
    
    asyncio.run(test_diagnosis())
