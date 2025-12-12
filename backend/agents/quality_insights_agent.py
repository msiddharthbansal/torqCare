"""
Quality Insights Agent - Manufacturing quality analysis
Feedback Agent - User feedback processing and sharing
"""

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from typing import Dict, List, Optional
from datetime import datetime
from collections import Counter
import os

# ==================== QUALITY INSIGHTS AGENT ====================
class QualityInsightsAgent:
    """
    Agent for analyzing patterns and providing insights to manufacturers
    """
    
    def __init__(self, groq_api_key: str = None):
        self.api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.llm = ChatGroq(
            temperature=0.2,
            model_name="llama-3.1-70b-versatile",
            groq_api_key=self.api_key
        )
    
    async def generate_insights(self, maintenance_records: List[Dict]) -> Dict:
        """
        Analyze maintenance patterns and generate quality insights
        """
        if not maintenance_records:
            return {'status': 'no_data'}
        
        # Aggregate data by component
        component_failures = Counter(r['component'] for r in maintenance_records)
        issue_types = Counter(r['issue_detected'] for r in maintenance_records)
        
        # Calculate statistics
        total_failures = len(maintenance_records)
        avg_cost = sum(r['cost_usd'] for r in maintenance_records) / total_failures
        
        # Identify patterns
        high_frequency_components = [
            comp for comp, count in component_failures.most_common(5)
        ]
        
        # Calculate severity distribution
        severity_dist = Counter(r['severity'] for r in maintenance_records)
        
        # Generate AI insights
        insights_text = await self._generate_insights_report(
            component_failures,
            issue_types,
            total_failures,
            avg_cost
        )
        
        return {
            'total_failures': total_failures,
            'component_distribution': dict(component_failures),
            'issue_types': dict(issue_types.most_common(10)),
            'average_repair_cost': round(avg_cost, 2),
            'severity_distribution': dict(severity_dist),
            'high_risk_components': high_frequency_components,
            'ai_insights': insights_text,
            'generated_at': datetime.now().isoformat()
        }
    
    async def _generate_insights_report(
        self,
        component_failures: Counter,
        issue_types: Counter,
        total_failures: int,
        avg_cost: float
    ) -> str:
        """Generate detailed insights using LLM"""
        
        top_components = ", ".join([f"{comp} ({count} cases)" 
                                    for comp, count in component_failures.most_common(3)])
        top_issues = ", ".join([f"{issue}" 
                               for issue, _ in issue_types.most_common(3)])
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a manufacturing quality analyst for electric vehicles.
            Analyze failure patterns and provide actionable insights for improving product quality.
            Focus on root causes and preventive measures."""),
            HumanMessage(content=f"""
Quality Analysis Summary:
- Total Failures: {total_failures}
- Average Repair Cost: ${avg_cost:.2f}
- Top Failing Components: {top_components}
- Common Issues: {top_issues}

Provide a concise quality insight report (3-4 sentences) that:
1. Identifies the primary quality concern
2. Suggests potential root causes
3. Recommends manufacturing improvements
4. Prioritizes actions based on impact
""")
        ])
        
        try:
            response = await self.llm.ainvoke(prompt.format_messages())
            return response.content
        except Exception as e:
            return f"Quality Analysis: {total_failures} failures recorded with average cost ${avg_cost:.2f}. Top concerns: {top_components}. Recommend investigation of manufacturing processes for these components."
    
    async def process_feedback(self, feedback_data: Dict) -> Dict:
        """
        Process feedback for quality insights
        """
        # Extract key information
        vehicle_id = feedback_data['vehicle_id']
        component = feedback_data.get('component', 'Unknown')
        issue = feedback_data.get('issue', 'Not specified')
        severity = feedback_data.get('severity', 'Medium')
        
        # Determine if manufacturer should be notified
        notify_manufacturer = (
            severity in ['Critical', 'High'] or
            feedback_data.get('rating', 5) <= 2 or
            'recurred' in feedback_data.get('comment', '').lower()
        )
        
        return {
            'vehicle_id': vehicle_id,
            'component': component,
            'issue': issue,
            'severity': severity,
            'notify_manufacturer': notify_manufacturer,
            'priority': 'High' if notify_manufacturer else 'Normal',
            'processed_at': datetime.now().isoformat()
        }

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_agents():
        quality_agent = QualityInsightsAgent()
        # feedback_agent = FeedbackAgent()
        
        # Test maintenance records
        test_records = [
            {'component': 'Battery', 'issue_detected': 'Cell degradation', 'cost_usd': 1500, 'severity': 'High'},
            {'component': 'Battery', 'issue_detected': 'Thermal issue', 'cost_usd': 2000, 'severity': 'Critical'},
            {'component': 'Motor', 'issue_detected': 'Bearing wear', 'cost_usd': 1200, 'severity': 'Medium'},
        ]
        
        insights = await quality_agent.generate_insights(test_records)
        print("Quality Insights:")
        print(insights['ai_insights'])
        
        # # Test feedback
        # test_feedback = {
        #     'feedback_id': 'FBK-001',
        #     'vehicle_id': 'EV-00001',
        #     'rating': 2,
        #     'comment': 'The problem occurred again after repair. Not satisfied with the service.',
        #     'repair_effectiveness': 1
        # }
        
        # processed = await feedback_agent.process_feedback(test_feedback)
        # print(f"\nFeedback Analysis:")
        # print(f"Sentiment: {processed['sentiment']}")
        # print(f"Actions: {', '.join(processed['recommended_actions'])}")
        
        # response = await feedback_agent.generate_response_to_feedback(test_feedback, processed['sentiment'])
        # print(f"\nResponse:\n{response}")
    
    asyncio.run(test_agents())
