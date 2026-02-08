"""
PDF export functionality for chat history and reports
"""

from datetime import datetime
from io import BytesIO
from modules.database import ChatHistory
import json

class PDFExporter:
    """Export chat history and reports to PDF"""
    
    @staticmethod
    def export_chat_history_html(contact_phone, limit=100):
        """Generate HTML for chat history (for PDF conversion)"""
        messages = ChatHistory.get_by_phone(contact_phone, limit)
        
        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Chat History - {contact_phone}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                    color: #333;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .header p {{
                    margin: 5px 0 0 0;
                    opacity: 0.9;
                }}
                .messages {{
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .message {{
                    margin-bottom: 20px;
                    border-left: 4px solid #ddd;
                    padding-left: 15px;
                }}
                .message.user {{
                    border-left-color: #667eea;
                }}
                .message.bot {{
                    border-left-color: #764ba2;
                }}
                .message-sender {{
                    font-weight: bold;
                    font-size: 12px;
                    color: #666;
                    text-transform: uppercase;
                    margin-bottom: 5px;
                }}
                .message-content {{
                    font-size: 14px;
                    line-height: 1.5;
                    color: #333;
                    margin-bottom: 5px;
                }}
                .message-time {{
                    font-size: 11px;
                    color: #999;
                }}
                .message-meta {{
                    font-size: 11px;
                    color: #aaa;
                    margin-top: 5px;
                }}
                .confidence {{
                    display: inline-block;
                    background: #e3f2fd;
                    padding: 2px 8px;
                    border-radius: 4px;
                    color: #1976d2;
                    margin-top: 5px;
                    font-size: 11px;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #999;
                    text-align: center;
                }}
                .stats {{
                    background: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .stats-item {{
                    display: inline-block;
                    margin-right: 30px;
                }}
                .stats-label {{
                    font-size: 12px;
                    color: #666;
                }}
                .stats-value {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                }}
                page-break-after {{
                    avoid;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📱 Chat History Export</h1>
                <p>Contact: <strong>{contact_phone}</strong></p>
                <p>Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="stats">
                <div class="stats-item">
                    <div class="stats-label">Total Messages</div>
                    <div class="stats-value">{len(messages)}</div>
                </div>
                <div class="stats-item">
                    <div class="stats-label">User Questions</div>
                    <div class="stats-value">{len([m for m in messages if m['role'] == 'user'])}</div>
                </div>
                <div class="stats-item">
                    <div class="stats-label">Bot Responses</div>
                    <div class="stats-value">{len([m for m in messages if m['role'] == 'bot'])}</div>
                </div>
            </div>
            
            <div class="messages">
        """
        
        for msg in messages:
            if msg['role'] == 'user':
                msg_type = 'user'
                sender = 'User'
                content = msg['user_message'] if isinstance(msg, dict) and 'user_message' in msg else msg.get('content', '')
            else:
                msg_type = 'bot'
                sender = '🤖 Nexora Bot'
                # Handle both old format and new format
                if isinstance(msg, dict) and 'bot_response' in msg:
                    response = msg['bot_response']
                    if isinstance(response, str) and response.startswith('{'):
                        try:
                            response = json.loads(response)
                            content = response.get('text', '')
                        except:
                            content = response
                    else:
                        content = response
                else:
                    content = msg.get('content', '')
            
            timestamp = msg.get('timestamp', datetime.now().isoformat())
            confidence = msg.get('confidence_score', 0)
            
            html += f"""
                <div class="message {msg_type}">
                    <div class="message-sender">{sender}</div>
                    <div class="message-content">{content}</div>
                    <div class="message-time">{timestamp}</div>
            """
            
            if msg_type == 'bot' and confidence:
                html += f'<div class="confidence">Confidence: {confidence:.1%}</div>'
            
            html += """
                </div>
            """
        
        html += """
            </div>
            
            <div class="footer">
                <p>This is an automated export from Nexora. For questions, contact support@nexora.com</p>
                <p>Nexora Business Suite | Nexora Investments</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def export_campaign_report_html(campaign_id):
        """Generate HTML report for campaign"""
        from modules.database import get_db
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get campaign details
        cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
        campaign = dict(cursor.fetchone())
        
        # Get message stats
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM campaign_messages 
            WHERE campaign_id = ? 
            GROUP BY status
        ''', (campaign_id,))
        
        status_stats = {row['status']: row['count'] for row in cursor.fetchall()}
        conn.close()
        
        total_messages = sum(status_stats.values())
        success_rate = (campaign['success_count'] / total_messages * 100) if total_messages > 0 else 0
        
        html = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Campaign Report - {campaign['campaign_name']}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                    color: #333;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    background: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .section {{
                    margin-bottom: 30px;
                }}
                .section h2 {{
                    font-size: 18px;
                    color: #667eea;
                    border-bottom: 2px solid #f0f0f0;
                    padding-bottom: 10px;
                    margin-bottom: 15px;
                }}
                .metrics {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 20px;
                    margin-bottom: 20px;
                }}
                .metric-card {{
                    background: #f9f9f9;
                    padding: 15px;
                    border-radius: 5px;
                    border-left: 4px solid #667eea;
                }}
                .metric-card.success {{
                    border-left-color: #4caf50;
                }}
                .metric-card.pending {{
                    border-left-color: #ff9800;
                }}
                .metric-card.failed {{
                    border-left-color: #f44336;
                }}
                .metric-label {{
                    font-size: 12px;
                    color: #666;
                    margin-bottom: 5px;
                }}
                .metric-value {{
                    font-size: 26px;
                    font-weight: bold;
                    color: #333;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th {{
                    background: #f5f5f5;
                    padding: 10px;
                    text-align: left;
                    font-weight: bold;
                    border-bottom: 2px solid #ddd;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }}
                .success-bar {{
                    background: #4caf50;
                    height: 20px;
                    border-radius: 3px;
                    display: inline-block;
                    min-width: 20px;
                    color: white;
                    text-align: center;
                    font-size: 12px;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    font-size: 12px;
                    color: #999;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Campaign Report</h1>
                <p><strong>{campaign['campaign_name']}</strong></p>
                <p>Created: {campaign['created_date']} | Export: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="content">
                <div class="section">
                    <h2>📈 Performance Summary</h2>
                    <div class="metrics">
                        <div class="metric-card">
                            <div class="metric-label">Total Recipients</div>
                            <div class="metric-value">{campaign['contacts_count']}</div>
                        </div>
                        <div class="metric-card success">
                            <div class="metric-label">Successfully Sent</div>
                            <div class="metric-value">{campaign['success_count']}</div>
                        </div>
                        <div class="metric-card failed">
                            <div class="metric-label">Failed</div>
                            <div class="metric-value">{campaign['failed_count']}</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-label">Success Rate</div>
                            <div class="metric-value">{success_rate:.1f}%</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>📋 Campaign Details</h2>
                    <table>
                        <tr>
                            <td><strong>Status</strong></td>
                            <td>{campaign['status'].upper()}</td>
                        </tr>
                        <tr>
                            <td><strong>Message Template</strong></td>
                            <td><pre>{campaign['message_template']}</pre></td>
                        </tr>
                        <tr>
                            <td><strong>Sent Time</strong></td>
                            <td>{campaign['sent_time'] or 'Not yet sent'}</td>
                        </tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>📊 Message Status Breakdown</h2>
                    <table>
                        <tr>
                            <th>Status</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
        """
        
        for status, count in status_stats.items():
            percentage = (count / total_messages * 100) if total_messages > 0 else 0
            html += f"""
                        <tr>
                            <td><strong>{status.upper()}</strong></td>
                            <td>{count}</td>
                            <td>
                                <div style="width: {percentage}%; background: #667eea;">
                                    {percentage:.1f}%
                                </div>
                            </td>
                        </tr>
            """
        
        html += """
                    </table>
                </div>
            </div>
            
            <div class="footer">
                <p>This report was generated by Nexora. For more information, contact support@nexora.com</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    @staticmethod
    def get_html_for_pdf(content_type, **kwargs):
        """Get HTML content ready for PDF conversion"""
        if content_type == 'chat_history':
            return PDFExporter.export_chat_history_html(kwargs.get('contact_phone'), kwargs.get('limit', 100))
        elif content_type == 'campaign_report':
            return PDFExporter.export_campaign_report_html(kwargs.get('campaign_id'))
        else:
            raise ValueError(f"Unknown content type: {content_type}")

# Helper function for generating PDFs (requires weasyprint or similar)
def generate_pdf_from_html(html_content, filename='export.pdf'):
    """Generate PDF from HTML content
    Requires: pip install weasyprint
    """
    try:
        from weasyprint import HTML
        from io import BytesIO
        
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except ImportError:
        # Fallback: return HTML if weasyprint not installed
        return html_content.encode('utf-8')
    except Exception as e:
        return f"Error generating PDF: {str(e)}".encode('utf-8')
