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
*   **MDS-6**: Ca dezvoltator, doresc o suită completă de teste unitare automate pentru asigurarea funcționării procesorului audio și a bazei de date. (In Progress)

### Epic 3: Inteligență Artificială (AI Agents)
*   **MDS-7**: Ca utilizator, doresc un agent AI care curăță zgomotul de fundal și evaluează calitatea audio înainte de recunoaștere. (In Progress)
*   **MDS-8**: Ca utilizator, doresc recomandări automate de melodii bazate pe similaritatea audio a melodiei recunoscute. (In Progress)

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
*   [/] Refactorizare Singleton (`db_manager.py`) și Strategy (`audio_source.py`).
*   [/] Creare agenți AI (`ai_noise_agent.py` și `ai_recommendation_agent.py`).
*   [ ] Scrierea testelor unitare automate pentru componentele core.
*   [ ] Integrare și testare de sistem.
*   [ ] Creare diagramă de clase UML.
