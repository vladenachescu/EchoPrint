# PyShazam: Rapoarte de Dezvoltare (Weeks 7 & 8)

Acest document reunește rapoartele tehnice și bunele practici de inginerie software aplicate în cadrul proiectului **PyShazam**, conform cerințelor disciplinare MDS pentru săptămânile 7 și 8.

---

## 1. Ghid de Bug Reporting (Actionable Bug Reports)

Un raport de eroare (bug report) de calitate oferă dezvoltatorilor toate informațiile necesare pentru a reproduce, diagnostica și repara o problemă fără a fi nevoie de discuții suplimentare.

### Structura unui Raport Actionabil (Format Recomandat)
1. **Titlu**: Clar și succint, prefixat cu `[BUG]`.
2. **Descriere**: O scurtă prezentare a contextului în care se manifestă problema.
3. **Pași de reproducere**: O listă ordonată de pași preciși.
4. **Comportament Așteptat vs. Actual**: Ce trebuia să facă sistemul și ce a făcut de fapt.
5. **Mediul de Rulare**: OS, versiune Python, biblioteci cheie.
6. **Loguri / Stack Trace**: Mesajul exact din consolă sau fișierul de log.

---

### Studiu de Caz: Bug-uri reale identificate și remediate în PyShazam

#### 🐛 Bug 1: Eroare de Threading în SQLite (`sqlite3.ProgrammingError`)
*   **Descriere**: La lansarea recunoașterii audio în GUI, interfața grafică se bloca sau consola afișa o eroare fatală atunci când thread-ul de fundal încerca să salveze rezultatele în baza de date.
*   **Comportament Actual**: `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.`
*   **Comportament Așteptat**: Salvarea istoricului de căutare să se realizeze asincron din thread-ul secundar fără blocaje.
*   **Remediere**: Deoarece `DatabaseManager` utilizează modelul *Singleton* și conexiunea este partajată, s-a adăugat parametrul `check_same_thread=False` la inițializarea conexiunii sqlite3:
    ```python
    self.conn = sqlite3.connect(db_path, check_same_thread=False)
```

#### 🐛 Bug 2: Blocarea GUI la Erori în Thread-uri de Fundal
*   **Descriere**: Dacă înregistrarea audio sau procesarea dădea eroare (de ex. lipsa microfonului sau format fișier invalid), thread-ul de fundal crăpa silențios, iar GUI-ul rămânea blocat permanent în starea "Se procesează...".
*   **Remediere**: Întreaga funcție executată pe thread-ul secundar (`bg_recognition_task`) a fost împachetată într-un bloc `try-except` robust, care prinde orice excepție, resetează starea GUI-ului (`is_processing = False`) și afișează o fereastră popup de eroare (`messagebox.showerror`).

#### 🐛 Bug 3: UnicodeEncodeError pe Terminalele Windows (CP1252)
*   **Descriere**: Rularea aplicației în CLI sub Windows arunca erori de encodare la scrierea caracterelor cu diacritice românești (ex: `ă`, `ș`, `ț`).
*   **Comportament Actual**: `UnicodeEncodeError: 'charmap' codec can't encode character '\u0103' in position 12`.
*   **Remediere**: S-a recomandat activarea modului UTF-8 în Python prin setarea variabilei de mediu `PYTHONUTF8=1` la pornire:
    ```powershell
    $env:PYTHONUTF8=1
    python main.py listen --mock
```

#### 🐛 Bug 4: HTTP Error 404/429 pe Gemini API
*   **Descriere**: Apelul către modelul implicit `gemini-1.5-flash` a început să eșueze cu HTTP 404 deoarece modelul a fost retras sau restricționat de gateway-ul API Google. Modelul `gemini-2.0-flash` a returnat HTTP 429 din cauza limitelor de cotă de 0 request-uri pe conturile free-tier.
*   **Remediere**: Am utilizat un script de diagnostic pentru a lista modelele active pe cheia API și am identificat că modelul **`gemini-2.5-flash-lite`** este activ și stabil pe endpoint-ul `v1`. Am actualizat URL-ul în `ai/llm_client.py`.

---

## 2. Fluxul de Lucru Git & Pull Requests (PR)

Pentru a menține calitatea codului într-o echipă, proiectul PyShazam folosește un flux bazat pe ramificații (*Feature Branches*) și Pull Requests.

```mermaid
gitGraph
    commit id: "Inițializare"
    branch develop
    checkout develop
    commit id: "Configurare Structură"
    branch feature/ai-agents
    checkout feature/ai-agents
    commit id: "Implementare LLM client"
    commit id: "Implementare Trivia Agent"
    checkout develop
    merge feature/ai-agents id: "PR #1: AI Integration"
    branch hotfix/api-404
    checkout hotfix/api-404
    commit id: "Fix model URL"
    checkout develop
    merge hotfix/api-404 id: "PR #2: Fix API Model"
    checkout master
    merge develop id: "Release v1.1"
```

### Pașii pentru realizarea unui Pull Request (PR)
1.  **Crearea unui Branch Local**:
    ```bash
    git checkout develop
    git pull origin develop
    git checkout -b feature/nume-functionalitate
```
2.  **Dezvoltare și Commits**: Se fac commit-uri atomice cu mesaje descriptive.
3.  **Rularea Testelor**: Înainte de push, se rulează testele local:
    ```bash
    python -m unittest discover -s tests
```
4.  **Push pe GitHub și Creare PR**:
    *   Se deschide PR-ul către branch-ul `develop`.
    *   Se descriu modificările și se asociază issue-urile rezolvate (ex: `Closes #12`).
    *   Este necesară aprobarea a cel puțin unui coleg (Peer Review) și trecerea testelor automate (CI) înainte de merge.

---

## 3. Design Patterns Implementate

### A. Singleton Pattern (`DatabaseManager`)
*   **Scop**: Asigură că există o singură instanță a clasei care administrează conexiunea la baza de date SQLite, prevenind deschiderea multiplă de fișiere, conflictele de scriere și blocarea tabelelor.
*   **Implementare**: Folosește o metodă de clasă `__new__` care reține instanța unică în variabila privată `_instance`:
    ```python
    class DatabaseManager:
        _instance = None
        def __new__(cls, db_path='shazam_clone.db', *args, **kwargs):
            if not cls._instance:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
```

### B. Strategy Pattern (`AudioInputStrategy`)
*   **Scop**: Permite comutarea dinamică între diferite surse de intrare audio (microfon fizic, fișier preînregistrat sau date de test/mock generate sintetic) fără a modifica logica de bază a înregistrării și recunoașterii.
*   **Implementare**:
    *   *Interfață*: `AudioInputStrategy` definește metoda abstractă `record()`.
    *   *Strategii concrete*: `MicrophoneInputStrategy`, `FileInputStrategy`, `MockInputStrategy`.
    *   *Context*: `AudioRecorder` primește o strategie la inițializare și o deleagă pentru a obține datele audio.

---

## 4. Raport AI (AI Agents Overview)

Aplicația integrează o arhitectură formată din **4 agenți AI**, fiecare având un rol specific și autonom:

1.  **AI Noise & Quality Agent (`AINoiseAgent`)**:
    *   *Input*: Semnalul audio brut de la microfon/fișier.
    *   *Metodă*: Evaluează calitatea audio (SNR, RMS, Clipping). Dacă zgomotul este prea mare sau volumul prea mic, avertizează utilizatorul. Aplică atenuare spectrală (*Spectral Gating / Subtraction*) pentru eliminarea zgomotului static de fundal înainte de trimiterea la recunoaștere.
2.  **AI Recommendation Agent (`AIRecommendationAgent`)**:
    *   *Input*: ID-ul melodiei recunoscute.
    *   *Metodă*: Extrage automat tempo-ul (BPM) și timbrul spectral (Spectral Centroid, Flatness, Zero Crossing Rate). Calculează distanța euclidiană în spațiul caracteristicilor normalizate pentru a recomanda top 3 melodii similare din baza de date locală.
3.  **AI Music Trivia & Bio Agent (`AIMusicTriviaAgent`)**:
    *   *Input*: Numele piesei și al artistului.
    *   *Metodă*: Interoghează modelul `gemini-2.5-flash-lite` pentru a oferi biografia artistului și 3 detalii fascinante despre producția melodiei.
4.  **AI Lyrics & Sentiment Agent (`AILyricsAgent`)**:
    *   *Input*: Numele piesei.
    *   *Metodă*: Utilizează Gemini LLM pentru a analiza semnificația literară a versurilor, deduce sentimentul dominant și generează un rezumat în limba română.

> [!TIP]
> Diagramele detaliate de clasă și de secvență ale sistemului pot fi vizualizate în documentul [uml_diagrams.md](file:///C:/Users/jeanl/.gemini/antigravity/brain/ae619ee2-fa02-4b62-8e16-56d4eab3bcab/uml_diagrams.md).
