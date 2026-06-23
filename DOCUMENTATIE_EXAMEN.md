# 🎓 Ghid de Pregătire pentru Examen / Evaluare: EchoPrint (PyShazam)

Acest document reprezintă un suport complet pentru prezentarea proiectului **EchoPrint** la disciplina **Metode de Dezvoltare Software (MDS)**. El explică pas cu pas cum funcționează aplicația, unde se află implementate cerințele din fișa proiectului, ce design pattern-uri au fost folosite și cum funcționează agenții AI, alături de răspunsuri la posibile întrebări capcană din partea profesorilor evaluatori.

---

## 1. Ce este EchoPrint și cum funcționează?

EchoPrint este o aplicație desktop de recunoaștere audio inspirată de celebrul algoritm **Shazam**. Scopul ei este să identifice o melodie înregistrată de la microfon sau citită dintr-un fișier local, căutând-o într-o bază de date proprie.

### Fluxul logic al recunoașterii audio (Pas cu Pas):
1.  **Captura Audio**: Semnalul audio analogic este înregistrat și convertit în format digital (o matrice de numere numită `ndarray` din NumPy) cu o rată de eșantionare standard de 22050 Hz.
2.  **Atenuarea Zgomotului (AI Noise Agent)**: Înainte ca semnalul să meargă spre analiză, agentul evaluează calitatea audio (信噪比 SNR, clipping). Dacă calitatea este acceptabilă, aplică o reducere a zgomotului static de fundal prin subtracție spectrală (*Spectral Gating*).
3.  **Generarea Spectrogramei**: Se aplică Transformata Fourier Rapidă pe Timp Scurt (STFT) prin biblioteca `librosa`. Aceasta transformă semnalul din domeniul timpului (amplitudine în funcție de timp) în domeniul frecvenței (energie în funcție de frecvență și timp).
4.  **Harta Constelațiilor (Constellation Map)**: Se scanează spectrograma și se extrag doar punctele de maxim local (vârfurile de energie) dintr-o fereastră bidimensională timp-frecvență. Această reducere drastică de date reține doar "amprenta" caracteristică a sunetului, eliminând restul informațiilor redundante.
5.  **Generarea de Hash-uri (Fingerprinting)**: Punctele de maxim sunt împerecheate temporal. Pentru fiecare pereche de vârfuri se calculează un hash unic bazat pe:
    *   Frecvența primului vârf ($f_1$).
    *   Frecvența celui de-al doilea vârf ($f_2$).
    *   Diferența de timp dintre ele ($\Delta t$).
    *   Fiecare hash este asociat cu un decalaj de timp (offset) care reprezintă momentul exact din melodie în care apare acea pereche de vârfuri.
6.  **Căutarea și Alinierea în Baza de Date**:
    *   Se caută aceste hash-uri în tabela `fingerprints` din SQLite.
    *   Pentru fiecare potrivire găsită, se extrage `song_id` și `db_offset`.
    *   Se calculează diferența dintre offset-ul din baza de date și cel din eșantionul înregistrat: $\text{diff} = \text{db\_offset} - \text{sample\_offset}$.
    *   **De ce este importantă diferența?** Dacă eșantionul înregistrat provine din melodia corectă, diferențele (`diff`) pentru toate hash-urile potrivite vor fi identice (se vor alinia la aceeași valoare constantă).
    *   Se grupează aceste diferențe și se folosește un histogram/contor (`Counter`). Melodia cu cel mai mare număr de diferențe identice (scor de încredere) este declarată câștigătoare.

---

## 2. Unde sunt implementate cerințele din fișa proiectului?

Profesorul te va pune să deschizi fișierele și să arăți exact liniile de cod. Iată ghidul complet:

### Cerința 1: Stocarea melodiilor într-o bază de date
*   **Unde arăți**: Deschide fișierul [db_manager.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/db/db_manager.py).
*   **Explicație**: Baza de date este SQLite (`echoprint.db`). Tabela `songs` stochează melodiile (id, nume, hash fișier pentru a evita duplicatele), iar tabela `fingerprints` stochează hash-urile spectrale asociate cu ID-ul melodiei și offset-ul corespunzător.
*   **Cod specific**: Metoda `create_tables()` din `db_manager.py` (liniile 29-75) creează automat aceste tabele la prima pornire a aplicației.

### Cerința 2: Adăugarea, ștergerea și modificarea intrărilor (CRUD)
*   **Unde arăți**: Fișierele [db_manager.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/db/db_manager.py) și [gui.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/gui/gui.py).
*   *   **Adăugare (Create)**: Metoda `insert_song()` și `insert_fingerprints()` din `db_manager.py`. În GUI, se realizează în Tab-ul **"Setări / Învață Melodii"** (metoda `start_learning_thread()` din `gui.py`).
*   *   **Modificare (Update)**: Metoda `update_song_name(self, song_id, new_name)` din `db_manager.py` (redenumirea unei melodii în baza de date). În GUI, se realizează prin dublu-click pe o melodie în tab-ul de Administrare sau selectare și apăsare pe butonul de Editare.
*   *   **Ștergere (Delete)**: Metoda `delete_song(self, song_id)` din `db_manager.py`.
    *   *Detaliu tehnic important*: Tabela `fingerprints` este creată cu `ON DELETE CASCADE`. Când o melodie este ștearsă din tabela `songs`, SQLite șterge automat și instantaneu toate milioanele de amprente asociate ei din tabela `fingerprints`, fără a lăsa date orfane.

### Cerința 3: Vizualizarea bazei de date în funcție de filtre
*   **Unde arăți**: În [gui.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/gui/gui.py) în clasa `EchoPrintGUI`.
*   **Explicație**: În Tab-ul **"Administrare DB"**, există o bară de căutare dinamică. Pe măsură ce utilizatorul tastează, interfața filtrează instantaneu melodiile.
*   **Cod specific**: Metoda `load_database_songs(self)` din `gui.py` citește din widget-ul de căutare (`self.search_entry.get()`) și redesenează tabela `Treeview` doar cu rândurile potrivite. Filtrarea este legată direct de evenimentul tastaturii `<KeyRelease>` (`self.search_entry.bind('<KeyRelease>', lambda e: self.load_database_songs())`).

### Cerința 4: Interfața Grafică pentru Utilizator (GUI)
*   **Unde arăți**: Fișierul [gui.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/gui/gui.py).
*   **Explicație**: Dezvoltată integral în Python folosind biblioteca standard `tkinter`. Interfața are un aspect premium *Dark Theme* și folosește un control de tip tab-uri (`ttk.Notebook`) pentru a structura aplicația în 4 secțiuni distincte.

### Cerința 5: Formarea unui istoric de căutări
*   **Unde arăți**: [db_manager.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/db/db_manager.py) (metodele de istoric) și Tab-ul 3 din [gui.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/gui/gui.py).
*   **Explicație**: Tabela `search_history` loghează automat fiecare căutare. Se salvează momentul căutării, sursa (microfon, fișier, mock), id-ul melodiei recunoscute (sau `NULL` dacă nu s-a găsit), raportul SNR calculat de AI și scorul de încredere.
*   **Cod specific**: Metoda `insert_history()` din `db_manager.py` este apelată la finalul recunoașterii în [main.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/main.py) și `gui.py`.

---

## 3. Ce Design Patterns (Șabloane de Proiectare) sunt folosite?

Trebuie să cunoști concepte clare și să arăți structura claselor:

### A. Singleton Pattern (în `DatabaseManager`)
*   **De ce este folosit?** Pentru a garanta că aplicația deschide **o singură conexiune** la fișierul bazei de date SQLite. Dacă am avea mai multe instanțe de `DatabaseManager`, acestea ar putea încerca să scrie simultan, cauzând blocarea bazei de date (`database is locked`) sau coruperea datelor.
*   **Unde arăți**: [db_manager.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/db/db_manager.py).
*   **Cum funcționează codul**:
    ```python
    class DatabaseManager:
        _instance = None
        def __new__(cls, db_path='echoprint.db', *args, **kwargs):
            if not cls._instance:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    ```
    Metoda magică `__new__` interceptează crearea obiectului. Dacă `_instance` este deja creat, returnează instanța existentă în loc să creeze una nouă.

### B. Strategy Pattern (în `AudioInputStrategy`)
*   **De ce este folosit?** Pentru a decupla clasa de înregistrare (`AudioRecorder`) de sursa fizică a datelor audio. Aceasta ne permite să testăm aplicația fără un microfon fizic conectat și să utilizăm fișiere sau date simulate (mock) într-un mod transparent.
*   **Unde arăți**: Fișierul [audio_source.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/audio/audio_source.py) (unde sunt definite strategiile) și [recorder.py](file:///c:/Users/jeanl/OneDrive/Desktop/MDS/PyShazam/audio/recorder.py) (unde este definit contextul).
*   **Componentele Pattern-ului**:
    1.  **Interfața Strategiei (`AudioInputStrategy`)**: Clasa de bază abstractă care declară metoda `record(self, duration_seconds)`.
    2.  **Strategiile Concrete**:
        *   `MicrophoneInputStrategy`: Înregistrează live de la placa de sunet folosind biblioteca `sounddevice`.
        *   `FileInputStrategy`: Citește date dintr-un fișier local folosind `librosa` / `soundfile`.
        *   `MockInputStrategy`: Generează o matrice de numere aleatoare NumPy (zgomot alb) pentru testarea sistemului în mod "silent" (util pe servere sau în medii de testare CI).
    3.  **Contextul (`AudioRecorder`)**: Clasa care primește o strategie la inițializare (`self.strategy`) și o folosește delegându-i sarcina de înregistrare.

---

## 4. Cum funcționează cei 4 Agenți AI?

Proiectul integrează o arhitectură bazată pe 4 agenți AI care colaborează în mod autonom:

### 1. AI Noise & Quality Agent (`AINoiseAgent`)
*   **Rol**: Evaluarea calității audio și eliminarea zgomotului de fundal.
*   **Metodologie**:
    *   Calculează energia semnalului (RMS) și raportul Semnal-Zgomot (SNR).
    *   Dacă SNR este prea scăzut (sunet prea slab sau zgomot masiv), agentul recomandă oprirea procesului pentru a nu irosi resurse.
    *   Dacă este acceptabil, aplică **Spectral Gating (subtracție spectrală)**: estimează zgomotul de fundal static din frecvențele cele mai slabe și îl scade matematic din întregul spectru al semnalului audio.

### 2. AI Recommendation Agent (`AIRecommendationAgent`)
*   **Rol**: Recomandă melodii similare din baza de date pe criterii acustice.
*   **Metodologie**:
    *   În timpul indexării (learn), extrage tempo-ul (BPM) și indicatori spectrali:
        *   *Spectral Centroid* (unde se află centrul de masă al spectrului - indică dacă o piesă este "luminoasă" sau "gravă").
        *   *Spectral Flatness* (măsoară dacă sunetul seamănă cu un zgomot sau este format din tonuri clare).
        *   *Zero Crossing Rate* (cât de des trece semnalul prin valoarea zero - măsoară frecvențele înalte/percuția).
    *   Salvează aceste caracteristici în tabela `song_features`.
    *   Când o melodie este recunoscută, agentul compară vectorul ei acustic cu cel al celorlalte melodii folosind **distanța Euclidiană** normalizată prin Min-Max și returnează primele 3 cele mai apropiate (similare) piese.

### 3. AI Music Trivia & Bio Agent (`AIMusicTriviaAgent`)
*   **Rol**: Generarea de detalii biografice și curiozități muzicale despre piesă.
*   **Metodologie**:
    *   Interoghează API-ul Google Gemini folosind modelul `gemini-2.5-flash-lite` cu un prompt specific.
    *   **Sistemul de Fallback**: Dacă utilizatorul nu are internet, dacă API Key-ul este invalid sau absent, agentul interceptează eroarea și rulează un modul offline de Mocking. Acesta citește o listă de răspunsuri predefinite coerente pentru piesele de test sau asamblează un răspuns generic inteligent bazat pe numele melodiei pentru a nu bloca rularea aplicației.

### 4. AI Lyrics & Sentiment Agent (`AILyricsAgent`)
*   **Rol**: Analiza versurilor, determinarea sentimentului (ex: vesel, melancolic) și generarea unui rezumat succint tradus în limba română.
*   **Metodologie**: Similar cu cel de Trivia, interoghează Gemini LLM cu instrucțiuni stricte de formatare și dispune de un fallback offline identic în caz de eșec.

---

## 5. Întrebări frecvente și Capcane la Examen (Q&A)

Pregătește-te pentru aceste întrebări din partea profesorilor:

### Q1: Cum funcționează alinierea temporală a hash-urilor în procesul de potrivire? De ce nu este suficient doar să numărăm câte potriviri de hash-uri avem?
*   **Răspuns**: Dacă am număra doar potrivirile simple de hash-uri, am putea avea rezultate fals pozitive masive. De exemplu, un anumit acord de chitară sau o bătaie de tobă se poate repeta în mii de melodii. Ceea ce face recunoașterea unică este ordinea temporală. Calculând diferența dintre timpul din melodie ($t_{\text{db}}$) și cel din înregistrare ($t_{\text{sample}}$), obținem o valoare constantă doar dacă acele hash-uri apar exact în aceeași succesiune. Dacă histograma diferențelor are un vârf clar pe o anumită valoare, înseamnă că melodia se potrivește perfect temporal.

### Q2: Ce se întâmplă în baza de date dacă șterg o melodie din GUI? Amprentele audio (fingerprints) rămân în baza de date?
*   **Răspuns**: Nu, nu rămân orfane datorită utilizării clauzei `ON DELETE CASCADE`. La crearea tabelei `fingerprints`, am setat cheia externă astfel:
    ```sql
    FOREIGN KEY(song_id) REFERENCES songs(song_id) ON DELETE CASCADE
    ```
    Când trimitem comanda de ștergere pe tabela `songs`, SQLite se ocupă automat de curățarea tuturor amprentelor spectrale asociate în tabela `fingerprints` și a caracteristicilor din `song_features`.

### Q3: De ce ați folosit Thread-uri secundare (multithreading) în Tkinter pentru procesul de înregistrare și recunoaștere?
*   **Răspuns**: Tkinter este un framework single-threaded (toate actualizările de interfață se desenează pe thread-ul principal). Dacă am rula înregistrarea audio (care blochează execuția timp de 10 secunde) direct pe thread-ul principal, interfața grafică s-ar bloca complet (starea "Not Responding"), utilizatorul nu ar mai putea apăsa niciun buton, iar animațiile s-ar opri. Folosind modulul `threading.Thread`, pornim procesul de înregistrare și apelul Gemini LLM în fundal, lăsând interfața principală activă și fluidă. La finalul execuției, thread-ul secundar trimite rezultatele înapoi în GUI.

### Q4: Cum ați gestionat concurența bazei de date SQLite când folosiți mai multe thread-uri?
*   **Răspuns**: SQLite restricționează implicit utilizarea conexiunilor pe alte thread-uri decât cel pe care au fost create. Deoarece GUI-ul rulează operațiile asincron din thread-uri secundare, am inițializat conexiunea SQLite folosind parametrul `check_same_thread=False` în clasa Singleton `DatabaseManager`. Astfel, conexiunea unică poate fi utilizată în siguranță de thread-ul principal pentru interfață și de thread-ul secundar pentru salvarea istoricului sau procesarea sunetului.

### Q5: Ce se întâmplă dacă utilizatorul nu a configurat sau nu are o cheie Google Gemini API validă? Aplicația crapă?
*   **Răspuns**: Nu. În clasa `GeminiLLMClient` am implementat un mecanism defensiv de tip `try-except` pentru toate apelurile HTTP către API. În cazul în care cheia este absentă, conexiunea la internet lipsește sau API-ul returnează o eroare (cum ar fi limita de cotă 429), excepția este prinsă, iar clientul LLM returnează automat un răspuns simulat (Mock response) care este formatat identic cu cel real. Acest lucru demonstrează robustețea codului în fața erorilor de runtime.
