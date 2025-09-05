import streamlit as st
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    st.error("🚨 GOOGLE_API_KEY not found! Please set it in your .env file.")
else:
    genai.configure(api_key=api_key)

# Define model
model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="OHS Safety Agent", page_icon="🦺", layout="wide")

st.markdown(
    """
    <style>
    .main {
        background-color: #f9fafb;
    }

    h1 {
        color: #2563eb;
        text-align: center;
        font-weight: 700;
        margin-bottom: 20px;
    }

    /* Section headers */
    h2 {
        color: #1e3a8a;
        border-left: 5px solid #2563eb;
        padding-left: 10px;
        margin-top: 30px;
    }

    .card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    .hazard-box {
        background: #fff7ed;
        border-left: 6px solid #f97316;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
    }

    .chat-user {
        background: #dbeafe;
        padding: 12px;
        border-radius: 12px;
        margin: 5px 0;
    }
    .chat-assistant {
        background: #dcfce7;
        padding: 12px;
        border-radius: 12px;
        margin: 5px 0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

SYSTEM_PROMPT = """
You are a specialized Occupational Health & Safety (OHS) AI Agent.
- Only answer questions related to Occupational Health & Safety.
- Reject all unrelated topics (sports, celebrities, random facts).
- When analyzing hazards, return structured JSON.
- When chatting, provide clear workplace safety advice.
"""

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "user", "parts": [{"text": SYSTEM_PROMPT}]}
    ]

def run_agent(user_prompt, structured=False):
    """Run the OHS Agent with structured or conversational output."""
    if structured:
        prompt = f"""
        {SYSTEM_PROMPT}

        Analyze the workplace and return JSON:
        {{
            "workplace_type": "...",
            "employees_count": ...,
            "hazards": [
                {{
                    "hazard": "...",
                    "category": "...",
                    "risk_level": "...",
                    "recommended_measures": "..."
                }}
            ]
        }}

        Workplace details:
        {user_prompt}
        """
        response = model.generate_content(prompt)
        return response.text
    else:
        conversation = st.session_state.messages + [
            {"role": "user", "parts": [{"text": user_prompt}]}
        ]
        response = model.generate_content(conversation)
        return response.text

def guardrails(user_input: str) -> str | None:
    """Block questions unrelated to OHS."""
    allowed_keywords = [
        "safety", "hazard", "workplace", "health", "ohs", "training",
        "risk", "accident", "emergency", "ppe", "regulations", "injury"
    ]
    if not any(word in user_input.lower() for word in allowed_keywords):
        return "⚠️ I can only answer questions related to Occupational Health & Safety."
    return None

st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Go to", ["🏠 Dashboard", "📝 Hazard Assessment", "💬 Safety Chat"])

if page == "🏠 Dashboard":
    st.markdown("<h1>🦺 OHS Safety Dashboard</h1>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='card'><h3>📊 Reports</h3><p>View workplace hazard reports</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='card'><h3>🧑‍🏫 Training</h3><p>Access safety training material</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='card'><h3>🚨 Alerts</h3><p>Track incidents & risks</p></div>", unsafe_allow_html=True)

elif page == "📝 Hazard Assessment":
    st.markdown("<h1>📝 Hazard Assessment Tool</h1>", unsafe_allow_html=True)

    with st.form("hazard_form"):
        workplace_type = st.text_input("🏭 Workplace Type", placeholder="e.g., Factory, Office, Construction Site")
        employees_count = st.number_input("👥 Number of Employees", min_value=1, step=1)
        hazards_description = st.text_area("⚠️ Hazards or Environment", placeholder="e.g., Noise, Dust, Slippery floors")
        submitted = st.form_submit_button("🔍 Analyze Hazards")

    if submitted:
        hazard_input = f"Workplace: {workplace_type}, Employees: {employees_count}, Hazards: {hazards_description}"

        block = guardrails(hazard_input)
        if block:
            st.warning(block)
        else:
            try:
                with st.spinner("🔎 Analyzing workplace hazards..."):
                    response_text = run_agent(hazard_input, structured=True)

                st.subheader("📊 Hazard Assessment Results")

                try:
                    json_response = json.loads(response_text)
                    for hz in json_response.get("hazards", []):
                        st.markdown(
                            f"<div class='hazard-box'><b>Hazard:</b> {hz['hazard']}<br>"
                            f"<b>Category:</b> {hz['category']}<br>"
                            f"<b>Risk Level:</b> {hz['risk_level']}<br>"
                            f"<b>Measures:</b> {hz['recommended_measures']}</div>",
                            unsafe_allow_html=True
                        )
                    st.success("✅ Hazard analysis completed successfully.")
                except json.JSONDecodeError:
                    st.error("⚠️ Invalid JSON response from AI. Showing raw output:")
                    st.code(response_text)

            except Exception as e:
                st.error(f"❌ Error: {e}")

elif page == "💬 Safety Chat":
    st.markdown("<h1>💬 OHS Safety Chat</h1>", unsafe_allow_html=True)

    for message in st.session_state.messages[1:]:
        if message["role"] == "user":
            st.markdown(f"<div class='chat-user'>👤 {message['parts'][0]['text']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-assistant'>🤖 {message['parts'][0]['text']}</div>", unsafe_allow_html=True)

    if user_input := st.chat_input("Ask the OHS Agent a question..."):
        block = guardrails(user_input)
        st.session_state.messages.append({"role": "user", "parts": [{"text": user_input}]})
        st.markdown(f"<div class='chat-user'>👤 {user_input}</div>", unsafe_allow_html=True)

        if block:
            st.session_state.messages.append({"role": "model", "parts": [{"text": block}]})
            st.markdown(f"<div class='chat-assistant'>🤖 {block}</div>", unsafe_allow_html=True)
        else:
            try:
                response_text = run_agent(user_input, structured=False)
                st.session_state.messages.append({"role": "model", "parts": [{"text": response_text}]})
                st.markdown(f"<div class='chat-assistant'>🤖 {response_text}</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ Error: {e}")
