"""
Chatbot Agent - Customer engagement for vehicle queries and support
Answers questions about real-time telemetry and product information
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langchain.memory import ConversationBufferMemory
from typing import Dict, List, Optional
from datetime import datetime
import os
import json

class ChatbotAgent:
    """
    Customer engagement agent for answering vehicle-related queries
    """
    
    def __init__(self, groq_api_key: str = None):
        self.api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            temperature=0.7,
            model_name="llama-3.1-70b-versatile",
            groq_api_key=self.api_key
        )
        
        # Conversation memory per vehicle
        self.conversations = {}
        
        # Vehicle knowledge base (mock)
        self.vehicle_knowledge = {
            'specifications': {
                'Tesla Model 3': {
                    'battery_capacity': '75 kWh',
                    'range': '358 miles',
                    'motor_power': '283 HP',
                    'acceleration': '0-60 mph in 5.8 seconds',
                    'charging': '30 min to 80% (Supercharger)',
                    'warranty': '8 years / 120,000 miles (battery)'
                }
            },
            'maintenance_schedule': {
                'battery_inspection': 'Every 50,000 miles',
                'brake_fluid': 'Every 2 years',
                'cabin_air_filter': 'Every 2 years',
                'tire_rotation': 'Every 6,250 miles',
                'brake_pads': 'Inspect every 12,500 miles'
            },
            'common_questions': {
                'range_anxiety': "Your vehicle's range depends on battery SoC, driving conditions, and climate control usage. Monitor the real-time SoC percentage for accurate range estimation.",
                'charging_tips': "For optimal battery health: charge to 80% daily, use 100% only for long trips, avoid frequent fast charging, and keep battery between 20-80%.",
                'regenerative_braking': "Regenerative braking recaptures energy during deceleration, extending range and reducing brake wear. Efficiency above 80% is optimal.",
                'battery_health': "Battery SoH (State of Health) indicates remaining capacity. Above 90% is excellent, 80-90% is good, below 80% may need attention.",
                'tire_pressure': "Maintain tire pressure at 42 PSI (cold) for optimal efficiency and safety. Check monthly and before long trips."
            }
        }
    
    def get_memory(self, vehicle_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for a vehicle"""
        if vehicle_id not in self.conversations:
            self.conversations[vehicle_id] = ConversationBufferMemory(
                return_messages=True,
                memory_key="chat_history"
            )
        return self.conversations[vehicle_id]
    
    async def chat(
        self, 
        vehicle_id: str, 
        user_message: str, 
        vehicle_data: Optional[Dict] = None,
        diagnosis: Optional[Dict] = None
    ) -> str:
        """
        Process user message and generate response
        """
        memory = self.get_memory(vehicle_id)
        
        # Build context
        context_parts = [f"Vehicle ID: {vehicle_id}"]
        
        if vehicle_data:
            context_parts.append(f"""
Current Vehicle Status:
- Battery: {vehicle_data.get('soc', 'N/A')}% SoC, {vehicle_data.get('soh', 'N/A')}% SoH
- Battery Temperature: {vehicle_data.get('battery_temp', 'N/A')}°C
- Motor Temperature: {vehicle_data.get('motor_temp', 'N/A')}°C
- Brake Pad Wear: {vehicle_data.get('brake_pad_wear', 'N/A')} mm
- Tire Pressures: FL:{vehicle_data.get('tire_pressure_fl', 'N/A')} FR:{vehicle_data.get('tire_pressure_fr', 'N/A')} RL:{vehicle_data.get('tire_pressure_rl', 'N/A')} RR:{vehicle_data.get('tire_pressure_rr', 'N/A')} PSI
- Total Distance: {vehicle_data.get('distance_traveled', 'N/A')} km
""")
        
        if diagnosis and diagnosis.get('issues'):
            issues_text = "\n".join([
                f"- {issue['component']}: {issue['severity']} severity"
                for issue in diagnosis['issues'][:3]
            ])
            context_parts.append(f"\nActive Issues:\n{issues_text}")
        
        context = "\n".join(context_parts)
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are TorqCare Assistant, a friendly and knowledgeable customer service agent for electric vehicle care.

Your role:
- Answer questions about the vehicle's current status, specifications, and maintenance
- Explain technical issues in simple terms
- Provide helpful recommendations for vehicle care
- Be empathetic if there are issues, and reassuring about solutions
- Encourage booking maintenance when issues are detected

Vehicle Knowledge Base:
{json.dumps(self.vehicle_knowledge, indent=2)}

Current Context:
{context}

Guidelines:
- Be conversational and helpful
- Use simple language, avoid excessive jargon
- Reference real-time data when relevant
- Suggest booking maintenance if serious issues are present
- Keep responses concise (2-4 sentences unless asked for details)
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content=user_message)
        ])
        
        # Get chat history
        history = memory.load_memory_variables({})
        chat_history = history.get("chat_history", [])
        
        try:
            # Generate response
            messages = prompt.format_messages(chat_history=chat_history)
            response = await self.llm.ainvoke(messages)
            
            # Save to memory
            memory.save_context(
                {"input": user_message},
                {"output": response.content}
            )
            
            return response.content
        
        except Exception as e:
            print(f"Chatbot error: {e}")
            return "I apologize, I'm having trouble processing your request right now. Please try again in a moment."
    
    async def suggest_maintenance_booking(
        self, 
        vehicle_id: str, 
        diagnosis: Dict
    ) -> str:
        """
        Proactively suggest booking maintenance based on diagnosis
        """
        if not diagnosis.get('issues'):
            return None
        
        critical_issues = [i for i in diagnosis['issues'] if i['severity'] in ['Critical', 'High']]
        
        if not critical_issues:
            return None
        
        issue_descriptions = ", ".join([f"{i['component']}" for i in critical_issues[:2]])
        
        message = f"""
🚨 Important: I've detected {len(critical_issues)} issue(s) that need attention: {issue_descriptions}.

For your safety and to prevent further damage, I recommend scheduling a service appointment soon. 
Would you like me to help you book an appointment at a nearby TorqCare service center?
"""
        
        return message.strip()
    
    async def handle_appointment_query(
        self, 
        vehicle_id: str, 
        user_message: str,
        available_workshops: List[Dict]
    ) -> str:
        """
        Handle appointment-related queries
        """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are helping a customer book a vehicle service appointment.

Available Service Centers:
{json.dumps([{
    'name': w['name'],
    'city': w['city'],
    'rating': w['rating'],
    'specialties': w['specialties'],
    'next_available': 'Within 2 days'
} for w in available_workshops[:3]], indent=2)}

Guidelines:
- Recommend the nearest or highest-rated center
- Mention their specialties if relevant
- Be encouraging about the booking process
- Keep response friendly and concise
"""),
            HumanMessage(content=user_message)
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            return response.content
        except Exception as e:
            return "I can help you book an appointment at one of our service centers. Which city works best for you?"
    
    def get_quick_answers(self, query_type: str) -> str:
        """
        Provide instant answers to common questions
        """
        return self.vehicle_knowledge['common_questions'].get(
            query_type,
            "I can help you with that. Could you provide more details?"
        )
    
    async def explain_metric(self, metric_name: str, current_value: float) -> str:
        """
        Explain what a specific metric means and whether the value is concerning
        """
        explanations = {
            'soc': f"State of Charge (SoC) is your battery's current charge level. At {current_value}%, {'you have good range' if current_value > 50 else 'consider charging soon' if current_value > 20 else 'please charge immediately'}.",
            'soh': f"State of Health (SoH) indicates battery degradation. At {current_value}%, your battery {'is in excellent condition' if current_value > 90 else 'is performing well' if current_value > 80 else 'may need professional assessment'}.",
            'battery_temp': f"Battery temperature is {current_value}°C. {'This is normal' if current_value < 40 else 'This is slightly elevated' if current_value < 50 else 'This is concerning and may indicate a cooling issue'}.",
            'motor_temp': f"Motor temperature is {current_value}°C. {'This is within normal range' if current_value < 85 else 'This is elevated' if current_value < 100 else 'This requires immediate attention'}.",
            'brake_pad_wear': f"Brake pad thickness is {current_value}mm. {'Brakes are in good condition' if current_value > 5 else 'Brakes should be inspected soon' if current_value > 2 else 'Brake pads need immediate replacement'}."
        }
        
        return explanations.get(
            metric_name,
            f"The {metric_name} reading is {current_value}. This metric helps monitor vehicle health."
        )
    
    def clear_conversation(self, vehicle_id: str):
        """Clear conversation history for a vehicle"""
        if vehicle_id in self.conversations:
            del self.conversations[vehicle_id]

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_chatbot():
        agent = ChatbotAgent()
        
        vehicle_data = {
            'vehicle_id': 'EV-00001',
            'soc': 45,
            'soh': 88,
            'battery_temp': 32,
            'motor_temp': 75,
            'brake_pad_wear': 4.5,
            'tire_pressure_fl': 35,
            'distance_traveled': 45000
        }
        
        diagnosis = {
            'issues': [
                {'component': 'Battery', 'severity': 'Medium'}
            ]
        }
        
        # Test conversation
        queries = [
            "What's my current battery health?",
            "Should I be worried about anything?",
            "How often should I rotate my tires?"
        ]
        
        for query in queries:
            print(f"\nUser: {query}")
            response = await agent.chat('EV-00001', query, vehicle_data, diagnosis)
            print(f"TorqCare: {response}")
        
        # Test maintenance suggestion
        suggestion = await agent.suggest_maintenance_booking('EV-00001', diagnosis)
        if suggestion:
            print(f"\n{suggestion}")
    
    asyncio.run(test_chatbot())
