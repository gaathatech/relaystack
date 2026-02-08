"""
Analytics module for tracking WhatsApp marketing campaigns and chatbot performance
"""

from datetime import datetime, timedelta
from modules.database import get_db, Analytics
import json

class MarketingAnalytics:
    """Analytics for marketing campaigns"""
    
    @staticmethod
    def get_campaign_performance(days=30):
        """Get overall campaign performance"""
        conn = get_db()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_campaigns,
                SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent_campaigns,
                SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled_campaigns,
                SUM(success_count) as total_messages_sent,
                SUM(failed_count) as total_messages_failed
            FROM campaigns
            WHERE created_date >= ?
        ''', (since,))
        
        stats = dict(cursor.fetchone())
        conn.close()
        
        return {
            'total_campaigns': stats['total_campaigns'] or 0,
            'sent_campaigns': stats['sent_campaigns'] or 0,
            'scheduled_campaigns': stats['scheduled_campaigns'] or 0,
            'total_messages_sent': stats['total_messages_sent'] or 0,
            'total_messages_failed': stats['total_messages_failed'] or 0,
            'success_rate': round(((stats['total_messages_sent'] or 0) / 
                                ((stats['total_messages_sent'] or 0) + (stats['total_messages_failed'] or 1))) * 100, 2)
        }
    
    @staticmethod
    def get_campaign_timeline(days=30):
        """Get campaign timeline for last N days"""
        conn = get_db()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT DATE(created_date) as date, COUNT(*) as campaigns, SUM(success_count) as messages
            FROM campaigns
            WHERE created_date >= ?
            GROUP BY DATE(created_date)
            ORDER BY date DESC
        ''', (since,))
        
        timeline = [{'date': row['date'], 'campaigns': row['campaigns'], 'messages': row['messages'] or 0} 
                   for row in cursor.fetchall()]
        conn.close()
        
        return timeline
    
    @staticmethod
    def get_top_campaigns(limit=10):
        """Get top performing campaigns"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, campaign_name, success_count, failed_count, contacts_count, created_date
            FROM campaigns
            ORDER BY success_count DESC
            LIMIT ?
        ''', (limit,))
        
        campaigns = []
        for row in cursor.fetchall():
            campaign_dict = dict(row)
            total = campaign_dict['success_count'] + campaign_dict['failed_count']
            campaign_dict['success_rate'] = round(campaign_dict['success_count'] / total * 100, 2) if total > 0 else 0
            campaigns.append(campaign_dict)
        
        conn.close()
        return campaigns
    
    @staticmethod
    def get_contact_engagement():
        """Get engagement stats per contact"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                c.id, c.name, c.phone_number,
                COUNT(DISTINCT cm.id) as messages_received,
                COUNT(DISTINCT ch.id) as chats
            FROM contacts c
            LEFT JOIN campaign_messages cm ON c.id = cm.contact_id AND cm.status = 'sent'
            LEFT JOIN chat_history ch ON c.phone_number = ch.contact_phone
            GROUP BY c.id
            ORDER BY messages_received DESC
            LIMIT 20
        ''')
        
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return contacts

class ChatbotAnalytics:
    """Analytics for chatbot performance"""
    
    @staticmethod
    def get_chatbot_stats(days=30):
        """Get overall chatbot statistics"""
        conn = get_db()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_chats,
                COUNT(DISTINCT contact_phone) as unique_users,
                COUNT(CASE WHEN matched_qa_id IS NOT NULL THEN 1 END) as answered,
                COUNT(CASE WHEN matched_qa_id IS NULL THEN 1 END) as unanswered,
                AVG(confidence_score) as avg_confidence
            FROM chat_history
            WHERE timestamp >= ?
        ''', (since,))
        
        stats = dict(cursor.fetchone())
        conn.close()
        
        return {
            'total_chats': stats['total_chats'] or 0,
            'unique_users': stats['unique_users'] or 0,
            'answered_questions': stats['answered'] or 0,
            'unanswered_questions': stats['unanswered'] or 0,
            'answer_rate': round((stats['answered'] or 0) / (stats['total_chats'] or 1) * 100, 2),
            'average_confidence': round(stats['avg_confidence'] or 0, 3)
        }
    
    @staticmethod
    def get_top_questions(limit=10, days=30):
        """Get most frequently asked questions"""
        conn = get_db()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT 
                k.id, k.question, k.answer, k.category,
                COUNT(ch.id) as ask_count,
                AVG(ch.confidence_score) as avg_confidence
            FROM knowledge_base k
            LEFT JOIN chat_history ch ON k.id = ch.matched_qa_id AND ch.timestamp >= ?
            GROUP BY k.id
            ORDER BY ask_count DESC
            LIMIT ?
        ''', (since, limit))
        
        questions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return questions
    
    @staticmethod
    def get_unanswered_questions(limit=20, days=30):
        """Get questions the chatbot couldn't answer"""
        conn = get_db()
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute('''
            SELECT user_message, COUNT(*) as count, AVG(confidence_score) as avg_confidence
            FROM chat_history
            WHERE matched_qa_id IS NULL AND timestamp >= ?
            GROUP BY user_message
            ORDER BY count DESC
            LIMIT ?
        ''', (since, limit))
        
        questions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return questions
    
    @staticmethod
    def get_user_conversation_flow(contact_phone, limit=50):
        """Get conversation flow for specific user"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_message, bot_response, confidence_score, timestamp
            FROM chat_history
            WHERE contact_phone = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (contact_phone, limit))
        
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return list(reversed(messages))  # Return in chronological order
    
    @staticmethod
    def get_conversation_stats():
        """Get statistics about conversations"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                contact_phone,
                COUNT(*) as message_count,
                AVG(confidence_score) as avg_confidence,
                MAX(timestamp) as last_message
            FROM chat_history
            GROUP BY contact_phone
            ORDER BY message_count DESC
        ''')
        
        stats = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return stats

class AnalyticsReport:
    """Generate comprehensive analytics reports"""
    
    @staticmethod
    def generate_executive_summary(days=30):
        """Generate executive summary report"""
        campaign_stats = MarketingAnalytics.get_campaign_performance(days)
        chatbot_stats = ChatbotAnalytics.get_chatbot_stats(days)
        
        return {
            'period_days': days,
            'generated_at': datetime.now().isoformat(),
            'marketing': campaign_stats,
            'chatbot': chatbot_stats,
            'total_interactions': campaign_stats['total_messages_sent'] + chatbot_stats['total_chats']
        }
    
    @staticmethod
    def generate_detailed_report(days=30):
        """Generate detailed report with all metrics"""
        report = {
            'period': f"Last {days} days",
            'generated_at': datetime.now().isoformat(),
            'summary': AnalyticsReport.generate_executive_summary(days),
            'marketing': {
                'performance': MarketingAnalytics.get_campaign_performance(days),
                'timeline': MarketingAnalytics.get_campaign_timeline(days),
                'top_campaigns': MarketingAnalytics.get_top_campaigns(5),
                'contact_engagement': MarketingAnalytics.get_contact_engagement()
            },
            'chatbot': {
                'statistics': ChatbotAnalytics.get_chatbot_stats(days),
                'top_questions': ChatbotAnalytics.get_top_questions(5),
                'unanswered_questions': ChatbotAnalytics.get_unanswered_questions(5)
            }
        }
        return report
    
    @staticmethod
    def export_report_json(days=30):
        """Export report as JSON"""
        report = AnalyticsReport.generate_detailed_report(days)
        return json.dumps(report, indent=2, default=str)
    
    @staticmethod
    def export_report_html(days=30):
        """Export report as HTML"""
        report = AnalyticsReport.generate_detailed_report(days)
        
        html = f"""
        <html>
        <head>
            <title>Nexora Analytics Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }}
                h1 {{ color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }}
                h2 {{ color: #555; margin-top: 30px; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; padding: 15px; background: #f0f0f0; border-radius: 5px; }}
                .metric-label {{ font-size: 12px; color: #666; }}
                .metric-value {{ font-size: 28px; font-weight: bold; color: #007bff; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th {{ background: #007bff; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                tr:hover {{ background: #f9f9f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Nexora Analytics Report</h1>
                <p>Generated: {report['generated_at']}</p>
                <p>Period: {report['period']}</p>
                
                <h2>Executive Summary</h2>
                <div class="metric">
                    <div class="metric-label">Total Interactions</div>
                    <div class="metric-value">{report['summary']['total_interactions']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Messages Sent</div>
                    <div class="metric-value">{report['summary']['marketing']['total_messages_sent']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Chat Conversations</div>
                    <div class="metric-value">{report['summary']['chatbot']['total_chats']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Chatbot Answer Rate</div>
                    <div class="metric-value">{report['summary']['chatbot']['answer_rate']}%</div>
                </div>
                
                <h2>📧 Marketing Performance</h2>
                <div class="metric">
                    <div class="metric-label">Total Campaigns</div>
                    <div class="metric-value">{report['marketing']['performance']['total_campaigns']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Success Rate</div>
                    <div class="metric-value">{report['marketing']['performance']['success_rate']}%</div>
                </div>
                
                <h2>🤖 Chatbot Performance</h2>
                <div class="metric">
                    <div class="metric-label">Unique Users</div>
                    <div class="metric-value">{report['chatbot']['statistics']['unique_users']}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Avg Confidence</div>
                    <div class="metric-value">{report['chatbot']['statistics']['average_confidence']:.2f}</div>
                </div>
            </div>
        </body>
        </html>
        """
        return html

# Helper function for quick stats
def get_quick_stats():
    """Get quick stats for dashboard"""
    return {
        'marketing': MarketingAnalytics.get_campaign_performance(7),
        'chatbot': ChatbotAnalytics.get_chatbot_stats(7),
        'timestamp': datetime.now().isoformat()
    }
