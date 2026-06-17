from ai.llm_client import GeminiLLMClient

class AILyricsAgent:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client or GeminiLLMClient()

    def get_lyrics_analysis(self, song_name: str) -> str:
        """
        Analizează mesajul piesei, determină sentimentul predominant (fericit, melancolic etc.)
        și oferă un rezumat al versurilor tradus în limba română.
        """
        prompt = (
            f"You are a renowned music critic and fine literary analyst. "
            f"Analyze the message and lyrics of the song '{song_name}'. "
            f"Determine the predominant sentiment of the song (e.g., melancholy, happiness, anger, nostalgia, etc.) "
            f"and provide a coherent summary of the lyrics in English. "
            f"Respond directly, well-structured with headings and bullet points. "
            f"Do not add any formal introductions or conclusions."
        )
        return self.llm_client.generate(prompt, fallback_type="lyrics", song_name=song_name)
