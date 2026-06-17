import numpy as np
import librosa
from db.db_manager import DatabaseManager

class AIRecommendationAgent:
    def __init__(self, db: DatabaseManager):
        self.db = db

    @staticmethod
    def extract_features(file_path: str) -> dict:
        """
        Extracts audio features (BPM, Spectral Centroid, Spectral Flatness, Zero Crossing Rate)
        from a file path.
        """
        # Load audio (mono)
        y, sr = librosa.load(file_path, sr=22050, duration=30) # 30s is enough for feature extraction
        
        # 1. Estimate BPM (Tempo)
        # librosa.beat.beat_track returns (tempo, beats)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Support both librosa v0.8+ (numpy array/float) and older versions
        bpm = float(tempo[0]) if isinstance(tempo, (list, np.ndarray)) else float(tempo)

        # 2. Spectral Centroid
        centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

        # 3. Spectral Flatness
        flatness = np.mean(librosa.feature.spectral_flatness(y=y))

        # 4. Zero Crossing Rate
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=y))

        return {
            "bpm": float(bpm),
            "spectral_centroid": float(centroid),
            "spectral_flatness": float(flatness),
            "zero_crossing_rate": float(zcr)
        }

    def recommend_for_song(self, song_id: int, top_n=3) -> list:
        """
        Finds the top_n most similar songs in the database based on normalized Euclidean distance.
        """
        target_features = self.db.get_features(song_id)
        if not target_features:
            print(f"[-] Caracteristicile pentru melodia {song_id} nu se află în baza de date.")
            return []

        all_songs = self.db.get_all_features()
        if len(all_songs) <= 1:
            return []

        # Parse songs features
        # target_features is (bpm, spectral_centroid, spectral_flatness, zero_crossing_rate)
        # all_songs is list of tuples: (song_id, song_name, bpm, centroid, flatness, zcr)
        
        song_ids = []
        song_names = []
        features_matrix = []

        for row in all_songs:
            # Skip the target song itself
            if row[0] == song_id:
                continue
            song_ids.append(row[0])
            song_names.append(row[1])
            features_matrix.append([row[2], row[3], row[4], row[5]])

        if not features_matrix:
            return []

        features_matrix = np.array(features_matrix)
        target_vector = np.array(target_features)

        # Normalize features using Min-Max scaling
        # Combine target and all features to normalize together
        combined = np.vstack([features_matrix, target_vector])
        
        min_vals = np.min(combined, axis=0)
        max_vals = np.max(combined, axis=0)
        
        # Avoid division by zero
        range_vals = max_vals - min_vals
        range_vals[range_vals == 0] = 1.0

        normalized_combined = (combined - min_vals) / range_vals
        
        normalized_features = normalized_combined[:-1]
        normalized_target = normalized_combined[-1]

        # Calculate Euclidean distance
        distances = np.linalg.norm(normalized_features - normalized_target, axis=1)

        # Sort recommendations
        sorted_indices = np.argsort(distances)
        
        recommendations = []
        for idx in sorted_indices[:top_n]:
            recommendations.append({
                "song_id": song_ids[idx],
                "song_name": song_names[idx],
                "distance": float(distances[idx])
            })
            
        return recommendations
