name: Bug Report
description: Raportează o problemă întâlnită în aplicația PyShazam
title: "[BUG] - Scurtă descriere a problemei"
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Mulțumim pentru raportarea bug-ului! Te rugăm să completezi câmpurile de mai jos pentru a ne ajuta să identificăm și să rezolvăm problema cât mai repede.
  - type: textarea
    id: description
    attributes:
      label: Descrierea Bug-ului
      description: O descriere clară și concisă a problemei constatate.
      placeholder: De exemplu: Aplicația se blochează atunci când...
    validations:
      required: true
  - type: textarea
    id: reproduction
    attributes:
      label: Pași pentru Reproducere
      description: Pașii pe care trebuie să îi urmăm pentru a reproduce comportamentul greșit.
      placeholder: |
        1. Rulați comanda 'python main.py'
        2. Selectați sursa 'Microfon'
        3. Apăsați butonul 'Ascultă'
        4. Observați eroarea în consolă...
    validations:
      required: true
  - type: textarea
    id: behavior
    attributes:
      label: Comportament Așteptat vs. Comportament Actual
      description: Ce ar fi trebuit să se întâmple și ce s-a întâmplat de fapt.
      placeholder: |
        Așteptat: Să înceapă înregistrarea și să afișeze contorul.
        Actual: GUI-ul îngheață și aruncă eroarea X.
    validations:
      required: true
  - type: input
    id: environment
    attributes:
      label: Mediu de Rulare
      description: Sistemul de operare, versiunea Python și alte detalii relevante.
      placeholder: Windows 11, Python 3.10.4, venv activat
    validations:
      required: true
  - type: textarea
    id: logs
    attributes:
      label: Loguri / Mesaje de Eroare
      description: Copiați logurile sau traceback-ul complet din consolă aici.
      placeholder: Traceback (most recent call last)...
    validations:
      required: false
