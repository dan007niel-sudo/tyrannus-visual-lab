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

# --- NEUES DESIGN: CLEAN & MODERN (Tyrannus Style) ---
st.markdown("""
    <style>
    /* BASIS: Schwarz & Weiss */
    .stApp { background-color: #050505; color: #f0f0f0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    
    /* INPUT FELDER: Clean Dark */
    .stTextInput>div>div>input { 
        background-color: #111; color: white; border: 1px solid #333; border-radius: 4px; 
    }
    .stTextInput>div>div>input:focus { border-color: #A81C1C; }

    /* BUTTONS: Minimalistisch & Stark */
    .stButton>button { 
        background-color: #0A0A0A; color: #ccc; border-radius: 4px; 
        border: 1px solid #333; padding: 15px 10px; font-weight: 500; letter-spacing: 1px; width: 100%;
        transition: all 0.3s ease; text-transform: uppercase; font-size: 0.85em;
    }
    .stButton>button:hover { 
        background-color: #A81C1C; color: white; border-color: #A81C1C; transform: translateY(-1px);
    }
    
    /* KLEINE BUTTONS (Navigation) */
    div[data-testid="stHorizontalBlock"] .stButton>button {
        background-color: transparent; border: none; text-align: left; padding: 0; color: #666;
    }
    div[data-testid="stHorizontalBlock"] .stButton>button:hover {
        color: #A81C1C; background-color: transparent; transform: none;
    }

    /* ERGEBNIS BOX: Clean & Hochwertig (Kein Hacker-Grün mehr) */
    .dna-box { 
        background-color: #0F0F0F; border-left: 3px solid #A81C1C; 
        padding: 30px; margin: 30px 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    }
    .human-vision { 
        font-family: 'Helvetica Neue', sans-serif; font-size: 1.05em; line-height: 1.6; color: #ddd; margin-bottom: 25px; 
        font-weight: 300;
    }
    .label { 
        color: #A81C1C; font-size: 0.7em; text-transform: uppercase; letter-spacing: 2px; font-weight: 700; margin-bottom: 10px; display: block;
    }
    .prompt-code {
        font-family: 'Courier New', monospace; font-size: 0.9em; color: #bbb; /* Helles Grau statt Grün */
        background-color: #080808; padding: 20px; border: 1px solid #222; display: block; white-space: pre-wrap;
    }
    
    /* FEHLER & INFO BOXEN ANPASSEN (Weg von Standard-Farben) */
    .stAlert { background-color: #111; color: #ccc; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- API SECURITY ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("Setup: API-Key fehlt.")
    st.stop()

# MODELL-LISTE
AVAILABLE_MODELS = [
    "gemini-1.5-pro-latest", "gemini-2.0-flash-lite-preview-02-05", "gemini-2.0-flash-exp", "gemini-2.0-flash", "gemini-flash-latest"
]
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/"

# --- STATE ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "finished" not in st.session_state: st.session_state.finished = False
if "mode" not in st.session_state: st.session_state.mode = None 

# --- FUNCTION ---
def call_gemini(messages, system_instruction=None, json_mode=False):
    payload = {
        "contents": messages,
        "systemInstruction": {"parts": [{"text": system_instruction}]} if system_instruction else None
    }
    if json_mode: payload["generationConfig"] = {"responseMimeType": "application/json"}

    for model_name in AVAILABLE_MODELS:
        try:
            full_url = f"{BASE_URL}{model_name}:generateContent"
            response = requests.post(f"{full_url}?key={API_KEY}", json=payload, timeout=40)
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result: return result['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                time.sleep(1); continue 
            else:
                time.sleep(1)
        except Exception: continue
    return "Verbindung fehlgeschlagen. Bitte neu laden."

# --- UI HEADER ---
col1, col2 = st.columns([2, 10])
with col1:
    possible_names = ["logo.jpg", "Logo.jpg", "Logo.JPG", "logo.JPG", "logo.png", "Logo.png"]
    for filename in possible_names:
        if os.path.exists(filename):
            st.image(filename, use_container_width=True)
            break

with col2:
    st.markdown("<h1 style='font-weight:300; letter-spacing:1px; margin-bottom:0;'>TYRANNUS VISUAL LAB</h1>", unsafe_allow_html=True)
    if st.session_state.mode:
        st.caption(f"MODUS: {st.session_state.mode} | V8.3 CLEAN")
    else:
        st.caption("AI IDENTITY ARCHITECT | V8.3")

st.markdown("<hr style='border: 1px solid #222; margin-top:0;'>", unsafe_allow_html=True)

# ---------------------------------------------------------
# PHASE 1: DASHBOARD
# ---------------------------------------------------------
if st.session_state.mode is None:
    st.markdown("""
    <div style="text-align:center; padding: 40px 0; color: #888;">
    Wähle den Fokus für das heutige Design-Konzept.
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("DNA & KULTUR"):
            st.session_state.mode = "IDENTITY_SCAN"
            st.rerun()
    with c2:
        if st.button("PROJEKT DESIGN"):
            st.session_state.mode = "PROJECT_DESIGN"
            st.rerun()
    with c3:
        if st.button("BRAINSTORMING"):
            st.session_state.mode = "BRAINSTORMING"
            st.rerun()

# ---------------------------------------------------------
# PHASE 2: CHAT
# ---------------------------------------------------------
else:
    col_back, col_space = st.columns([3, 7])
    with col_back:
        if st.button("← ZURÜCK"):
            st.session_state.mode = None
            st.session_state.chat_history = []
            st.session_state.finished = False
            st.rerun()

    # SYSTEM PROMPTS (CLEAN AGENCY STYLE)
    BASE_INSTRUCTION = f"""
    Du bist das 'Tyrannus Visual Lab', ein professioneller Art Director.
    AKTUELLER MODUS: {st.session_state.mode}
    
    TONALITÄT:
    - Professionell, clean, "Agency-Style".
    - Keine Metaphern ("Samen", "Reise"). Sei direkt.
    - Du lieferst Bild-Konzepte für HINTERGRÜNDE, keinen fertigen Text.
    - Achte immer auf "Negative Space" (Platz für Text).
    
    ABLAUF:
    1. Stelle 1-2 präzise Fragen (Zielgruppe, Vibe, Format).
    2. Schlage ein Bildkonzept vor (Farben, Licht, Motiv).
    3. Beende das Gespräch, wenn das Konzept steht.
    """
    
    if st.session_state.mode == "IDENTITY_SCAN":
        SPECIFIC_INSTRUCTION = "FOKUS: Visuelle DNA. Moodboard-Style. Farben & Licht."
    elif st.session_state.mode == "PROJECT_DESIGN":
        SPECIFIC_INSTRUCTION = "FOKUS: Konkretes Asset (Flyer). Welches Motiv dient als Hintergrund?"
    elif st.session_state.mode == "BRAINSTORMING":
        SPECIFIC_INSTRUCTION = "FOKUS: Ideenfindung. Moderne Metaphern, nicht kitschig."
    
    FULL_SYSTEM_PROMPT = BASE_INSTRUCTION + "\n" + SPECIFIC_INSTRUCTION

    # Chat Anzeige
    for msg in st.session_state.chat_history:
        role = "assistant" if msg["role"] == "model" else "user"
        with st.chat_message(role):
            st.write(msg["parts"][0]["text"])

    # Start-Trigger
    if not st.session_state.chat_history:
        if st.session_state.mode == "IDENTITY_SCAN":
            welcome = "Modus: DNA-Analyse.\nLass uns den Look definieren. Beschreibe den Charakter der Gemeinde (Modern, Klassisch, Laut, Still)?"
        elif st.session_state.mode == "PROJECT_DESIGN":
            welcome = "Modus: Projekt-Design.\nWas steht an (Flyer, Post)? Und welche Stimmung soll das Bild transportieren?"
        else:
            welcome = "Modus: Brainstorming.\nWelches Thema möchtest du visuell übersetzen?"
        st.session_state.chat_history.append({"role": "model", "parts": [{"text": welcome}]})
        st.rerun()

    # Input Logic
    if not st.session_state.finished:
        if user_input := st.chat_input("Antwort eingeben..."):
            st.session_state.chat_history.append({"role": "user", "parts": [{"text": user_input}]})
            with st.chat_message("assistant"):
                with st.spinner("..."):
                    response = call_gemini(st.session_state.chat_history, FULL_SYSTEM_PROMPT)
                    if "SYSTEM OVERLOAD" in response:
                        st.error(response)
                    else:
                        st.write(response)
                        st.session_state.chat_history.append({"role": "model", "parts": [{"text": response}]})
            if len(st.session_state.chat_history) >= 11: 
                st.session_state.finished = True
                st.rerun()

    # ERGEBNIS OUTPUT (Clean Style)
    if st.session_state.finished:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("NEUSTART", key="reset_btn"):
             st.session_state.chat_history = []
             st.session_state.finished = False
             st.session_state.mode = None
             st.rerun()

        with st.spinner("Erstelle Blueprint..."):
            analysis_prompt = """
            Erstelle ein JSON mit zwei Feldern:
            1. 'human_vision': Zusammenfassung des Bildkonzepts (Deutsch). Erwähne Platzhalter für Text.
            2. 'ai_prompt': Englischer Prompt für Midjourney/Gemini (Photorealistic, clean, negative space).
            """
            temp_history = st.session_state.chat_history + [{"role": "user", "parts": [{"text": analysis_prompt}]}]
            dna_json = call_gemini(temp_history, "JSON Output only.", json_mode=True)
            
            if "SYSTEM" not in dna_json:
                try:
                    dna = json.loads(dna_json)
                    # HIER IST DAS NEUE DESIGN DER ERGEBNIS-BOX
                    st.markdown(f"""
                    <div class="dna-box">
                        <span class="label">VISUELLES KONZEPT</span>
                        <div class="human-vision">{dna.get('human_vision', '...')}</div>
                        <br>
                        <span class="label">KI-PROMPT (COPY & PASTE)</span>
                        <div class="prompt-code">{dna.get('ai_prompt', '...')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception:
                    st.error("Fehler bei der Datenausgabe.")
