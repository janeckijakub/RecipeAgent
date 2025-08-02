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

                # Tworzymy 3 kolumny
                cols = st.columns(3)

                for i, (przepis, col) in enumerate(zip(przepisy.przepisy, cols), 1):
                    with col:
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

                        # Przygotowujemy tekst przepisu do skopiowania
                        przepis_text = f"Przepis: {przepis.nazwa}\nCzas przygotowania: {przepis.czas_przygotowania}\nPoziom trudności: {przepis.poziom_trudnosci}\n\nSkładniki:\n"
                        for skladnik in przepis.skladniki:
                            przepis_text += f"- {skladnik.ilosc} {skladnik.jednostka} {skladnik.nazwa}\n"
                        przepis_text += "\nSposób przygotowania:\n"
                        for krok in przepis.kroki:
                            przepis_text += f"{krok.numer}. {krok.opis}\n"
                        if przepis.sugestie.strip():
                            przepis_text += f"\nSugestie:\n{przepis.sugestie}\n"

                        # Wyświetlamy pole z kodem i przyciskiem kopiowania
                        st.code(przepis_text, language=None)

            except Exception as e:
                st.error(f"Wystąpił błąd podczas generowania przepisów: {e}")
