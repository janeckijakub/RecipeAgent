# ─────────────────────────────────────────────────────────────────────────────
#  🍳 Generator przepisów – wersja zoptymalizowana pod kątem szybkości
#  (Streamlit  ≥ 1.31, Python 3.9+)
# ─────────────────────────────────────────────────────────────────────────────
import json
from typing import List, Union, Optional

import streamlit as st
import google.generativeai as genai
from pydantic import BaseModel, Field, field_validator

# ─────────────────────────────────────────────────────────────────────────────
#  Konfiguracja strony
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Generator Przepisów", layout="wide")

# ─────────────────────────────────────────────────────────────────────────────
#  Stałe – kategorie składników i ikony
# ─────────────────────────────────────────────────────────────────────────────
KATEGORIE_SKLADNIKOW = {
    "Przyprawy i dodatki smakowe": [
        "Sól",
        "Pieprz czarny",
        "Czosnek granulowany",
        "Papryka słodka",
        "Papryka ostra",
        "Oregano",
        "Bazylia",
        "Curry",
        "Kminek",
        "Tymianek",
        "Liść laurowy",
        "Ziele angielskie",
        "Imbir mielony",
        "Sos sojowy",
    ],
    "Produkty zbożowe i mączne": [
        "Makaron",
        "Ryż biały",
        "Kasza gryczana",
        "Kasza jaglana",
        "Mąka pszenna",
        "Mąka żytnia",
        "Płatki owsiane",
        "Płatki kukurydziane",
        "Bułka tarta",
        "Chleb",
        "Tortilla pszenna",
        "Kuskus",
        "Quinoa",
    ],
    "Produkty białkowe": [
        "Jajka",
        "Filet z kurczaka",
        "Mięso mielone",
        "Tuńczyk w puszce",
        "Soczewica czerwona",
        "Soczewica zielona",
        "Ciecierzyca",
        "Fasola czerwona",
        "Fasola biała",
        "Groszek zielony",
        "Tofu",
        "Tempeh",
        "Parówki",
        "Ser biały (twaróg)",
    ],
    "Produkty mleczne i zamienniki": [
        "Mleko",
        "Mleko roślinne (np. owsiane)",
        "Masło",
        "Margaryna",
        "Jogurt naturalny",
        "Ser żółty",
        "Ser feta",
        "Śmietana",
        "Maślanka",
        "Serek wiejski",
        "Kefir",
    ],
    "Warzywa": [
        "Ziemniaki",
        "Marchewka",
        "Cebula",
        "Czosnek świeży",
        "Kapusta",
        "Ogórek",
        "Papryka",
        "Pomidory świeże",
        "Pomidory w puszce",
        "Cukinia",
        "Brokuł",
        "Kalafior",
        "Sałata",
        "Por",
    ],
    "Owoce": [
        "Jabłko",
        "Banan",
        "Cytryna",
        "Gruszka",
        "Śliwka",
        "Truskawki",
        "Maliny",
        "Winogrona",
        "Ananas w puszce",
        "Brzoskwinia",
        "Awokado",
    ],
    "Tłuszcze i oleje": [
        "Olej rzepakowy",
        "Oliwa z oliwek",
        "Olej kokosowy",
        "Masło klarowane",
        "Smalec",
        "Olej lniany",
        "Olej słonecznikowy",
    ],
    "Dodatki słodzące i konserwujące": [
        "Cukier biały",
        "Cukier trzcinowy",
        "Miód",
        "Syrop klonowy",
        "Ocet spirytusowy",
        "Ocet jabłkowy",
        "Sól peklująca",
        "Dżem",
        "Musztarda",
        "Ketchup",
    ],
}
IKONY_KATEGORII = {
    "Przyprawy i dodatki smakowe": "🌶️",
    "Produkty zbożowe i mączne": "🌾",
    "Produkty białkowe": "🍗",
    "Produkty mleczne i zamienniki": "🥛",
    "Warzywa": "🥕",
    "Owoce": "🍎",
    "Tłuszcze i oleje": "🫒",
    "Dodatki słodzące i konserwujące": "🍯",
    "Dodatkowe": "➕",
}

# ─────────────────────────────────────────────────────────────────────────────
#  Pydantic – modele z polskimi nazwami pól
# ─────────────────────────────────────────────────────────────────────────────
class Skladnik(BaseModel):
    nazwa: str
    ilosc: Union[str, int, float]
    jednostka: str = ""
    
    @field_validator('jednostka', mode='before')
    @classmethod
    def validate_jednostka(cls, v):
        """Zamień None na pusty string"""
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

# ─────────────────────────────────────────────────────────────────────────────
#  Pomocnicze funkcje – wygenerowanie przepisu, cache
# ─────────────────────────────────────────────────────────────────────────────
def _generuj_przepisy(api_key: str, skladniki_str: str) -> Optional[Przepisy]:
    """Komunikacja z modelem Gemini – zwraca obiekt Przepisy lub None w przypadku błędu."""
    genai.configure(api_key=api_key)

    prompt = f"""Jesteś asystentem kulinarnym. Odpowiadaj wyłącznie w języku polskim.
Na podstawie podanych składników ("{skladniki_str}") zaproponuj TRZY różne przepisy.
Każdy przepis powinien być inny i wykorzystywać dostępne składniki.

WYNIK ZWRÓĆ WYŁĄCZNIE JAKO POPRAWNY JSON, bez żadnego dodatkowego tekstu, bez markdown, bez komentarzy.
Użyj dokładnie następującej struktury i kluczy po polsku:

{{
  "przepisy": [
    {{
      "nazwa": "Nazwa przepisu 1",
      "czas_przygotowania": "30 minut",
      "poziom_trudnosci": "łatwy",
      "skladniki": [
        {{ "nazwa": "jajka", "ilosc": "2", "jednostka": "szt." }},
        {{ "nazwa": "mąka", "ilosc": "200", "jednostka": "g" }}
      ],
      "kroki": [
        {{ "numer": 1, "opis": "Pierwszy krok przygotowania." }},
        {{ "numer": 2, "opis": "Drugi krok przygotowania." }}
      ],
      "sugestie": "Dodatkowe sugestie dotyczące przepisu."
    }}
  ]
}}

PRZYKŁAD POPRAWNEJ ODPOWIEDZI:
{{
  "przepisy": [
    {{
      "nazwa": "Sałatka z pomidorów i bazylii",
      "czas_przygotowania": "15 minut",
      "poziom_trudnosci": "łatwy",
      "skladniki": [
        {{ "nazwa": "pomidory", "ilosc": "3", "jednostka": "szt." }},
        {{ "nazwa": "bazylia świeża", "ilosc": "1", "jednostka": "garść" }},
        {{ "nazwa": "oliwa", "ilosc": "2", "jednostka": "łyżki" }},
        {{ "nazwa": "sól", "ilosc": "1", "jednostka": "szczypta" }}
      ],
      "kroki": [
        {{ "numer": 1, "opis": "Pokrój pomidory w cząstki." }},
        {{ "numer": 2, "opis": "Dodaj listki bazylii, skrop oliwą i dopraw solą." }}
      ],
      "sugestie": "Można dodać ser mozzarella lub feta dla większej sytości."
    }}
  ]
}}

WAŻNE ZASADY:
- Każdy przepis MUSI być kompletny i wykonalny
- Użyj realistycznych ilości składników
- Podaj jasne instrukcje krok po kroku
- Zaproponuj przydatne sugestie
- Wszystko w języku polskim
- Zwróć WYŁĄCZNIE JSON, bez żadnego tekstu przed ani po
- Użyj dokładnie tych kluczy: nazwa, czas_przygotowania, poziom_trudnosci, skladniki, kroki, sugestie
- W składnikach: nazwa, ilosc, jednostka
- W krokach: numer, opis

Składniki do wykorzystania: {skladniki_str}"""

    try:
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=4000,
                candidate_count=1,
            ),
        )
        
        # Sprawdzenie czy response zawiera tekst
        if not response.text or not response.text.strip():
            st.error("Model nie zwrócił żadnej odpowiedzi. Spróbuj ponownie.")
            return None
            
        try:
            # Oczyszczenie odpowiedzi z ewentualnych znaczników markdown
            clean_response = response.text.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response[7:]
            if clean_response.endswith("```"):
                clean_response = clean_response[:-3]
            clean_response = clean_response.strip()
            
            recipes_dict = json.loads(clean_response)
            
            # Bezpośrednia walidacja Pydantic - bez konwersji
            return Przepisy(**recipes_dict)
            
        except json.JSONDecodeError as je:
            st.error(f"Błąd parsowania odpowiedzi JSON: {je}")
            st.error("Otrzymana odpowiedź:")
            st.code(response.text)
            return None
        except Exception as pe:
            st.error(f"Błąd walidacji danych przepisów: {pe}")
            st.error("Model nie zwrócił odpowiedzi w oczekiwanym formacie polskim.")
            with st.expander("Zobacz surową odpowiedź"):
                st.code(response.text)
            return None
            
    except Exception as e:
        st.error(f"Błąd komunikacji z API Gemini: {e}")
        st.info("Spróbuj ponownie lub zmodyfikuj listę składników.")
        return None


@st.cache_data(show_spinner=False)
def generuj_przepisy_z_cache(api_key: str, skladniki_str: str) -> Optional[Przepisy]:
    """
    Wrapper z cache. Klucz cache jest wyliczany z posortowanej,
    znormalizowanej listy składników.
    """
    # Normalizacja – usuń spacje, małe litery, sortuj, połącz przecinkami
    normalized = ",".join(
        sorted([s.strip().lower() for s in skladniki_str.split(",") if s.strip()])
    )
    # Wywołujemy jednorazowo funkcję generującą (wynik zostanie zapamiętany)
    return _generuj_przepisy(api_key, normalized)


# ─────────────────────────────────────────────────────────────────────────────
#  Callbacki – poprawione zarządzanie stanem
# ─────────────────────────────────────────────────────────────────────────────
def _toggle_ingredient(skladnik_name):
    """
    Wywoływany po zmianie konkretnego checkboxa.
    Dodaje lub usuwa składnik z listy wybranych.
    """
    checkbox_key = f"cb_{skladnik_name}"
    if st.session_state.get(checkbox_key, False):
        # Checkbox zaznaczony - dodaj składnik
        st.session_state.wybrane_skladniki.add(skladnik_name)
    else:
        # Checkbox odznaczony - usuń składnik
        st.session_state.wybrane_skladniki.discard(skladnik_name)


def _add_custom():
    """
    Dodaje wpisany w polu tekstowym własny składnik.
    """
    nowy = st.session_state.get("custom_input", "").strip()
    if nowy:
        # unikamy duplikatów (ignorujemy wielkość liter)
        dolower = [x.lower() for x in st.session_state.dodatkowe_skladniki]
        if nowy.lower() not in dolower:
            st.session_state.dodatkowe_skladniki.append(nowy)
    # czyścimy pole tekstowe
    st.session_state.custom_input = ""


def _clear_all():
    """Czyści wszystkie wybrane składniki"""
    # Wyczyść checkboxy
    for kat, lista in KATEGORIE_SKLADNIKOW.items():
        for s in lista:
            key = f"cb_{s}"
            if key in st.session_state:
                st.session_state[key] = False
    
    # Wyczyść listy składników
    st.session_state.wybrane_skladniki = set()
    st.session_state.dodatkowe_skladniki = []
    
    # Wyczyść przepisy
    st.session_state.przepisy = None


# ─────────────────────────────────────────────────────────────────────────────
#  Inicjalizacja session_state (pierwszy dostęp)
# ─────────────────────────────────────────────────────────────────────────────
if "wybrane_skladniki" not in st.session_state:
    st.session_state.wybrane_skladniki = set()
if "dodatkowe_skladniki" not in st.session_state:
    st.session_state.dodatkowe_skladniki = []
if "przepisy" not in st.session_state:
    st.session_state.przepisy = None

# -------------------------------------------------------------------------
#  Interfejs użytkownika
# -------------------------------------------------------------------------
st.title("🍳 Generator przepisów kulinarnych")
st.write(
    "Wybierz składniki z listy po lewej, dodaj własne, a otrzymasz 3 różne przepisy."
)

# -------------------------------------------------------------------------
#  Sidebar – wybór kategorii i składników (checkboxy z `on_change`)
# -------------------------------------------------------------------------
with st.sidebar:
    st.header("📦 Wybierz składniki")
    wybrana_kategoria = st.radio(
        "Kategoria:",
        options=list(KATEGORIE_SKLADNIKOW.keys()),
        index=0,
        label_visibility="collapsed",
    )
    st.markdown("---")
    # wyświetlamy tylko składniki z aktualnie wybranej kategorii
    for skladnik in KATEGORIE_SKLADNIKOW[wybrana_kategoria]:
        st.checkbox(
            skladnik,
            key=f"cb_{skladnik}",
            value=skladnik in st.session_state.wybrane_skladniki,
            on_change=lambda s=skladnik: _toggle_ingredient(s),
        )

# -------------------------------------------------------------------------
#  Główne kolumny: po lewej – kontrolki, po prawej – wyniki
# -------------------------------------------------------------------------
col_controls, col_results = st.columns([2, 3])

# ------------------------ POLE KONTROLE (lewa kolumna) --------------------
with col_controls:
    st.subheader("🛒 Twoje wybrane składniki")
    wszystkie_skladniki = list(
        st.session_state.wybrane_skladniki
    ) + st.session_state.dodatkowe_skladniki

    if not wszystkie_skladniki:
        st.info("👈 Zacznij wybierać składniki z listy po lewej.")
    else:
        # grupowanie po kategoriach (tylko te, które naprawdę mają wybrane pozycje)
        for kat, lista in KATEGORIE_SKLADNIKOW.items():
            wybrane_w_kat = st.session_state.wybrane_skladniki.intersection(lista)
            if wybrane_w_kat:
                with st.container(border=True):
                    st.markdown(f"**{IKONY_KATEGORII.get(kat, '🛒')} {kat}**")
                    for s in sorted(wybrane_w_kat):
                        st.markdown(f"&nbsp;&nbsp;&nbsp;• {s}")

        # własne składniki – oddzielna sekcja
        if st.session_state.dodatkowe_skladniki:
            with st.container(border=True):
                st.markdown(f"**{IKONY_KATEGORII['Dodatkowe']} Dodatkowe**")
                for s in st.session_state.dodatkowe_skladniki:
                    st.markdown(f"&nbsp;&nbsp;&nbsp;• {s}")

    st.markdown("---")
    st.subheader("➕ Dodaj własne składniki")
    st.text_input(
        "Wpisz składnik i naciśnij Enter:",
        key="custom_input",
        placeholder="np. świeży imbir...",
        on_change=_add_custom,
        label_visibility="collapsed",
    )

    if wszystkie_skladniki:
        st.markdown("---")
        c1, c2 = st.columns(2)
        if c1.button("🧹 Wyczyść wszystko", use_container_width=True, on_click=_clear_all):
            pass  # Callback już wszystko obsłuży
            
        if c2.button("🍳 Generuj przepisy!", type="primary", use_container_width=True):
            # -----------------------------------------------------------------
            #  Pobranie klucza API
            # -----------------------------------------------------------------
            api_key = "AIzaSyBAGk9dEdcSqJPxXFW6spIzEDcCdClUzk4"
            if not api_key:
                st.error("Podaj klucz API Gemini.")
            else:
                with st.spinner("🤖 Myślę nad przepisami..."):
                    result = generuj_przepisy_z_cache(
                        api_key, ", ".join(sorted(ws.strip() for ws in wszystkie_skladniki))
                    )
                    st.session_state.przepisy = result

# ------------------------ POLE WYNIKI (prawa kolumna) --------------------
with col_results:
    # Bezpieczne sprawdzenie istnienia przepisów
    if (hasattr(st.session_state, 'przepisy') and 
        st.session_state.przepisy is not None and 
        hasattr(st.session_state.przepisy, 'przepisy') and 
        st.session_state.przepisy.przepisy):
        
        st.header("📋 Twoje propozycje przepisów")
        for idx, przepis in enumerate(st.session_state.przepisy.przepisy, start=1):
            with st.container(border=True):
                st.markdown(f"### {idx}. {przepis.nazwa}")
                c1, c2 = st.columns(2)
                c1.metric("Czas przygotowania", przepis.czas_przygotowania)
                c2.metric("Poziom trudności", przepis.poziom_trudnosci.capitalize())
                st.markdown("---")
                # składniki i instrukcje
                col_ing, col_inst = st.columns([2, 3])
                with col_ing:
                    st.markdown("##### 🥑 Składniki:")
                    for sklad in przepis.skladniki:
                        ilosc = (
                            f"{sklad.ilosc:.1f}"
                            if isinstance(sklad.ilosc, float)
                            else str(sklad.ilosc)
                        )
                        jednostka = f" {sklad.jednostka}" if sklad.jednostka else ""
                        st.markdown(f"- **{sklad.nazwa}**: {ilosc}{jednostka}")
                with col_inst:
                    st.markdown("##### 📝 Sposób przygotowania:")
                    for krok in sorted(przepis.kroki, key=lambda k: k.numer):
                        st.markdown(f"**Krok {krok.numer}:** {krok.opis}")

                if przepis.sugestie and przepis.sugestie.strip():
                    with st.expander("💡 Sugestie i warianty"):
                        st.write(przepis.sugestie)
                st.write("")  # odstęp między przepisami
                
    elif (hasattr(st.session_state, 'przepisy') and 
          st.session_state.przepisy is not None):
        # Przypadek gdy przepisy zostały ustawione ale są puste/nieprawidłowe
        st.warning("Nie udało się wygenerować przepisów. Spróbuj ponownie z innymi składnikami.")

# -------------------------------------------------------------------------
#  Koniec skryptu
# -------------------------------------------------------------------------
