# PyShazam (MDS Project)

PyShazam este o aplicație de recunoaștere audio dezvoltată în Python, inspirată de algoritmul de fingerprinting utilizat de Shazam. Proiectul este structurat conform cerințelor academice și specificațiilor oficiale pentru disciplina **Metode de Dezvoltare Software (MDS)** de la FMI Unibuc.

Aplicația scanează și „învață” melodii dintr-o bibliotecă muzicală locală (generând amprente spectrale), iar apoi poate recunoaște o melodie ascultată live prin microfon sau dintr-un fișier, curățând zgomotul de fundal cu AI, oferind recomandări similare și logând rezultatele într-un istoric persistat în baza de date.

---

## 🏗️ Structura Proiectului & Diagrama UML

Proiectul respectă o arhitectură modulară, separând procesarea digitală a semnalelor, managementul persistenței, controlul dispozitivelor fizice și logica agenților de inteligență artificială.

### Diagrama de Clase (Mermaid UML)
```mermaid
classDiagram
    class AudioInputStrategy {
        <<interface>>
        +record(duration_seconds: int) ndarray*
    }
    class MicrophoneInputStrategy {
        +sample_rate: int
        +record(duration) ndarray
    }
    class FileInputStrategy {
        +file_path: str
        +sample_rate: int
        +record(duration) ndarray
    }
    class MockInputStrategy {
        +sample_rate: int
        +record(duration) ndarray
    }
    
    AudioInputStrategy <|.. MicrophoneInputStrategy
    AudioInputStrategy <|.. FileInputStrategy
    AudioInputStrategy <|.. MockInputStrategy
    
    class AudioRecorder {
        -strategy: AudioInputStrategy
        +record(duration_seconds) ndarray
    }
    AudioRecorder --> AudioInputStrategy : uses
    
    class DatabaseManager {
        -conn: Connection
        -cursor: Cursor
        -instance: DatabaseManager$
        +connect()
        +create_tables()
        +insert_song(song_name, file_hash) int
        +insert_fingerprints(fingerprints)
        +find_song_by_file_hash(file_hash) int
        +get_song_by_id(song_id) str
        +find_matches(hashes) list
        +insert_features(song_id, bpm, centroid, flatness, zcr) bool
        +get_features(song_id) tuple
        +get_all_features() list
        +update_song_name(song_id, new_name) bool
        +delete_song(song_id) bool
        +get_all_songs_metadata() list
        +insert_history(input_source, recognized_song_id, snr, confidence_score) bool
        +get_history() list
        +clear_history() bool
        +close()
    }
    
    class AudioProcessor {
        +load_audio(file_path) tuple
        +get_spectrogram(y) ndarray
        +get_constellation_map(spectrogram) list
        +generate_hashes(peaks) list
        +fingerprint_file(file_path) list
        +fingerprint_audio_data(y) list
    }
    
    class AINoiseAgent {
        +sample_rate: int
        +assess_quality(y) dict
        +denoise(y) ndarray
    }
    
    class AIRecommendationAgent {
        -db: DatabaseManager
        +extract_features(file_path) dict
        +recommend_for_song(song_id, top_n) list
    }
    AIRecommendationAgent --> DatabaseManager : queries
    
    class PyShazamGUI {
        -db: DatabaseManager
        -is_processing: bool
        -selected_file_path: str
        +__init__(db)
        +create_widgets()
        +load_database_songs()
        +load_search_history()
        +modify_selected_song()
        +delete_selected_song()
        +start_recognition_thread()
        +start_learning_thread()
        +run()
    }
    PyShazamGUI --> DatabaseManager : CRUD & History
    PyShazamGUI --> AINoiseAgent : Denoise Check
    PyShazamGUI --> AIRecommendationAgent : Recommendations
    PyShazamGUI --> AudioRecorder : Strategy Record
```

---

## 🛠️ Specificații Proiect Implementate (Conform Fișei)

Aplicația implementează în totalitate specificațiile din fișa oficială a proiectului:

1. **Stocarea melodiilor într-o bază de date**: Baza de date SQLite (`shazam_clone.db`) păstrează melodiile, amprentele unice și caracteristicile AI.
2. **Adăugarea, ștergerea și modificarea intrărilor**:
   - *Adăugare*: Prin tab-ul de învățare sau din CLI.
   - *Ștergere*: Ștergerea completă a unei melodii și a amprentelor/trăsăturilor sale asociate direct din tabel (cu constrângere `ON DELETE CASCADE` activată).
   - *Modificare*: Redenumirea numelui de afișare al oricărei melodii salvate.
3. **Vizionarea bazei de date în funcție de filtre**: Tab-ul de Administrare conține un tabel `Treeview` cu un câmp de căutare dinamic care filtrează în timp real melodiile pe măsură ce utilizatorul tastează litere din nume.
4. **Interfață grafică pentru utilizator (GUI)**: Dezvoltată în Tkinter cu un aspect premium de tip *Dark Theme*. Permite:
   - Selectarea sursei audio (Microfon fizic, Fișier din PC sau Simulare test/Mock).
   - Înregistrarea live și monitorizarea calității audio.
   - Învățarea folderelor prin selectare vizuală.
5. **Formarea unui istoric de căutări**: Tabela `search_history` din SQLite salvează automat fiecare recunoaștere (data/ora, sursa audio, piesa identificată/eșuată, SNR estimat și scor de încredere). Istoricul este afișat într-un tabel dedicat în GUI și poate fi golit oricând.
6. **Design Patterns**: 
   - **Singleton** (`DatabaseManager`) pentru o conexiune sigură și unică.
   - **Strategy** (`AudioInputStrategy`) pentru flexibilitatea sursei audio (utilă în special la testare fără microfon).

---

## 🧠 Agenți de Inteligență Artificială (AI Agents)

Aplicația integrează **2 agenți AI** autonomi:

1. **AI Noise & Quality Agent (`AINoiseAgent`)**:
   - Evaluează RMS, distorsiunile și raportul SNR.
   - Aplică atenuare spectrală (*spectral subtraction / gating*) pentru eliminarea zgomotului static de fundal înainte de recunoaștere.

2. **AI Recommendation Agent (`AIRecommendationAgent`)**:
   - Extrage tempo-ul (BPM) și timbrul spectral în timpul indexării melodiei.
   - Recomandă top 3 piese similare folosind distanța euclidiană a vectorilor normalizați (Min-Max).

---

## 🚀 Instalare și Rulare

### Dependențe
1. Asigură-te că ai instalat Python 3.10+.
2. Instalează pachetele listate în `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

### Lansare Interfață Grafică (GUI)
Pentru a lansa interfața grafică desktop (implicit dacă nu se trimit argumente):
```bash
python main.py --gui
# sau simplu
python main.py
```

### Rulare mod CLI (Command Line Interface)
- **Modul Învățare**:
  ```bash
  python main.py learn --dir /calea/catre/muzica
  ```
- **Modul Ascultare**:
  ```bash
  python main.py listen --duration 10
  ```

---

## 🧪 Testare Unitară

Pentru rularea celor 18 teste unitare automate (ce acoperă integral logica audio, Singleton-ul DB, operațiile CRUD de ștergere/modificare, istoricul și agenții AI):

```bash
python -m unittest discover -s tests -p "test_*.py"
```
