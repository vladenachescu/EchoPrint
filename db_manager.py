import sqlite3
import os

class DatabaseManager:
    _instance = None

    def __new__(cls, db_path='shazam_clone.db', *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path='shazam_clone.db'):
        if getattr(self, '_initialized', False):
            return
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
        self._initialized = True

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS songs (
                song_id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_name TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fingerprints (
                hash TEXT NOT NULL,
                song_id INTEGER NOT NULL,
                offset INTEGER NOT NULL,
                FOREIGN KEY(song_id) REFERENCES songs(song_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS song_features (
                song_id INTEGER PRIMARY KEY,
                bpm REAL NOT NULL,
                spectral_centroid REAL NOT NULL,
                spectral_flatness REAL NOT NULL,
                zero_crossing_rate REAL NOT NULL,
                FOREIGN KEY(song_id) REFERENCES songs(song_id)
            )
        ''')
        # Index for fast lookup by hash
        self.cursor.execute('CREATE INDEX IF NOT EXISTS hash_idx ON fingerprints(hash)')
        self.conn.commit()

    def insert_song(self, song_name, file_hash):
        try:
            self.cursor.execute('INSERT INTO songs (song_name, file_hash) VALUES (?, ?)', (song_name, file_hash))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            # Song already exists
            return None

    def insert_fingerprints(self, fingerprints):
        # fingerprints is a list of tuples: (hash, song_id, offset)
        self.cursor.executemany('INSERT INTO fingerprints (hash, song_id, offset) VALUES (?, ?, ?)', fingerprints)
        self.conn.commit()

    def find_song_by_file_hash(self, file_hash):
        self.cursor.execute('SELECT song_id FROM songs WHERE file_hash = ?', (file_hash,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_song_by_id(self, song_id):
        self.cursor.execute('SELECT song_name FROM songs WHERE song_id = ?', (song_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def find_matches(self, hashes):
        # hashes is a list of hash strings
        if not hashes:
            return []
        all_results = []
        CHUNK_SIZE = 900
        for i in range(0, len(hashes), CHUNK_SIZE):
            chunk = hashes[i:i + CHUNK_SIZE]
            placeholders = ','.join(['?'] * len(chunk))
            query = f'SELECT hash, song_id, offset FROM fingerprints WHERE hash IN ({placeholders})'
            self.cursor.execute(query, chunk)
            all_results.extend(self.cursor.fetchall())
        return all_results

    def insert_features(self, song_id, bpm, spectral_centroid, spectral_flatness, zero_crossing_rate):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO song_features 
                (song_id, bpm, spectral_centroid, spectral_flatness, zero_crossing_rate) 
                VALUES (?, ?, ?, ?, ?)
            ''', (song_id, bpm, spectral_centroid, spectral_flatness, zero_crossing_rate))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"[-] Eroare la salvarea caracteristicilor în DB: {e}")
            return False

    def get_features(self, song_id):
        self.cursor.execute('SELECT bpm, spectral_centroid, spectral_flatness, zero_crossing_rate FROM song_features WHERE song_id = ?', (song_id,))
        return self.cursor.fetchone()

    def get_all_features(self):
        self.cursor.execute('''
            SELECT f.song_id, s.song_name, f.bpm, f.spectral_centroid, f.spectral_flatness, f.zero_crossing_rate 
            FROM song_features f
            JOIN songs s ON f.song_id = s.song_id
        ''')
        return self.cursor.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()

