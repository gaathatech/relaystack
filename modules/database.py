"""
Database models for WhatsApp marketing and AI chatbot
SQLite-based with support for storing contacts, campaigns, Q&A, and analytics
"""

import sqlite3
from datetime import datetime
import os
import json

DB_PATH = os.environ.get('DB_PATH', os.path.join(os.path.dirname(__file__), '..', 'relaystack.db'))

def init_db():
    """Initialize database with all required tables"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Contacts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        phone_number TEXT UNIQUE NOT NULL,
        email TEXT,
        company TEXT,
        tags TEXT,
        added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_contacted TIMESTAMP
    )
    ''')
    
    # Marketing campaigns table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS campaigns (
        id INTEGER PRIMARY KEY,
        campaign_name TEXT UNIQUE NOT NULL,
        message_template TEXT NOT NULL,
        status TEXT DEFAULT 'draft',
        contacts_count INTEGER DEFAULT 0,
        scheduled_time TIMESTAMP,
        sent_time TIMESTAMP,
        success_count INTEGER DEFAULT 0,
        failed_count INTEGER DEFAULT 0,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Campaign messages log
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS campaign_messages (
        id INTEGER PRIMARY KEY,
        campaign_id INTEGER NOT NULL,
        contact_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        sent_time TIMESTAMP,
        delivery_status TEXT,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
        FOREIGN KEY (contact_id) REFERENCES contacts(id)
    )
    ''')
    
    # Knowledge base (Q&A)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY,
        question TEXT UNIQUE NOT NULL,
        answer TEXT NOT NULL,
        category TEXT,
        app_source TEXT,
        keywords TEXT,
        confidence_score REAL DEFAULT 1.0,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Chat history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY,
        contact_phone TEXT,
        user_message TEXT NOT NULL,
        bot_response TEXT NOT NULL,
        matched_qa_id INTEGER,
        confidence_score REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matched_qa_id) REFERENCES knowledge_base(id)
    )
    ''')
    
    # Analytics table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS analytics (
        id INTEGER PRIMARY KEY,
        metric_type TEXT,
        campaign_id INTEGER,
        value INTEGER DEFAULT 0,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
    )
    ''')
    
    # IVR flow configuration
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ivr_flow (
        id INTEGER PRIMARY KEY,
        flow_name TEXT UNIQUE NOT NULL,
        flow_data TEXT NOT NULL,
        app_type TEXT,
        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class Contact:
    @staticmethod
    def add(name, phone_number, email=None, company=None, tags=None):
        """Add new contact"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO contacts (name, phone_number, email, company, tags) VALUES (?, ?, ?, ?, ?)',
                (name, phone_number, email, company, tags)
            )
            conn.commit()
            contact_id = cursor.lastrowid
            conn.close()
            return {'status': 'success', 'id': contact_id}
        except sqlite3.IntegrityError:
            return {'status': 'error', 'message': 'Phone number already exists'}
    
    @staticmethod
    def get_all(limit=None):
        """Get all contacts"""
        conn = get_db()
        cursor = conn.cursor()
        if limit:
            cursor.execute('SELECT * FROM contacts ORDER BY added_date DESC LIMIT ?', (limit,))
        else:
            cursor.execute('SELECT * FROM contacts ORDER BY added_date DESC')
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return contacts
    
    @staticmethod
    def search(query):
        """Search contacts by name or phone"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM contacts WHERE name LIKE ? OR phone_number LIKE ?',
            (f'%{query}%', f'%{query}%')
        )
        contacts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return contacts
    
    @staticmethod
    def delete(contact_id):
        """Delete contact"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
        conn.commit()
        conn.close()
        return {'status': 'success'}

class Campaign:
    @staticmethod
    def create(campaign_name, message_template):
        """Create new campaign"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO campaigns (campaign_name, message_template) VALUES (?, ?)',
                (campaign_name, message_template)
            )
            conn.commit()
            campaign_id = cursor.lastrowid
            conn.close()
            return {'status': 'success', 'id': campaign_id}
        except sqlite3.IntegrityError:
            return {'status': 'error', 'message': 'Campaign name already exists'}
    
    @staticmethod
    def schedule(campaign_id, scheduled_time, contact_ids):
        """Schedule campaign send"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE campaigns SET scheduled_time = ?, status = ? WHERE id = ?',
                      (scheduled_time, 'scheduled', campaign_id))
        conn.commit()
        conn.close()
        return {'status': 'success'}
    
    @staticmethod
    def get_all():
        """Get all campaigns"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM campaigns ORDER BY created_date DESC')
        campaigns = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return campaigns

class KnowledgeBase:
    @staticmethod
    def add_qa(question, answer, category, app_source, keywords=None):
        """Add Q&A to knowledge base"""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO knowledge_base (question, answer, category, app_source, keywords) VALUES (?, ?, ?, ?, ?)',
                (question, answer, category, app_source, keywords)
            )
            conn.commit()
            qa_id = cursor.lastrowid
            conn.close()
            return {'status': 'success', 'id': qa_id}
        except sqlite3.IntegrityError:
            return {'status': 'error', 'message': 'Question already exists'}
    
    @staticmethod
    def search(query):
        """Search knowledge base"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM knowledge_base WHERE question LIKE ? OR keywords LIKE ? OR answer LIKE ? ORDER BY confidence_score DESC LIMIT 5',
            (f'%{query}%', f'%{query}%', f'%{query}%')
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    @staticmethod
    def get_by_category(category):
        """Get Q&A by category"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM knowledge_base WHERE category = ?', (category,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    @staticmethod
    def get_all():
        """Get all Q&A"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM knowledge_base')
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

class ChatHistory:
    @staticmethod
    def log(contact_phone, user_message, bot_response, matched_qa_id=None, confidence=None):
        """Log chat message"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO chat_history (contact_phone, user_message, bot_response, matched_qa_id, confidence_score) VALUES (?, ?, ?, ?, ?)',
            (contact_phone, user_message, bot_response, matched_qa_id, confidence)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_by_phone(contact_phone, limit=50):
        """Get chat history for contact"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM chat_history WHERE contact_phone = ? ORDER BY timestamp DESC LIMIT ?',
            (contact_phone, limit)
        )
        messages = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return list(reversed(messages))  # Return oldest first

class Analytics:
    @staticmethod
    def record(metric_type, value=1, campaign_id=None):
        """Record analytics metric"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO analytics (metric_type, value, campaign_id) VALUES (?, ?, ?)',
            (metric_type, value, campaign_id)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_stats(days=7):
        """Get analytics stats for last N days"""
        conn = get_db()
        cursor = conn.cursor()
        query = '''
        SELECT metric_type, COUNT(*) as count, SUM(value) as total
        FROM analytics
        WHERE date >= datetime('now', '-' || ? || ' days')
        GROUP BY metric_type
        '''
        cursor.execute(query, (days,))
        stats = {row['metric_type']: {'count': row['count'], 'total': row['total']} 
                for row in cursor.fetchall()}
        conn.close()
        return stats
