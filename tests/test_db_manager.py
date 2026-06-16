import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db_manager import DatabaseManager

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

if __name__ == '__main__':
    unittest.main()
