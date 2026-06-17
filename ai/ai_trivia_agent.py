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
            f"Ești un istoric muzical expert și un ghid enciclopedic. "
            f"Oferă o scurtă biografie a artistului și exact 3 detalii interesante (trivia/trivia facts) "
            f"despre melodia '{song_name}'. "
            f"Răspunde în limba română într-un mod captivant și bine structurat cu titluri și bullet points. "
            f"Nu adăuga alte introduceri sau concluzii inutile."
        )
        return self.llm_client.generate(prompt, fallback_type="trivia", song_name=song_name)
