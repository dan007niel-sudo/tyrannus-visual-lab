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
    .vibe-header { color: #A81C1C; font-size: 0.9em; text-transform: uppercase; letter-spacing: 2px; }
    </style>
    """, unsafe_allow_html=True)

# --- API SECURITY & CONFIGURATION ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("CRITICAL ERROR: API-Key nicht gefunden. Bitte 'GEMINI_API_KEY' in den Streamlit Secrets konfigurieren.")
    st.stop()

# Modell-Endpunkt (Flash Preview)
MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# --- SYSTEM PROMPT (CULTURE & EMOTION VERSION) ---
SYSTEM_PROMPT = """Du bist der 'Visual Identity Architect' (Tyrannus Standard).
DEINE MISSION: Erfasse die *geistliche DNA* und *Kultur* einer Gemeinde, um daraus später ein Design abzuleiten.

REGELN FÜR DAS GESPRÄCH:
1. VERBOTEN: Nutze KEINE technischen Fachbegriffe (wie "Textur", "Lichtsetzung", "Modularität") in deinen Fragen.
2. NUTZE METAPHERN: Frage stattdessen nach Gefühlen, Orten und Vergleichen. 
   - Statt "Welches Licht?", frage: "Ist die Atmosphäre eher wie ein lautes Konzert (dynamisch, bunt) oder wie ein gemütlicher Abend am Kamin (warm, intim)?"
   - Statt "Welche Architektur?", frage: "Fühlt man sich bei euch eher wie in einem cleanen Tech-Start-up oder in einer kreativen Werkstatt?"
3. KULTUR-CHECK: Eine Frage muss den "Herzschlag" klären (z.B. "Was sollen Besucher fühlen, wenn sie nach Hause gehen?").
4. Sei ein proaktiver Guide. Kurz, knackig, inspirierend. Keine Floskeln.
5. Nach 4-5 Fragen bedanke dich herzlich für den Einblick in die Vision und beende das Interview.
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

    # Retry-Logik
    for delay in [1, 2, 4]:
        try:
            response = requests.post(f"{MODEL_URL}?key={API_KEY}", json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and result['candidates']:
                    return result['candidates'][0]['content']['parts'][0]['text']
                else:
                    return "Der Architect empfängt keine klaren Signale (Leere Antwort)."
            elif response.status_code == 429:
                time.sleep(delay)
            else:
                return f"Verbindungsfehler: {response.status_code} - {response.text}"
        except Exception:
            time.sleep(delay)
            
    return "Systemausfall: Verbindung zum Architect Core konnte nicht hergestellt werden."

# --- SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "finished" not in st.session_state:
    st.session_state.finished = False

# --- UI HEADER ---
col1, col2 = st.columns([2, 10])
with col1:
    # Stellt sicher, dass das Logo 'logo.jpg' im Repository liegt
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    else:
        st.warning("logo.jpg fehlt")
with col2:
    st.title("Tyrannus Visual Lab")
    st.markdown("**AI IDENTITY ARCHITECT** | V3.2")

st.divider()

# --- CHAT DISPLAY ---
for msg in st.session_state.chat_history:
    role = "assistant" if msg["role"] == "model" else "user"
    with st.chat_message(role):
        st.write(msg["parts"][0]["text"])

# --- ERSTKONTAKT ---
if not st.session_state.chat_history:
    initial_msg = "Willkommen im Visual Lab. Welches Projekt oder welche Vision soll heute visuell definiert werden?"
    st.session_state.chat_history.append({"role": "model", "parts": [{"text": initial_msg}]})
    st.rerun()

# --- INPUT HANDLING ---
if not st.session_state.finished:
    if user_input := st.chat_input("Deine Antwort..."):
        st.session_state.chat_history.append({"role": "user", "parts": [{"text": user_input}]})
        
        with st.chat_message("assistant"):
            with st.spinner("Der Architect analysiert die Kultur..."):
                response = call_gemini(st.session_state.chat_history, SYSTEM_PROMPT)
                st.write(response)
                st.session_state.chat_history.append({"role": "model", "parts": [{"text": response}]})
        
        # Abbruchbedingung (nach ca. 4 Fragen/Antworten Paaren)
        if len(st.session_state.chat_history) >= 9:
            st.session_state.finished = True
            st.rerun()

# --- FINALER EXPORT (TRANSLATION ENGINE) ---
if st.session_state.finished:
    st.success("Vision erfasst. Der Architect übersetzt Emotionen in Design-Parameter.")
    
    if st.button("Visual DNA generieren"):
        with st.spinner("Kalkuliere visuelle Übersetzung..."):
            # Hier geschieht die Magie: Die Übersetzung von "Gefühl" zu "Prompt"
            analysis_prompt = """
            Analysiere das Gespräch. Erstelle eine technische Style-DNA als JSON.
            WICHTIG:
            1. Nutze das Feld 'brand_category' für eine kurze Zusammenfassung des 'Cultural Vibe' (z.B. 'Warmes Wohnzimmer-Feeling').
            2. Übersetze die emotionalen Antworten in visuelle Parameter (z.B. 'Geborgenheit' -> 'Warm Lighting, Soft Focus').
            """
            
            temp_history = st.session_state.chat_history + [{"role": "user", "parts": [{"text": analysis_prompt}]}]
            dna_json = call_gemini(temp_history, "Erstelle nur das JSON.", json_mode=True)
            
            try:
                dna = json.loads(dna_json)
                st.markdown(f"""
                <div class="dna-box">
                    <span class="vibe-header">VISUAL SOUL DETECTED</span>
                    <h2 style="color:white; margin-top:5px;">{dna.get('brand_category', 'Community Vibe')}</h2>
                    <br>
                    <p><strong>Atmosphere (Light):</strong><br>{dna.get('lighting', 'N/A')}</p>
                    <p><strong>Perspective (Camera):</strong><br>{dna.get('camera', 'N/A')}</p>
                    <p><strong>Aesthetics (Style):</strong><br>{dna.get('style_keywords', 'N/A')}</p>
                    <p><strong>Composition:</strong><br>{dna.get('negative_space', 'N/A')}</p>
                    <hr style="border-color:#333">
                    <p style="font-size:11px; color:#777; font-family:sans-serif;">MIDJOURNEY PROMPT (COPY & PASTE):</p>
                    <code style="background-color:#111; color:#0f0; display:block; padding:10px;">
                    /imagine prompt: {dna.get('style_keywords')}, {dna.get('lighting')}, {dna.get('brand_category')} vibe, {dna.get('negative_space')} --ar 4:5 --v 6.5 --style raw
                    </code>
                </div>
                """, unsafe_allow_html=True)
            except json.JSONDecodeError:
                st.error("Fehler bei der DNA-Konstruktion. Bitte neu versuchen.")
            
    if st.button("Neues Projekt starten"):
        st.session_state.chat_history = []
        st.session_state.finished = False
        st.rerun()

