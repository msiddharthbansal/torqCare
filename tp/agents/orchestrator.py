"""
TorqCare Multi-Agent System - COMPLETE VERSION
agents/orchestrator.py

Central Orchestrator and All Specialized Agents
"""

import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================
# BASE AGENT CLASS
# ============================================

class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.task_count = 0
        self.status = "active"
        self.error_count = 0
    
    @abstractmethod
    async def process(self, data: Dict) -> Dict:
        """Process agent-specific task"""
        pass
    
    async def log_activity(self, action: str, input_data: Dict, output_data: Dict):
        """Log agent activity"""
        self.task_count += 1
        logger.info(f"[{self.name}] Action: {action} | Tasks: {self.task_count}")
        
    def get_status(self) -> Dict:
        """Get agent status"""
        return {
            "name": self.name,
            "status": self.status,
            "tasks_processed": self.task_count,
            "error_count": self.error_count
        }


# ============================================
# AGENT ORCHESTRATOR
# ============================================

class AgentOrchestrator:
    """
    Central orchestrator that coordinates all agents
    Manages agent communication, task routing, and workflow execution
    """
    
    def __init__(self):
        self.agents = {}
        self.active_workflows = {}
        self.event_queue = asyncio.Queue()
        self.workflow_history = []
        
    def register_agent(self, agent_id: str, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent_id] = agent
        logger.info(f"✅ Agent registered: {agent_id} - {agent.name}")
    
    def get_agent_status(self) -> Dict:
        """Get status of all agents"""
        return {
            agent_id: agent.get_status()
            for agent_id, agent in self.agents.items()
        }
    
    async def process_sensor_data(self, sensor_data: Dict) -> Dict:
        """
        Main Workflow: Sensor data received
        1. Data Analysis Agent analyzes data
        2. If anomalies detected, trigger Diagnosis Agent
        3. If critical, trigger Scheduling Agent
        4. Log to Quality Insights
        """
        workflow_id = f"workflow_{datetime.now().timestamp()}"
        self.active_workflows[workflow_id] = {
            "started_at": datetime.now().isoformat(),
            "status": "processing"
        }
        
        try:
            # Step 1: Data Analysis
            analysis_result = await self.agents['data_analysis'].process({
                'action': 'analyze_sensors',
                'data': sensor_data
            })
            
            # Step 2: Check for anomalies
            if analysis_result.get('anomalies'):
                logger.info(f"🚨 {len(analysis_result['anomalies'])} anomalies detected")
                
                # Parallel processing: Diagnosis + Quality Insights
                diagnosis_task = self.agents['diagnosis'].process({
                    'action': 'diagnose',
                    'sensor_data': sensor_data,
                    'anomalies': analysis_result['anomalies']
                })
                
                quality_task = self.agents['quality_insights'].process({
                    'action': 'log_anomaly',
                    'vehicle_id': sensor_data.get('vehicle_id'),
                    'anomalies': analysis_result['anomalies']
                })
                
                diagnosis_result, _ = await asyncio.gather(diagnosis_task, quality_task)
                analysis_result['diagnosis'] = diagnosis_result
                
                # Step 3: If critical, auto-schedule
                if diagnosis_result.get('severity') == 'critical':
                    logger.info("⚠️ Critical issue detected - Auto-scheduling appointment")
                    
                    appointment = await self.agents['scheduling'].process({
                        'action': 'auto_schedule',
                        'vehicle_id': sensor_data.get('vehicle_id'),
                        'diagnosis': diagnosis_result,
                        'urgency': 'critical'
                    })
                    
                    analysis_result['appointment'] = appointment
                    
                    # Notify customer via engagement agent
                    await self.agents['customer_engagement'].process({
                        'action': 'send_alert',
                        'vehicle_id': sensor_data.get('vehicle_id'),
                        'diagnosis': diagnosis_result,
                        'appointment': appointment
                    })
            
            self.active_workflows[workflow_id]['status'] = 'completed'
            self.workflow_history.append(self.active_workflows[workflow_id])
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"❌ Workflow error: {e}")
            self.active_workflows[workflow_id]['status'] = 'failed'
            self.active_workflows[workflow_id]['error'] = str(e)
            raise
    
    async def diagnose_issue(self, sensor_data: Dict, analysis: Dict) -> Dict:
        """Diagnose vehicle issue"""
        return await self.agents['diagnosis'].process({
            'action': 'diagnose',
            'sensor_data': sensor_data,
            'analysis': analysis
        })
    
    async def schedule_appointment(self, vehicle_id: str, issue: Dict, urgency: str) -> Dict:
        """Schedule appointment for repair"""
        return await self.agents['scheduling'].process({
            'action': 'schedule',
            'vehicle_id': vehicle_id,
            'issue': issue,
            'urgency': urgency
        })
    
    async def process_feedback(self, feedback_data: Dict):
        """
        Workflow: Feedback received
        1. Feedback Agent processes and categorizes
        2. Quality Insights Agent aggregates for manufacturer
        3. Customer Engagement Agent may respond
        """
        try:
            # Process feedback
            feedback_result = await self.agents['feedback'].process({
                'action': 'process_feedback',
                'data': feedback_data
            })
            
            # Parallel: Update quality insights and notify customer
            quality_task = self.agents['quality_insights'].process({
                'action': 'ingest_feedback',
                'feedback': feedback_result
            })
            
            engagement_task = self.agents['customer_engagement'].process({
                'action': 'acknowledge_feedback',
                'feedback': feedback_result
            })
            
            await asyncio.gather(quality_task, engagement_task)
            
            return feedback_result
            
        except Exception as e:
            logger.error(f"❌ Feedback processing error: {e}")
            raise


# ============================================
# AGENT 1: DATA ANALYSIS AGENT
# ============================================

class DataAnalysisAgent(BaseAgent):
    """
    Agent 1: Continuous monitoring and analysis of vehicle telemetry data
    Detects anomalies and patterns in real-time sensor readings
    """
    
    def __init__(self):
        super().__init__("Data Analysis Agent")
        self.baseline_thresholds = {
            'engine_temp': {'min': 70, 'max': 95, 'critical': 100},
            'battery_voltage': {'min': 12.0, 'max': 14.5, 'critical': 11.5},
            'oil_pressure': {'min': 20, 'max': 60, 'critical': 15},
            'tire_pressure': {'min': 28, 'max': 35, 'critical': 25},
            'brake_fluid': {'min': 70, 'max': 100, 'critical': 60}
        }
        self.analysis_count = 0
    
    async def process(self, data: Dict) -> Dict:
        """Analyze sensor data for anomalies"""
        action = data.get('action')
        
        if action == 'analyze_sensors':
            return await self._analyze_sensors(data['data'])
        
        return {}
    
    async def _analyze_sensors(self, sensor_data: Dict) -> Dict:
        """Perform real-time analysis of sensor data"""
        self.analysis_count += 1
        anomalies = []
        metrics = {}
        
        # Analyze engine temperature
        engine_temp = sensor_data.get('engine_temp', 0)
        if engine_temp > self.baseline_thresholds['engine_temp']['critical']:
            anomalies.append({
                'type': 'engine_overheating',
                'severity': 'critical',
                'value': engine_temp,
                'threshold': self.baseline_thresholds['engine_temp']['critical'],
                'message': f"Engine temperature critically high: {engine_temp:.1f}°C",
                'recommended_action': 'Stop vehicle immediately and let engine cool'
            })
        elif engine_temp > self.baseline_thresholds['engine_temp']['max']:
            anomalies.append({
                'type': 'engine_high_temp',
                'severity': 'warning',
                'value': engine_temp,
                'threshold': self.baseline_thresholds['engine_temp']['max'],
                'message': f"Engine temperature elevated: {engine_temp:.1f}°C",
                'recommended_action': 'Monitor temperature closely, reduce speed'
            })
        
        # Analyze battery
        battery_voltage = sensor_data.get('battery_voltage', 12.6)
        if battery_voltage < self.baseline_thresholds['battery_voltage']['critical']:
            anomalies.append({
                'type': 'battery_critical',
                'severity': 'critical',
                'value': battery_voltage,
                'threshold': self.baseline_thresholds['battery_voltage']['critical'],
                'message': f"Battery voltage critically low: {battery_voltage:.1f}V",
                'recommended_action': 'Battery replacement needed immediately'
            })
        elif battery_voltage < self.baseline_thresholds['battery_voltage']['min']:
            anomalies.append({
                'type': 'battery_low',
                'severity': 'warning',
                'value': battery_voltage,
                'threshold': self.baseline_thresholds['battery_voltage']['min'],
                'message': f"Battery voltage low: {battery_voltage:.1f}V",
                'recommended_action': 'Battery test recommended within 3 days'
            })
        
        # Analyze oil pressure
        oil_pressure = sensor_data.get('oil_pressure', 35)
        if oil_pressure < self.baseline_thresholds['oil_pressure']['critical']:
            anomalies.append({
                'type': 'oil_pressure_critical',
                'severity': 'critical',
                'value': oil_pressure,
                'threshold': self.baseline_thresholds['oil_pressure']['critical'],
                'message': f"Oil pressure critically low: {oil_pressure:.0f} PSI",
                'recommended_action': 'Stop vehicle immediately, check oil level'
            })
        elif oil_pressure < self.baseline_thresholds['oil_pressure']['min']:
            anomalies.append({
                'type': 'oil_pressure_low',
                'severity': 'warning',
                'value': oil_pressure,
                'threshold': self.baseline_thresholds['oil_pressure']['min'],
                'message': f"Oil pressure low: {oil_pressure:.0f} PSI",
                'recommended_action': 'Schedule oil system inspection'
            })
        
        # Analyze tire pressures
        tire_pressures = {
            'fl': sensor_data.get('tire_pressure_fl', 32),
            'fr': sensor_data.get('tire_pressure_fr', 32),
            'rl': sensor_data.get('tire_pressure_rl', 32),
            'rr': sensor_data.get('tire_pressure_rr', 32)
        }
        
        for position, pressure in tire_pressures.items():
            if pressure < self.baseline_thresholds['tire_pressure']['critical']:
                anomalies.append({
                    'type': f'tire_pressure_{position}',
                    'severity': 'critical',
                    'value': pressure,
                    'threshold': self.baseline_thresholds['tire_pressure']['critical'],
                    'message': f"Tire pressure critically low ({position.upper()}): {pressure:.1f} PSI",
                    'recommended_action': f'Inflate {position.upper()} tire immediately to 32 PSI'
                })
            elif pressure < self.baseline_thresholds['tire_pressure']['min']:
                anomalies.append({
                    'type': f'tire_pressure_{position}',
                    'severity': 'warning',
                    'value': pressure,
                    'threshold': self.baseline_thresholds['tire_pressure']['min'],
                    'message': f"Tire pressure low ({position.upper()}): {pressure:.1f} PSI",
                    'recommended_action': f'Inflate {position.upper()} tire to 32 PSI'
                })
        
        # Analyze brake fluid
        brake_fluid = sensor_data.get('brake_fluid_level', 85)
        if brake_fluid < self.baseline_thresholds['brake_fluid']['critical']:
            anomalies.append({
                'type': 'brake_fluid_critical',
                'severity': 'critical',
                'value': brake_fluid,
                'threshold': self.baseline_thresholds['brake_fluid']['critical'],
                'message': f"Brake fluid critically low: {brake_fluid:.0f}%",
                'recommended_action': 'Do not drive - brake system inspection required'
            })
        elif brake_fluid < self.baseline_thresholds['brake_fluid']['min']:
            anomalies.append({
                'type': 'brake_fluid_low',
                'severity': 'warning',
                'value': brake_fluid,
                'threshold': self.baseline_thresholds['brake_fluid']['min'],
                'message': f"Brake fluid low: {brake_fluid:.0f}%",
                'recommended_action': 'Schedule brake system inspection'
            })
        
        # Calculate health metrics
        metrics = {
            'engine_health': self._calculate_component_health('engine', sensor_data),
            'battery_health': self._calculate_component_health('battery', sensor_data),
            'tire_health': self._calculate_component_health('tires', sensor_data),
            'brake_health': self._calculate_component_health('brakes', sensor_data),
            'overall_health': max(0, 100 - (len([a for a in anomalies if a['severity'] == 'critical']) * 20) - (len([a for a in anomalies if a['severity'] == 'warning']) * 5))
        }
        
        await self.log_activity('analyze_sensors', sensor_data, {'anomaly_count': len(anomalies)})
        
        return {
            'anomalies': anomalies,
            'metrics': metrics,
            'status': 'critical' if any(a['severity'] == 'critical' for a in anomalies) else 'warning' if anomalies else 'normal',
            'timestamp': datetime.now().isoformat(),
            'analysis_id': self.analysis_count
        }
    
    def _calculate_component_health(self, component: str, sensor_data: Dict) -> float:
        """Calculate health score for a vehicle component (0-100)"""
        if component == 'engine':
            temp = sensor_data.get('engine_temp', 75)
            oil = sensor_data.get('oil_pressure', 35)
            temp_score = max(0, 100 - abs(temp - 85) * 2)
            oil_score = max(0, min(100, (oil / 35) * 100))
            return round((temp_score + oil_score) / 2, 1)
        
        elif component == 'battery':
            voltage = sensor_data.get('battery_voltage', 12.6)
            score = max(0, min(100, ((voltage - 11) / 3) * 100))
            return round(score, 1)
        
        elif component == 'tires':
            pressures = [
                sensor_data.get('tire_pressure_fl', 32),
                sensor_data.get('tire_pressure_fr', 32),
                sensor_data.get('tire_pressure_rl', 32),
                sensor_data.get('tire_pressure_rr', 32)
            ]
            avg_pressure = sum(pressures) / len(pressures)
            score = max(0, 100 - abs(avg_pressure - 32) * 5)
            return round(score, 1)
        
        elif component == 'brakes':
            brake_fluid = sensor_data.get('brake_fluid_level', 85)
            score = max(0, min(100, brake_fluid))
            return round(score, 1)
        
        return 100.0


# ============================================
# AGENT 2: DIAGNOSIS AGENT
# ============================================

class DiagnosisAgent(BaseAgent):
    """
    Agent 2: Predictive diagnosis of mechanical issues
    Uses ML models and rule-based systems to predict failures
    """
    
    def __init__(self):
        super().__init__("Diagnosis Agent")
        self.diagnosis_rules = self._load_diagnosis_rules()
    
    async def process(self, data: Dict) -> Dict:
        """Diagnose vehicle issues"""
        action = data.get('action')
        
        if action == 'diagnose':
            return await self._diagnose(data.get('sensor_data'), data.get('anomalies', []))
        
        return {}
    
    async def _diagnose(self, sensor_data: Dict, anomalies: List) -> Dict:
        """Perform diagnosis based on sensor data and anomalies"""
        diagnosis = {
            'issues': [],
            'severity': 'normal',
            'recommended_actions': [],
            'estimated_cost_range': (0, 0),
            'confidence': 0.0,
            'time_to_failure_estimate': None
        }
        
        # Analyze each anomaly
        for anomaly in anomalies:
            issue = self._analyze_anomaly(anomaly, sensor_data)
            if issue:
                diagnosis['issues'].append(issue)
        
        # Determine overall severity
        if any(i['severity'] == 'critical' for i in diagnosis['issues']):
            diagnosis['severity'] = 'critical'
            diagnosis['time_to_failure_estimate'] = '0-24 hours'
        elif any(i['severity'] == 'high' for i in diagnosis['issues']):
            diagnosis['severity'] = 'high'
            diagnosis['time_to_failure_estimate'] = '1-7 days'
        elif diagnosis['issues']:
            diagnosis['severity'] = 'medium'
            diagnosis['time_to_failure_estimate'] = '1-4 weeks'
        
        # Aggregate recommendations and costs
        all_actions = []
        for issue in diagnosis['issues']:
            all_actions.extend(issue.get('actions', []))
        diagnosis['recommended_actions'] = list(set(all_actions))
        
        # Calculate cost range
        if diagnosis['issues']:
            min_cost = min(issue.get('estimated_cost_range', (0, 0))[0] for issue in diagnosis['issues'])
            max_cost = sum(issue.get('estimated_cost_range', (0, 0))[1] for issue in diagnosis['issues'])
            diagnosis['estimated_cost_range'] = (min_cost, max_cost)
        
        # Calculate average confidence
        if diagnosis['issues']:
            diagnosis['confidence'] = sum(
                issue.get('confidence', 0) 
                for issue in diagnosis['issues']
            ) / len(diagnosis['issues'])
        
        await self.log_activity('diagnose', sensor_data, diagnosis)
        
        return diagnosis
    
    def _analyze_anomaly(self, anomaly: Dict, sensor_data: Dict) -> Optional[Dict]:
        """Analyze specific anomaly and provide diagnosis"""
        anomaly_type = anomaly['type']
        
        diagnosis_map = {
            'engine_overheating': {
                'issue': 'Engine Overheating',
                'severity': 'critical',
                'probable_causes': [
                    'Low coolant level',
                    'Thermostat failure',
                    'Radiator blockage',
                    'Water pump failure',
                    'Cooling fan malfunction'
                ],
                'actions': [
                    'Stop vehicle immediately',
                    'Check coolant level',
                    'Inspect radiator for leaks',
                    'Professional diagnosis required',
                    'Do not continue driving'
                ],
                'estimated_cost_range': (200, 1200),
                'confidence': 0.85,
                'urgency': 'immediate'
            },
            'engine_high_temp': {
                'issue': 'Elevated Engine Temperature',
                'severity': 'medium',
                'probable_causes': [
                    'Low coolant level',
                    'Thermostat beginning to fail',
                    'Cooling system needs service'
                ],
                'actions': [
                    'Monitor temperature closely',
                    'Check coolant level',
                    'Schedule cooling system inspection'
                ],
                'estimated_cost_range': (100, 500),
                'confidence': 0.70,
                'urgency': 'within_week'
            },
            'battery_critical': {
                'issue': 'Battery Failure Imminent',
                'severity': 'critical',
                'probable_causes': [
                    'Battery end of life',
                    'Alternator not charging',
                    'Parasitic electrical drain',
                    'Faulty voltage regulator'
                ],
                'actions': [
                    'Battery replacement needed',
                    'Alternator output test',
                    'Electrical system diagnosis',
                    'Test for parasitic drain'
                ],
                'estimated_cost_range': (150, 400),
                'confidence': 0.90,
                'urgency': 'immediate'
            },
            'battery_low': {
                'issue': 'Weak Battery',
                'severity': 'medium',
                'probable_causes': [
                    'Battery aging',
                    'Alternator charging issue',
                    'Frequent short trips'
                ],
                'actions': [
                    'Battery load test',
                    'Check alternator output',
                    'Consider battery replacement'
                ],
                'estimated_cost_range': (50, 300),
                'confidence': 0.75,
                'urgency': 'within_week'
            },
            'oil_pressure_critical': {
                'issue': 'Critical Oil Pressure Loss',
                'severity': 'critical',
                'probable_causes': [
                    'Oil leak',
                    'Oil pump failure',
                    'Critically low oil level',
                    'Worn engine bearings',
                    'Blocked oil filter'
                ],
                'actions': [
                    'Stop vehicle immediately',
                    'Check oil level urgently',
                    'Do not drive vehicle',
                    'Towing recommended',
                    'Engine damage risk'
                ],
                'estimated_cost_range': (300, 2500),
                'confidence': 0.80,
                'urgency': 'immediate'
            },
            'oil_pressure_low': {
                'issue': 'Low Oil Pressure',
                'severity': 'high',
                'probable_causes': [
                    'Low oil level',
                    'Oil pump wearing',
                    'Oil filter needs replacement',
                    'Using wrong oil viscosity'
                ],
                'actions': [
                    'Check oil level immediately',
                    'Oil change if overdue',
                    'Oil system inspection',
                    'Use correct oil grade'
                ],
                'estimated_cost_range': (100, 600),
                'confidence': 0.75,
                'urgency': 'within_3_days'
            },
            'brake_fluid_critical': {
                'issue': 'Critical Brake Fluid Level',
                'severity': 'critical',
                'probable_causes': [
                    'Brake fluid leak',
                    'Worn brake pads',
                    'Master cylinder leak',
                    'Brake line leak'
                ],
                'actions': [
                    'Do not drive vehicle',
                    'Brake system inspection required',
                    'Check for visible leaks',
                    'Towing recommended'
                ],
                'estimated_cost_range': (200, 1000),
                'confidence': 0.85,
                'urgency': 'immediate'
            },
            'brake_fluid_low': {
                'issue': 'Low Brake Fluid',
                'severity': 'high',
                'probable_causes': [
                    'Brake pad wear',
                    'Minor brake fluid leak',
                    'Normal fluid consumption'
                ],
                'actions': [
                    'Brake system inspection',
                    'Check brake pads',
                    'Inspect for leaks',
                    'Top up brake fluid'
                ],
                'estimated_cost_range': (100, 600),
                'confidence': 0.80,
                'urgency': 'within_3_days'
            }
        }
        
        # Handle tire pressure anomalies
        if 'tire_pressure' in anomaly_type:
            position = anomaly_type.split('_')[-1].upper()
            severity = anomaly.get('severity', 'warning')
            
            return {
                'issue': f'Low Tire Pressure - {position}',
                'severity': severity,
                'probable_causes': [
                    'Slow leak or puncture',
                    'Temperature change',
                    'Valve stem issue',
                    'Tire damage'
                ],
                'actions': [
                    f'Inflate {position} tire to 32 PSI',
                    'Inspect tire for punctures',
                    'Check valve stem',
                    'Monitor pressure daily' if severity == 'warning' else 'Do not drive - tire change may be needed'
                ],
                'estimated_cost_range': (0, 200) if severity == 'warning' else (50, 400),
                'confidence': 0.95,
                'urgency': 'immediate' if severity == 'critical' else 'within_3_days'
            }
        
        return diagnosis_map.get(anomaly_type)
    
    def _load_diagnosis_rules(self) -> Dict:
        """Load diagnosis rules (placeholder for ML model integration)"""
        return {
            'engine': ['overheating', 'oil_pressure', 'coolant'],
            'electrical': ['battery', 'alternator', 'starter'],
            'brakes': ['fluid', 'pads', 'rotors'],
            'tires': ['pressure', 'tread', 'alignment']
        }


# ============================================
# AGENT 3: CUSTOMER ENGAGEMENT AGENT
# ============================================

class CustomerEngagementAgent(BaseAgent):
    """
    Agent 3: AI chatbot for customer queries
    Handles questions about telemetry, maintenance, and vehicle information
    """
    
    def __init__(self):
        super().__init__("Customer Engagement Agent")
        self.knowledge_base = self._build_knowledge_base()
        self.conversation_history = {}
    
    async def process(self, data: Dict) -> Dict:
        """Process customer interaction"""
        action = data.get('action')
        
        if action == 'process_query':
            return await self._process_query(
                data['message'],
                data.get('vehicle_id'),
                data.get('sensor_data'),
                data.get('context')
            )
        elif action == 'acknowledge_feedback':
            return await self._acknowledge_feedback(data['feedback'])
        elif action == 'send_alert':
            return await self._send_alert(
                data['vehicle_id'],
                data['diagnosis'],
                data.get('appointment')
            )
        
        return {}
    
    async def _process_query(self, message: str, vehicle_id: str, sensor_data: Dict, context: Dict) -> str:
        """Process customer query and generate response"""
        message_lower = message.lower()
        
        # Store conversation history
        if vehicle_id not in self.conversation_history:
            self.conversation_history[vehicle_id] = []
        self.conversation_history[vehicle_id].append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'type': 'user'
        })
        
        # Identify query type and respond
        response = ""
        
        if any(word in message_lower for word in ['temperature', 'hot', 'overheat', 'heat']):
            response = self._respond_temperature_query(sensor_data)
        
        elif any(word in message_lower for word in ['battery', 'voltage', 'start', 'electrical']):
            response = self._respond_battery_query(sensor_data)
        
        elif any(word in message_lower for word in ['tire', 'pressure', 'psi', 'flat']):
            response = self._respond_tire_query(sensor_data)
        
        elif any(word in message_lower for word in ['oil', 'lubrication', 'leak']):
            response = self._respond_oil_query(sensor_data)
        
        elif any(word in message_lower for word in ['brake', 'braking', 'stop']):
            response = self._respond_brake_query(sensor_data)
        
        elif any(word in message_lower for word in ['service', 'maintenance', 'schedule', 'appointment']):
            response = self._respond_maintenance_query(sensor_data)
        
        elif any(word in message_lower for word in ['cost', 'price', 'estimate', 'expensive']):
            response = self._respond_cost_query()
        
        elif any(word in message_lower for word in ['health', 'status', 'condition', 'overall']):
            response = self._respond_health_query(sensor_data)
        
        elif any(word in message_lower for word in ['help', 'what can you do', 'assist']):
            response = self._respond_help_query()
        
        else:
            response = "I can help you with vehicle diagnostics, real-time telemetry analysis, maintenance scheduling, and repair cost estimates. Could you please be more specific about what information you need?"
        
        # Store response
        self.conversation_history[vehicle_id].append({
            'timestamp': datetime.now().isoformat(),
            'message': response,
            'type': 'assistant'
        })
        
        await self.log_activity('process_query', {'message': message}, {'response_length': len(response)})
        
        return response
    
    def _respond_temperature_query(self, sensor_data: Dict) -> str:
        """Respond to temperature-related query"""
        if not sensor_data:
            return "I don't have current telemetry data. Please ensure your vehicle is connected."
        
        temp = sensor_data.get('engine_temp', 0)
        
        if temp > 100:
            return f"⚠️ CRITICAL ALERT: Your engine temperature is {temp:.1f}°C, which is dangerously high! Normal range is 70-95°C.\n\n🚨 IMMEDIATE ACTIONS REQUIRED:\n• Pull over safely immediately\n• Turn off the engine\n• Do not open the hood right away (risk of burns)\n• Let the engine cool for at least 30 minutes\n• Check coolant level\n• Do NOT continue driving\n\nThis could indicate a serious cooling system failure. I've automatically created an urgent service appointment for you."
        elif temp > 95:
            return f"⚠️ WARNING: Your engine temperature is {temp:.1f}°C, which is above normal operating range (70-95°C).\n\nRECOMMENDED ACTIONS:\n• Reduce speed and avoid heavy acceleration\n• Turn on heater to help cool engine\n• Monitor temperature closely\n• If temperature continues to rise, pull over safely\n• Schedule a cooling system inspection within 48 hours\n\nPossible causes: Low coolant, thermostat issue, or cooling fan problem."
        elif temp > 90:
            return f"Your engine temperature is {temp:.1f}°C, slightly elevated but manageable. Normal range is 70-95°C.\n\nTIPS:\n• Monitor it closely\n• Avoid stop-and-go traffic if possible\n• Ensure coolant is at proper level\n• Consider a cooling system check at your next service"
        else:
            return f"✅ Your engine temperature is {temp:.1f}°C, which is within normal operating range (70-95°C). Engine thermal management is functioning properly. No concerns at this time."
    
    def _respond_battery_query(self, sensor_data: Dict) -> str:
        """Respond to battery-related query"""
        if not sensor_data:
            return "Unable to access current battery data. Please check your vehicle connection."
        
        voltage = sensor_data.get('battery_voltage', 0)
        
        if voltage < 11.5:
            return f"🚨 CRITICAL: Battery voltage is {voltage:.1f}V, which is critically low!\n\nA healthy battery reads 12.6V or higher when off, 13.5-14.5V when running.\n\nIMMEDIATE RISKS:\n• Vehicle may not start\n• Risk of being stranded\n• Potential alternator damage\n\nACTION REQUIRED:\n• Do not turn off the vehicle if currently running\n• Drive directly to nearest service center\n• Battery replacement needed immediately\n• Have alternator tested\n\nEstimated Cost: $150-$300 for battery replacement"
        elif voltage < 12.0:
            return f"⚠️ WARNING: Battery voltage is {voltage:.1f}V, which is below optimal levels.\n\nHEALTHY RANGE: 12.6-12.8V (engine off), 13.5-14.5V (engine running)\n\nRECOMMENDED ACTIONS:\n• Battery load test within 3 days\n• Check alternator charging system\n• Avoid leaving lights/accessories on\n• Consider battery replacement soon\n\nSYMPTOMS TO WATCH:\n• Slow engine cranking\n• Dimming lights\n• Electrical accessories malfunctioning"
        elif voltage < 12.4:
            return f"Your battery voltage is {voltage:.1f}V, slightly below optimal.\n\nOPTIMAL RANGE: 12.6-12.8V (fully charged)\n\nSUGGESTIONS:\n• Have battery tested at next service\n• May need charging or replacement soon\n• Check for parasitic drain if this persists\n• Ensure battery terminals are clean and tight"
        else:
            return f"✅ Battery health is good at {voltage:.1f}V. This is within the healthy range of 12.4-14.5V. Your charging system is functioning properly. No immediate concerns."
    
    def _respond_tire_query(self, sensor_data: Dict) -> str:
        """Respond to tire-related query"""
        if not sensor_data:
            return "Unable to access tire pressure data."
        
        pressures = {
            'Front Left': sensor_data.get('tire_pressure_fl', 0),
            'Front Right': sensor_data.get('tire_pressure_fr', 0),
            'Rear Left': sensor_data.get('tire_pressure_rl', 0),
            'Rear Right': sensor_data.get('tire_pressure_rr', 0)
        }
        
        response = "🚗 CURRENT TIRE PRESSURES:\n"
        critical_tires = []
        low_tires = []
        
        for position, pressure in pressures.items():
            status = "✅"
            if pressure < 25:
                status = "🚨 CRITICAL"
                critical_tires.append(position)
            elif pressure < 28:
                status = "⚠️ LOW"
                low_tires.append(position)
            
            response += f"• {position}: {pressure:.1f} PSI {status}\n"
        
        response += f"\nRECOMMENDED PRESSURE: 32 PSI (all tires)\n"
        
        if critical_tires:
            response += f"\n🚨 CRITICAL ISSUE:\n"
            response += f"{', '.join(critical_tires)} tire(s) are critically underinflated!\n\n"
            response += "IMMEDIATE ACTIONS:\n"
            response += "• Do not drive at high speeds\n"
            response += "• Inflate immediately to 32 PSI\n"
            response += "• Inspect for punctures or damage\n"
            response += "• Risk of tire failure if not addressed\n"
            response += "• May need tire replacement if damaged\n"
        elif low_tires:
            response += f"\n⚠️ ATTENTION NEEDED:\n"
            response += f"{', '.join(low_tires)} tire(s) need inflation.\n\n"
            response += "RECOMMENDED ACTIONS:\n"
            response += "• Inflate to 32 PSI within 2-3 days\n"
            response += "• Check for slow leaks\n"
            response += "• Inspect valve stems\n"
            response += "• Underinflation reduces fuel efficiency by 3-5%\n"
        else:
            response += "\n✅ All tires are properly inflated! Good pressure maintenance improves:\n"
            response += "• Fuel efficiency\n"
            response += "• Tire lifespan\n"
            response += "• Vehicle handling\n"
            response += "• Braking performance\n"
        
        return response
    
    def _respond_oil_query(self, sensor_data: Dict) -> str:
        """Respond to oil-related query"""
        if not sensor_data:
            return "Unable to access oil system data."
        
        oil_pressure = sensor_data.get('oil_pressure', 0)
        
        if oil_pressure < 15:
            return f"🚨 CRITICAL ALERT: Oil pressure is {oil_pressure:.0f} PSI - Dangerously Low!\n\nNORMAL RANGE: 25-60 PSI (varies with RPM)\n\nIMMEDIATE ACTIONS REQUIRED:\n• Stop the engine immediately\n• Do not continue driving\n• Check oil level urgently\n• Look for oil leaks under vehicle\n• Call for towing service\n\nRISKS OF CONTINUING:\n• Complete engine failure\n• Catastrophic damage to engine bearings\n• Repair costs: $2,000-$5,000+\n\nPOSSIBLE CAUSES:\n• Critically low oil level\n• Oil pump failure\n• Severe oil leak\n• Engine bearing damage"
        elif oil_pressure < 20:
            return f"⚠️ WARNING: Oil pressure is {oil_pressure:.0f} PSI - Below Normal\n\nNORMAL RANGE: 25-60 PSI\n\nURGENT ACTIONS:\n• Check oil level immediately\n• Do not drive aggressively\n• Schedule immediate inspection\n• Avoid high RPMs\n\nThis could indicate:\n• Low oil level\n• Worn oil pump\n• Oil leak\n• Wrong oil viscosity\n• Engine wear\n\nRecommended: Professional diagnosis within 24-48 hours"
        elif oil_pressure < 25:
            return f"Your oil pressure is {oil_pressure:.0f} PSI, slightly below optimal range (25-60 PSI).\n\nRECOMMENDATIONS:\n• Check oil level\n• Verify using correct oil grade\n• Schedule oil system inspection\n• Monitor pressure closely\n\nThis may be normal at idle, but should increase with RPM."
        else:
            return f"✅ Oil pressure is healthy at {oil_pressure:.0f} PSI. Normal range is 25-60 PSI (varies with engine speed).\n\nOIL MAINTENANCE TIPS:\n• Change oil every 5,000 km or 6 months\n• Use manufacturer-recommended oil grade\n• Check oil level monthly\n• Look for leaks during oil changes"
    
    def _respond_brake_query(self, sensor_data: Dict) -> str:
        """Respond to brake-related query"""
        if not sensor_data:
            return "Unable to access brake system data."
        
        brake_fluid = sensor_data.get('brake_fluid_level', 0)
        
        if brake_fluid < 60:
            return f"🚨 CRITICAL: Brake fluid level is {brake_fluid:.0f}% - Safety Risk!\n\nNORMAL LEVEL: 70-100%\n\nIMMEDIATE DANGER:\n• Brake failure risk\n• Extended stopping distances\n• Complete loss of brakes possible\n\nDO NOT DRIVE THIS VEHICLE\n\nACTIONS REQUIRED:\n• Have vehicle towed to service center\n• Brake system inspection mandatory\n• Check for fluid leaks\n• Brake line inspection needed\n\nPOSSIBLE CAUSES:\n• Brake fluid leak\n• Worn brake pads (fluid drops as pads wear)\n• Master cylinder failure\n• Brake line damage\n\nEstimated repair: $200-$1,000"
        elif brake_fluid < 70:
            return f"⚠️ WARNING: Brake fluid level is {brake_fluid:.0f}% - Below Normal\n\nNORMAL LEVEL: 70-100%\n\nRECOMMENDED ACTIONS:\n• Brake system inspection within 3 days\n• Check brake pad thickness\n• Inspect for visible leaks\n• Top up brake fluid if needed\n• Test brake performance carefully\n\nSYMPTOMS TO MONITOR:\n• Soft or spongy brake pedal\n• Longer stopping distances\n• Brake warning light\n• Grinding or squealing noises\n\nDO NOT IGNORE: Low brake fluid is always serious"
        else:
            return f"✅ Brake fluid level is good at {brake_fluid:.0f}%. Normal range is 70-100%.\n\nBRAKE MAINTENANCE TIPS:\n• Inspect brake pads every 15,000 km\n• Flush brake fluid every 2 years\n• Address any brake noises immediately\n• Don't ignore brake warning lights\n\nSIGNS OF BRAKE ISSUES:\n• Squealing or grinding sounds\n• Vibration when braking\n• Soft or spongy pedal\n• Vehicle pulls to one side\n• Longer stopping distances"
    
    def _respond_maintenance_query(self, sensor_data: Dict) -> str:
        """Respond to maintenance-related query"""
        return """📋 MAINTENANCE SCHEDULE & SERVICES

ROUTINE MAINTENANCE:
🔧 Oil Change: Every 5,000 km or 6 months
   Cost: $50-$100 | Duration: 30-45 minutes

🔧 Tire Rotation: Every 10,000 km or 6 months
   Cost: $40-$80 | Duration: 30 minutes

🔧 Brake Inspection: Every 15,000 km or annually
   Cost: $50-$100 (inspection) | Duration: 45 minutes

🔧 Battery Test: Annually
   Cost: Free-$50 | Duration: 15 minutes

🔧 Air Filter: Every 20,000 km
   Cost: $30-$70 | Duration: 15 minutes

🔧 Coolant Flush: Every 50,000 km or 2 years
   Cost: $100-$150 | Duration: 1 hour

BASED ON YOUR CURRENT VEHICLE DATA:
• Next oil change: Due in ~2,500 km
• Tire rotation: Recommended within 3 months
• Overall vehicle health: Check dashboard for status

Would you like me to schedule an appointment for any of these services? I can find available time slots at certified service centers near you."""
    
    def _respond_cost_query(self) -> str:
        """Respond to cost-related query"""
        return """💰 TYPICAL REPAIR & MAINTENANCE COSTS

ROUTINE MAINTENANCE:
• Oil Change: $50-$100
• Tire Rotation: $40-$80
• Brake Pad Replacement: $300-$800 (all wheels)
• Battery Replacement: $150-$300
• Air Filter: $30-$70
• Coolant Flush: $100-$150

COMMON REPAIRS:
• Alternator: $400-$800
• Starter: $300-$600
• Brake Rotors: $400-$900 (pair)
• Water Pump: $300-$750
• Thermostat: $150-$400
• Fuel Pump: $400-$1,000

MAJOR REPAIRS:
• Transmission: $1,000-$3,500
• Engine Work: $1,500-$5,000+
• AC System: $500-$2,000

FACTORS AFFECTING COST:
✓ Vehicle make and model
✓ Parts quality (OEM vs aftermarket)
✓ Labor rates in your area
✓ Extent of damage
✓ Warranty coverage

For a specific estimate based on your vehicle's diagnosed issues, I can connect you with our scheduling agent who will provide detailed quotes from certified service centers."""
    
    def _respond_health_query(self, sensor_data: Dict) -> str:
        """Respond to overall health query"""
        if not sensor_data:
            return "Unable to access vehicle health data."
        
        # Calculate component healths
        engine_health = self._calculate_health_score('engine', sensor_data)
        battery_health = self._calculate_health_score('battery', sensor_data)
        tire_health = self._calculate_health_score('tires', sensor_data)
        brake_health = self._calculate_health_score('brakes', sensor_data)
        
        overall = (engine_health + battery_health + tire_health + brake_health) / 4
        
        status_emoji = "✅" if overall >= 80 else "⚠️" if overall >= 60 else "🚨"
        status_text = "Excellent" if overall >= 90 else "Good" if overall >= 80 else "Fair" if overall >= 60 else "Poor"
        
        response = f"{status_emoji} VEHICLE HEALTH REPORT\n\n"
        response += f"Overall Health Score: {overall:.0f}/100 - {status_text}\n\n"
        response += "COMPONENT BREAKDOWN:\n"
        response += f"🔧 Engine System: {engine_health:.0f}/100\n"
        response += f"🔋 Battery/Electrical: {battery_health:.0f}/100\n"
        response += f"🚗 Tires: {tire_health:.0f}/100\n"
        response += f"🛑 Brakes: {brake_health:.0f}/100\n\n"
        
        if overall >= 80:
            response += "Your vehicle is in good condition! Continue with regular maintenance schedule."
        elif overall >= 60:
            response += "Some attention needed. Review component scores and address issues with lower scores."
        else:
            response += "⚠️ Multiple systems need attention. Schedule a comprehensive inspection soon."
        
        return response
    
    def _respond_help_query(self) -> str:
        """Respond to help query"""
        return """🤖 TorqCare AI Assistant - What I Can Help You With:

📊 REAL-TIME DIAGNOSTICS:
• Current engine temperature
• Battery voltage status
• Tire pressure readings
• Oil pressure levels
• Brake system status
• Overall vehicle health

🔧 MAINTENANCE INFORMATION:
• Service schedule recommendations
• Maintenance cost estimates
• Service history
• Upcoming service reminders

📅 APPOINTMENT SCHEDULING:
• Book service appointments
• Find nearby service centers
• Get available time slots
• Urgent repair scheduling

💡 VEHICLE ADVICE:
• Troubleshooting guidance
• Warning light explanations
• Preventive maintenance tips
• Cost estimates for repairs

📈 REPORTS & INSIGHTS:
• Vehicle health reports
• Performance trends
• Maintenance history
• Predictive failure warnings

EXAMPLE QUESTIONS:
• "What's my current engine temperature?"
• "Is my battery healthy?"
• "When is my next service due?"
• "Schedule a brake inspection"
• "What does low oil pressure mean?"
• "Show me my vehicle health report"

How can I assist you today?"""
    
    def _calculate_health_score(self, component: str, sensor_data: Dict) -> float:
        """Calculate health score for component"""
        if component == 'engine':
            temp = sensor_data.get('engine_temp', 75)
            oil = sensor_data.get('oil_pressure', 35)
            temp_score = max(0, 100 - abs(temp - 85) * 2)
            oil_score = max(0, min(100, (oil / 35) * 100))
            return (temp_score + oil_score) / 2
        elif component == 'battery':
            voltage = sensor_data.get('battery_voltage', 12.6)
            return max(0, min(100, ((voltage - 11) / 3) * 100))
        elif component == 'tires':
            pressures = [
                sensor_data.get('tire_pressure_fl', 32),
                sensor_data.get('tire_pressure_fr', 32),
                sensor_data.get('tire_pressure_rl', 32),
                sensor_data.get('tire_pressure_rr', 32)
            ]
            avg = sum(pressures) / len(pressures)
            return max(0, 100 - abs(avg - 32) * 5)
        elif component == 'brakes':
            fluid = sensor_data.get('brake_fluid_level', 85)
            return max(0, min(100, fluid))
        return 100.0
    
    async def _acknowledge_feedback(self, feedback: Dict) -> Dict:
        """Acknowledge customer feedback"""
        rating = feedback.get('rating', 3)
        feedback_type = feedback.get('feedback_type', 'general')
        
        if rating >= 4:
            message = "Thank you for your positive feedback! We're delighted that you had a great experience with our service. Your input helps us maintain our high standards and has been shared with our team and service partners."
        elif rating == 3:
            message = "Thank you for your feedback. We appreciate your honest input and are always looking to improve. Your comments have been forwarded to our service team and quality assurance department for review."
        else:
            message = "We're sorry to hear about your less-than-satisfactory experience. Your feedback is very important to us. A member of our customer care team will reach out to you within 24 hours to address your concerns. We've immediately shared your feedback with our service partners and quality team."
        
        await self.log_activity('acknowledge_feedback', feedback, {})
        
        return {
            'message': message,
            'tracking_id': feedback.get('feedback_id', 'pending'),
            'next_steps': 'Follow-up email within 24-48 hours' if rating < 4 else 'Thank you for your continued trust',
            'escalated': rating <= 2
        }
    
    async def _send_alert(self, vehicle_id: str, diagnosis: Dict, appointment: Dict = None) -> Dict:
        """Send alert to customer about critical issue"""
        severity = diagnosis.get('severity', 'normal')
        issues = diagnosis.get('issues', [])
        
        if severity == 'critical':
            alert_message = f"🚨 CRITICAL VEHICLE ALERT\n\n"
            alert_message += f"We've detected critical issues with your vehicle that require immediate attention:\n\n"
            
            for issue in issues:
                if issue.get('severity') == 'critical':
                    alert_message += f"• {issue['issue']}\n"
            
            alert_message += f"\n⚠️ DO NOT IGNORE THIS ALERT\n\n"
            
            if appointment:
                alert_message += f"We've automatically scheduled an urgent appointment for you:\n"
                alert_message += f"Workshop: {appointment.get('workshop', 'TBD')}\n"
                alert_message += f"Time: {appointment.get('scheduled_time', 'TBD')}\n\n"
                alert_message += f"Please confirm or reschedule at your earliest convenience."
            else:
                alert_message += f"Please schedule service immediately through the app or call our 24/7 hotline."
        else:
            alert_message = f"Vehicle Alert: {severity.upper()} priority\n"
            alert_message += f"Issues detected: {len(issues)}\n"
            alert_message += f"Please review your dashboard for details."
        
        await self.log_activity('send_alert', diagnosis, {'alert_sent': True})
        
        return {
            'alert_sent': True,
            'message': alert_message,
            'channel': 'app_notification',
            'timestamp': datetime.now().isoformat()
        }
    
    def _build_knowledge_base(self) -> Dict:
        """Build knowledge base for common queries"""
        return {
            'maintenance_schedule': {
                'oil_change': {'interval_km': 5000, 'interval_months': 6, 'cost_range': (50, 100)},
                'tire_rotation': {'interval_km': 10000, 'interval_months': 6, 'cost_range': (40, 80)},
                'brake_inspection': {'interval_km': 15000, 'interval_months': 12, 'cost_range': (50, 100)},
                'battery_test': {'interval_km': None, 'interval_months': 12, 'cost_range': (0, 50)},
                'air_filter': {'interval_km': 20000, 'interval_months': 12, 'cost_range': (30, 70)},
                'coolant_flush': {'interval_km': 50000, 'interval_months': 24, 'cost_range': (100, 150)}
            },
            'warning_signs': {
                'engine': ['unusual noises', 'loss of power', 'check engine light', 'rough idling', 'excessive smoke'],
                'brakes': ['squealing', 'grinding', 'soft pedal', 'vibration', 'pulling'],
                'transmission': ['slipping', 'delayed shifting', 'burning smell', 'unusual noises'],
                'electrical': ['dim lights', 'slow start', 'battery warning', 'electrical failures']
            },
            'emergency_numbers': {
                'roadside_assistance': '1-800-TORQCARE',
                'customer_support': '1-800-123-4567',
                'emergency_towing': '1-800-TOW-HELP'
            }
        }


# ============================================
# AGENT 4: SCHEDULING AGENT  
# ============================================

class SchedulingAgent(BaseAgent):
    """
    Agent 4: Automatic appointment scheduling
    Finds optimal time slots and coordinates with workshops
    """
    
    def __init__(self):
        super().__init__("Scheduling Agent")
        self.workshops = self._load_workshops()
        self.booking_history = []
    
    async def process(self, data: Dict) -> Dict:
        """Process scheduling request"""
        action = data.get('action')
        
        if action == 'get_available_slots':
            return await self._get_available_slots(
                data.get('urgency'),
                data.get('issue_type'),
                data.get('preferred_date')
            )
        elif action == 'auto_schedule':
            return await self._auto_schedule(
                data['vehicle_id'],
                data['diagnosis'],
                data['urgency']
            )
        elif action == 'schedule':
            return await self._schedule_appointment(
                data['vehicle_id'],
                data['issue'],
                data['urgency']
            )
        elif action == 'notify_workshop':
            return await self._notify_workshop(
                data['appointment_id'],
                data['slot']
            )
        
        return {}
    
    async def _get_available_slots(self, urgency: str, issue_type: str, preferred_date: Optional[str]) -> List[Dict]:
        """Get available appointment slots based on urgency"""
        slots = []
        start_date = datetime.now()
        
        if preferred_date:
            try:
                start_date = datetime.fromisoformat(preferred_date)
            except:
                pass
        
        # Determine search parameters based on urgency
        if urgency == 'critical':
            days_ahead = 2
            time_slots = ['09:00', '11:00', '14:00']  # Emergency slots
            min_availability = 0.3  # Lower threshold for critical
        elif urgency == 'urgent':
            days_ahead = 5
            time_slots = ['09:00', '11:00', '14:00', '16:00']
            min_availability = 0.5
        else:  # routine
            days_ahead = 14
            time_slots = ['09:00', '11:00', '14:00', '16:00']
            min_availability = 0.7
        
        # Generate slots for each day
        for day in range(days_ahead):
            date = start_date + timedelta(days=day)
            
            # Skip Sundays for routine maintenance
            if urgency == 'routine' and date.weekday() == 6:
                continue
            
            for time_slot in time_slots:
                # Rank workshops by suitability
                suitable_workshops = self._rank_workshops(issue_type, urgency)
                
                for workshop in suitable_workshops[:3]:  # Top 3 workshops
                    # Simulate availability (in production, check actual calendar)
                    availability_score = self._check_availability(workshop, date, time_slot)
                    
                    if availability_score >= min_availability:
                        estimated_duration = self._estimate_duration(issue_type)
                        
                        slots.append({
                            'workshop_id': workshop['id'],
                            'workshop_name': workshop['name'],
                            'date': date.strftime('%Y-%m-%d'),
                            'time': time_slot,
                            'datetime': f"{date.strftime('%Y-%m-%d')} {time_slot}",
                            'location': workshop['location'],
                            'address': workshop.get('address', 'See details'),
                            'distance_km': workshop['distance'],
                            'rating': workshop['rating'],
                            'estimated_duration': estimated_duration,
                            'estimated_cost_range': self._estimate_cost(issue_type),
                            'available': True,
                            'availability_score': availability_score,
                            'specializations': workshop.get('specializations', [])
                        })
        
        # Sort by date, then by workshop rating
        slots.sort(key=lambda x: (x['datetime'], -x['rating']))
        
        await self.log_activity('get_slots', {'urgency': urgency}, {'slot_count': len(slots)})
        
        return slots[:20]  # Return top 20 slots
    
    async def _auto_schedule(self, vehicle_id: str, diagnosis: Dict, urgency: str) -> Dict:
        """Automatically schedule appointment for critical issues"""
        try:
            # Get issue type from diagnosis
            issues = diagnosis.get('issues', [])
            issue_type = issues[0].get('issue', 'diagnostic') if issues else 'diagnostic'
            
            # Get first available slots
            slots = await self._get_available_slots(urgency, issue_type, None)
            
            if not slots:
                return {
                    'error': 'No available slots found',
                    'message': 'All service centers are fully booked. Please call our 24/7 hotline.'
                }
            
            # Select best slot (earliest with highest rated workshop)
            best_slot = max(slots[:5], key=lambda x: x['rating'])
            
            appointment = {
                'vehicle_id': vehicle_id,
                'workshop_id': best_slot['workshop_id'],
                'workshop': best_slot['workshop_name'],
                'scheduled_time': best_slot['datetime'],
                'location': best_slot['location'],
                'urgency': urgency,
                'issue_type': issue_type,
                'issues': [issue.get('issue') for issue in issues],
                'estimated_duration': best_slot['estimated_duration'],
                'estimated_cost_range': best_slot['estimated_cost_range'],
                'status': 'pending_confirmation',
                'auto_scheduled': True,
                'created_at': datetime.now().isoformat()
            }
            
            self.booking_history.append(appointment)
            
            await self.log_activity('auto_schedule', diagnosis, appointment)
            
            logger.info(f"✅ Auto-scheduled appointment for {vehicle_id} at {best_slot['workshop_name']}")
            
            return appointment
            
        except Exception as e:
            logger.error(f"❌ Auto-scheduling failed: {e}")
            return {'error': str(e)}
    
    async def _schedule_appointment(self, vehicle_id: str, issue: Dict, urgency: str) -> Dict:
        """Manual appointment scheduling"""
        issue_type = issue.get('type', 'general_service')
        slots = await self._get_available_slots(urgency, issue_type, None)
        
        return {
            'vehicle_id': vehicle_id,
            'available_slots': slots,
            'urgency': urgency,
            'issue': issue,
            'message': f'Found {len(slots)} available appointments'
        }
    
    async def _notify_workshop(self, appointment_id: int, slot: Dict) -> Dict:
        """Notify workshop of confirmed appointment"""
        notification = {
            'appointment_id': appointment_id,
            'workshop_id': slot['workshop_id'],
            'workshop_name': slot['workshop_name'],
            'scheduled_time': slot['datetime'],
            'notification_sent': True,
            'notification_method': 'email_and_sms',
            'timestamp': datetime.now().isoformat()
        }
        
        await self.log_activity('notify_workshop', slot, notification)
        
        logger.info(f"📧 Workshop notified: {slot['workshop_name']} for appointment {appointment_id}")
        
        return notification
    
    def _rank_workshops(self, issue_type: str, urgency: str) -> List[Dict]:
        """Rank workshops by suitability for the issue"""
        ranked = []
        
        for workshop in self.workshops:
            score = workshop['rating'] * 10  # Base score from rating
            
            # Bonus for specialization match
            specializations = workshop.get('specializations', [])
            if issue_type.lower() in [s.lower() for s in specializations]:
                score += 20
            
            # Bonus for proximity (inverse of distance)
            score += max(0, 10 - workshop['distance'])
            
            # Urgency factor
            if urgency == 'critical':
                # Prefer closer workshops for critical issues
                score += max(0, 15 - workshop['distance'] * 2)
            
            ranked.append({**workshop, 'suitability_score': score})
        
        return sorted(ranked, key=lambda x: x['suitability_score'], reverse=True)
    
    def _check_availability(self, workshop: Dict, date: datetime, time_slot: str) -> float:
        """Check workshop availability (0-1 score)"""
        # Simulate availability based on various factors
        base_availability = 0.7
        
        # Reduce availability for weekdays 9-11am (busy time)
        if date.weekday() < 5 and time_slot in ['09:00', '11:00']:
            base_availability -= 0.2
        
        # Better availability on less busy days
        if date.weekday() in [1, 3]:  # Tuesday, Thursday
            base_availability += 0.1
        
        # Random factor
        import random
        return min(1.0, base_availability + random.uniform(-0.1, 0.2))
    
    def _estimate_duration(self, issue_type: str) -> str:
        """Estimate service duration"""
        durations = {
            'diagnostic': '1-2 hours',
            'oil_change': '30-45 minutes',
            'brake_service': '2-3 hours',
            'battery_replacement': '30-45 minutes',
            'tire_service': '1 hour',
            'engine_work': '3-5 hours',
            'transmission_service': '3-4 hours',
            'electrical_diagnosis': '1-2 hours',
            'cooling_system': '2-3 hours',
            'general_service': '1-2 hours'
        }
        return durations.get(issue_type.lower().replace(' ', '_'), '1-2 hours')
    
    def _estimate_cost(self, issue_type: str) -> tuple:
        """Estimate service cost range"""
        costs = {
            'diagnostic': (80, 150),
            'oil_change': (50, 100),
            'brake_service': (300, 800),
            'battery_replacement': (150, 300),
            'tire_service': (200, 600),
            'engine_work': (500, 3000),
            'transmission_service': (1000, 3500),
            'electrical_diagnosis': (100, 500),
            'cooling_system': (200, 800),
            'general_service': (100, 300)
        }
        return costs.get(issue_type.lower().replace(' ', '_'), (100, 500))
    
    def _load_workshops(self) -> List[Dict]:
        """Load workshop data"""
        return [
            {
                'id': 1,
                'name': 'AutoCare Center Downtown',
                'location': 'Downtown',
                'address': '123 Main Street, San Francisco, CA 94102',
                'rating': 4.8,
                'distance': 2.5,
                'specializations': ['general', 'diagnostics', 'electrical', 'brakes'],
                'certifications': ['ASE Certified', 'Tesla Certified'],
                'hours': 'Mon-Sat 8am-6pm'
            },
            {
                'id': 2,
                'name': 'Premium Motors Westside',
                'location': 'Westside',
                'address': '456 Oak Avenue, San Francisco, CA 94109',
                'rating': 4.6,
                'distance': 5.1,
                'specializations': ['luxury', 'engine', 'transmission', 'diagnostics'],
                'certifications': ['BMW Certified', 'Mercedes Certified', 'ASE Certified'],
                'hours': 'Mon-Fri 8am-7pm, Sat 9am-5pm'
            },
            {
                'id': 3,
                'name': 'QuickFix Garage Eastside',
                'location': 'Eastside',
                'address': '789 Pine Road, San Francisco, CA 94110',
                'rating': 4.9,
                'distance': 3.8,
                'specializations': ['quick_service', 'brakes', 'tires', 'oil_change'],
                'certifications': ['ASE Certified', 'AAA Approved'],
                'hours': 'Mon-Sat 7am-7pm, Sun 9am-4pm'
            },
            {
                'id': 4,
                'name': 'TechAuto Service Center',
                'location': 'Midtown',
                'address': '321 Tech Boulevard, San Francisco, CA 94107',
                'rating': 4.7,
                'distance': 4.2,
                'specializations': ['diagnostics', 'electrical', 'hybrid', 'engine'],
                'certifications': ['ASE Master Certified', 'Hybrid Specialist'],
                'hours': 'Mon-Fri 8am-6pm, Sat 9am-3pm'
            },
            {
                'id': 5,
                'name': 'Family Auto Repair',
                'location': 'South District',
                'address': '555 Family Lane, San Francisco, CA 94112',
                'rating': 4.5,
                'distance': 6.3,
                'specializations': ['general', 'brakes', 'engine', 'transmission'],
                'certifications': ['ASE Certified', '25+ Years Experience'],
                'hours': 'Mon-Sat 8am-6pm'
            }
        ]


# ============================================
# AGENT 5: QUALITY INSIGHTS AGENT
# ============================================

class QualityInsightsAgent(BaseAgent):
    """
    Agent 5: Manufacturing quality insights
    Aggregates failure data and notifies manufacturers
    """
    
    def __init__(self):
        super().__init__("Quality Insights Agent")
        self.failure_database = {}
        self.feedback_database = []
        self.manufacturer_reports = []
    
    async def process(self, data: Dict) -> Dict:
        """Process quality insights request"""
        action = data.get('action')
        
        if action == 'log_anomaly':
            return await self._log_anomaly(data['vehicle_id'], data['anomalies'])
        elif action == 'ingest_feedback':
            return await self._ingest_feedback(data['feedback'])
        elif action == 'generate_insights':
            return await self._generate_insights(data.get('vehicle_model'))
        elif action == 'report_potential_failure':
            return await self.report_potential_failure(
                data['vehicle_id'],
                data['predictions']
            )
        
        return {}
    
    async def _log_anomaly(self, vehicle_id: str, anomalies: List) -> Dict:
        """Log anomalies for trend analysis"""
        logged_count = 0
        
        for anomaly in anomalies:
            failure_type = anomaly['type']
            severity = anomaly.get('severity', 'warning')
            
            # Initialize failure type if not exists
            if failure_type not in self.failure_database:
                self.failure_database[failure_type] = {
                    'count': 0,
                    'vehicles_affected': set(),
                    'first_seen': datetime.now(),
                    'last_seen': datetime.now(),
                    'severity_distribution': {'critical': 0, 'warning': 0},
                    'total_incidents': 0
                }
            
            # Update statistics
            self.failure_database[failure_type]['count'] += 1
            self.failure_database[failure_type]['vehicles_affected'].add(vehicle_id)
            self.failure_database[failure_type]['last_seen'] = datetime.now()
            self.failure_database[failure_type]['severity_distribution'][severity] += 1
            self.failure_database[failure_type]['total_incidents'] += 1
            logged_count += 1
            
            # Check if manufacturer notification is needed
            if self._should_notify_manufacturer(failure_type):
                await self._notify_manufacturer(failure_type)
        
        await self.log_activity('log_anomaly', {'vehicle_id': vehicle_id}, {'logged': logged_count})
        
        return {'status': 'logged', 'anomalies_logged': logged_count}
    
    async def _ingest_feedback(self, feedback: Dict) -> Dict:
        """Ingest and analyze customer feedback"""
        self.feedback_database.append({
            **feedback,
            'ingested_at': datetime.now().isoformat()
        })
        
        rating = feedback.get('rating', 0)
        feedback_type = feedback.get('feedback_type')
        vehicle_id = feedback.get('vehicle_id')
        issue_recurring = feedback.get('issue_recurring', False)
        
        # Analyze for quality issues
        action_required = False
        manufacturer_alert = False
        
        # Low rating indicates potential quality issue
        if rating <= 2:
            action_required = True
            manufacturer_alert = True
        
        # Recurring issues are critical quality signals
        if issue_recurring:
            manufacturer_alert = True
            await self._log_recurring_issue(vehicle_id, feedback)
        
        # Check feedback comment for quality keywords
        comment = feedback.get('comment', '').lower()
        quality_keywords = ['defect', 'broken', 'failed again', 'poor quality', 'manufacturing', 'design flaw']
        if any(keyword in comment for keyword in quality_keywords):
            manufacturer_alert = True
        
        result = {
            'action_required': action_required,
            'manufacturer_notified': manufacturer_alert,
            'issue_category': feedback_type,
            'quality_score': rating
        }
        
        if manufacturer_alert:
            await self._create_quality_report(feedback)
        
        await self.log_activity('ingest_feedback', feedback, result)
        
        return result
    
    async def _generate_insights(self, vehicle_model: Optional[str] = None) -> Dict:
        """Generate comprehensive quality insights report"""
        insights = {
            'report_generated_at': datetime.now().isoformat(),
            'total_failures_tracked': sum(
                data['count'] for data in self.failure_database.values()
            ),
            'unique_vehicles_affected': len(set(
                vehicle for data in self.failure_database.values()
                for vehicle in data['vehicles_affected']
            )),
            'top_failure_types': [],
            'critical_patterns': [],
            'feedback_summary': {},
            'manufacturer_alerts': len(self.manufacturer_reports),
            'recommendations': []
        }
        
        # Analyze top failure types
        failure_list = [
            {
                'failure_type': k,
                'occurrence_count': v['count'],
                'vehicles_affected': len(v['vehicles_affected']),
                'criticality_rate': v['severity_distribution']['critical'] / max(v['total_incidents'], 1),
                'first_seen': v['first_seen'].isoformat(),
                'last_seen': v['last_seen'].isoformat()
            }
            for k, v in self.failure_database.items()
        ]
        insights['top_failure_types'] = sorted(
            failure_list,
            key=lambda x: x['occurrence_count'],
            reverse=True
        )[:10]
        
        # Identify critical patterns
        for failure_type, data in self.failure_database.items():
            if len(data['vehicles_affected']) >= 5:  # Affecting 5+ vehicles
                criticality = data['severity_distribution']['critical'] / max(data['total_incidents'], 1)
                if criticality > 0.5:  # More than 50% critical
                    insights['critical_patterns'].append({
                        'failure_type': failure_type,
                        'vehicles_affected': len(data['vehicles_affected']),
                        'criticality_rate': round(criticality * 100, 1),
                        'recommendation': 'Immediate manufacturer investigation required'
                    })
        
        # Feedback summary
        if self.feedback_database:
            total_feedback = len(self.feedback_database)
            avg_rating = sum(f.get('rating', 0) for f in self.feedback_database) / total_feedback
            negative_feedback = len([f for f in self.feedback_database if f.get('rating', 0) <= 2])
            recurring_issues = len([f for f in self.feedback_database if f.get('issue_recurring', False)])
            
            insights['feedback_summary'] = {
                'total_feedback_count': total_feedback,
                'average_rating': round(avg_rating, 2),
                'negative_feedback_count': negative_feedback,
                'negative_feedback_rate': round((negative_feedback / total_feedback) * 100, 1),
                'recurring_issues_count': recurring_issues,
                'recurring_issues_rate': round((recurring_issues / total_feedback) * 100, 1)
            }
        
        # Generate recommendations
        insights['recommendations'] = self._generate_recommendations(insights)
        
        await self.log_activity('generate_insights', {}, insights)
        
        return insights
    
    async def report_potential_failure(self, vehicle_id: str, predictions: List[Dict]) -> Dict:
        """Report high-confidence failure predictions to manufacturer"""
        critical_predictions = [
            p for p in predictions 
            if p.get('probability', 0) > 0.7
        ]
        
        if not critical_predictions:
            return {'status': 'no_critical_predictions'}
        
        report = {
            'vehicle_id': vehicle_id,
            'predictions': critical_predictions,
            'prediction_count': len(critical_predictions),
            'highest_probability': max(p.get('probability', 0) for p in critical_predictions),
            'manufacturer_notified': True,
            'report_created_at': datetime.now().isoformat(),
            'action_required': True
        }
        
        self.manufacturer_reports.append(report)
        
        await self.log_activity('report_failure', report, {})
        
        logger.info(f"📊 Quality report created for {vehicle_id} - {len(critical_predictions)} critical predictions")
        
        return report
    
    def _should_notify_manufacturer(self, failure_type: str) -> bool:
        """Determine if manufacturer should be notified"""
        if failure_type not in self.failure_database:
            return False
        
        data = self.failure_database[failure_type]
        
        # Notify if affecting 10+ vehicles
        if len(data['vehicles_affected']) >= 10:
            return True
        
        # Notify if high criticality rate
        criticality_rate = data['severity_distribution']['critical'] / max(data['total_incidents'], 1)
        if criticality_rate > 0.6 and data['total_incidents'] >= 5:
            return True
        
        return False
    
    async def _notify_manufacturer(self, failure_type: str):
        """Send notification to manufacturer"""
        logger.info(f"📧 Manufacturer notified about: {failure_type}")
        # In production: Send actual email/API call to manufacturer
    
    async def _log_recurring_issue(self, vehicle_id: str, feedback: Dict):
        """Log recurring issues for special tracking"""
        logger.warning(f"⚠️ Recurring issue reported for vehicle {vehicle_id}")
    
    async def _create_quality_report(self, feedback: Dict):
        """Create quality report from feedback"""
        logger.info(f"📋 Quality report created from feedback ID: {feedback.get('feedback_id')}")
    
    def _generate_recommendations(self, insights: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Check failure patterns
        if insights['critical_patterns']:
            recommendations.append(
                f"URGENT: {len(insights['critical_patterns'])} critical failure patterns detected. Immediate manufacturer investigation required."
            )
        
        # Check feedback quality
        feedback_summary = insights.get('feedback_summary', {})
        if feedback_summary:
            negative_rate = feedback_summary.get('negative_feedback_rate', 0)
            if negative_rate > 30:
                recommendations.append(
                    f"Service quality concern: {negative_rate}% negative feedback rate. Review service partner performance."
                )
            
            recurring_rate = feedback_summary.get('recurring_issues_rate', 0)
            if recurring_rate > 15:
                recommendations.append(
                    f"Quality alert: {recurring_rate}% of issues are recurring. Root cause analysis needed."
                )
        
        # Check top failures
        top_failures = insights.get('top_failure_types', [])
        if top_failures and top_failures[0]['occurrence_count'] > 20:
            recommendations.append(
                f"Most common failure: {top_failures[0]['failure_type']} ({top_failures[0]['occurrence_count']} occurrences). "
                f"Consider preventive maintenance program or design review."
            )
        
        return recommendations


# ============================================
# AGENT 6: FEEDBACK AGENT
# ============================================

class FeedbackAgent(BaseAgent):
    """
    Agent 6: Feedback collection and distribution
    Manages feedback from customers and shares with stakeholders
    """
    
    def __init__(self):
        super().__init__("Feedback Agent")
        self.processed_feedback = []
    
    async def process(self, data: Dict) -> Dict:
        """Process feedback"""
        action = data.get('action')
        
        if action == 'process_feedback':
            return await self._process_feedback(data['data'])
        
        return {}
    
    async def _process_feedback(self, feedback_data: Dict) -> Dict:
        """Process and categorize feedback"""
        # Categorize feedback
        category = self._categorize_feedback(feedback_data)
        sentiment = self._analyze_sentiment(feedback_data.get('rating', 3))
        priority = self._determine_priority(feedback_data)
        
        # Determine distribution strategy
        distribution = {
            'to_manufacturer': self._should_send_to_manufacturer(feedback_data, sentiment),
            'to_workshop': feedback_data.get('feedback_type') == 'repair',
            'to_quality_team': sentiment == 'negative' or feedback_data.get('issue_recurring', False),
            'requires_followup': sentiment == 'negative' or priority == 'high',
            'escalate_to_management': priority == 'critical'
        }
        
        # Process tags and keywords
        tags = self._extract_tags(feedback_data)
        
        result = {
            'feedback_id': feedback_data.get('feedback_id', f'FB_{len(self.processed_feedback)+1}'),
            'category': category,
            'sentiment': sentiment,
            'priority': priority,
            'distribution': distribution,
            'tags': tags,
            'processed_at': datetime.now().isoformat(),
            'actionable_insights': self._extract_insights(feedback_data)
        }
        
        # Execute distribution
        if distribution['to_manufacturer']:
            await self._share_with_manufacturer(feedback_data, result)
        
        if distribution['to_workshop']:
            await self._share_with_workshop(feedback_data, result)
        
        if distribution['to_quality_team']:
            await self._share_with_quality_team(feedback_data, result)
        
        self.processed_feedback.append(result)
        
        await self.log_activity('process_feedback', feedback_data, result)
        
        return result
    
    def _categorize_feedback(self, feedback: Dict) -> str:
        """Categorize feedback into types"""
        feedback_type = feedback.get('feedback_type', 'general')
        comment = feedback.get('comment', '').lower()
        
        # Analyze comment for specific categories
        if any(word in comment for word in ['quality', 'workmanship', 'poor', 'shoddy', 'excellent work']):
            return 'service_quality'
        elif any(word in comment for word in ['cost', 'expensive', 'price', 'overpriced', 'reasonable', 'cheap']):
            return 'pricing'
        elif any(word in comment for word in ['time', 'wait', 'delay', 'slow', 'quick', 'fast']):
            return 'timeliness'
        elif any(word in comment for word in ['issue', 'problem', 'recurring', 'again', 'still', 'fixed']):
            return 'technical_issue'
        elif any(word in comment for word in ['staff', 'mechanic', 'service', 'friendly', 'rude', 'helpful']):
            return 'customer_service'
        elif any(word in comment for word in ['communication', 'explain', 'told', 'informed', 'understood']):
            return 'communication'
        
        return feedback_type
    
    def _analyze_sentiment(self, rating: int) -> str:
        """Analyze sentiment from rating"""
        if rating >= 4:
            return 'positive'
        elif rating == 3:
            return 'neutral'
        else:
            return 'negative'
    
    def _determine_priority(self, feedback: Dict) -> str:
        """Determine priority level"""
        rating = feedback.get('rating', 3)
        recurring = feedback.get('issue_recurring', False)
        unresolved = not feedback.get('issue_fully_resolved', True)
        
        # Critical priority
        if rating == 1 and (recurring or unresolved):
            return 'critical'
        
        # High priority
        if rating <= 2 or (recurring and rating <= 3):
            return 'high'
        
        # Medium priority
        if rating == 3 or unresolved:
            return 'medium'
        
        # Low priority
        return 'low'
    
    def _should_send_to_manufacturer(self, feedback: Dict, sentiment: str) -> bool:
        """Determine if feedback should be sent to manufacturer"""
        # Always send negative feedback
        if sentiment == 'negative':
            return True
        
        # Send if recurring issue
        if feedback.get('issue_recurring', False):
            return True
        
        # Send if issue not fully resolved
        if not feedback.get('issue_fully_resolved', True):
            return True
        
        # Send if rating is very low
        if feedback.get('rating', 3) <= 2:
            return True
        
        return False
    
    def _extract_tags(self, feedback: Dict) -> List[str]:
        """Extract relevant tags from feedback"""
        tags = []
        comment = feedback.get('comment', '').lower()
        
        tag_keywords = {
            'quality_issue': ['poor quality', 'defect', 'broken', 'failed'],
            'cost_concern': ['expensive', 'overpriced', 'too much', 'cost'],
            'time_issue': ['delay', 'slow', 'waiting', 'late'],
            'recurring_problem': ['again', 'recurring', 'still', 'not fixed'],
            'positive_experience': ['excellent', 'great', 'amazing', 'perfect'],
            'communication_issue': ['not informed', 'didnt explain', 'no communication'],
            'warranty_concern': ['warranty', 'covered', 'should be free']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in comment for keyword in keywords):
                tags.append(tag)
        
        # Add feedback type as tag
        tags.append(feedback.get('feedback_type', 'general'))
        
        # Add sentiment as tag
        tags.append(f"sentiment_{self._analyze_sentiment(feedback.get('rating', 3))}")
        
        return list(set(tags))  # Remove duplicates
    
    def _extract_insights(self, feedback: Dict) -> List[str]:
        """Extract actionable insights from feedback"""
        insights = []
        comment = feedback.get('comment', '').lower()
        rating = feedback.get('rating', 3)
        
        if feedback.get('issue_recurring', False):
            insights.append("Recurring issue - root cause analysis needed")
        
        if not feedback.get('issue_fully_resolved', True):
            insights.append("Issue remains unresolved - follow-up service required")
        
        if rating <= 2:
            insights.append("Critical customer satisfaction issue - immediate attention needed")
        
        if 'expensive' in comment or 'overpriced' in comment:
            insights.append("Pricing concern - review service costs")
        
        if 'wait' in comment or 'delay' in comment:
            insights.append("Service time concern - review workshop efficiency")
        
        if feedback.get('additional_issues_found'):
            insights.append("Additional issues discovered during service - transparency concern")
        
        return insights
    
    async def _share_with_manufacturer(self, feedback: Dict, analysis: Dict):
        """Share feedback with manufacturer"""
        logger.info(f"📤 Feedback shared with manufacturer: {feedback.get('feedback_id')}")
        logger.info(f"   Category: {analysis['category']}, Priority: {analysis['priority']}")
        # In production: Send to manufacturer's feedback API/email
    
    async def _share_with_workshop(self, feedback: Dict, analysis: Dict):
        """Share feedback with workshop"""
        logger.info(f"📤 Feedback shared with workshop: {feedback.get('feedback_id')}")
        # In production: Send to workshop management system
    
    async def _share_with_quality_team(self, feedback: Dict, analysis: Dict):
        """Share feedback with quality team"""
        logger.info(f"📤 Feedback escalated to quality team: {feedback.get('feedback_id')}")
        # In production: Create ticket in quality management system


# ============================================
# EXAMPLE USAGE & TESTING
# ============================================

if __name__ == "__main__":
    async def main():
        print("="*70)
        print("🚗 TorqCare Multi-Agent System - Complete Implementation")
        print("="*70)
        
        # Initialize orchestrator
        orchestrator = AgentOrchestrator()
        
        # Create and register all agents
        agents = {
            'data_analysis': DataAnalysisAgent(),
            'diagnosis': DiagnosisAgent(),
            'customer_engagement': CustomerEngagementAgent(),
            'scheduling': SchedulingAgent(),
            'quality_insights': QualityInsightsAgent(),
            'feedback': FeedbackAgent()
        }
        
        for agent_id, agent in agents.items():
            orchestrator.register_agent(agent_id, agent)
        
        print("\n✅ All 6 agents registered successfully!\n")
        
        # Test with critical sensor data
        test_sensor_data = {
            'vehicle_id': 'VEH001',
            'engine_temp': 102,  # Critical
            'rpm': 2500,
            'fuel_level': 45,
            'tire_pressure_fl': 26,  # Critical
            'tire_pressure_fr': 32,
            'tire_pressure_rl': 32,
            'tire_pressure_rr': 32,
            'battery_voltage': 11.4,  # Critical
            'oil_pressure': 17,  # Critical
            'brake_fluid_level': 58,  # Critical
            'speed': 60
        }
        
        print("🧪 Testing with critical sensor data...")
        print(f"   Vehicle: {test_sensor_data['vehicle_id']}")
        print(f"   Engine Temp: {test_sensor_data['engine_temp']}°C (CRITICAL)")
        print(f"   Battery: {test_sensor_data['battery_voltage']}V (CRITICAL)")
        print(f"   Oil Pressure: {test_sensor_data['oil_pressure']} PSI (CRITICAL)")
        print()
        
        # Process through orchestrator
        result = await orchestrator.process_sensor_data(test_sensor_data)
        
        print("📊 ANALYSIS RESULTS:")
        print(f"   Status: {result.get('status', 'unknown').upper()}")
        print(f"   Anomalies Detected: {len(result.get('anomalies', []))}")
        print(f"   Overall Health: {result.get('metrics', {}).get('overall_health', 0):.1f}/100")
        print()
        
        if result.get('anomalies'):
            print("⚠️  DETECTED ANOMALIES:")
            for anomaly in result['anomalies'][:5]:
                print(f"   • {anomaly['severity'].upper()}: {anomaly['message']}")
        
        if result.get('diagnosis'):
            print(f"\n🔍 DIAGNOSIS:")
            diagnosis = result['diagnosis']
            print(f"   Severity: {diagnosis['severity'].upper()}")
            print(f"   Issues Found: {len(diagnosis['issues'])}")
            print(f"   Confidence: {diagnosis['confidence']:.0%}")
            print(f"   Estimated Cost: ${diagnosis['estimated_cost_range'][0]}-${diagnosis['estimated_cost_range'][1]}")
        
        if result.get('appointment'):
            print(f"\n📅 AUTO-SCHEDULED APPOINTMENT:")
            apt = result['appointment']
            print(f"   Workshop: {apt['workshop']}")
            print(f"   Time: {apt['scheduled_time']}")
            print(f"   Status: {apt['status']}")
        
        print(f"\n🤖 AGENT STATUS:")
        status = orchestrator.get_agent_status()
        for agent_id, info in status.items():
            print(f"   • {info['name']}: {info['tasks_processed']} tasks processed")
        
        print("\n" + "="*70)
        print("✅ Multi-Agent System Test Complete!")
        print("="*70)
    
    asyncio.run(main())
