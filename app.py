import streamlit as st
import requests
import time
import json
import os

# --- KONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="Tyrannus Visual Lab | AI Architect",
    page_icon="https://static.wixstatic.com/media/9a8941_e2029560697449669041103545901272~mv2.png",
    layout="centered"
)

# Custom CSS für den Tyrannus-Standard
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #f0f0f0; }
    .stButton>button { 
        background-color: #A81C1C; color: white; border-radius: 12px; 
        border: none; padding: 10px 24px; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-color: #8B1717; box-shadow: 0 0 15px rgba(168,28,28,0.4); }
    .stTextInput>div>div>input { background-color: #111; color: white; border: 1px solid #222; border-radius: 12px; }
    .dna-box { 
        background-color: #0A0A0A; border-left: 5px solid #A81C1C; 
        padding: 25px; border-radius: 0 15px 15px 0; margin: 20px 0;
        font-family: 'Courier New', monospace;
    }
    </style>
    """, unsafe_allow_html=True)

# --- API SECURITY & CONFIGURATION ---
# Check für API Key in den Secrets (Deployment) oder Environment (Lokal)
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("CRITICAL ERROR: API-Key nicht gefunden. Bitte 'GEMINI_API_KEY' in den Streamlit Secrets konfigurieren.")
    st.stop()

# Modell-Endpunkt (Flash Preview)
MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# --- SYSTEM PROMPT (OPTIMIERT) ---
SYSTEM_PROMPT = """Du bist der 'Visual Identity Architect' (Tyrannus Standard).
DEINE MISSION: Erstelle effizient ein visuelles Profil (Style-DNA).
REGELN:
1. KEIN Smalltalk zu Beginn, keine Begrüßungsfloskeln, kein "Das klingt super".
2. Sei präzise, analytisch, direkt und knapp.
3. Stelle immer nur EINE gezielte Frage pro Turn (Fokus: Licht, Textur, Architektur, Farben).
4. Maximal 2 kurze Sätze pro Antwort.
5. WICHTIG: Wenn du 4 Kern-Parameter gesammelt hast, bedanke dich kurz für die Zusammenarbeit und beende das Interview.
"""

# --- HELFERFUNKTIONEN ---
def call_gemini(messages, system_instruction=None, json_mode=False):
    """Ruft die Gemini API mit Exponential Backoff auf."""
    payload = {
        "contents": messages,
        "systemInstruction": {"parts": [{"text": system_instruction}]} if system_instruction else None
    }
    
    if json_mode:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "OBJECT",
                "properties": {
                    "brand_category": {"type": "STRING"},
                    "lighting": {"type": "STRING"},
                    "camera": {"type": "STRING"},
                    "style_keywords": {"type": "STRING"},
                    "negative_space": {"type": "STRING"}
                }
            }
        }

    # Retry-Logik für Stabilität
    for delay in [1, 2, 4]:
        try:
            response = requests.post(f"{MODEL_URL}?key={API_KEY}", json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                # Sicherheitscheck falls API Struktur abweicht
                if 'candidates' in result and result['candidates']:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    return "Der Architect empfängt keine klaren Signale (Leere Antwort)."
            elif response.status_code == 429:
                time.sleep(delay) # Rate Limit Hit
            else:
                return f"Verbindungsfehler: {response.status_code} - {response.text}"
        except Exception as e:
            time.sleep(delay)
            
    return "Systemausfall: Verbindung zum Architect Core konnte nicht hergestellt werden."

# --- SESSION STATE INITIALISIERUNG ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "finished" not in st.session_state:
    st.session_state.finished = False

# --- UI HEADER ---
col1, col2 = st.columns([2, 10]) # Spalte 1 breiter für das Logo
with col1:
    # Stellt sicher, dass das Logo 'logo.jpg' im Repository liegt
    st.image("logo.jpg", use_container_width=True)
with col2:
    st.title("Tyrannus Visual Lab")
    st.markdown("**AI IDENTITY ARCHITECT** | V3.1")

st.divider()

# --- CHAT DISPLAY ---
for msg in st.session_state.chat_history:
    role = "assistant" if msg["role"] == "model" else "user"
    with st.chat_message(role):
        st.write(msg["parts"][0]["text"])

# --- ERSTKONTAKT (TRIGGER) ---
if not st.session_state.chat_history:
    # Deine gewählte Begrüßung
    initial_msg = "Willkommen im Visual Lab. Welches Projekt soll heute visuell definiert werden?"
    st.session_state.chat_history.append({"role": "model", "parts": [{"text": initial_msg}]})
    st.rerun()

# --- INPUT HANDLING ---
if not st.session_state.finished:
    if user_input := st.chat_input("Schreibe dem Architect..."):
        # User Nachricht speichern und anzeigen
        st.session_state.chat_history.append({"role": "user", "parts": [{"text": user_input}]})
        
        # Antwort generieren
        with st.chat_message("assistant"):
            with st.spinner("Der Architect analysiert..."):
                response = call_gemini(st.session_state.chat_history, SYSTEM_PROMPT)
                st.write(response)
                st.session_state.chat_history.append({"role": "model", "parts": [{"text": response}]})
        
        # Logik zum Beenden des Interviews (nach 8 Turns = 4 Fragen/Antworten)
        if len(st.session_state.chat_history) >= 8:
            st.session_state.finished = True
            st.rerun()

# --- FINALER EXPORT ---
if st.session_state.finished:
    st.success("Das Interview ist abgeschlossen. Der Architect extrahiert nun die Style-DNA.")
    
    if st.button("Style-DNA generieren"):
        with st.spinner("Extrahiere technische Parameter..."):
            analysis_prompt = "Analysiere das vorangegangene Gespräch und erstelle eine technische Style-DNA für einen Bildgenerator nach dem Tyrannus-Standard."
            # Temporäre History für die Analyse (ohne sie in den Chat zu schreiben)
            temp_history = st.session_state.chat_history + [{"role": "user", "parts": [{"text": analysis_prompt}]}]
            
            dna_json = call_gemini(temp_history, "Extrahiere nur die technischen Daten als JSON.", json_mode=True)
            
            try:
                dna = json.loads(dna_json)
                st.markdown(f"""
                <div class="dna-box">
                    <h3 style="color:#A81C1C; margin-top:0;">DNA EXPORT READY</h3>
                    <p><strong>Brand:</strong> {dna.get('brand_category', 'N/A')}</p>
                    <p><strong>Lighting:</strong> {dna.get('lighting', 'N/A')}</p>
                    <p><strong>Camera:</strong> {dna.get('camera', 'N/A')}</p>
                    <p><strong>Style:</strong> {dna.get('style_keywords', 'N/A')}</p>
                    <p><strong>Negative Space:</strong> {dna.get('negative_space', 'N/A')}</p>
                    <hr style="border-color:#222">
                    <p style="font-size:10px; color:#555">PROMPT SUFFIX: --ar 4:5 --v 6.5 --style raw</p>
                </div>
                """, unsafe_allow_html=True)
            except json.JSONDecodeError:
                st.error("Fehler bei der DNA-Konstruktion. Bitte neu versuchen.")
            
    if st.button("Neues Projekt starten"):
        st.session_state.chat_history = []
        st.session_state.finished = False
        st.rerun()
