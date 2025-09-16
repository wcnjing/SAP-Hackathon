# app.py
import os
import time
from uuid import uuid4
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, current_app
from flask_cors import CORS

from agents import load_agents

# -----------------------------------------------------------------------------
# Global system prompt 
SYSTEM_PROMPT = """
You are a chatbot in the SAP Company.
Your job is to help the employees in the company with different tasks.
Answer in a concise and professional manner.
If you don't know the answer, say that you don't know. Do NOT make up an answer.
Use UK English.
If you encounter a new employee, welcome them to the company and help them onboard.
""".strip()
# -----------------------------------------------------------------------------

FEATURES = {
    "Onboarding": "Guide new joiners with a week-1 checklist, sandbox + dummy data.",
    "Resources": "Find installers, guides, trainings. Try: resources for 'SAP GUI'.",
    "Acronyms": "Explain company acronyms. Try: what is 'SFSF'?",
    "Who to ask": "Find the person/owner for a topic. Try: who handles dummy data?",
    "Policy Q&A": "Grounded answers with citations (RAG-lite).",
    "Work feedback": "Paste code/docs/slides and say: review this for a Junior Engineer.",
    "Feedback on bot": "Thumbs up/down + notes.",
}

def render_help() -> str:
    lines = ["Here's what I can do:\n"]
    for k, v in FEATURES.items():
        lines.append(f"• {k} — {v}")
    lines.append("\nTips: say \"I just joined\" to start onboarding, or type /help anytime.")
    return "\n".join(lines)


def create_app():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set. Create a .env with OPENAI_API_KEY=...")

    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize LLM and agents
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY")
    )


    app.extensions = getattr(app, "extensions", {})
    app.extensions["llm"] = llm
    app.extensions["system_prompt"] = SYSTEM_PROMPT
    app.extensions["agents"] = load_agents(llm=llm, system_prompt=SYSTEM_PROMPT)
    app.extensions["metrics"] = {"tool_calls": 0}  # Initialize metrics for tools

    # Routes
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/help", methods=["GET"])
    def api_help():
        return jsonify({"features": FEATURES, "text": render_help()})

    @app.route("/api/clear", methods=["POST"])
    def clear_chat():
        """Clear chat history for all agents"""
        try:
            for agent_name, agent in current_app.extensions["agents"].items():
                if hasattr(agent, 'clear_history'):
                    agent.clear_history()
            return jsonify({"message": "Chat cleared successfully"})
        except Exception as e:
            return jsonify({"error": f"Failed to clear chat: {str(e)}"}), 500

    @app.route("/api/chat", methods=["POST"])
    def chat():
        try:
            data = request.get_json(silent=True) or {}
            user_msg = (data.get("message") or "").strip()
            agent_name = (data.get("agent") or "chatbot").strip()
            session_id = data.get("session_id") or str(uuid4())

            if not user_msg:
                return jsonify({"error": "message is required"}), 400

            # Handle slash commands
            if user_msg.lower() in ("/help", "help"):
                return jsonify({
                    "reply": render_help(),
                    "session_id": session_id
                })

            # Handle special onboarding triggers
            if any(phrase in user_msg.lower() for phrase in ["i just joined", "i'm new", "new employee", "just started"]):
                user_msg = f"New employee onboarding help: {user_msg}"

            # Get the agent
            try:
                agent = current_app.extensions["agents"][agent_name]
            except KeyError:
                available_agents = list(current_app.extensions["agents"].keys())
                return jsonify({
                    "error": f"Unknown agent '{agent_name}'. Available agents: {available_agents}"
                }), 400

            # Get response from agent
            reply = agent.reply(user_msg)

            return jsonify({
                "reply": reply,
                "session_id": session_id,
                "agent": agent_name
            })

        except Exception as e:
            print(f"Chat error: {str(e)}")
            return jsonify({"error": "Chat failed. Please try again."}), 500

    @app.route("/api/feedback", methods=["POST"])
    def feedback():
        """Handle user feedback on bot responses"""
        try:
            data = request.get_json(silent=True) or {}
            rating = data.get("rating")
            message = data.get("message", "")
            session_id = data.get("session_id", "unknown")
            
            feedback_data = {
                "session_id": session_id,
                "rating": rating,
                "message": message,
                "timestamp": time.time()
            }
            
            print(f"Feedback received: {feedback_data}")
            return jsonify({"message": "Thank you for your feedback!"})
            
        except Exception as e:
            return jsonify({"error": "Failed to record feedback"}), 500

    @app.route("/health", methods=["GET"])
    def health():
        try:
            agents_status = {}
            for name, agent in current_app.extensions["agents"].items():
                agents_status[name] = {
                    "available": True,
                    "type": type(agent).__name__
                }
            
            return jsonify({
                "ok": True,
                "agents": agents_status,
                "features": list(FEATURES.keys()),
                "tool_calls": current_app.extensions["metrics"]["tool_calls"]
            })
        except Exception as e:
            return jsonify({"ok": False, "error": str(e)}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    print("🚀 Starting SAP Chatbot on http://localhost:5000")
    print("📋 Available features:", ", ".join(FEATURES.keys()))
    app.run(host="0.0.0.0", port=5000, debug=True)