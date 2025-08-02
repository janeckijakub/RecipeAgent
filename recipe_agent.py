import streamlit as st
from pydantic import BaseModel, Field
from typing import List
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

Odpowiedź musi być w formacie JSON zgodnym z następującą strukturą:
{{
  "przepisy": [
    {{
      "nazwa": "Nazwa przepisu 1",
      "czas_przygotowania": "np. 30 minut",
      "poziom_trudnosci": "łatwy/średni/trudny",
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
      "poziom_trudnosci": "łatwy/średni/trudny",
      "skladniki": [...],
      "kroki": [...],
      "sugestie": "Dodatkowe sugestie dotyczące przepisu"
    }},
    {{
      "nazwa": "Nazwa przepisu 3",
      "czas_przygotowania": "np. 20 minut",
      "poziom_trudnosci": "łatwy/średni/trudny",
      "skladniki": [...],
      "kroki": [...],
      "sugestie": "Dodatkowe sugestie dotyczące przepisu"
    }}
  ]
}}
"""

    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    response_text = response.content[0].text
    json_start = response_text.find('{')
    json_end = response_text.rfind('}') + 1
    json_str = response_text[json_start:json_end]

    recipes_dict = json.loads(json_str)
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
                for i, przepis in enumerate(przepisy.przepisy, 1):
                    st.header(f"Przepis {i}: {przepis.nazwa}")
                    st.markdown(f"**Czas przygotowania:** {przepis.czas_przygotowania}")
                    st.markdown(f"**Poziom trudności:** {przepis.poziom_trudnosci}")

                    st.subheader("Składniki:")
                    for skladnik in przepis.skladniki:
                        st.write(f"- {skladnik.ilosc} {skladnik.jednostka} {skladnik.nazwa}")

                    st.subheader("Sposób przygotowania:")
                    for krok in przepis.kroki:
                        st.write(f"{krok.numer}. {krok.opis}")

                    if przepis.sugestie.strip():
                        st.subheader("Sugestie:")
                        st.write(przepis.sugestie)

                    st.markdown("---")

            except Exception as e:
                st.error(f"Wystąpił błąd podczas generowania przepisów: {e}")

if __name__ == "__main__":
    main()

