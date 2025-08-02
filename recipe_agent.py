import streamlit as st
from pydantic import BaseModel, Field
from typing import List, Union
import json
from anthropic import Anthropic

class Skladnik(BaseModel):
    nazwa: str = Field(description="Nazwa składnika")
    ilosc: Union[str, int] = Field(description="Ilość składnika")
    jednostka: str = Field(description="Jednostka miary, np. gram, łyżka, sztuka")

class KrokPrzygotowania(BaseModel):
    numer: int = Field(description="Numer kroku")
    opis: str = Field(description="Opis czynności do wykonania")

class Przepis(BaseModel):
    nazwa: str = Field(description="Nazwa potrawy")
    czas_przygotowania: str = Field(description="Czas potrzebny na przygotowanie")
    poziom_trudnosci: str = Field(description="Poziom trudności: łatwy, średni lub trudny")
    skladniki: List[Skladnik] = Field(description="Lista składników potrzebnych do przygotowania")
    kroki: List[KrokPrzygotowania] = Field(description="Lista kroków przygotowania potrawy")
    sugestie: str = Field(description="Dodatkowe sugestie lub warianty przepisu")

class Przepisy(BaseModel):
    przepisy: List[Przepis] = Field(description="Lista przepisów na podstawie podanych składników")

def generuj_przepisy(api_key: str, skladniki_w_lodowce: str) -> Przepisy:
    client = Anthropic(api_key=api_key)

    prompt = f"""Na podstawie podanych składników, które użytkownik ma w lodówce, zaproponuj TRZY różne przepisy kulinarne.
Składniki dostępne w lodówce: {skladniki_w_lodowce}

Utwórz 3 różne przepisy, które wykorzystują te składniki. Każdy przepis powinien być inny - np. z innej kuchni świata
lub reprezentować inny typ dania (przystawka, danie główne, deser). Jeśli brakuje jakichś podstawowych składników,
możesz założyć, że użytkownik ma je w swojej kuchni (jak sól, pieprz, oliwa).

Odpowiedź musi być wyłącznie w formacie JSON, bez dodatkowego tekstu, zgodnym z następującą strukturą:
{{
  "przepisy": [
    {{
      "nazwa": "Nazwa przepisu 1",
      "czas_przygotowania": "np. 30 minut",
      "poziom_trudnosci": "łatwy, średni lub trudny",
      "skladniki": [
        {{ "nazwa": "składnik 1", "ilosc": "liczba", "jednostka": "np. gram/sztuka/łyżka" }},
        {{ "nazwa": "składnik 2", "ilosc": "liczba", "jednostka": "np. gram/sztuka/łyżka" }}
      ],
      "kroki": [
        {{ "numer": 1, "opis": "Pierwszy krok przygotowania" }},
        {{ "numer": 2, "opis": "Drugi krok przygotowania" }}
      ],
      "sugestie": "Dodatkowe sugestie dotyczące przepisu"
    }},
    {{
      "nazwa": "Nazwa przepisu 2",
      "czas_przygotowania": "np. 45 minut",
      "poziom_trudnosci": "łatwy, średni lub trudny",
      "skladniki": [
        {{ "nazwa": "składnik 1", "ilosc": "liczba", "jednostka": "np. gram/sztuka/łyżka" }}
      ],
      "kroki": [
        {{ "numer": 1, "opis": "Pierwszy krok przygotowania" }}
      ],
      "sugestie": "Dodatkowe sugestie dotyczące przepisu"
    }},
    {{
      "nazwa": "Nazwa przepisu 3",
      "czas_przygotowania": "np. 20 minut",
      "poziom_trudnosci": "łatwy, średni lub trudny",
      "skladniki": [
        {{ "nazwa": "składnik 1", "ilosc": "liczba", "jednostka": "np. gram/sztuka/łyżka" }}
      ],
      "kroki": [
        {{ "numer": 1, "opis": "Pierwszy krok przygotowania" }}
      ],
      "sugestie": "Dodatkowe sugestie dotyczące przepisu"
    }}
  ]
}}
"""

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    response_text = response.content[0].text
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    json_str = response_text[json_start:json_end]

    try:
        recipes_dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        print("Błąd parsowania JSON:", e)
        print("Odpowiedź API:", response_text)
        raise e
    
    przepisy = Przepisy(**recipes_dict)
    return przepisy

def main():
    st.title("Generator przepisów kulinarnych 🍳")
    st.write("Podaj składniki, które masz w lodówce, a ja zaproponuję Ci 3 różne przepisy.")

    api_key = st.text_input("Wpisz swój klucz API Anthropic (ukryty)", type="password")
    skladniki = st.text_area("Składniki (oddzielone przecinkami)", height=100)

    if st.button("Generuj przepisy"):
        if not api_key:
            st.error("Proszę podać klucz API Anthropic.")
            return
        if not skladniki.strip():
            st.error("Proszę podać składniki.")
            return

        with st.spinner("Generuję przepisy..."):
            try:
                przepisy = generuj_przepisy(api_key, skladniki)

                # Tworzymy 5 kolumn: 3 na przepisy (25% każda), 2 na odstępy (12.5% każda)
                cols = st.columns([0.25, 0.125, 0.25, 0.125, 0.25])

                for i, przepis in enumerate(przepisy.przepisy):
                    col = cols[i*2]  # 0, 2, 4 - kolumny na przepisy
                    with col:
                        przepis_text = f"Przepis: {przepis.nazwa}\nCzas przygotowania: {przepis.czas_przygotowania}\nPoziom trudności: {przepis.poziom_trudnosci}\n\nSkładniki:\n"
                        for skladnik in przepis.skladniki:
                            przepis_text += f"- {skladnik.ilosc} {skladnik.jednostka} {skladnik.nazwa}\n"
                        przepis_text += "\nSposób przygotowania:\n"
                        for krok in przepis.kroki:
                            przepis_text += f"{krok.numer}. {krok.opis}\n"
                        if przepis.sugestie.strip():
                            przepis_text += f"\nSugestie:\n{przepis.sugestie}\n"

                        st.code(przepis_text, language=None)

            except Exception as e:
                st.error(f"Wystąpił błąd podczas generowania przepisów: {e}")

if __name__ == "__main__":
    main()








