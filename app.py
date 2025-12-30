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

# Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #f0f0f0; }
    
    /* Intro Text Styling */
    .intro-text { font-size: 1.1em; color: #ccc; margin-bottom: 30px; line-height: 1.5; }
    
    /* Button Styling */
    .stButton>button { 
        background-color: #1a1a1a; color: white; border-radius: 12px; 
        border: 1px solid #333; padding: 20px 10px; font-weight: bold; width: 100%;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { 
        background-color: #A81C1C; border-color: #A81C1C; transform: translateY(-2px);
    }
    
    /* Kleinerer Style für den Zurück-Button */
    div[data-testid="stHorizontalBlock"] .stButton>button {
        background-color: #111; border: 1px solid #444; padding: 5px 10px; font-size: 0.8em;
    }
    
    /* Input Felder */
    .stTextInput>div>div>input { background-color: #111; color: white; border: 1px solid #222; border-radius: 12px; }
    
    /* DNA Box Style */
    .dna-box { 
        background-color: #0A0A0A; border-left: 5px solid #A81C1C; 
        padding: 25px; border-radius: 0 15px 15px 0; margin: 20px 0;
        font-family: 'Courier New', monospace;
    }
    .human-vision { font-family: sans-serif; font-size: 1.1em; line-height: 1.6; color: #e0e0e0; margin-bottom: 20px; }
    .label { color: #A81C1C; font-size: 0.8em; text-transform: uppercase; letter-spacing: 1px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- API SECURITY ---
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    st.error("CRITICAL ERROR: API-Key nicht gefunden.")
    st.stop()

# FIX: Wechsel auf das stabile Flash-Modell (verhindert Verbindungsfehler)
MODEL_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

# --- SESSION STATE SETUP ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "finished" not in st.session_state:
    st.session_state.finished = False
if "mode" not in st.session_state:
    st.session_state.mode = None 

# --- HELFERFUNKTIONEN ---
def call_gemini(messages, system_instruction=None, json_mode=False):
    payload = {
        "contents": messages,
        "systemInstruction": {"parts": [{"text": system_instruction}]} if system_instruction else None
    }
    if json_mode:
        payload["generationConfig"] = {"responseMimeType": "application/json"}

    # Retry-Logik erhöht auf 5 Versuche für Stabilität
    for delay in [1, 2, 3, 5, 8]:
        try:
            response = requests.post(f"{MODEL_URL}?key={API_KEY}", json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result:
                    return result['candidates'][0]['content']['parts'][0]['text']
            elif response.status_code == 429:
                time.sleep(delay) # Warten bei Überlastung
        except Exception:
            time.sleep(delay)
            
    return "FEHLER: Verbindung instabil. Bitte erneut senden."

# --- UI HEADER (LOGO FIX) ---
col1, col2 = st.columns([2, 10])
with col1:
    # FIX: Intelligenter Logo-Lader. Wenn lokal nicht da, nimm Online-Bild.
    if os.path.exists("logo.jpg"):
        st.image("logo.jpg", use_container_width=True)
    elif os.path.exists("Logo.jpg"): # Check für Großschreibung
        st.image("Logo.jpg", use_container_width=True)
    else:
        # Fallback URL (Tyrannus Logo von Wix)
        st.image("https://static.wixstatic.com/media/9a8941_e2029560697449669041103545901272~mv2.png", use_container_width=True)

with col2:
    st.title("Tyrannus Visual Lab")
    if st.session_state.mode:
        st.caption(f"MODUS: {st.session_state.mode}")
    else:
        st.caption("AI IDENTITY ARCHITECT | V5.3 (Stable)")

st.divider()

# ---------------------------------------------------------
# PHASE 1: DASHBOARD / AUSWAHL
# ---------------------------------------------------------
if st.session_state.mode is None:
    st.markdown("""
    <div class="intro-text">
    Willkommen im Visual Lab.<br>
    Dies ist dein visueller Sparringspartner. Egal ob du die <b>tiefgreifende DNA</b> deiner Gemeinde entschlüsseln willst oder nur einen <b>konkreten Impuls</b> für das nächste Projekt brauchst – der Architect führt dich zum Ziel.
    <br><br>
    <b>Wähle deine Mission:</b>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("🏛️\nDNA & KULTUR\n(Identität finden)"):
            st.session_state.mode = "IDENTITY_SCAN"
            st.rerun()
            
    with c2:
        if st.button("🎨\nPROJEKT & DESIGN\n(Flyer / Grafik)"):
            st.session_state.mode = "PROJECT_DESIGN"
            st.rerun()
            
    with c3:
        if st.button("🧠\nBRAINSTORMING\n(Jahresthema / Ideen)"):
            st.session_state.mode = "BRAINSTORMING"
            st.rerun()

# ---------------------------------------------------------
# PHASE 2: DER CHAT
# ---------------------------------------------------------
else:
    # --- NAVIGATION: ZURÜCK BUTTON (Dein Wunsch-Feature) ---
    col_back, col_space = st.columns([3, 7])
    with col_back:
        if st.button("← Zurück zur Auswahl"):
            st.session_state.mode = None
            st.session_state.chat_history = []
            st.session_state.finished = False
            st.rerun()

    # --- DYNAMISCHER SYSTEM PROMPT ---
    BASE_INSTRUCTION = f"""Du bist der 'Visual Identity Architect' (Tyrannus Standard).
    AKTUELLER MODUS: {st.session_state.mode}
    
    REGELN:
    1. Nutze KEINE technischen Fachbegriffe, sondern Metaphern.
    2. Bestätige Antworten kurz ("Verstanden."), wiederhole NICHTS.
    3. Nach 3-4 Fragen beende das Interview.
    """
    
    if st.session_state.mode == "IDENTITY_SCAN":
        SPECIFIC_INSTRUCTION = "ZIEL: Erfasse die tiefe geistliche DNA der Gemeinde. Frage nach Gefühlen und Vergleichen."
    elif st.session_state.mode == "PROJECT_DESIGN":
        SPECIFIC_INSTRUCTION = "ZIEL: Konzept für ein KONKRETES Projekt (Flyer, Plakat). Frage nach Thema, Zielgruppe, Stimmung."
    elif st.session_state.mode == "BRAINSTORMING":
        SPECIFIC_INSTRUCTION = "ZIEL: Brainstorming für Jahresthema/Ideen. Frage nach Zielen und biblischen Bildern."
    
    FULL_SYSTEM_PROMPT = BASE_INSTRUCTION + SPECIFIC_INSTRUCTION

    # --- CHAT DISPLAY ---
    for msg in st.session_state.chat_history:
        role = "assistant" if msg["role"] == "model" else "user"
        with st.chat_message(role):
            st.write(msg["parts"][0]["text"])

    # --- INITIAL MESSAGE ---
    if not st.session_state.chat_history:
        if st.session_state.mode == "IDENTITY_SCAN":
            welcome = "Modus: DNA-Analyse.\nLass uns den Kern deiner Gemeinde finden. Beschreibe mir kurz eure Gemeinschaft."
        elif st.session_state.mode == "PROJECT_DESIGN":
            welcome = "Modus: Projekt-Design.\nWas steht an? Ein Flyer, ein Predigt-Cover oder ein Event-Bild?"
        else:
            welcome = "Modus: Brainstorming.\nLass uns kreativ werden. Wonach suchen wir heute? (Jahresthema, Predigtreihe...)"
            
        st.session_state.chat_history.append({"role": "model", "parts": [{"text": welcome}]})
        st.rerun()

    # --- INPUT ---
    if not st.session_state.finished:
        if user_input := st.chat_input("Deine Antwort..."):
            st.session_state.chat_history.append({"role": "user", "parts": [{"text": user_input}]})
            
            with st.chat_message("assistant"):
                with st.spinner("Der Architect arbeitet..."):
                    response = call_gemini(st.session_state.chat_history, FULL_SYSTEM_PROMPT)
                    
                    # FIX: Error Handling für den Chat
                    if response.startswith("FEHLER"):
                        st.error(response)
                    else:
                        st.write(response)
                        st.session_state.chat_history.append({"role": "model", "parts": [{"text": response}]})
            
            if len(st.session_state.chat_history) >= 9:
                st.session_state.finished = True
                st.rerun()

    # --- OUTPUT GENERATOR ---
    if st.session_state.finished:
        if st.button("Neues Projekt starten"):
             st.session_state.chat_history = []
             st.session_state.finished = False
             st.session_state.mode = None
             st.rerun()

        st.success("Konzept finalisiert. Generiere Daten...")
        
        if st.button("Ergebnisse anzeigen"):
            with st.spinner("Rendere Prompt für Gemini 3 Pro Image..."):
                analysis_prompt = """
                Erstelle ein JSON mit genau zwei Feldern:
                1. 'human_vision': Eine kraftvolle deutsche Zusammenfassung des Konzepts.
                2. 'ai_prompt': Ein perfekter englischer Bild-Prompt für 'Gemini 3 Pro Image'. 
                   - Natural Language. Photorealistic description.
                   - Beginne mit: "A high resolution image of..."
                """
                
                temp_history = st.session_state.chat_history + [{"role": "user", "parts": [{"text": analysis_prompt}]}]
                dna_json = call_gemini(temp_history, "JSON Output only.", json_mode=True)
                
                # FIX: Verhindert Absturz bei API-Fehler
                if dna_json.startswith("FEHLER"):
                    st.error("Verbindung unterbrochen. Bitte versuche es noch einmal.")
                else:
                    try:
                        dna = json.loads(dna_json)
                        st.markdown(f"""
                        <div class="dna-box">
                            <p class="label">VISION / KONZEPT</p>
                            <div class="human-vision">"{dna.get('human_vision', 'Processing...')}"</div>
                            <br><hr style="border-color:#333"><br>
                            <p class="label">GEMINI 3 PRO IMAGE PROMPT</p>
                            <code style="background-color:#111; color:#0f0; display:block; padding:15px; white-space: pre-wrap;">
{dna.get('ai_prompt', 'Generating prompt...')}
                            </code>
                        </div>
                        """, unsafe_allow_html=True)
                    except Exception:
                        st.error("Daten konnten nicht verarbeitet werden. Bitte 'Ergebnisse anzeigen' erneut klicken.")
