import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Ollama API setup
API_KEY = os.getenv("OLLAMA_API_KEY")
OLLAMA_API_URL = "https://ollama.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# ------------------------------
# HTML Loader & Cleaner
# ------------------------------
def load_html_content(filename="index.html"):
    """Load the HTML file and extract readable text."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            html_text = f.read()
        # Remove scripts and styles
        soup = BeautifulSoup(html_text, "html.parser")
        for s in soup(["script", "style"]):
            s.extract()
        # Extract clean text
        text = soup.get_text(separator="\n")
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        return text
    except Exception as e:
        return "Error loading website content."

# ------------------------------
# AI Answer Generator
# ------------------------------
def ai_generate_answer(question, context_text):
    if not API_KEY:
        return "System Error: Ollama API Key missing."

    system_instruction = f"""
You are ChatDIS, the official and friendly AI assistant for Dunes International School (DIS), Abu Dhabi.

GUIDELINES:
1. Use the PROVIDED CONTEXT below to answer the user's question accurately.
2. If the answer is in the context, be specific (mention timings, dates, and contact info).
3. If the answer is NOT in the context, politely state that you don't have that specific information and suggest contacting the school office at +971 2 552 7527.
4. Keep the tone professional, welcoming, and helpful.
5. Use bullet points for lists and bold text for important details.

WEBSITE CONTEXT:
{context_text}
"""

    payload = {
        "model": "gemini-3-flash-preview",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": question}
        ],
        "temperature": 0.5
    }

    try:
        response = requests.post(OLLAMA_API_URL, headers=HEADERS, json=payload)
        if response.status_code != 200:
            return f"API Error {response.status_code}: {response.text}"

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0].get("message", {}).get("content", "No content returned")

        return f"Unexpected API response: {result}"

    except Exception as e:
        return f"Connection Error: {str(e)}"

# ------------------------------
# Flask Routes
# ------------------------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_question = request.json.get("question", "").strip()
    # Load and clean HTML content each time
    website_text = load_html_content("index.html")
    answer = ai_generate_answer(user_question, website_text)
    return jsonify({"answer": answer})

# ------------------------------
# Run Server
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)
