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
            f"Ești un critic muzical de renume și un fin analist literar. "
            f"Analizează mesajul și versurile piesei '{song_name}'. "
            f"Determină sentimentul predominant al piesei (de ex: melancolie, fericire, furie, nostalgie etc.) "
            f"și oferă un rezumat coerent al versurilor în limba română. "
            f"Răspunde direct, bine structurat cu titluri și bullet points. "
            f"Nu adăuga introduceri sau concluzii formale."
        )
        return self.llm_client.generate(prompt, fallback_type="lyrics", song_name=song_name)
