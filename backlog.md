# Project Backlog - PyShazam (MDS)

Acest document conține backlog-ul de produs și planificarea pe sprint-uri pentru proiectul **PyShazam**.

## Product Backlog (User Stories & Tasks)

### Epic 1: Funcționalități de Bază (Audio Recognition)
*   **MDS-1**: Ca utilizator, doresc să pot înregistra sunete de la microfon pentru a le recunoaște. (Done)
*   **MDS-2**: Ca utilizator, doresc să pot procesa un folder de melodii locale pentru a genera amprente audio în baza de date. (Done)
*   **MDS-3**: Ca utilizator, doresc o interfață CLI prietenoasă pentru rularea aplicației. (Done)

### Epic 2: Structură Project & Calitate Cod
*   **MDS-4**: Ca dezvoltator, doresc să am un repo Git configurat corect cu reguli de ignore pentru baze de date și mediu virtual. (Done)
*   **MDS-5**: Ca dezvoltator, doresc implementarea a cel puțin 2 Design Patterns pentru a asigura modularitatea (Singleton și Strategy). (Done)
*   **MDS-6**: Ca dezvoltator, doresc o suită completă de teste unitare automate pentru asigurarea funcționării procesorului audio și a bazei de date. (Done)

### Epic 3: Inteligență Artificială (AI Agents)
*   **MDS-7**: Ca utilizator, doresc un agent AI care curăță zgomotul de fundal și evaluează calitatea audio înainte de recunoaștere. (Done)
*   **MDS-8**: Ca utilizator, doresc recomandări de melodii bazate pe similaritatea audio a melodiei recunoscute. (Done)

### Epic 4: GUI & Administrare Bază de Date (Specificații Noi)
*   **MDS-9**: Ca utilizator, doresc o interfață grafică desktop (GUI) de unde să pot încărca fișiere de analizat sau să folosesc microfonul. (Done)
*   **MDS-10**: Ca utilizator, doresc să pot vizualiza melodiile din baza de date în interfață și să pot aplica filtre de căutare după nume. (Done)
*   **MDS-11**: Ca utilizator, doresc posibilitatea de a șterge melodii și de a le modifica numele (CRUD complet) direct din interfață. (Done)
*   **MDS-12**: Ca utilizator, doresc formarea și vizualizarea unui istoric al căutărilor realizate. (Done)

### Epic 5: Structură Modulară & Integrare Gemini LLM
*   **MDS-13**: Ca dezvoltator, doresc organizarea codului pe pachete modulare standard Python (`db/`, `audio/`, `ai/`, `gui/`, `tests/`). (Done)
*   **MDS-14**: Ca utilizator, doresc integrarea a doi agenți AI LLM (Gemini API) pentru trivia/biografie și semnificația versurilor, cu sistem de fallback offline (Mock). (Done)
*   **MDS-15**: Ca utilizator, doresc posibilitatea de a configura cheia Gemini API direct din GUI și salvarea ei în DB SQLite. (Done)

---

## Planificare Sprint-uri

### Sprint 1: Weeks 3-4 (Planificare și Arhitectură)
*   [x] Definire specificații și arhitectură de bază.
*   [x] Stabilire schemă bază de date SQLite.
*   [x] Alegerea algoritmului de fingerprinting (Constellation Map + Hashing).

### Sprint 2: Weeks 9-10 (MVP - Minimum Viable Product)
*   [x] Implementare `audio_processor.py` (librosa FFT spectrogram).
*   [x] Implementare `db_manager.py` pentru salvarea amprentelor.
*   [x] Implementare CLI în `main.py`.

### Sprint 3: Weeks 11-12 (Design Patterns & Teste & AI - Curent)
*   [x] Inițializare Git local și creare `.gitignore`.
*   [x] Refactorizare Singleton (`db_manager.py`) și Strategy (`audio_source.py`).
*   [x] Creare agenți AI (`ai_noise_agent.py` și `ai_recommendation_agent.py`).
*   [x] Scrierea testelor unitare automate pentru componentele core.
*   [x] Integrare și testare de sistem.
*   [x] Creare diagramă de clase UML.

### Sprint 4: Weeks 13-14 (GUI, CRUD & Search History - Finalizare)
*   [x] Creare tabelă `search_history` în baza de date SQLite.
*   [x] Implementare funcționalități CRUD de ștergere și actualizare melodie în `db_manager.py`.
*   [x] Dezvoltare interfață grafică desktop (`gui.py`) în format premium Dark Theme cu 4 tab-uri:
    - *Tab Recunoaștere* (inclusiv rulare AI Noise Agent, Denoising și Recomandări AI).
    - *Tab Administrare* (tabel cu melodii, filtrare după nume, editare nume, ștergere).
    - *Tab Istoric Căutări* (tabel cu căutările logate în DB).
    - *Tab Adăugare Melodii* (învață folder prin selectare vizuală).
*   [x] Adăugare teste unitare pentru CRUD și istoricul de căutare.
*   [x] Integrare argument `--gui` în `main.py`.

### Sprint 5: Weeks 15-16 (Restructurare Modulară & Google Gemini API)
*   [x] Creare directoare de pachet `db/`, `audio/`, `ai/`, `gui/` și organizare fișiere.
*   [x] Implementare tabelă `config` pentru salvarea API Key în SQLite.
*   [x] Implementare `ai/llm_client.py` pentru interogarea HTTP Gemini API cu fallback offline (Mock) complet.
*   [x] Implementare agenți AI `AIMusicTriviaAgent` (trivia melodie & bio) și `AILyricsAgent` (sens versuri & sentiment).
*   [x] Modificare GUI pentru a include câmp de salvare Gemini API Key și panouri tabulate pentru agenții LLM.
*   [x] Actualizare importuri în codul sursă și suita de teste automate (23 de teste unitare de succes).
