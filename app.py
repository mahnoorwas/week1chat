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

model = genai.GenerativeModel("gemini-1.5-flash")

st.set_page_config(page_title="OHS Hazard Assessment", page_icon="⚠️", layout="wide")


st.title("⚠️ Occupational Health & Safety AI Advisor")
st.markdown("""
This AI-powered tool helps identify **workplace hazards** and provides recommendations
based on the **Occupational Health & Safety (OHS)** framework.
""")

# -------------------------
# Input Form
# -------------------------
st.header("📝 Workplace Details")
with st.form("hazard_form"):
    workplace_type = st.text_input("🏭 Workplace Type", placeholder="e.g., Construction Site, Office, Factory")
    employees_count = st.number_input("👥 Number of Employees", min_value=1, step=1)
    hazards_description = st.text_area("⚠️ Describe Hazards or Environment", placeholder="e.g., Noise, Dust, Slippery floors")
    submitted = st.form_submit_button("🔍 Analyze Hazards")

if submitted:
    if not api_key:
        st.error("🚨 API key not found.")
    else:
        prompt = f"""
        You are an advanced Occupational Health & Safety (OHS) AI.
        Analyze the following workplace and provide a detailed report in a **single JSON object**.
        The JSON object should have the following structure:
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
        
        Do not include any other text, greetings, or explanations outside the JSON object.
        
        Workplace Type: {workplace_type}
        Number of Employees: {employees_count}
        Hazards: {hazards_description}
        """

        try:
            with st.spinner("🔍 Analyzing workplace hazards..."):
                response = model.generate_content(prompt)
                
            st.subheader("📊 Hazard Assessment Results")
            
            # Attempt to parse the response as JSON
            json_response = json.loads(response.text)
            
            # Display the workplace details
            st.write(f"**Workplace Type:** {json_response.get('workplace_type', 'N/A')}")
            st.write(f"**Number of Employees:** {json_response.get('employees_count', 'N/A')}")
            
            st.markdown("### Identified Hazards")
            
            # Display each hazard in a collapsible expander
            for hazard_info in json_response.get('hazards', []):
                with st.expander(f"**{hazard_info.get('hazard', 'Unknown Hazard')}**"):
                    st.write(f"**Category:** {hazard_info.get('category', 'N/A')}")
                    st.write(f"**Risk Level:** {hazard_info.get('risk_level', 'N/A')}")
                    st.write(f"**Recommended Measures:** {hazard_info.get('recommended_measures', 'N/A')}")

        except json.JSONDecodeError as e:
            st.error(f"❌ JSON Parse Error: {e}")
            st.text("Received an invalid response from the AI. Here is the raw text:")
            st.code(response.text)
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {e}")

st.markdown("---")
st.header("💬 OHS AI Chat Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_prompt := st.chat_input("Ask a follow-up safety question..."):
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        try:
            response = model.generate_content(user_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"❌ Error: {e}")