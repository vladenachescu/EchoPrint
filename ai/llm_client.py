import urllib.request
import urllib.error
import json
import ssl
from db.db_manager import DatabaseManager

class GeminiLLMClient:
    def __init__(self, db_manager=None):
        self.db = db_manager or DatabaseManager()
        self.api_url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"

    def get_api_key(self):
        """Preia cheia API din tabela de configurare SQLite."""
        return self.db.get_config_value("gemini_api_key")

    def call_gemini_api(self, prompt: str) -> str:
        """Efectuează un apel HTTP direct către API-ul Google Gemini."""
        api_key = self.get_api_key()
        if not api_key:
            raise ValueError("Gemini API key is not configured in DB.")

        url = f"{self.api_url}?key={api_key}"
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        req_body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        # We bypass SSL verification issues if any exist locally
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                resp_data = json.loads(response.read().decode("utf-8"))
                
                # Extract response text
                candidates = resp_data.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {})
                    parts = content.get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
                
                return "[Eroare] Răspunsul API-ului Gemini nu conține text."
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            raise RuntimeError(f"HTTP Error {e.code}: {err_msg}")
        except Exception as e:
            raise RuntimeError(f"Eroare de conexiune Gemini API: {str(e)}")

    def generate(self, prompt: str, fallback_type: str, song_name: str) -> str:
        """
        Încearcă să apeleze Gemini API. 
        Dacă cheia lipsește sau apelul eșuează, returnează un răspuns offline simulat (Mock).
        """
        api_key = self.get_api_key()
        if not api_key:
            return self._get_mock_response(fallback_type, song_name, "Cheia API nu este configurată (Mod Offline Mock)")
        
        try:
            return self.call_gemini_api(prompt)
        except Exception as e:
            print(f"[-] Gemini API call failed, falling back to mock: {e}")
            return self._get_mock_response(fallback_type, song_name, f"Eroare API ({str(e)}) - Mod Offline Mock activat")

    def _get_mock_response(self, fallback_type: str, song_name: str, notice: str) -> str:
        """Generează răspunsuri offline convingătoare în funcție de melodie."""
        # Normalize name for better mock matching
        song_lower = song_name.lower()
        
        # Split into possible song and artist parts if containing '-'
        parts = song_name.split("-", 1)
        artist_part = parts[0].strip() if len(parts) > 1 else "Unknown Artist"
        title_part = parts[1].strip() if len(parts) > 1 else song_name.strip()

        if fallback_type == "trivia":
            # Let's provide some realistic mock facts for common test tracks
            if "hotel california" in song_lower:
                return (
                    f"[{notice}]\n\n"
                    "🎤 **Artist Bio: The Eagles**\n"
                    "The Eagles este una dintre cele mai de succes trupe rock americane din anii '70, "
                    "cunoscută pentru armoniile lor vocale strânse și sound-ul country-rock rafinat.\n\n"
                    f"🎵 **Trivia despre '{title_part}':**\n"
                    "1. Piesa a fost lansată în 1977 și a câștigat Premiul Grammy pentru Record of the Year în 1978.\n"
                    "2. Textul misterios a stârnit numeroase speculații, dar membrii trupei au declarat că piesa vorbește despre excesul american, materialism și autodistrugere.\n"
                    "3. Soloul final de chitară, interpretat de Don Felder și Joe Walsh, este considerat unul dintre cele mai bune din istoria muzicii rock."
                )
            elif "billie jean" in song_lower:
                return (
                    f"[{notice}]\n\n"
                    "🎤 **Artist Bio: Michael Jackson**\n"
                    "Cunoscut ca 'Regele Muzicii Pop', Michael Jackson a transformat muzica, dansul și arta videoclipurilor muzicale în fenomene culturale globale.\n\n"
                    f"🎵 **Trivia despre '{title_part}':**\n"
                    "1. Piesa a fost un hit masiv de pe legendarul album 'Thriller' (1982), cel mai bine vândut album din toate timpurile.\n"
                    "2. Producătorul Quincy Jones nu a dorit inițial piesa pe album și a vrut să schimbe numele în 'Not My Lover' pentru a evita confuzia cu o tenismenă.\n"
                    "3. Jackson a introdus faimosul dans 'Moonwalk' pentru prima dată în timpul interpretării live a acestei piese la emisiunea Motown 25."
                )
            else:
                return (
                    f"[{notice}]\n\n"
                    f"🎤 **Artist Bio: {artist_part}**\n"
                    f"Un artist remarcabil în scena muzicală, apreciat pentru stilul unic și contribuția la genul său.\n\n"
                    f"🎵 **Trivia despre '{title_part}':**\n"
                    f"1. Melodia '{title_part}' este o creație de referință în portofoliul {artist_part}, atrăgând aprecierile criticilor.\n"
                    "2. Din punct de vedere muzical, piesa folosește o structură armonică expresivă care pune în valoare calitățile interpretative.\n"
                    "3. A fost primită cu entuziasm de fani, devenind rapid o piesă îndrăgită în concertele live."
                )
        
        elif fallback_type == "lyrics":
            if "hotel california" in song_lower:
                return (
                    f"[{notice}]\n\n"
                    f"🔍 **Analiză Mesaj & Semnificație ('{title_part}'):**\n"
                    "Piesa folosește metafora unui hotel de lux din care 'poți pleca oricând vrei, dar pe care nu îl poți părăsi niciodată' "
                    "pentru a descrie capcana materialismului, dependența de stilul de viață decadent din California și iluzia succesului facil.\n\n"
                    "❤️ **Sentiment dominant:** Melancolic, Misterios și Avertizor\n\n"
                    "🇷🇴 **Rezumat Versuri (Tradus în Română):**\n"
                    "Călătorul obosit oprește la un hotel primitor, dar realizează curând că locul este o închisoare de aur, "
                    "populată de oaspeți prizonieri ai propriilor vicii și iluzii, incapabili să scape din 'raiul' transformat în coșmar."
                )
            elif "billie jean" in song_lower:
                return (
                    f"[{notice}]\n\n"
                    f"🔍 **Analiză Mesaj & Semnificație ('{title_part}'):**\n"
                    "Piesa prezintă povestea unei femei care susține în mod fals că protagonistul este tatăl copilului ei. "
                    "Tema centrală abordează paranoia, presiunea faimei și responsabilitatea personală, avertizând să fim atenți pe cine iubim și ce promisiuni facem.\n\n"
                    "❤️ **Sentiment dominant:** Tensionat, Paranoic și Alert\n\n"
                    "🇷🇴 **Rezumat Versuri (Tradus în Română):**\n"
                    "Billie Jean susține că eu sunt tatăl copilului ei, dar ea nu este iubita mea, iar băiatul nu este fiul meu. "
                    "Mama mea mereu m-a sfătuit: ai grijă ce faci, nu umbla prin jur frângând inimi și ai grijă ce minciuni spui, pentru că minciuna devine adevăr."
                )
            else:
                return (
                    f"[{notice}]\n\n"
                    f"🔍 **Analiză Mesaj & Semnificație ('{title_part}'):**\n"
                    f"Piesa '{title_part}' explorează teme universale legate de experiențele umane, trăirile emoționale profunde sau reflecții asupra vieții de zi cu zi.\n\n"
                    "❤️ **Sentiment dominant:** Emoționant, Nostalgic și Reflexiv\n\n"
                    "🇷🇴 **Rezumat Versuri (Tradus în Română):**\n"
                    "Versurile evocă o stare de introspecție, subliniind importanța momentului prezent și relațiile interumane. "
                    "Traducerea liberă a mesajului pune accentul pe speranță, depășirea momentelor grele și regăsirea de sine."
                )
        
        return f"[{notice}]\nMock response for {song_name} ({fallback_type})"
