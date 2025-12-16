from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter
import os

# ==================== FEEDBACK AGENT ====================
class FeedbackAgent:
    """
    Agent for collecting, analyzing, and sharing user feedback
    """
    
    def __init__(self, groq_api_key: str = None):
        self.api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            temperature=0.3,
            model_name="llama-3.1-70b-versatile",
            groq_api_key=self.api_key
        )
    
    async def process_feedback(self, feedback_data: Dict) -> Dict:
        """
        Process and analyze user feedback
        """
        # Analyze sentiment
        sentiment = await self._analyze_sentiment(feedback_data.get('comment', ''))
        
        # Extract key themes
        themes = self._extract_themes(feedback_data)
        
        # Determine actions
        actions = self._determine_actions(feedback_data, sentiment)
        
        return {
            'feedback_id': feedback_data.get('feedback_id'),
            'sentiment': sentiment,
            'themes': themes,
            'recommended_actions': actions,
            'share_with_manufacturer': feedback_data.get('rating', 5) <= 2 or sentiment == 'Negative',
            'share_with_workshop': True,
            'requires_follow_up': sentiment == 'Negative',
            'processed_at': datetime.now().isoformat()
        }
    
    async def _analyze_sentiment(self, comment: str) -> str:
        """Analyze sentiment of feedback comment"""
        if not comment:
            return 'Neutral'
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="Analyze the sentiment of the following feedback. Respond with only one word: Positive, Neutral, or Negative."),
            HumanMessage(content=comment)
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            sentiment = response.content.strip()
            return sentiment if sentiment in ['Positive', 'Neutral', 'Negative'] else 'Neutral'
        except:
            # Fallback to keyword-based
            comment_lower = comment.lower()
            if any(word in comment_lower for word in ['excellent', 'great', 'satisfied', 'good']):
                return 'Positive'
            elif any(word in comment_lower for word in ['poor', 'bad', 'terrible', 'disappointed']):
                return 'Negative'
            return 'Neutral'
    
    def _extract_themes(self, feedback_data: Dict) -> List[str]:
        """Extract themes from feedback"""
        themes = []
        
        comment = feedback_data.get('comment', '').lower()
        
        # Theme keywords
        theme_keywords = {
            'service_quality': ['service', 'staff', 'communication', 'professional'],
            'repair_effectiveness': ['fixed', 'resolved', 'working', 'problem'],
            'wait_time': ['wait', 'time', 'delay', 'schedule'],
            'cost': ['expensive', 'cost', 'price', 'charge'],
            'recurring_issue': ['again', 'recurred', 'same problem', 'still']
        }
        
        for theme, keywords in theme_keywords.items():
            if any(kw in comment for kw in keywords):
                themes.append(theme)
        
        return themes if themes else ['general_feedback']
    
    def _determine_actions(self, feedback_data: Dict, sentiment: str) -> List[str]:
        """Determine recommended actions based on feedback"""
        actions = []
        
        if sentiment == 'Negative':
            actions.append('immediate_follow_up')
            actions.append('quality_review')
        
        if feedback_data.get('rating', 5) <= 2:
            actions.append('customer_service_contact')
        
        if feedback_data.get('repair_effectiveness', 5) <= 2:
            actions.append('re_inspection_recommended')
        
        if 'recurring_issue' in self._extract_themes(feedback_data):
            actions.append('escalate_to_engineering')
            actions.append('notify_manufacturer')
        
        return actions if actions else ['log_feedback']
    
    async def generate_response_to_feedback(self, feedback_data: Dict, sentiment: str) -> str:
        """Generate appropriate response to user feedback"""
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""You are a customer service representative for TorqCare.
            Generate a professional, empathetic response to customer feedback.
            Sentiment: {sentiment}
            Keep it concise (2-3 sentences)."""),
            HumanMessage(content=f"""
Feedback:
Rating: {feedback_data.get('rating')}/5
Comment: {feedback_data.get('comment')}

Generate an appropriate response.
""")
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            return response.content
        except:
            if sentiment == 'Positive':
                return "Thank you for your positive feedback! We're glad we could help keep your vehicle in top condition."
            elif sentiment == 'Negative':
                return "We sincerely apologize for your experience. A customer service representative will contact you shortly to address your concerns."
            else:
                return "Thank you for your feedback. We appreciate your input and will use it to improve our services."
    
    def aggregate_feedback_metrics(self, feedback_list: List[Dict]) -> Dict:
        """Aggregate feedback metrics for reporting"""
        if not feedback_list:
            return {'status': 'no_data'}
        
        total = len(feedback_list)
        avg_rating = sum(f.get('rating', 0) for f in feedback_list) / total
        
        sentiment_dist = Counter(f.get('sentiment', 'Neutral') for f in feedback_list)
        
        return {
            'total_feedback': total,
            'average_rating': round(avg_rating, 2),
            'sentiment_distribution': dict(sentiment_dist),
            'recommendation_rate': sum(1 for f in feedback_list if f.get('would_recommend', False)) / total * 100,
            'generated_at': datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_agents():
        # quality_agent = QualityInsightsAgent()
        feedback_agent = FeedbackAgent()
        
        # # Test maintenance records
        # test_records = [
        #     {'component': 'Battery', 'issue_detected': 'Cell degradation', 'cost_usd': 1500, 'severity': 'High'},
        #     {'component': 'Battery', 'issue_detected': 'Thermal issue', 'cost_usd': 2000, 'severity': 'Critical'},
        #     {'component': 'Motor', 'issue_detected': 'Bearing wear', 'cost_usd': 1200, 'severity': 'Medium'},
        # ]
        
        # insights = await quality_agent.generate_insights(test_records)
        # print("Quality Insights:")
        # print(insights['ai_insights'])
        
        # Test feedback
        test_feedback = {
            'feedback_id': 'FBK-001',
            'vehicle_id': 'EV-00001',
            'rating': 2,
            'comment': 'The problem occurred again after repair. Not satisfied with the service.',
            'repair_effectiveness': 1
        }
        
        processed = await feedback_agent.process_feedback(test_feedback)
        print(f"\nFeedback Analysis:")
        print(f"Sentiment: {processed['sentiment']}")
        print(f"Actions: {', '.join(processed['recommended_actions'])}")
        
        response = await feedback_agent.generate_response_to_feedback(test_feedback, processed['sentiment'])
        print(f"\nResponse:\n{response}")
    
    asyncio.run(test_agents())