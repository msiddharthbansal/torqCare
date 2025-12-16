"""
Scheduling Agent - Automatic appointment scheduling with mechanic workshops
Finds available slots and books appointments based on diagnosis
"""

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import os
import json
import random

class SchedulingAgent:
    """
    Agent responsible for scheduling maintenance appointments
    """
    
    def __init__(self, groq_api_key: str = None):
        self.api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            temperature=0.3,
            model_name="llama-3.1-70b-versatile",
            groq_api_key=self.api_key
        )
    
    def find_available_workshops(
        self, 
        component: str, 
        severity: str,
        workshops: List[Dict],
        preferred_city: Optional[str] = None
    ) -> List[Dict]:
        """
        Find workshops capable of handling the repair
        """
        suitable_workshops = []
        
        for workshop in workshops:
            # Check if workshop can handle this component
            specialties = workshop.get('specialties', '').split(', ')
            
            # Match component to specialties
            component_match = (
                component in specialties or
                'Diagnostics' in specialties or
                len(specialties) >= 3  # General service centers
            )
            
            if component_match:
                # Check city preference
                if preferred_city and workshop.get('city') != preferred_city:
                    continue
                
                # Parse available slots
                try:
                    available_slots = eval(workshop.get('available_slots', '{}'))
                except:
                    available_slots = {}
                
                # Count total available slots
                total_slots = sum(len(slots) for slots in available_slots.values())
                
                if total_slots > 0:
                    suitable_workshops.append({
                        **workshop,
                        'available_slots_parsed': available_slots,
                        'total_available_slots': total_slots
                    })
        
        # Sort by rating and availability
        suitable_workshops.sort(
            key=lambda x: (x['rating'], x['total_available_slots']),
            reverse=True
        )
        
        return suitable_workshops
    
    def get_recommended_slot(
        self, 
        workshop: Dict, 
        severity: str,
        preferred_date: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get recommended appointment slot based on severity
        """
        available_slots = workshop.get('available_slots_parsed', {})
        
        if not available_slots:
            return None
        
        # Determine how soon appointment should be
        if severity == 'Critical':
            days_ahead = 0  # Same day
        elif severity == 'High':
            days_ahead = 1  # Next day
        elif severity == 'Medium':
            days_ahead = 3  # Within 3 days
        else:
            days_ahead = 7  # Within a week
        
        # Find suitable date
        for i in range(days_ahead, 8):
            target_date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            
            if target_date in available_slots and available_slots[target_date]:
                time_slot = available_slots[target_date][0]  # First available
                
                return {
                    'workshop_id': workshop['workshop_id'],
                    'workshop_name': workshop['name'],
                    'date': target_date,
                    'time': time_slot,
                    'datetime': f"{target_date} {time_slot}",
                    'estimated_duration': self._estimate_duration(severity),
                    'rating': workshop['rating']
                }
        
        return None
    
    def _estimate_duration(self, severity: str) -> int:
        """Estimate repair duration based on severity"""
        duration_map = {
            'Critical': 8,
            'High': 6,
            'Medium': 4,
            'Low': 2
        }
        return duration_map.get(severity, 4)
    
    async def create_appointment_proposal(
        self,
        vehicle_id: str,
        diagnosis: Dict,
        workshops: List[Dict],
        preferred_city: Optional[str] = None
    ) -> Dict:
        """
        Create appointment proposal based on diagnosis
        """
        if not diagnosis.get('issues'):
            return {
                'status': 'no_issues',
                'message': 'No maintenance required at this time'
            }
        
        # Get primary issue
        primary_issue = diagnosis['issues'][0]
        component = primary_issue['component']
        severity = primary_issue['severity']
        
        # Find suitable workshops
        suitable_workshops = self.find_available_workshops(
            component, severity, workshops, preferred_city
        )
        
        if not suitable_workshops:
            return {
                'status': 'no_availability',
                'message': 'No workshops available. Please contact support.',
                'component': component,
                'severity': severity
            }
        
        # Get top 3 workshop options
        options = []
        for workshop in suitable_workshops[:3]:
            slot = self.get_recommended_slot(workshop, severity)
            if slot:
                # Estimate cost based on component
                cost_estimates = {
                    'Battery': (500, 3000),
                    'Motor': (800, 4000),
                    'Brake': (200, 1000),
                    'Tire': (100, 800),
                    'Suspension': (400, 2000)
                }
                cost_range = cost_estimates.get(component, (200, 1500))
                
                options.append({
                    **slot,
                    'city': workshop['city'],
                    'address': workshop['address'],
                    'phone': workshop['phone'],
                    'specialties': workshop['specialties'],
                    'estimated_cost_min': cost_range[0],
                    'estimated_cost_max': cost_range[1]
                })
        
        if not options:
            return {
                'status': 'no_slots',
                'message': 'All workshops are fully booked. Checking additional dates...',
                'workshops': suitable_workshops[:3]
            }
        
        # Generate appointment proposal using LLM
        proposal_text = await self._generate_proposal_text(
            vehicle_id, component, severity, options
        )
        
        return {
            'status': 'proposal_ready',
            'vehicle_id': vehicle_id,
            'component': component,
            'severity': severity,
            'recommended_option': options[0],
            'alternative_options': options[1:],
            'proposal_text': proposal_text,
            'requires_approval': True,
            'created_at': datetime.now().isoformat()
        }
    
    async def _generate_proposal_text(
        self,
        vehicle_id: str,
        component: str,
        severity: str,
        options: List[Dict]
    ) -> str:
        """
        Generate human-friendly appointment proposal
        """
        primary = options[0]
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a scheduling assistant helping customers book vehicle maintenance.
            Create a concise, friendly proposal message that:
            - Acknowledges the issue
            - Recommends the best appointment option
            - Mentions 1-2 alternative options briefly
            - Encourages the customer to accept or choose an alternative
            Keep it under 100 words."""),
            HumanMessage(content=f"""
Vehicle: {vehicle_id}
Issue: {component} ({severity} severity)

Recommended Appointment:
- Workshop: {primary['workshop_name']} ({primary['city']})
- Date & Time: {primary['date']} at {primary['time']}
- Duration: ~{primary['estimated_duration']} hours
- Cost: ${primary['estimated_cost_min']}-${primary['estimated_cost_max']}
- Rating: {primary['rating']}/5.0

Create an appointment proposal message.
""")
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            return response.content
        except Exception as e:
            return f"Based on your {component} issue ({severity} priority), we recommend scheduling at {primary['workshop_name']} in {primary['city']} on {primary['date']} at {primary['time']}. The service will take approximately {primary['estimated_duration']} hours and cost ${primary['estimated_cost_min']}-${primary['estimated_cost_max']}."
    
    def confirm_appointment(
        self,
        vehicle_id: str,
        appointment_option: Dict,
        user_notes: Optional[str] = None
    ) -> Dict:
        """
        Confirm and create appointment record
        """
        appointment_id = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        appointment = {
            'appointment_id': appointment_id,
            'vehicle_id': vehicle_id,
            'workshop_id': appointment_option['workshop_id'],
            'workshop_name': appointment_option['workshop_name'],
            'scheduled_datetime': appointment_option['datetime'],
            'date': appointment_option['date'],
            'time': appointment_option['time'],
            'estimated_duration_hours': appointment_option['estimated_duration'],
            'estimated_cost': (
                appointment_option['estimated_cost_min'],
                appointment_option['estimated_cost_max']
            ),
            'status': 'Confirmed',
            'created_at': datetime.now().isoformat(),
            'user_notes': user_notes,
            'confirmation_number': f"TC{random.randint(100000, 999999)}"
        }
        
        return appointment
    
    def cancel_appointment(
        self,
        appointment_id: str,
        reason: Optional[str] = None
    ) -> Dict:
        """
        Cancel an appointment
        """
        return {
            'appointment_id': appointment_id,
            'status': 'Cancelled',
            'cancelled_at': datetime.now().isoformat(),
            'cancellation_reason': reason,
            'refund_status': 'N/A'
        }
    
    def reschedule_appointment(
        self,
        appointment_id: str,
        new_date: str,
        new_time: str
    ) -> Dict:
        """
        Reschedule an existing appointment
        """
        return {
            'appointment_id': appointment_id,
            'original_datetime': None,  # Would come from database
            'new_datetime': f"{new_date} {new_time}",
            'status': 'Rescheduled',
            'updated_at': datetime.now().isoformat()
        }
    
    async def send_appointment_reminder(
        self,
        appointment: Dict,
        hours_before: int = 24
    ) -> str:
        """
        Generate appointment reminder message
        """
        reminder_time = datetime.fromisoformat(appointment['scheduled_datetime']) - timedelta(hours=hours_before)
        
        message = f"""
🔔 Appointment Reminder

Vehicle: {appointment['vehicle_id']}
Service Center: {appointment['workshop_name']}
Date & Time: {appointment['date']} at {appointment['time']}
Confirmation: #{appointment['confirmation_number']}

Please arrive 10 minutes early. Bring your vehicle documents.
Need to reschedule? Reply 'reschedule' or call the service center.
"""
        return message.strip()

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_scheduling():
        agent = SchedulingAgent()
        
        diagnosis = {
            'vehicle_id': 'EV-00001',
            'issues': [
                {
                    'component': 'Battery',
                    'severity': 'High',
                    'rul_hours': 48
                }
            ]
        }
        
        workshops = [
            {
                'workshop_id': 'WS-001',
                'name': 'TorqCare Service Center San Francisco',
                'city': 'San Francisco',
                'address': '123 Main St',
                'phone': '+1-555-0001',
                'specialties': 'Battery, Motor, Diagnostics',
                'rating': 4.8,
                'available_slots': str({
                    (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"): 
                    [f"{h:02d}:00" for h in range(9, 17, 2)]
                    for i in range(7)
                })
            }
        ]
        
        proposal = await agent.create_appointment_proposal(
            'EV-00001', diagnosis, workshops
        )
        
        print(f"Status: {proposal['status']}")
        if proposal['status'] == 'proposal_ready':
            print(f"\n{proposal['proposal_text']}")
            print(f"\nRecommended: {proposal['recommended_option']['workshop_name']}")
            print(f"Date: {proposal['recommended_option']['date']} at {proposal['recommended_option']['time']}")
    
    asyncio.run(test_scheduling())
