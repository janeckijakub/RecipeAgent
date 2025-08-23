import json
from typing import List, Union, Optional

import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
from pydantic import BaseModel, field_validator

# ──────────────────────────────────────────────
# KONFIGURACJA STRONY
# ──────────────────────────────────────────────
st.set_page_config(page_title="Generator Przepisów (z głosem)", layout="wide")

# ──────────────────────────────────────────────
# KATEGORIE SKŁADNIKÓW + IKONY
# ──────────────────────────────────────────────
KATEGORIE_SKLADNIKOW = {
    "Produkty białkowe": ["Kurczak", "Jajka", "Tuńczyk w puszce"],
    "Produkty mleczne": ["Masło", "Ser żółty", "Mleko"],
    "Warzywa": ["Marchewka", "Cebula", "Pomidory"],
    "Owoce": ["Jabłko", "Banan"],
}
IKONY_KATEGORII = {"Produkty białkowe": "🍗", "Produkty mleczne": "🥛", "Warzywa": "🥕", "Owoce": "🍎", "Dodatkowe": "➕"}

# ──────────────────────────────────────────────
# MODELE Pydantic
# ──────────────────────────────────────────────
class Skladnik(BaseModel):
    nazwa: str
    ilosc: Union[str, int, float]
    jednostka: str = ""

    @field_validator('jednostka', mode='before')
    @classmethod
    def validate_jednostka(cls, v):
        return v if v is not None else ""


class KrokPrzygotowania(BaseModel):
    numer: int
    opis: str


class Przepis(BaseModel):
    nazwa: str
    czas_przygotowania: str
    poziom_trudnosci: str
    skladniki: List[Skladnik]
    kroki: List[KrokPrzygotowania]
    sugestie: str


class Przepisy(BaseModel):
    przepisy: List[Przepis]

# ──────────────────────────────────────────────
# GENEROWANIE PRZEPISÓW
# ──────────────────────────────────────────────
def _generuj_przepisy(api_key: str, skladniki_str: str) -> Optional[Przepisy]:
    genai.configure(api_key=api_key)
    prompt = f"""Na podstawie składników: {skladniki_str}
Wygeneruj TRZY różne przepisy kulinarne w formacie JSON
(z polami: nazwa, czas_przygotowania, poziom_trudnosci, skladniki[nazwa, ilosc, jednostka], kroki[numer, opis], sugestie).
Odpowiadaj TYLKO w formacie JSON, po polsku."""
    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=3000,
            ),
        )
        clean_response = response.text.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]
        return Przepisy(**json.loads(clean_response))
    except Exception as e:
        st.error(f"Błąd: {e}")
        return None


@st.cache_data(show_spinner=False)
def generuj_przepisy_z_cache(api_key: str, skladniki_str: str) -> Optional[Przepisy]:
    normalized = ",".join(sorted([s.strip().lower() for s in skladniki_str.split(",") if s.strip()]))
    return _generuj_przepisy(api_key, normalized)

# ──────────────────────────────────────────────
# FUNKCJE STANU
# ──────────────────────────────────────────────
def _toggle_ingredient(skladnik_name):
    checkbox_key = f"cb_{skladnik_name}"
    if st.session_state.get(checkbox_key, False):
        st.session_state.wybrane_skladniki.add(skladnik_name)
    else:
        st.session_state.wybrane_skladniki.discard(skladnik_name)

def _add_custom():
    nowy = st.session_state.get("custom_input", "").strip()
    if nowy and nowy not in st.session_state.dodatkowe_skladniki:
        st.session_state.dodatkowe_skladniki.append(nowy)
    st.session_state.custom_input = ""

def _clear_all():
    for kat, lista in KATEGORIE_SKLADNIKOW.items():
        for s in lista:
            key = f"cb_{s}"
            if key in st.session_state:
                st.session_state[key] = False
    st.session_state.wybrane_skladniki = set()
    st.session_state.dodatkowe_skladniki = []
    st.session_state.przepisy = None

# ──────────────────────────────────────────────
# GŁOSOWY KOMPONENT
# ──────────────────────────────────────────────
def speech_component():
    html_code = """
    <div style="text-align:center; margin:10px;">
      <button id="micButton" style="border-radius:50%; width:80px; height:80px; font-size:30px;">🎤</button>
      <div id="status">Kliknij mikrofon i mów...</div>
      <div id="result" style="margin-top:10px; font-weight:bold;"></div>
    </div>
    <script>
      let recognition;
      let isListening = false;
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'pl-PL';
        recognition.onresult = (event) => {
          let finalTranscript = "";
          for (let i=event.resultIndex; i<event.results.length; i++) {
            if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript;
          }
          if (finalTranscript) {
            document.getElementById('result').innerText = finalTranscript;
            window.parent.postMessage({type:'streamlit:setComponentValue', value:finalTranscript}, '*');
          }
        };
      }
      document.getElementById('micButton').onclick = () => {
        if (!isListening) { recognition.start(); isListening=true; document.getElementById('micButton').style.background="red";}
        else { recognition.stop(); isListening=false; document.getElementById('micButton').style.background=""; }
      };
    </script>
    """
    return components.html(html_code, height=200)

# ──────────────────────────────────────────────
# INICJALIZACJA STANU
# ──────────────────────────────────────────────
if "voice_command" not in st.session_state:
    st.session_state.voice_command = ""
if "wybrane_skladniki" not in st.session_state:
    st.session_state.wybrane_skladniki = set()
if "dodatkowe_skladniki" not in st.session_state:
    st.session_state.dodatkowe_skladniki = []
if "przepisy" not in st.session_state:
    st.session_state.przepisy = None

# ──────────────────────────────────────────────
# UI – GŁOS
# ──────────────────────────────────────────────
st.title("🍳 Generator przepisów z obsługą głosu")
st.subheader("🎤 Sterowanie głosowe")
voice_text = speech_component()

if voice_text:
    st.session_state.voice_command = voice_text.strip().lower()
    st.write(f"➡️ Rozpoznano: **{st.session_state.voice_command}**")
    cmd = st.session_state.voice_command

    if cmd.startswith("mam "):
        lista = cmd.replace("mam", "").strip().split(",")
        for item in lista:
            s = item.strip().capitalize()
            if s and s not in st.session_state.dodatkowe_skladniki:
                st.session_state.dodatkowe_skladniki.append(s)
        st.success("Dodano składniki głosowo.")

    elif cmd.startswith("usuń "):
        item = cmd.replace("usuń", "").strip().capitalize()
        if item in st.session_state.dodatkowe_skladniki:
            st.session_state.dodatkowe_skladniki.remove(item)
            st.success(f"Usunięto składnik: {item}")

    elif "wygeneruj przepis" in cmd or "generuj przepis" in cmd:
        wszystkie = list(st.session_state.wybrane_skladniki) + st.session_state.dodatkowe_skladniki
        if wszystkie:
            with st.spinner("🤖 Myślę nad przepisami..."):
                api_key = "TWOJ_API_KEY"  # ← wpisz swój klucz Gemini
                result = generuj_przepisy_z_cache(api_key, ", ".join(wszystkie))
                st.session_state.przepisy = result
        else:
            st.warning("Nie podałeś żadnych składników!")

# ──────────────────────────────────────────────
# SIDEBAR – wybór składników
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("📦 Wybierz składniki")
    wybrana_kategoria = st.radio("Kategoria:", options=list(KATEGORIE_SKLADNIKOW.keys()), index=0, label_visibility="collapsed")
    for skladnik in KATEGORIE_SKLADNIKOW[wybrana_kategoria]:
        st.checkbox(
            skladnik,
            key=f"cb_{skladnik}",
            value=skladnik in st.session_state.wybrane_skladniki,
            on_change=lambda s=skladnik: _toggle_ingredient(s),
        )

# ──────────────────────────────────────────────
# KONTROLKI – składniki + przyciski
# ──────────────────────────────────────────────
st.subheader("🛒 Twoje składniki")
wszystkie_skladniki = list(st.session_state.wybrane_skladniki) + st.session_state.dodatkowe_skladniki
if wszystkie_skladniki:
    st.write(", ".join(wszystkie_skladniki))
    c1, c2 = st.columns(2)
    if c1.button("🧹 Wyczyść wszystko", use_container_width=True): _clear_all()
    if c2.button("🍳 Generuj przepisy!", type="primary", use_container_width=True):
        api_key = "AIzaSyBAGk9dEdcSqJPxXFW6spIzEDcCdClUzk4"
        with st.spinner("🤖 Myślę nad przepisami..."):
            result = generuj_przepisy_z_cache(api_key, ", ".join(wszystkie_skladniki))
            st.session_state.przepisy = result
else:
    st.info("Dodaj składniki (kliknięciem lub głosem).")

# ──────────────────────────────────────────────
# WYNIKI
# ──────────────────────────────────────────────
if st.session_state.przepisy:
    st.header("📋 Twoje przepisy")
    for idx, przepis in enumerate(st.session_state.przepisy.przepisy, start=1):
        with st.container(border=True):
            st.markdown(f"### {idx}. {przepis.nazwa}")
            c1, c2 = st.columns(2)
            c1.metric("Czas", przepis.czas_przygotowania)
            c2.metric("Trudność", przepis.poziom_trudnosci)
            st.markdown("**🥑 Składniki:**")
            for s in przepis.skladniki:
                st.write(f"- {s.nazwa}: {s.ilosc} {s.jednostka}")
            st.markdown("**📝 Przygotowanie:**")
            for krok in przepis.kroki:
                st.write(f"{krok.numer}. {krok.opis}")
            if przepis.sugestie:
                with st.expander("💡 Sugestie"):
                    st.write(przepis.sugestie)
