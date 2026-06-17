from ai.llm_client import GeminiLLMClient

class AIMusicTriviaAgent:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client or GeminiLLMClient()

    def get_trivia(self, song_name: str) -> str:
        """
        Interoghează agentul pentru a obține o biografie succintă a artistului
        și 3 detalii interesante (trivia facts) despre piesa respectivă.
        """
        prompt = (
            f"You are an expert music historian and encyclopedic guide. "
            f"Provide a brief biography of the artist and exactly 3 interesting details (trivia/trivia facts) "
            f"about the song '{song_name}'. "
            f"Respond in English in an engaging and well-structured format with headings and bullet points. "
            f"Do not add any unnecessary introductions or conclusions."
        )
        return self.llm_client.generate(prompt, fallback_type="trivia", song_name=song_name)
