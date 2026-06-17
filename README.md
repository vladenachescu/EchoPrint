# 🎙️ EchoPrint (PyShazam)

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-SQLite-lightgrey.svg)](https://www.sqlite.org/)
[![UI Framework](https://img.shields.io/badge/UI-Tkinter-orange.svg)](https://docs.python.org/3/library/tkinter.html)
[![AI Integration](https://img.shields.io/badge/AI-Google%20Gemini%20API-purple.svg)](https://aistudio.google.com/)
[![Audio Processing](https://img.shields.io/badge/audio-Librosa%20%2F%20SciPy-red.svg)](https://librosa.org/)

**EchoPrint** este o aplicație desktop de recunoaștere audio dezvoltată în Python, inspirată de algoritmul de fingerprinting spectral utilizat de Shazam. Proiectul a fost realizat conform cerințelor academice și standardelor de inginerie software pentru disciplina **Metode de Dezvoltare Software (MDS)** de la FMI Unibuc.

Aplicația scanează și „învață” melodii dintr-o bibliotecă locală (generând amprente spectrale stocate eficient în SQLite), iar apoi poate identifica în timp real o piesă redată live la microfon sau încărcată dintr-un fișier. De asemenea, folosește agenți AI autonomi pentru atenuarea zgomotului de fundal, generarea de recomandări similare și extragerea de trivia/biografii și analiza versurilor prin LLM.


## ✨ Funcționalități Cheie


Aplicația este structurată în jurul a patru piloni funcționali:

### 1. Recunoaștere Audio Algoritmică
*   **Strategii Flexibile de Input**: Înregistrare directă de la microfonul fizic, citirea unui fișier audio existent (MP3, WAV, FLAC etc.) sau generarea unui flux Mock artificial pentru testare (implementate prin *Strategy Pattern*).
*   **Procesare Digitală a Semnalelor (DSP)**: Utilizarea transformatei Fourier rapide (FFT) prin intermediul bibliotecii `librosa` pentru generarea de spectrograme.
*   **Constellation Map & Hashing**: Extragerea punctelor de maxim din spectrogramă (vârfuri locale) și formarea de perechi de hash-uri bazate pe frecvențe și decalaje temporale pentru o căutare ultrarapidă.

### 2. Administrare Bază de Date (CRUD)
*   **Interfață de Vizualizare**: Afișarea tuturor melodiilor stocate într-un tabel de tip `Treeview` Tkinter.
*   **Filtrare Dinamică**: Căutare instanta în baza de date pe măsură ce utilizatorul tastează numele melodiei.
*   **Ștergere & Modificare**: Editarea numelui de afișare al melodiilor sau ștergerea lor completă (cu constrângerea `ON DELETE CASCADE` care curăță automat amprentele și caracteristicile asociate în SQLite).

### 3. Istoric Căutări & Monitorizare
*   Logarea automată a fiecărei încercări de recunoaștere în tabela `search_history`.
*   Monitorizarea parametrilor tehnici: data/ora, sursa audio utilizată, piesa identificată, raportul semnal-zgomot (SNR) estimat și scorul de încredere (numărul de potriviri de hash-uri).
*   Posibilitatea golirii complete a istoricului direct din interfață.

### 4. Agenți de Inteligență Artificială (AI Agents)
Aplicația folosește **4 agenți AI autonomi** care cooperează în pipeline:
*   🧼 **AI Noise Agent (`AINoiseAgent`)**: Evaluează calitatea audio brută (SNR, RMS, clipping) și elimină zgomotul static de fundal prin subtracție spectrală (*Spectral Gating*) înainte de analiză.
*   🎵 **AI Recommendation Agent (`AIRecommendationAgent`)**: Extrage tempo-ul (BPM) și timbrul spectral (flatness, centroid, zero crossing rate) pentru a sugera top 3 melodii similare din baza de date folosind distanța Euclidiană normalizată.
*   💡 **AI Music Trivia Agent (`AIMusicTriviaAgent`)**: Folosește Gemini LLM pentru a oferi detalii de trivia inedite despre piesă și o scurtă biografie a artistului.
*   📝 **AI Lyrics Agent (`AILyricsAgent`)**: Utilizează Gemini LLM pentru a extrage sentimentul predominant din versurile melodiei și a genera un rezumat tradus în limba română.

---

## 🏗️ Arhitectură și Design Patterns

Proiectul este proiectat modular, asigurând decuplarea responsabilităților:

```
PyShazam/
│
├── main.py                # Punctul de intrare (CLI parser și lansator GUI)
├── echoprint.db           # Baza de date SQLite auto-generată
├── requirements.txt       # Dependențele de biblioteci Python
│
├── audio/                 # Pachetul pentru procesare audio
│   ├── audio_processor.py # FFT, Constellation Map și hashing spectral
│   ├── audio_source.py    # Strategiile de input audio (Strategy Pattern)
│   └── recorder.py        # Clasa utilitară de înregistrare audio
│
├── db/                    # Pachetul pentru persistența datelor
│   └── db_manager.py      # SQLite Database Manager (Singleton Pattern)
│
├── ai/                    # Pachetul pentru logica agenților AI
│   ├── ai_noise_agent.py          # Analiză calitate și atenuare zgomot
│   ├── ai_recommendation_agent.py # Extragere features și similaritate
│   ├── llm_client.py              # Client HTTP securizat pentru Gemini API
│   ├── ai_trivia_agent.py         # Agent Trivia & Biografie (LLM)
│   └── ai_lyrics_agent.py         # Agent Analiză Versuri & Sentiment (LLM)
│
├── gui/                   # Pachetul pentru interfața grafică
│   └── gui.py             # GUI în Tkinter cu Dark Theme
│
└── tests/                 # Suita de teste automate
    ├── test_audio_processor.py
    ├── test_db_manager.py
    └── test_ai_agents.py
```

### Design Patterns Utilizate:
1.  **Singleton (`DatabaseManager`)**: Conexiunea SQLite este instanțiată o singură dată și partajată la nivelul întregii aplicații pentru a preveni blocarea fișierului bazei de date și conflictele de scriere pe thread-uri diferite.
2.  **Strategy (`AudioInputStrategy`)**: Decuplează `AudioRecorder` de sursa fizică. La runtime sau în teste se poate injecta `MicrophoneInputStrategy`, `FileInputStrategy` sau `MockInputStrategy` fără a afecta codul de înregistrare.

### Diagrama de Clase UML:
```mermaid
classDiagram
    class AudioInputStrategy {
        <<interface>>
        +record(duration_seconds: int)* ndarray
    }
    class MicrophoneInputStrategy {
        +sample_rate: int
        +record(duration_seconds: int) ndarray
    }
    class FileInputStrategy {
        +file_path: str
        +sample_rate: int
        +record(duration_seconds: int) ndarray
    }
    class MockInputStrategy {
        +sample_rate: int
        +record(duration_seconds: int) ndarray
    }
    
    AudioInputStrategy <|.. MicrophoneInputStrategy
    AudioInputStrategy <|.. FileInputStrategy
    AudioInputStrategy <|.. MockInputStrategy
    
    class AudioRecorder {
        -strategy: AudioInputStrategy
        -sample_rate: int
        +record(duration_seconds: int) ndarray
    }
    AudioRecorder --> AudioInputStrategy : utilizează
    
    class DatabaseManager {
        -conn: Connection
        -cursor: Cursor
        -instance: DatabaseManager$
        +connect()
        +create_tables()
        +get_config_value(key: str) str
        +set_config_value(key: str, val: str) bool
        +insert_song(song_name: str, file_hash: str) int
        +insert_fingerprints(fingerprints: list)
        +find_song_by_file_hash(file_hash: str) int
        +get_song_by_id(song_id: int) str
        +find_matches(hashes: list) list
        +insert_features(song_id: int, bpm: float, centroid: float, flatness: float, zcr: float) bool
        +get_features(song_id: int) tuple
        +get_all_features() list
        +update_song_name(song_id: int, new_name: str) bool
        +delete_song(song_id: int) bool
        +get_all_songs_metadata() list
        +insert_history(source: str, song_id: int, snr: float, score: int) bool
        +get_history() list
        +clear_history() bool
        +close()
    }
    
    class AudioProcessor {
        +load_audio(file_path: str) tuple
        +get_spectrogram(y: ndarray) ndarray
        +get_constellation_map(spectrogram: ndarray) list
        +generate_hashes(peaks: list) list
        +fingerprint_file(file_path: str) list
        +fingerprint_audio_data(y: ndarray) list
    }
    
    class AINoiseAgent {
        +sample_rate: int
        +assess_quality(y: ndarray) dict
        +denoise(y: ndarray) ndarray
    }
    
    class AIRecommendationAgent {
        -db: DatabaseManager
        +extract_features(file_path: str) dict
        +recommend_for_song(song_id: int, top_n: int) list
    }
    AIRecommendationAgent --> DatabaseManager : interoghează
    
    class GeminiLLMClient {
        -db: DatabaseManager
        -api_url: str
        +get_api_key() str
        +call_gemini_api(prompt: str) str
        +generate(prompt: str, fallback_type: str, song_name: str) str
    }
    GeminiLLMClient --> DatabaseManager : citește cheia API
    
    class AIMusicTriviaAgent {
        -llm_client: GeminiLLMClient
        +get_trivia(song_name: str) str
    }
    AIMusicTriviaAgent --> GeminiLLMClient : utilizează
    
    class AILyricsAgent {
        -llm_client: GeminiLLMClient
        +get_lyrics_analysis(song_name: str) str
    }
    AILyricsAgent --> GeminiLLMClient : utilizează
    
    class EchoPrintGUI {
        -db: DatabaseManager
        -recorder: AudioRecorder
        -noise_agent: AINoiseAgent
        -recommender: AIRecommendationAgent
        -trivia_agent: AIMusicTriviaAgent
        -lyrics_agent: AILyricsAgent
        +create_widgets()
        +run()
    }
    EchoPrintGUI --> DatabaseManager
    EchoPrintGUI --> AudioRecorder
    EchoPrintGUI --> AINoiseAgent
    EchoPrintGUI --> AIRecommendationAgent
    EchoPrintGUI --> AIMusicTriviaAgent
    EchoPrintGUI --> AILyricsAgent
```

---

## ⚙️ Precondiții și Cerințe

Înainte de a rula proiectul, asigurați-vă că aveți instalate:
*   **Python 3.10+** (descărcat de pe site-ul oficial sau Microsoft Store).
*   **FFmpeg** (utilizat în fundal de `librosa` / `soundfile` pentru decodarea fișierelor audio). Aplicația va încerca automat să instaleze și să configureze căile statice de FFmpeg folosind pachetul `static_ffmpeg` la prima rulare.
*   **Microfon funcțional** (pentru recunoașterea în timp real a sunetelor).
*   *(Opțional)* O cheie API **Google Gemini** gratuită pentru funcționalitățile LLM reale. Poate fi generată de pe [Google AI Studio](https://aistudio.google.com/). În lipsa cheii, aplicația folosește un sistem de **Mock offline** complet integrat.

---

## 🚀 Instalare și Configurare

### Pasul 1: Descărcarea proiectului
Navigați în folderul proiectului MDS:
```cmd
cd "C:\Users\jeanl\OneDrive\Desktop\MDS\PyShazam"
```

### Pasul 2: Crearea și activarea mediului virtual (`venv`)
Este recomandat să izolați dependințele aplicației într-un mediu virtual:
```cmd
# Creare venv
python -m venv venv

# Activare venv pe Windows (Command Prompt)
venv\Scripts\activate.bat

# Activare venv pe Windows (PowerShell)
.\venv\Scripts\Activate.ps1
```

### Pasul 3: Instalarea dependințelor necesare
Cu mediul virtual activat, instalați pachetele listate în `requirements.txt`:
```cmd
pip install -r requirements.txt
```

### Pasul 4: Configurare Gemini API Key
Puteți adăuga cheia de API direct din interfața grafică desktop a aplicației:
1. Lansați interfața GUI.
2. Accesați Tab-ul **"Setări / Învață Melodii"**.
3. Introduceți cheia în câmpul dedicat **"Gemini API Key"** și apăsați pe **"Salvează Cheie API"**. Aceasta va fi stocată criptat/securizat în SQLite și refolosită la fiecare căutare.

---

## 🖥️ Ghid de Rulare

Aplicația acceptă două moduri principale de operare:

### A. Rulare în mod GUI (Interfață Grafică Desktop) - Recomandat
Acesta este modul implicit. Lansați interfața grafică de tip *Dark Mode* rulând:
```cmd
python main.py
# sau explicit
python main.py --gui
```

**Utilizare GUI:**
1.  **Tab 1 (Recunoaștere)**: Permite selectarea sursei de intrare (Microfon, Fișier sau Mock de test). Apăsați **"Ascultă / Recunoaște"** pentru a porni înregistrarea. După identificare, vor apărea automat recomandările similare, biografia artistului și analiza versurilor în panourile dedicate.
2.  **Tab 2 (Administrare DB)**: Afișează melodiile învățate. Puteți căuta instant în tabel, redenumi melodiile selectate sau le puteți șterge.
3.  **Tab 3 (Istoric Căutări)**: Afișează istoricul interogărilor tehnice salvate în DB și permite curățarea lui.
4.  **Tab 4 (Setări & Învățare)**: Permite configurarea API Key-ului și indexarea vizuală a unui întreg folder local plin de melodii.

---

### B. Rulare în mod CLI (Command Line Interface)
Dacă preferați terminalul, puteți rula comenzi dedicate:

1.  **Modul Învățare (Indexare folder muzică locală)**:
    Scanează recursiv un folder local de muzică, generează amprentele spectrale și caracteristicile AI, salvându-le în baza de date SQLite:
    ```cmd
    python main.py learn --dir "C:\Calea\Catre\Muzica"
    ```
2.  **Modul Ascultare (Recunoaștere directă din terminal)**:
    *   *Prin Microfon* (ascultă timp de 10 secunde):
        ```cmd
        python main.py listen --duration 10
        ```
    *   *Prin Fișier Audio*:
        ```cmd
        python main.py listen --file "C:\Calea\Catre\melodie.mp3"
        ```
    *   *Prin Semnal Mock de test* (util pentru verificarea pipeline-ului fără sunet fizic):
        ```cmd
        python main.py listen --mock
        ```

---

## 🧪 Testare Automată

Aplicația include o suită robustă de **23 de teste unitare automate** care verifică izolat funcționalitățile audio, algoritmii de fingerprinting, comportamentul Singleton al bazei de date, operațiile CRUD, istoricul și funcționarea corectă a agenților LLM (atât în scenariul real, cât și în cel cu fallback/mock).

Pentru a rula întreaga suită de teste automate:
```cmd
python -m unittest discover -s tests -p "test_*.py"
```

---

## ⚠️ Troubleshooting (Depanare Erori)

### 1. Diacritice românești și encoding în CLI Windows
Dacă obțineți o eroare de tipul `UnicodeEncodeError: 'charmap' codec can't encode...` la afișarea textului în română pe consola Windows CMD/PowerShell, forțați terminalul să folosească encodarea UTF-8 definind variabila de mediu la lansare:
```cmd
set PYTHONUTF8=1
python main.py listen
```

### 2. Eroare SQLite cu thread-uri (`sqlite3.ProgrammingError`)
Dacă aveți probleme la rularea concomitentă a interfeței cu procesele asincrone pe thread-uri secundare, asigurați-vă că DatabaseManager include parametrul `check_same_thread=False` în conexiune. Această remediere este deja implementată nativ în cod:
```python
self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
```

### 3. Erori HTTP 404 sau 429 la Gemini API
Dacă apelurile Gemini LLM eșuează cu erori de rețea, aplicația va trece automat pe modul **Mock offline**, afișând texte coerente predefinite în panourile GUI, pentru a nu perturba deloc experiența utilizatorului. Modelul utilizat în mod implicit este **`gemini-2.5-flash-lite`** (endpoint `v1`), care oferă cel mai bun timp de răspuns și stabilitate pe conturile de utilizare gratuită.

<!-- Test commit for username update -->

