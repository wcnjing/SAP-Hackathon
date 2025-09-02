# app.py
from flask import Flask, send_from_directory
from flask_cors import CORS
import os
import getpass
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

app = Flask(__name__, static_folder="public")
CORS(app)

@app.route("/")
def index():
    return send_from_directory("public", "index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    return {"reply": "Hello from Flask 👋"}

if __name__ == "__main__":
    print("Starting Flask on http://localhost:5000")
    app.run(port=5000, debug=True)

api_key = os.getenv("OPENAI_API_KEY")

if not os.environ.get("OPENAI_API_KEY"):
  os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

model = init_chat_model("gpt-4o-mini", model_provider="openai")