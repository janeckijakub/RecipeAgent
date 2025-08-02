import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Union
import json
import google.generativeai as genai

# Konfiguracja strony
st.set_page_config(layout="wide", page_title="Generator Przepisów AI")

# --- Cache i stałe ---
cache_memory = {}
KATEGORIE_SKLADNIKOW = {
    # ... (bez zmian)
    "Przyprawy i dodatki smakowe": ["Sól", "Pieprz czarny", "Czosnek granulowany", "Papryka słodka", "Papryka ostra", "Oregano", "Bazylia", "Curry", "Kminek", "Tymianek", "Liść laurowy", "Ziele angielskie", "Imbir mielony", "Sos sojowy"],
    "Produkty zbożowe i mączne": ["Makaron", "Ryż biały", "Kasza gryczana", "Kasza jaglana", "Mąka pszenna", "Mąka żytnia", "Płatki owsiane", "Płatki kukurydziane", "Bułka tarta", "Chleb", "Tortilla pszenna", "Kuskus", "Quinoa"],
    "Produkty białkowe": ["Jajka", "Filet z kurczaka", "Mięso mielone", "Tuńczyk w puszce", "Soczewica czerwona", "Soczewica zielona", "Ciecierzyca", "Fasola czerwona", "Fasola biała", "Groszek zielony", "Tofu", "Tempeh", "Parówki", "Ser biały (twaróg)"],
    "Produkty mleczne i zamienniki": ["Mleko", "Mleko roślinne (np. owsiane)", "Masło", "Margaryna", "Jogurt naturalny", "Ser żółty", "Ser feta", "Śmietana", "Maślanka", "Serek wiejski", "Kefir"],
    "Warzywa": ["Ziemniaki", "Marchewka", "Cebula", "Czosnek świeży", "Kapusta", "Ogórek", "Papryka", "Pomidory świeże", "Pomidory w puszce", "Cukinia", "Brokuł", "Kalafior", "Sałata", "Por"],
    "Owoce": ["Jabłko", "Banan", "Cytryna", "Gruszka", "Śliwka", "Truskawki", "Maliny", "Winogrona", "Ananas w puszce", "Brzoskwinia", "Awokado"],
    "Tłuszcze i oleje": ["Olej rzepakowy", "Oliwa z oliwek", "Olej kokosowy", "Masło klarowane", "Smalec", "Olej lniany", "Olej słonecznikowy"],
    "Dodatki słodzące i konserwujące": ["Cukier biały", "Cukier trzcinowy", "Miód", "Syrop klonowy", "Ocet spirytusowy", "Ocet jabłkowy", "Sól peklująca", "Dżem", "Musztarda", "Ketchup"]
}
IKONY_KATEGORII = {
    "Przyprawy i dodatki smakowe": "🌶️", "Produkty zbożowe i mączne": "🌾", "Produkty białkowe": "🍗", "Produkty mleczne i zamienniki": "🥛",
    "Warzywa": "🥕", "Owoce": "🍎", "Tłuszcze i oleje": "🫒", "Dodatki słodzące i konserwujące": "🍯", "Dodatkowe": "➕"
}

# --- Modele Pydantic z aliasami ---
class Skladnik(BaseModel):
    nazwa: str = Field(alias="name", description="Nazwa składnika")
    ilosc: Union[str, int, float] = Field(alias="quantity", description="Ilość składnika")
    jednostka: str = Field(alias="unit", description="Jednostka miary, np. gram, łyżka, sztuka")

class KrokPrzygotowania(BaseModel):
    numer: int = Field(alias="step", description="Numer kroku")
    opis: str = Field(alias="description", description="Opis czynności do wykonania")

class Przepis(BaseModel):
    nazwa: str = Field(alias="name", description="Nazwa potrawy")
    czas_przygotowania: str = Field(alias="preparation_time", description="Czas potrzebny na przygotowanie")
    poziom_trudnosci: str = Field(alias="difficulty", description="Poziom trudności: łatwy, średni lub trudny")
    skladniki: List[Skladnik] = Field(alias="ingredients", description="Lista składników potrzebnych do przygotowania")
    kroki: List[KrokPrzygotowania] = Field(alias="instructions", description="Lista kroków przygotowania potrawy")
    sugestie: str = Field(alias="suggestions", description="Dodatkowe sugestie lub warianty przepisu")

class Przepisy(BaseModel):
    przepisy: List[Przepis] = Field(alias="recipes", description="Lista przepisów na podstawie podanych składników")

# --- Logika backendu ---
def _generuj_przepisy(api_key: str, skladniki_w_lodowce: str) -> Przepisy:
    genai.configure(api_key=api_key)
    # ZMIANA: Prompt zaktualizowany, aby pokazywać modelowi angielskie klucze,
    # co zwiększa szansę na poprawną odpowiedź zgodną z naszymi aliasami.
    prompt = f"""Na podstawie podanych składników ("{skladniki_w_lodowce}") zaproponuj TRZY różne przepisy.
Każdy przepis powinien być inny.
Odpowiedz wyłącznie w formacie JSON zgodnym z poniższym schematem. Użyj angielskich nazw kluczy.
{{
  "recipes": [
    {{
      "name": "Nazwa przepisu 1",
      "preparation_time": "np. 30 minut",
      "difficulty": "łatwy",
      "ingredients": [
        {{ "name": "jajka", "quantity": 2, "unit": "szt." }}
      ],
      "instructions": [
        {{ "step": 1, "description": "Pierwszy krok przygotowania." }}
      ],
      "suggestions": "Dodatkowe sugestie."
    }}
  ]
}}
"""
    try:
        #model = genai.GenerativeModel("gemini-1.5-pro-latest")
        model = genai.GenerativeModel("gemini-2.5-pro-preview-03-25")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", temperature=0.4, max_output_tokens=8192,
            )
        )
        recipes_dict = json.loads(response.text)
        return Przepisy(**recipes_dict)
    except Exception as e:
        st.error(f"Wystąpił błąd podczas komunikacji z API Gemini: {e}")
        st.info("Spróbuj ponownie lub zmień listę składników.")
        raise e

@st.cache_data(show_spinner=False)
def generuj_przepisy_z_cache(_api_key: str, skladniki_w_lodowce: str) -> Przepisy:
    skladniki_sorted = sorted([s.strip().lower() for s in skladniki_w_lodowce.split(',') if s.strip()])
    key = ",".join(skladniki_sorted)
    if key in cache_memory: return cache_memory[key]
    przepisy = _generuj_przepisy(_api_key, skladniki_w_lodowce)
    cache_memory[key] = przepisy
    return przepisy

# --- Interfejs użytkownika ---
def main():
    st.title("🍳 Generator przepisów kulinarnych AI")
    st.write("Wybierz składniki z listy po lewej, dodaj własne, a ja zaproponuję Ci 3 różne przepisy.")

    if 'wybrane_skladniki' not in st.session_state: st.session_state.wybrane_skladniki = set()
    if 'dodatkowe_skladniki' not in st.session_state: st.session_state.dodatkowe_skladniki = []

    #api_key = st.text_input("Wpisz swój klucz API Google Gemini", type="password", help="Twój klucz nie będzie nigdzie zapisywany.")
    api_key = "AIzaSyBAGk9dEdcSqJPxXFW6spIzEDcCdClUzk4"

    with st.sidebar:
        st.header("📦 Wybierz składniki")
        wybrana_kategoria = st.radio("Wybierz kategorię:", options=KATEGORIE_SKLADNIKOW.keys(), label_visibility="collapsed")
        st.markdown("---")
        st.write(f"**{wybrana_kategoria}**")
        for skladnik in KATEGORIE_SKLADNIKOW[wybrana_kategoria]:
            if st.checkbox(skladnik, key=f"cb_{skladnik}", value=(skladnik in st.session_state.wybrane_skladniki)):
                if skladnik not in st.session_state.wybrane_skladniki:
                    st.session_state.wybrane_skladniki.add(skladnik)
                    st.rerun()
            elif skladnik in st.session_state.wybrane_skladniki:
                st.session_state.wybrane_skladniki.remove(skladnik)
                st.rerun()

    col_controls, col_results = st.columns([2, 3])

    with col_controls:
        st.subheader("🛒 Twoje wybrane składniki")
        wszystkie_skladniki = list(st.session_state.wybrane_skladniki) + st.session_state.dodatkowe_skladniki
        
        if not wszystkie_skladniki: st.info("👈 Zacznij wybierać składniki z listy po lewej.")
        
        for kategoria, lista_skladnikow_kat in KATEGORIE_SKLADNIKOW.items():
            wybrane_w_kategorii = st.session_state.wybrane_skladniki.intersection(lista_skladnikow_kat)
            if wybrane_w_kategorii:
                with st.container(border=True):
                    st.markdown(f"**{IKONY_KATEGORII.get(kategoria, '🛒')} {kategoria}**")
                    for skladnik in sorted(list(wybrane_w_kategorii)): st.markdown(f"&nbsp;&nbsp;&nbsp;• {skladnik}")
        
        if st.session_state.dodatkowe_skladniki:
            with st.container(border=True):
                st.markdown(f"**{IKONY_KATEGORII['Dodatkowe']} Dodatkowe**")
                for skladnik in st.session_state.dodatkowe_skladniki: st.markdown(f"&nbsp;&nbsp;&nbsp;• {skladnik}")

        st.markdown("---")
        st.subheader("➕ Dodaj własne składniki")
        nowy_skladnik = st.text_input("Wpisz składnik i naciśnij Enter:", placeholder="np. świeży imbir...", label_visibility="collapsed")
        if nowy_skladnik and nowy_skladnik.strip():
            if nowy_skladnik.strip().lower() not in [s.lower() for s in st.session_state.dodatkowe_skladniki]:
                st.session_state.dodatkowe_skladniki.append(nowy_skladnik.strip())
            st.rerun()
        
        if wszystkie_skladniki:
            st.markdown("---")
            c1, c2 = st.columns(2)
            if c1.button("🧹 Wyczyść wszystko", use_container_width=True):
                st.session_state.wybrane_skladniki.clear(); st.session_state.dodatkowe_skladniki.clear()
                if 'przepisy' in st.session_state: del st.session_state['przepisy']
                st.rerun()
            if c2.button("🍳 Generuj przepisy!", type="primary", use_container_width=True):
                if not api_key: st.error("Proszę podać klucz API Gemini.")
                else:
                    with st.spinner("🤖 Myślę nad przepisami..."):
                        try:
                            st.session_state.przepisy = generuj_przepisy_z_cache(api_key, ", ".join(sorted(wszystkie_skladniki)))
                        except Exception:
                            if 'przepisy' in st.session_state: del st.session_state['przepisy']
    
    with col_results:
        if 'przepisy' in st.session_state and st.session_state.przepisy:
            st.header("📋 Twoje propozycje przepisów")
            for i, przepis in enumerate(st.session_state.przepisy.przepisy):
                with st.container(border=True):
                    # Dzięki aliasom, w kodzie wciąż możemy używać polskich nazw pól
                    st.markdown(f"### {i+1}. {przepis.nazwa}")
                    r_col1, r_col2 = st.columns(2)
                    r_col1.metric("Czas przygotowania", przepis.czas_przygotowania)
                    r_col2.metric("Poziom trudności", przepis.poziom_trudnosci.capitalize())
                    st.markdown("---")
                    r_col1, r_col2 = st.columns([2, 3])
                    with r_col1:
                        st.markdown("##### 🥑 Składniki:")
                        for skladnik in przepis.skladniki:
                            ilosc_str = f"{skladnik.ilosc:.1f}" if isinstance(skladnik.ilosc, float) else str(skladnik.ilosc)
                            st.markdown(f"- **{skladnik.nazwa}**: {ilosc_str} {skladnik.jednostka}")
                    with r_col2:
                        st.markdown("##### 📝 Sposób przygotowania:")
                        for krok in sorted(przepis.kroki, key=lambda x: x.numer): st.markdown(f"**Krok {krok.numer}:** {krok.opis}")
                    if przepis.sugestie and przepis.sugestie.strip():
                        with st.expander("💡 Sugestie i warianty"): st.write(przepis.sugestie)
                st.write("")

if __name__ == "__main__":
    main()
