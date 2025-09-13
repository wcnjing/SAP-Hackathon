from langchain_core.tools import Tool
from typing import List
from pathlib import Path
import json
import time
from typing import Dict, Any, Optional
from langchain_core.tools import tool

# Data storage setup
DATA = Path("data")
DATA.mkdir(exist_ok=True)
STORE = DATA / "onboarding.json"
BASE = Path("data")  # For the new tools

def _load_file(p): 
    """Load JSON file from data directory"""
    fp = BASE / p
    return json.loads(fp.read_text(encoding="utf-8")) if fp.exists() else []

# Default onboarding checklist
DEFAULT_CHECKLIST = [
    {"id": "d1-setup", "title": "Day 1: Laptop, SSO, email, chat", "done": False},
    {"id": "join-channels", "title": "Join team channels & calendars", "done": False},
    {"id": "install-tools", "title": "Install dev/tools (IDE, VPN, ticketing)", "done": False},
    {"id": "sandbox", "title": "Request sandbox access", "done": False},
    {"id": "train-sec", "title": "Security Awareness training", "done": False},
    {"id": "train-data", "title": "Data Protection training", "done": False},
    {"id": "dummy", "title": "Get dummy data in sandbox", "done": False},
    {"id": "demo", "title": "5-min end-of-week demo", "done": False},
]

def _load() -> Dict[str, Any]:
    if STORE.exists():
        return json.loads(STORE.read_text(encoding="utf-8"))
    return {}

def _save(db: Dict[str, Any]):
    STORE.write_text(json.dumps(db, indent=2), encoding="utf-8")

def _ensure_user(db, user: str):
    if user not in db:
        db[user] = {"checklist": DEFAULT_CHECKLIST.copy(), "history": []}

# NEW TOOLS - Using @tool decorator as in your example
@tool
def acronym_meaning(key: str) -> str:
    """Return the meaning of a company acronym."""
    for row in _load_file("acronyms.json"):
        if row["key"].lower() == key.lower():
            try: 
                from flask import current_app
                current_app.extensions["metrics"]["tool_calls"] += 1
            except Exception: 
                pass
            return f"{row['key']} = {row['value']}"
    return f"No entry for '{key}'. Try common ones like 'SFSF', 'S4H', 'EC', 'BTP'."

@tool
def who_to_ask(topic: str) -> str:
    """Return the person in charge for a topic."""
    for row in _load_file("contacts.json"):
        if topic.lower() in row["topic"].lower():
            try: 
                from flask import current_app
                current_app.extensions["metrics"]["tool_calls"] += 1
            except Exception: 
                pass
            return f"{row['topic'].title()}: {row['name']} ({row.get('contact','n/a')})"
    return f"I couldn't find an owner for '{topic}'—try topics like 'dummy data', 'sandbox', 'training', or 'onboarding'."

@tool
def find_docs(query: str, limit: int = 3) -> str:
    """Find relevant docs by keyword. Returns a short bulleted list."""
    items = _load_file("docs.json")
    q = query.lower()
    hits: List[str] = []
    for row in items:
        if q in row["title"].lower() or any(q in t.lower() for t in row.get("tags", [])):
            hits.append(f"- {row['title']} — {row['link']}")
            if len(hits) >= limit: 
                break
    if not hits:
        return f"No docs matched '{query}'. Try terms like 'SAP GUI', 'installation', 'training', or 'setup'."
    try: 
        from flask import current_app
        current_app.extensions["metrics"]["tool_calls"] += 1
    except Exception: 
        pass
    return "\n".join(hits)

# EXISTING ONBOARDING FUNCTIONS
def get_onboarding_checklist(user: str) -> str:
    """Return the user's onboarding checklist as formatted text."""
    db = _load()
    _ensure_user(db, user)
    
    checklist = db[user]["checklist"]
    result = "Your Onboarding Checklist:\n\n"
    
    for item in checklist:
        status = "✅" if item["done"] else "⭕"
        result += f"{status} {item['title']}\n"
    
    completed = sum(1 for item in checklist if item["done"])
    total = len(checklist)
    result += f"\nProgress: {completed}/{total} completed"
    
    return result

def mark_onboarding_step(user_and_step: str) -> str:
    """Mark a checklist step as done. Format: 'username:step_id' or 'username:step_id:done/undone'"""
    parts = user_and_step.split(":")
    if len(parts) < 2:
        return "Format: 'username:step_id' or 'username:step_id:done'"
    
    user = parts[0]
    step_id = parts[1]
    done = True if len(parts) == 2 else parts[2].lower() in ["done", "true", "yes"]
    
    db = _load()
    _ensure_user(db, user)
    
    for s in db[user]["checklist"]:
        if s["id"] == step_id:
            s["done"] = bool(done)
            db[user]["history"].append({
                "ts": time.time(), 
                "step": step_id, 
                "done": done
            })
            _save(db)
            return f"✅ Step '{s['title']}' marked {'done' if done else 'not done'}."
    
    return f"❌ Step '{step_id}' not found. Available steps: {', '.join([s['id'] for s in db[user]['checklist']])}"

def request_sandbox_access(user: str) -> str:
    """Create a sandbox access request for the user."""
    db = _load()
    _ensure_user(db, user)
    
    ticket_id = f"SANDBOX-{int(time.time())}"
    db[user]["history"].append({
        "ts": time.time(), 
        "action": "sandbox_request", 
        "ticket": ticket_id
    })
    _save(db)
    
    return f"🎫 Sandbox access requested! Ticket: {ticket_id}\n📅 Expected within 1 business day.\n💡 You'll receive an email when it's ready."

def request_dummy_data(query: str) -> str:
    """Request dummy data for sandbox. Format: 'username' or 'username:dataset:size'"""
    parts = query.split(":")
    user = parts[0] if parts else "unknown"
    dataset = parts[1] if len(parts) > 1 else "sample_orders"
    size = parts[2] if len(parts) > 2 else "small"
    
    req_id = f"DUMMY-{int(time.time())}"
    
    db = _load()
    _ensure_user(db, user)
    db[user]["history"].append({
        "ts": time.time(), 
        "action": "dummy_data", 
        "dataset": dataset, 
        "size": size, 
        "req": req_id
    })
    _save(db)
    
    return f"📊 Dummy data requested!\n🎫 Request ID: {req_id}\n📋 Dataset: {dataset} ({size})\n👤 Notifying Jean from Data Team\n⚠️  Reminder: Use sandbox only - no PII allowed!"

# SAP Company info functions
def get_company_info(query: str) -> str:
    """Retrieve SAP company-specific information"""
    sap_info = {
        "about": "SAP is a German multinational software corporation that makes enterprise software to manage business operations and customer relations.",
        "founded": "1972",
        "headquarters": "Walldorf, Germany", 
        "employees": "Over 100,000 worldwide",
        "products": ["SAP S/4HANA", "SAP SuccessFactors", "SAP Concur", "SAP Ariba", "SAP Fieldglass"]
    }
    
    query_lower = query.lower()
    
    if "about" in query_lower or "what is sap" in query_lower:
        return sap_info["about"]
    elif "founded" in query_lower or "history" in query_lower:
        return f"SAP was founded in {sap_info['founded']}"
    elif "headquarters" in query_lower or "location" in query_lower:
        return f"SAP headquarters are in {sap_info['headquarters']}"
    elif "employees" in query_lower or "staff" in query_lower:
        return f"SAP has {sap_info['employees']}"
    elif "products" in query_lower or "software" in query_lower:
        return f"Main SAP products include: {', '.join(sap_info['products'])}"
    else:
        return f"Here's some information about SAP related to: {query}. Ask me more specific questions about our history, products, or company details!"

def get_hr_policies(query: str) -> str:
    """Retrieve HR policies and employee handbook information"""
    hr_topics = {
        "holiday": "SAP employees are entitled to 25 days annual leave plus public holidays. Holiday requests should be submitted via the HR portal at least 2 weeks in advance.",
        "sick leave": "Employees should notify their manager and HR within 24 hours of absence. Medical certificates required for absences longer than 3 days.",
        "working hours": "Standard working hours are 37.5 hours per week, typically 9:00-17:30 with flexible start times between 8:00-10:00.",
        "remote work": "Hybrid working is supported with up to 3 days per week remote work. Speak to your line manager to arrange.",
        "benefits": "SAP offers comprehensive benefits including health insurance, pension scheme, life insurance, and employee share purchase plan."
    }
    
    query_lower = query.lower()
    for topic, info in hr_topics.items():
        if topic in query_lower:
            return info
    
    return "I can help with information about holidays, sick leave, working hours, remote work, and benefits. What specific HR topic would you like to know about?"

def get_it_support(query: str) -> str:
    """Provide IT support information and troubleshooting"""
    it_help = {
        "password": "To reset your password, visit the IT self-service portal or contact the IT helpdesk on ext. 2200.",
        "wifi": "Connect to 'SAP-Corporate' network using your domain credentials. For guest access, use 'SAP-Guest' with the daily password from reception.",
        "laptop": "For laptop issues, log a ticket via the IT portal or call ext. 2200. Emergency laptop loans available from IT desk (Floor 2).",
        "software": "Software installation requests must go through the IT portal. Standard business software is pre-approved.",
        "vpn": "VPN access is automatically configured on company laptops. For personal devices, download SAP VPN client from the IT portal."
    }
    
    query_lower = query.lower()
    for topic, info in it_help.items():
        if topic in query_lower:
            return info
    
    return "I can help with password resets, WiFi, laptop issues, software installation, and VPN access. What IT issue can I help you with?"

def load_tools() -> List[Tool]:
    """Load and return all available tools for the SAP chatbot."""
    tools = [
        # New tools using @tool decorator - convert to Tool objects
        Tool(
            name="acronym_meaning",
            description="Get the meaning of SAP company acronyms like SFSF, S4H, EC, BTP, etc.",
            func=lambda x: acronym_meaning.invoke({"key": x})
        ),
        Tool(
            name="who_to_ask",
            description="Find the person/team responsible for a topic like 'dummy data', 'sandbox access', 'training'",
            func=lambda x: who_to_ask.invoke({"topic": x})
        ),
        Tool(
            name="find_docs",
            description="Search for documentation, guides, or resources by keyword",
            func=lambda x: find_docs.invoke({"query": x, "limit": 3})
        ),
        # Existing onboarding tools
        Tool(
            name="get_onboarding_checklist",
            description="Get a new employee's onboarding checklist and progress. Use their username/email.",
            func=get_onboarding_checklist
        ),
        Tool(
            name="mark_onboarding_step", 
            description="Mark an onboarding step as complete. Format: 'username:step_id' (step_id like 'd1-setup', 'sandbox', etc.)",
            func=mark_onboarding_step
        ),
        Tool(
            name="request_sandbox_access",
            description="Request sandbox/development environment access for a new employee. Use their username.",
            func=request_sandbox_access
        ),
        Tool(
            name="request_dummy_data",
            description="Request dummy/test data for sandbox environment. Format: 'username' or 'username:dataset:size'",
            func=request_dummy_data
        ),
        # Company info tools
        Tool(
            name="company_info",
            description="Get information about SAP company, history, products, and general company details",
            func=get_company_info
        ),
        Tool(
            name="hr_policies", 
            description="Retrieve HR policies, employee benefits, holiday information, working hours, and employee handbook details",
            func=get_hr_policies
        ),
        Tool(
            name="it_support",
            description="Get IT support information, troubleshooting help, password resets, WiFi, laptop issues, and software installation",
            func=get_it_support
        )
    ]
    
    return tools