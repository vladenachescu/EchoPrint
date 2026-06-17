import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.db_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Reset the Singleton instance to ensure a fresh test database connection
        DatabaseManager._instance = None
        self.db_path = 'test_shazam_clone.db'
        self.db = DatabaseManager(self.db_path)

    def tearDown(self):
        self.db.close()
        # Clean up database file
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
        DatabaseManager._instance = None

    def test_singleton_pattern(self):
        db2 = DatabaseManager(self.db_path)
        # Verify both variables point to the exact same instance in memory
        self.assertIs(self.db, db2)

    def test_insert_and_get_song(self):
        song_name = "Test Song"
        file_hash = "abcdef123456"
        
        # Test Insertion
        song_id = self.db.insert_song(song_name, file_hash)
        self.assertIsNotNone(song_id)
        
        # Test Duplicate Insertion (should return None due to unique constraint)
        song_id_dup = self.db.insert_song(song_name, file_hash)
        self.assertIsNone(song_id_dup)
        
        # Test Retrieve Song ID
        retrieved_id = self.db.find_song_by_file_hash(file_hash)
        self.assertEqual(song_id, retrieved_id)
        
        # Test Retrieve Song Name
        retrieved_name = self.db.get_song_by_id(song_id)
        self.assertEqual(song_name, retrieved_name)

    def test_insert_and_find_fingerprints(self):
        song_name = "Fingerprint Song"
        file_hash = "hash123"
        song_id = self.db.insert_song(song_name, file_hash)
        
        fingerprints = [
            ("hash_a", song_id, 10),
            ("hash_b", song_id, 20),
            ("hash_c", song_id, 30)
        ]
        
        self.db.insert_fingerprints(fingerprints)
        
        # Find matches for a subset
        matches = self.db.find_matches(["hash_a", "hash_c", "nonexistent_hash"])
        self.assertEqual(len(matches), 2)
        
        # Verify matched details
        matched_hashes = [m[0] for m in matches]
        self.assertIn("hash_a", matched_hashes)
        self.assertIn("hash_c", matched_hashes)
        self.assertNotIn("hash_b", matched_hashes)

    def test_insert_and_get_features(self):
        song_id = self.db.insert_song("Feature Song", "feature_hash")
        self.assertIsNotNone(song_id)
        
        # Insert features
        success = self.db.insert_features(song_id, 120.0, 1500.0, 0.05, 0.08)
        self.assertTrue(success)
        
        # Retrieve features
        features = self.db.get_features(song_id)
        self.assertIsNotNone(features)
        # (bpm, centroid, flatness, zcr)
        self.assertEqual(features[0], 120.0)
        self.assertEqual(features[1], 1500.0)
        self.assertEqual(features[2], 0.05)
        self.assertEqual(features[3], 0.08)
        
        # Retrieve all features
        all_features = self.db.get_all_features()
        self.assertEqual(len(all_features), 1)
        self.assertEqual(all_features[0][1], "Feature Song")
        self.assertEqual(all_features[0][2], 120.0)

    # --- NEW TESTS FOR CRUD & HISTORY ---

    def test_update_song_name(self):
        song_id = self.db.insert_song("Old Name", "hash_update")
        self.assertIsNotNone(song_id)
        
        # Update name
        success = self.db.update_song_name(song_id, "New Name")
        self.assertTrue(success)
        
        # Check update
        retrieved_name = self.db.get_song_by_id(song_id)
        self.assertEqual(retrieved_name, "New Name")

    def test_delete_song_cascade(self):
        song_id = self.db.insert_song("Delete Me", "hash_delete")
        self.assertIsNotNone(song_id)
        
        # Insert fingerprints and features linked to song_id
        self.db.insert_fingerprints([("del_hash", song_id, 5)])
        self.db.insert_features(song_id, 100.0, 1200.0, 0.1, 0.1)
        
        # Insert history entry linked to this song
        self.db.insert_history("Microfon", song_id, 15.0, 10)
        
        # Verify presence
        matches_before = self.db.find_matches(["del_hash"])
        self.assertEqual(len(matches_before), 1)
        
        # Delete song
        success = self.db.delete_song(song_id)
        self.assertTrue(success)
        
        # Verify song is gone
        self.assertIsNone(self.db.get_song_by_id(song_id))
        
        # Verify fingerprints are gone (ON DELETE CASCADE)
        matches_after = self.db.find_matches(["del_hash"])
        self.assertEqual(len(matches_after), 0)
        
        # Verify features are gone
        self.assertIsNone(self.db.get_features(song_id))
        
        # Verify history reference is SET NULL (ON DELETE SET NULL)
        history = self.db.get_history()
        self.assertEqual(len(history), 1)
        # Row layout: history_id, search_time, input_source, song_name, snr, confidence_score
        self.assertIsNone(history[0][3]) # Recognized song name should be None

    def test_get_all_songs_metadata(self):
        song_id1 = self.db.insert_song("Song A", "hash_a")
        song_id2 = self.db.insert_song("Song B", "hash_b")
        
        # Insert 2 fingerprints for A, 1 for B
        self.db.insert_fingerprints([
            ("hash1", song_id1, 1),
            ("hash2", song_id1, 2),
            ("hash3", song_id2, 1)
        ])
        
        meta = self.db.get_all_songs_metadata()
        self.assertEqual(len(meta), 2)
        # Sorted by name (Song A, Song B)
        self.assertEqual(meta[0][1], "Song A")
        self.assertEqual(meta[0][2], 2) # 2 fingerprints
        self.assertEqual(meta[1][1], "Song B")
        self.assertEqual(meta[1][2], 1) # 1 fingerprint

    def test_search_history_operations(self):
        # Insert entries
        self.db.insert_history("Microfon", None, 12.5, 0)
        song_id = self.db.insert_song("Matched Song", "matched_hash")
        self.db.insert_history("Fișier: song.wav", song_id, 35.0, 42)
        
        history = self.db.get_history()
        self.assertEqual(len(history), 2)
        
        # Most recent first
        self.assertEqual(history[0][2], "Fișier: song.wav")
        self.assertEqual(history[0][3], "Matched Song")
        self.assertEqual(history[0][4], 35.0)
        self.assertEqual(history[0][5], 42)
        
        self.assertEqual(history[1][2], "Microfon")
        self.assertIsNone(history[1][3])
        self.assertEqual(history[1][4], 12.5)
        self.assertEqual(history[1][5], 0)
        
        # Clear history
        success_clear = self.db.clear_history()
        self.assertTrue(success_clear)
        self.assertEqual(len(self.db.get_history()), 0)

    def test_config_table_operations(self):
        # Set a config value
        self.db.set_config_value("test_key", "test_value")
        # Retrieve it
        value = self.db.get_config_value("test_key")
        self.assertEqual(value, "test_value")
        
        # Overwrite value
        self.db.set_config_value("test_key", "new_value")
        value2 = self.db.get_config_value("test_key")
        self.assertEqual(value2, "new_value")
        
        # Get non-existent key
        non_existent = self.db.get_config_value("non_existent_key")
        self.assertIsNone(non_existent)

if __name__ == '__main__':
    unittest.main()
