# app.py
import os
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


def create_app():
    load_dotenv()  # loads .env (OPENAI_API_KEY, etc.)
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set. Create a .env with OPENAI_API_KEY=...")

    app = Flask(__name__, static_folder="static", template_folder="templates")
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ---- Initialise LLM and agents and attach to app --------------------
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

    # ---- Routes --------------------------------------------------------------
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/api/chat")
    def chat():
        data = request.get_json(silent=True) or {}
        user_msg = (data.get("message") or "").strip()
        agent_name = (data.get("agent") or "chatbot").strip()
        if not user_msg:
            return jsonify({"error": "message is required"}), 400

        try:
            agent = current_app.extensions["agents"][agent_name]
        except KeyError:
            return jsonify({"error": f"unknown agent '{agent_name}'"}), 400

        try:
            reply = agent.reply(user_msg)
            return jsonify({"reply": reply})
        except Exception:
            return jsonify({"error": "chat failed"}), 500

    @app.get("/health")
    def health():
        return {"ok": True, "agents": list(current_app.extensions["agents"].keys())}

    return app


if __name__ == "__main__":
    app = create_app()
    print("Starting Flask on http://localhost:5000")
    app.run(port=5000, debug=True)
