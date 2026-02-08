"""
Knowledge base initialization with Q&A data from Nexora Business Suite and Nexora Investments
"""

from modules.database import KnowledgeBase, get_db

# Q&A Data from both apps
KNOWLEDGE_BASE_DATA = [
    # Nexora Business Suite - General
    {
        "question": "What is Nexora Business Suite?",
        "answer": "Nexora Business Suite is a comprehensive, all-in-one business management platform that includes CRM, accounting, inventory, payroll, HR, projects, POS, helpdesk support, and payments.",
        "category": "General",
        "app_source": "Nexora Business",
        "keywords": "platform, features, overview"
    },
    {
        "question": "What modules are included in Nexora Business Suite?",
        "answer": "Nexora includes: CRM (customers, leads, opportunities), Books (accounting, invoices), Inventory (stock management), Payroll (salary automation), HR (employees, attendance), Projects (tasks, teams), POS (sales), Desk (support tickets), and Pay (payments & billing).",
        "category": "Features",
        "app_source": "Nexora Business",
        "keywords": "modules, features, components"
    },
    {
        "question": "How do I manage customers in Nexora CRM?",
        "answer": "In Nexora CRM, go to Customers section. You can add new customers, track their information, manage leads, opportunities, and view account history. Use the search function to find customers quickly.",
        "category": "CRM",
        "app_source": "Nexora Business",
        "keywords": "customer, CRM, manage"
    },
    {
        "question": "How do I create an invoice?",
        "answer": "Go to Books → Invoices → Create Invoice. Fill in customer details, add line items, set payment terms, and generate PDF. Invoices are automatically sequenced and saved.",
        "category": "Accounting",
        "app_source": "Nexora Business",
        "keywords": "invoice, accounting, billing"
    },
    {
        "question": "Can I track inventory stock levels?",
        "answer": "Yes! Nexora Inventory tracks stock levels across multiple warehouses. Set minimum stock alerts, track stock transactions, and get automated low-stock notifications.",
        "category": "Inventory",
        "app_source": "Nexora Business",
        "keywords": "inventory, stock, warehouse"
    },
    {
        "question": "How do I manage employee payroll?",
        "answer": "In Nexora Payroll, add employees, set salaries, track attendance, and auto-generate payslips. Payroll calculations are automated and compliant.",
        "category": "Payroll",
        "app_source": "Nexora Business",
        "keywords": "payroll, salary, employee"
    },
    {
        "question": "How do I create a project and assign tasks?",
        "answer": "Go to Projects → Create Project. Add project details, create tasks, assign to team members, set deadlines. Track progress and dependencies in real-time.",
        "category": "Projects",
        "app_source": "Nexora Business",
        "keywords": "project, task, team"
    },
    {
        "question": "How do I handle customer support tickets?",
        "answer": "Use Nexora Desk to manage support tickets. Create tickets, assign to team, track status, add notes, and resolve issues. All communication is logged.",
        "category": "Support",
        "app_source": "Nexora Business",
        "keywords": "support, ticket, helpdesk"
    },
    {
        "question": "How do I process payments?",
        "answer": "In Nexora Pay, you can process payments, create payment records, track invoices, and generate billing reports. Multiple payment methods are supported.",
        "category": "Payments",
        "app_source": "Nexora Business",
        "keywords": "payment, billing, transaction"
    },
    {
        "question": "Does Nexora support multiple user roles?",
        "answer": "Yes! Nexora has role-based access control (RBAC). Assign roles like Admin, Manager, User, and customize permissions for each role.",
        "category": "Security",
        "app_source": "Nexora Business",
        "keywords": "role, permission, access"
    },
    
    # Nexora Investments - Residency Programs
    {
        "question": "What is Nexora Investments?",
        "answer": "Nexora Investments is a global residency and investment platform helping users discover, compare, and apply for residency programs and investment opportunities worldwide across 46 countries.",
        "category": "General",
        "app_source": "Nexora Investments",
        "keywords": "residency, investment, visa"
    },
    {
        "question": "How many countries and programs are available?",
        "answer": "Nexora has 75+ investment programs across 46 countries worldwide. Programs include residency by investment, visa sponsorship, work permits, and citizenship paths.",
        "category": "Programs",
        "app_source": "Nexora Investments",
        "keywords": "countries, programs, options"
    },
    {
        "question": "How do I find a residency program that matches my budget?",
        "answer": "Use the Smart Eligibility Checker. Enter your investment budget, annual income, citizenship requirements, and preferred countries. The system will recommend top 5 matching programs.",
        "category": "Eligibility",
        "app_source": "Nexora Investments",
        "keywords": "eligibility, budget, match"
    },
    {
        "question": "Can I compare multiple residency programs?",
        "answer": "Yes! Use the Program Comparison Tool. Select multiple programs and compare investment requirements, processing times, family benefits, visa-free access, and other key factors side-by-side.",
        "category": "Comparison",
        "app_source": "Nexora Investments",
        "keywords": "compare, programs, analysis"
    },
    {
        "question": "How does the ROI calculator work?",
        "answer": "Enter your investment amount, expected return percentage, and time period. The calculator shows total profit, final value, cost breakdown, and investment analysis.",
        "category": "Tools",
        "app_source": "Nexora Investments",
        "keywords": "ROI, calculator, investment"
    },
    {
        "question": "What is the global job search feature?",
        "answer": "Nexora integrates with CareerJet to provide global job search across 50+ countries. Filter by location, industry, salary, and apply directly through the platform.",
        "category": "Jobs",
        "app_source": "Nexora Investments",
        "keywords": "job, search, career"
    },
    {
        "question": "How do I connect with immigration consultants?",
        "answer": "Browse the Consultant Directory to find verified immigration experts. View their profiles, ratings, experience, and book consultations directly through Nexora.",
        "category": "Services",
        "app_source": "Nexora Investments",
        "keywords": "consultant, expert, immigration"
    },
    {
        "question": "Can I track my residency application?",
        "answer": "Yes! Nexora provides an Application Dashboard where you can track all residency applications, upload required documents, monitor progress, and receive status updates.",
        "category": "Applications",
        "app_source": "Nexora Investments",
        "keywords": "application, tracking, documents"
    },
    {
        "question": "What currencies are supported?",
        "answer": "Nexora supports 8 major currencies (USD, EUR, GBP, CAD, AUD, SGD, AED, INR) with real-time conversion rates for investment calculations.",
        "category": "Tools",
        "app_source": "Nexora Investments",
        "keywords": "currency, conversion, payment"
    },
    {
        "question": "Is there a blog or educational content?",
        "answer": "Yes! Nexora Blog provides guides, case studies, immigration tips, success stories, and visa/residency information to help users make informed decisions.",
        "category": "Resources",
        "app_source": "Nexora Investments",
        "keywords": "blog, education, guides"
    },
    
    # Common questions
    {
        "question": "How do I reset my password?",
        "answer": "Click 'Forgot Password' on the login page. Enter your email, and we'll send a password reset link. Click the link and create a new password.",
        "category": "Account",
        "app_source": "Both",
        "keywords": "password, reset, account"
    },
    {
        "question": "Is my data secure?",
        "answer": "Yes! Both Nexora platforms use encryption, secure authentication, CSRF protection, and follow security best practices. Your data is protected and never shared.",
        "category": "Security",
        "app_source": "Both",
        "keywords": "security, privacy, data"
    },
    {
        "question": "How do I contact support?",
        "answer": "Visit our support page or email support@nexora.com. Our team typically responds within 24 hours. For Nexora Business, use the Desk module for internal tickets.",
        "category": "Support",
        "app_source": "Both",
        "keywords": "support, help, contact"
    },
    {
        "question": "Can I export my data?",
        "answer": "Yes! You can export reports, invoices, and data as PDF or CSV from most modules. This data can be used for backups or importing to other systems.",
        "category": "Data",
        "app_source": "Both",
        "keywords": "export, download, report"
    },
    {
        "question": "Do you offer training or documentation?",
        "answer": "Yes! Comprehensive documentation, video tutorials, and quick start guides are available. For enterprise customers, we offer onboarding training.",
        "category": "Resources",
        "app_source": "Both",
        "keywords": "training, documentation, help"
    },
    {
        "question": "What are your pricing plans?",
        "answer": "Both Nexora products offer flexible pricing. Nexora Business has subscription tiers by features. Nexora Investments has usage-based and consultation fees. Contact sales for details.",
        "category": "Pricing",
        "app_source": "Both",
        "keywords": "price, cost, payment"
    },
    {
        "question": "Do you support multiple languages?",
        "answer": "Nexora Business supports English, Romanian, Spanish, and Portuguese. Nexora Investments supports English with multi-language expansion planned.",
        "category": "Features",
        "app_source": "Both",
        "keywords": "language, localization"
    },
    {
        "question": "Can I integrate with other tools?",
        "answer": "Nexora Business provides API endpoints and webhooks for integration. Nexora Investments integrates with CareerJet for job search and supports document imports.",
        "category": "Integration",
        "app_source": "Both",
        "keywords": "API, integration, webhook"
    },
]

def init_knowledge_base():
    """Initialize knowledge base with predefined Q&A data"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if already initialized
    cursor.execute('SELECT COUNT(*) as count FROM knowledge_base')
    if cursor.fetchone()['count'] > 0:
        print("✅ Knowledge base already initialized")
        conn.close()
        return
    
    # Add all Q&A pairs
    added = 0
    for qa in KNOWLEDGE_BASE_DATA:
        result = KnowledgeBase.add_qa(
            question=qa['question'],
            answer=qa['answer'],
            category=qa['category'],
            app_source=qa['app_source'],
            keywords=qa['keywords']
        )
        if result['status'] == 'success':
            added += 1
    
    conn.close()
    print(f"✅ Initialized knowledge base with {added} Q&A pairs")
    return added

# IVR Flow configurations
IVR_FLOWS = {
    "nexora_business": {
        "name": "Nexora Business Support",
        "greeting": "Welcome to Nexora Business Suite. Press 1 for CRM help, 2 for Accounting, 3 for Inventory, 4 for Payroll, 5 for Human Resources, 6 for Projects, 0 for General Help",
        "menu": {
            "1": {"title": "CRM", "category": "CRM"},
            "2": {"title": "Accounting", "category": "Accounting"},
            "3": {"title": "Inventory", "category": "Inventory"},
            "4": {"title": "Payroll", "category": "Payroll"},
            "5": {"title": "HR", "category": "HR"},
            "6": {"title": "Projects", "category": "Projects"},
            "0": {"title": "General Help", "category": "General"}
        }
    },
    "nexora_investments": {
        "name": "Nexora Investments Support",
        "greeting": "Welcome to Nexora Investments. Press 1 to find residency programs, 2 for ROI calculator, 3 to find consultants, 4 to check eligibility, 5 for job search, 0 for General Help",
        "menu": {
            "1": {"title": "Residency Programs", "category": "Programs"},
            "2": {"title": "ROI Calculator", "category": "Tools"},
            "3": {"title": "Find Consultants", "category": "Services"},
            "4": {"title": "Check Eligibility", "category": "Eligibility"},
            "5": {"title": "Job Search", "category": "Jobs"},
            "0": {"title": "General Help", "category": "General"}
        }
    }
}

def init_ivr_flows():
    """Initialize IVR flow configurations"""
    import json
    conn = get_db()
    cursor = conn.cursor()
    
    for flow_key, flow_data in IVR_FLOWS.items():
        try:
            cursor.execute(
                'INSERT INTO ivr_flow (flow_name, flow_data, app_type) VALUES (?, ?, ?)',
                (flow_data['name'], json.dumps(flow_data), flow_key)
            )
        except:
            pass  # Already exists
    
    conn.commit()
    conn.close()
