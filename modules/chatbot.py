"""
AI Chatbot module with NLP-based response matching
Handles Q&A matching, IVR flows, and conversation management
"""

import re
from difflib import SequenceMatcher
from modules.database import KnowledgeBase, ChatHistory, Analytics

class SimpleNLP:
    """Simple NLP for keyword matching and similarity scoring"""
    
    @staticmethod
    def extract_keywords(text):
        """Extract keywords from text"""
        # Remove special characters and convert to lowercase
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', '', text)
        # Split and remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'am', 'be', 'been',
                      'how', 'what', 'when', 'where', 'why', 'which', 'who', 'do', 'does',
                      'can', 'could', 'should', 'would', 'will', 'may', 'might', 'must',
                      'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'from', 'as',
                      'i', 'me', 'my', 'you', 'your', 'he', 'she', 'it', 'we', 'they'}
        words = [w for w in text.split() if w not in stop_words and len(w) > 2]
        return set(words)
    
    @staticmethod
    def calculate_similarity(text1, text2):
        """Calculate similarity between two texts (0-1)"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    @staticmethod
    def score_match(user_message, qa_item):
        """Score how well a Q&A item matches user message"""
        score = 0
        
        # Direct similarity match
        text_similarity = SimpleNLP.calculate_similarity(user_message, qa_item['question'])
        score += text_similarity * 0.4
        
        # Keyword overlap
        user_keywords = SimpleNLP.extract_keywords(user_message)
        qa_keywords = SimpleNLP.extract_keywords(qa_item['question'])
        if qa_keywords:
            overlap = len(user_keywords & qa_keywords) / len(qa_keywords)
            score += overlap * 0.3
        
        # Answer keyword match
        if qa_item.get('answer'):
            answer_keywords = SimpleNLP.extract_keywords(qa_item['answer'])
            if answer_keywords:
                answer_overlap = len(user_keywords & answer_keywords) / len(answer_keywords)
                score += answer_overlap * 0.2
        
        # Stored keywords match
        if qa_item.get('keywords'):
            stored_keywords = set(qa_item['keywords'].lower().split(','))
            keyword_overlap = len(user_keywords & stored_keywords) / len(stored_keywords) if stored_keywords else 0
            score += keyword_overlap * 0.1
        
        return min(score, 1.0)  # Cap at 1.0

class Chatbot:
    """Main chatbot engine"""
    
    def __init__(self, min_confidence=0.3, app_type=None):
        self.min_confidence = min_confidence
        self.app_type = app_type
        self.nlp = SimpleNLP()
    
    def find_best_match(self, user_message):
        """Find best matching Q&A for user message"""
        all_qa = KnowledgeBase.get_all()
        
        if not all_qa:
            return None, 0
        
        # Score all Q&A items
        scores = []
        for qa in all_qa:
            score = self.nlp.score_match(user_message, qa)
            scores.append((qa, score))
        
        # Return best match if confidence is high enough
        best_match, best_score = max(scores, key=lambda x: x[1])
        
        if best_score >= self.min_confidence:
            return best_match, best_score
        else:
            return None, best_score
    
    def get_response(self, user_message, contact_phone=None):
        """Get chatbot response for user message"""
        # Find best matching Q&A
        matched_qa, confidence = self.find_best_match(user_message)
        
        if matched_qa:
            response = {
                'type': 'answer',
                'text': matched_qa['answer'],
                'question': matched_qa['question'],
                'category': matched_qa['category'],
                'app_source': matched_qa['app_source'],
                'confidence': confidence,
                'matched_qa_id': matched_qa['id']
            }
            # Log the chat
            ChatHistory.log(contact_phone, user_message, matched_qa['answer'], 
                           matched_qa['id'], confidence)
            Analytics.record('chat_message_answered')
        else:
            # No match found
            response = {
                'type': 'fallback',
                'text': self._get_fallback_response(user_message),
                'confidence': 0,
                'matched_qa_id': None
            }
            ChatHistory.log(contact_phone, user_message, response['text'], None, 0)
            Analytics.record('chat_message_unmatched')
        
        return response
    
    def _get_fallback_response(self, user_message):
        """Generate fallback response when no match is found"""
        # Try to identify topic and give relevant direction
        if any(word in user_message.lower() for word in ['customer', 'crm', 'lead', 'opportunity']):
            return "I couldn't find a specific answer about that CRM topic. Please visit /nexora-business or contact support@nexora.com for detailed CRM help."
        elif any(word in user_message.lower() for word in ['invoice', 'accounting', 'books', 'billing']):
            return "For accounting/invoicing help, visit /nexora-business Books module or contact our support team."
        elif any(word in user_message.lower() for word in ['residency', 'visa', 'program', 'investment']):
            return "For residency program information, visit /nexora-investments or use the Smart Eligibility Checker."
        elif any(word in user_message.lower() for word in ['job', 'career', 'employment']):
            return "For job search, try our global job search feature at /nexora-investments/job-search."
        else:
            return "I'm not sure about that. Try asking about Nexora Business Suite, Nexora Investments, residency programs, or CRM features. You can also contact support@nexora.com."
    
    def get_category_responses(self, category):
        """Get all Q&A for a specific category"""
        return KnowledgeBase.get_by_category(category)
    
    def search_knowledge_base(self, query):
        """Search knowledge base for relevant Q&A"""
        return KnowledgeBase.search(query)

class IVRHandler:
    """IVR (Interactive Voice Response) flow handler"""
    
    def __init__(self):
        self.chatbot = Chatbot()
    
    def handle_ivr_flow(self, app_type, selected_option, user_message=None):
        """Handle IVR menu navigation"""
        import json
        from modules.database import get_db
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT flow_data FROM ivr_flow WHERE app_type = ?', (app_type,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {"error": f"IVR flow not found for {app_type}"}
        
        flow_data = json.loads(row['flow_data'])
        
        # Validate option
        if selected_option not in flow_data['menu']:
            return {"error": "Invalid option. Please select from the menu."}
        
        menu_item = flow_data['menu'][selected_option]
        category = menu_item['category']
        
        # Get Q&A for this category
        qa_responses = self.chatbot.get_category_responses(category)
        
        return {
            "menu_title": menu_item['title'],
            "category": category,
            "qa_count": len(qa_responses),
            "sample_questions": [qa['question'] for qa in qa_responses[:5]],
            "help_text": f"Found {len(qa_responses)} help articles for {menu_item['title']}. Type your question now."
        }

class ConversationManager:
    """Manage multi-turn conversations"""
    
    def __init__(self):
        self.chatbot = Chatbot()
        self.conversations = {}  # Store conversation context
    
    def start_conversation(self, contact_phone):
        """Start a new conversation"""
        self.conversations[contact_phone] = {
            'messages': [],
            'context': {},
            'app_type': None
        }
        return "Hi! Welcome to Nexora. How can I help you today?"
    
    def continue_conversation(self, contact_phone, user_message):
        """Continue existing conversation"""
        if contact_phone not in self.conversations:
            return self.start_conversation(contact_phone)
        
        # Get response from chatbot
        response = self.chatbot.get_response(user_message, contact_phone)
        
        # Add to conversation history
        self.conversations[contact_phone]['messages'].append({
            'role': 'user',
            'content': user_message
        })
        self.conversations[contact_phone]['messages'].append({
            'role': 'bot',
            'content': response
        })
        
        return response
    
    def get_conversation_history(self, contact_phone):
        """Get conversation history"""
        if contact_phone not in self.conversations:
            return []
        return self.conversations[contact_phone]['messages']
    
    def clear_conversation(self, contact_phone):
        """Clear conversation history"""
        if contact_phone in self.conversations:
            del self.conversations[contact_phone]

# Global chatbot instance
chatbot = Chatbot()
conversation_manager = ConversationManager()
