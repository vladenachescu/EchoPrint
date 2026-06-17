import unittest
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai.ai_noise_agent import AINoiseAgent
from ai.ai_recommendation_agent import AIRecommendationAgent
from db.db_manager import DatabaseManager

class TestAIAgents(unittest.TestCase):
    def setUp(self):
        # Setup clean test DB for recommendation testing
        DatabaseManager._instance = None
        self.db_path = 'test_ai_agents.db'
        self.db = DatabaseManager(self.db_path)
        self.noise_agent = AINoiseAgent(sample_rate=22050)
        self.recommender = AIRecommendationAgent(self.db)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except PermissionError:
                pass
        DatabaseManager._instance = None

    def test_noise_agent_assess_quality_empty(self):
        # Empty signal
        empty_signal = np.array([])
        quality = self.noise_agent.assess_quality(empty_signal)
        self.assertEqual(quality["rating"], "EMPTY")

    def test_noise_agent_assess_quality_low(self):
        # Quiet signal (all zeros or near zero)
        low_signal = np.zeros(1000)
        quality = self.noise_agent.assess_quality(low_signal)
        self.assertEqual(quality["rating"], "TOO_LOW")

    def test_noise_agent_assess_quality_clipping(self):
        # Signal with massive clipping (constant max value)
        clipping_signal = np.ones(1000)
        quality = self.noise_agent.assess_quality(clipping_signal)
        self.assertEqual(quality["rating"], "DISTORTED")

    def test_noise_agent_assess_quality_normal(self):
        # Normal sine wave with low noise
        t = np.linspace(0, 1.0, 22050, endpoint=False)
        signal = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.01 * np.random.randn(len(t))
        quality = self.noise_agent.assess_quality(signal)
        self.assertIn(quality["rating"], ["EXCELLENT", "NOISY"])

    def test_noise_agent_denoise(self):
        t = np.linspace(0, 0.5, 11025, endpoint=False)
        signal = 0.5 * np.sin(2 * np.pi * 440 * t) + 0.1 * np.random.randn(len(t))
        
        denoised = self.noise_agent.denoise(signal)
        self.assertIsInstance(denoised, np.ndarray)
        self.assertEqual(len(denoised), len(signal))

    def test_recommendation_agent(self):
        # Insert target song
        s1 = self.db.insert_song("Song 1", "hash_song1")
        self.db.insert_features(s1, 120.0, 1000.0, 0.1, 0.05)
        
        # Insert similar song (Song 2 has similar features)
        s2 = self.db.insert_song("Song 2 (Similar)", "hash_song2")
        self.db.insert_features(s2, 122.0, 1050.0, 0.11, 0.052)
        
        # Insert different song (Song 3 has very different features)
        s3 = self.db.insert_song("Song 3 (Different)", "hash_song3")
        self.db.insert_features(s3, 80.0, 3000.0, 0.4, 0.25)
        
        recs = self.recommender.recommend_for_song(s1, top_n=2)
        self.assertEqual(len(recs), 2)
        
        # Song 2 should be more similar (smaller distance) than Song 3
        # Since indices are sorted by distance ascending:
        self.assertEqual(recs[0]["song_id"], s2)
        self.assertEqual(recs[1]["song_id"], s3)
        self.assertTrue(recs[0]["distance"] < recs[1]["distance"])

    def test_gemini_client_fallback_trivia(self):
        from ai.llm_client import GeminiLLMClient
        # Clear config API key if any to ensure fallback
        self.db.set_config_value("gemini_api_key", None)
        client = GeminiLLMClient(self.db)
        
        trivia = client.generate("Mock prompt", "trivia", "Hotel California")
        self.assertIn("Offline Mock", trivia)
        self.assertIn("Hotel California", trivia)

    def test_gemini_client_fallback_lyrics(self):
        from ai.llm_client import GeminiLLMClient
        self.db.set_config_value("gemini_api_key", None)
        client = GeminiLLMClient(self.db)
        
        lyrics = client.generate("Mock prompt", "lyrics", "Billie Jean")
        self.assertIn("Offline Mock", lyrics)
        self.assertIn("Billie Jean", lyrics)

    def test_music_trivia_agent(self):
        from ai.ai_trivia_agent import AIMusicTriviaAgent
        from ai.llm_client import GeminiLLMClient
        self.db.set_config_value("gemini_api_key", None)
        agent = AIMusicTriviaAgent(GeminiLLMClient(self.db))
        res = agent.get_trivia("Billie Jean")
        self.assertIn("Michael Jackson", res)
        self.assertIn("Billie Jean", res)

    def test_lyrics_agent(self):
        from ai.ai_lyrics_agent import AILyricsAgent
        from ai.llm_client import GeminiLLMClient
        self.db.set_config_value("gemini_api_key", None)
        agent = AILyricsAgent(GeminiLLMClient(self.db))
        res = agent.get_lyrics_analysis("Hotel California")
        self.assertIn("California", res)
        self.assertIn("Hotel California", res)

if __name__ == '__main__':
    unittest.main()
