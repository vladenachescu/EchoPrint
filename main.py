import os
import sys
import hashlib
import argparse
from collections import Counter

# Add static FFmpeg binaries to PATH dynamically
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    pass
from audio.audio_processor import AudioProcessor
from db.db_manager import DatabaseManager
from audio.recorder import AudioRecorder
from audio.audio_source import MicrophoneInputStrategy, FileInputStrategy, MockInputStrategy
from ai.ai_noise_agent import AINoiseAgent
from ai.ai_recommendation_agent import AIRecommendationAgent

def get_file_hash(file_path):
    """Generate a hash for the file to prevent processing the same file twice."""
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def learn_directory(directory_path, db):
    print(f"[*] Caut fisiere audio in {directory_path}...")
    valid_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(valid_extensions):
                file_path = os.path.join(root, file)
                file_hash = get_file_hash(file_path)
                
                # Check if song is already in db
                if db.find_song_by_file_hash(file_hash):
                    print(f"[*] Sari peste {file} (deja in baza de date)")
                    continue
                
                print(f"[*] Procesez: {file}...")
                try:
                    hashes = AudioProcessor.fingerprint_file(file_path)
                    song_id = db.insert_song(file, file_hash)
                    
                    if song_id:
                        # Format for db insertion: (hash, song_id, offset)
                        db_hashes = [(h[0], song_id, h[1]) for h in hashes]
                        db.insert_fingerprints(db_hashes)
                        
                        # Extract and insert audio features for AI recommendations
                        try:
                            features = AIRecommendationAgent.extract_features(file_path)
                            db.insert_features(
                                song_id, 
                                features['bpm'], 
                                features['spectral_centroid'], 
                                features['spectral_flatness'], 
                                features['zero_crossing_rate']
                            )
                            print(f"    [+] Caracteristici extrase: BPM={features['bpm']:.1f}, Centroid={features['spectral_centroid']:.1f}")
                        except Exception as fe:
                            print(f"    [-] Nu s-au putut extrage caracteristicile AI: {fe}")
                            
                        print(f"    [+] Adaugat cu succes ({len(db_hashes)} amprente)")
                except Exception as e:
                    print(f"    [-] Eroare la procesarea {file}: {e}")

def recognize_audio(duration, db, strategy=None, source_name="Microfon"):
    # Strategy injection (Strategy Design Pattern)
    recorder = AudioRecorder(strategy=strategy, sample_rate=22050)
    audio_data = recorder.record(duration_seconds=duration)
    
    # 1. AI Quality assessment (AI Agent 1)
    noise_agent = AINoiseAgent(sample_rate=22050)
    quality = noise_agent.assess_quality(audio_data)
    
    print("\n" + "-"*50)
    print(f"[AI Quality Agent] Calitate semnal: {quality['rating']}")
    print(f"[AI Quality Agent] SNR estimat: {quality['snr']:.1f} dB")
    print(f"[AI Quality Agent] Clipping (distorsiune): {quality['clipping']:.2f}%")
    print(f"[AI Quality Agent] Recomandare: {quality['reason']}")
    print("-"*50 + "\n")
    
    if quality['rating'] == 'TOO_LOW':
        print("[-] Sunetul captat este prea slab. Recunoaștere anulată.")
        # Log failure to history
        db.insert_history(source_name, None, quality['snr'], 0)
        return
        
    # 2. AI Denoising (Spectral Gating)
    print("[*] Se aplică eliminarea zgomotului de fundal (denoising)...")
    audio_clean = noise_agent.denoise(audio_data)
    
    print("[*] Generare amprente pentru audio curățat...")
    hashes = AudioProcessor.fingerprint_audio_data(audio_clean)
    
    if not hashes:
        print("[-] Nu s-au putut extrage amprente din sunetul captat. Încearcă din nou.")
        db.insert_history(source_name, None, quality['snr'], 0)
        return
        
    print(f"[*] S-au generat {len(hashes)} amprente. Caut potriviri în baza de date...")
    
    # Extract just the hash strings to search in db
    hash_strings = [h[0] for h in hashes]
    matches = db.find_matches(hash_strings)
    
    if not matches:
        print("[-] Nu am găsit nicio potrivire în baza de date.")
        db.insert_history(source_name, None, quality['snr'], 0)
        return
        
    # Align matches
    sample_hash_dict = {}
    for h, offset in hashes:
        if h not in sample_hash_dict:
            sample_hash_dict[h] = []
        sample_hash_dict[h].append(offset)
        
    song_diffs = {}
    for db_hash, song_id, db_offset in matches:
        if db_hash in sample_hash_dict:
            for sample_offset in sample_hash_dict[db_hash]:
                diff = db_offset - sample_offset
                if song_id not in song_diffs:
                    song_diffs[song_id] = []
                song_diffs[song_id].append(diff)
                
    if not song_diffs:
        print("[-] Nu am găsit nicio aliniere validă.")
        db.insert_history(source_name, None, quality['snr'], 0)
        return
        
    # Score songs
    scores = {}
    for song_id, diffs in song_diffs.items():
        binned_diffs = [d - (d % 2) for d in diffs]
        counter = Counter(binned_diffs)
        best_diff, max_count = counter.most_common(1)[0]
        scores[song_id] = max_count
        
    # Find the best song
    best_song_id = max(scores, key=scores.get)
    best_score = scores[best_song_id]
    
    # Threshold for match
    if best_score < 5:
        print(f"[-] Potrivire prea slabă (Scor: {best_score}). Melodia nu a fost recunoscută sigur.")
        db.insert_history(source_name, None, quality['snr'], best_score)
        return
        
    song_name = db.get_song_by_id(best_song_id)
    print("\n" + "="*50)
    print(f"[!] MELODIE RECUNOSCUTĂ: {song_name}")
    print(f"[!] SCOR ÎNCREDERE: {best_score} potriviri")
    print("="*50 + "\n")
    
    # Log successful search in history
    db.insert_history(source_name, best_song_id, quality['snr'], best_score)
    
    # 3. AI Music Recommendations (AI Agent 2)
    recommender = AIRecommendationAgent(db)
    recs = recommender.recommend_for_song(best_song_id, top_n=3)
    if recs:
        print("="*50)
        print("[AI Recommendation Agent] Melodii similare recomandate:")
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec['song_name']} (Distanță metrică: {rec['distance']:.3f})")
        print("="*50 + "\n")

    # 4. LLM Agents (Trivia & Lyrics)
    print("[*] Interogare agenți LLM pentru trivia și versuri...")
    from ai.llm_client import GeminiLLMClient
    from ai.ai_trivia_agent import AIMusicTriviaAgent
    from ai.ai_lyrics_agent import AILyricsAgent

    llm_client = GeminiLLMClient(db_manager=db)
    trivia_agent = AIMusicTriviaAgent(llm_client=llm_client)
    lyrics_agent = AILyricsAgent(llm_client=llm_client)

    trivia = trivia_agent.get_trivia(song_name)
    lyrics = lyrics_agent.get_lyrics_analysis(song_name)

    print("="*50)
    print("[AI Music Trivia & Bio Agent]")
    print(trivia)
    print("="*50 + "\n")

    print("="*50)
    print("[AI Lyrics & Sentiment Agent]")
    print(lyrics)
    print("="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="EchoPrint - Aplicație de recunoaștere audio cu agenți AI (MDS)")
    parser.add_argument('mode', nargs='?', choices=['learn', 'listen'], help="Modul de funcționare: 'learn' (învață) sau 'listen' (ascultă)")
    parser.add_argument('--dir', type=str, help="Directorul cu fișiere audio (necesar pentru 'learn')")
    parser.add_argument('--duration', type=int, default=10, help="Durata de ascultare în secunde (pentru 'listen', default: 10)")
    parser.add_argument('--file', type=str, help="Folosește un fișier audio ca input (opțiune pentru testare)")
    parser.add_argument('--mock', action='store_true', help="Generează sunet artificial pentru testare (opțiune pentru testare)")
    parser.add_argument('--gui', action='store_true', help="Lansează interfața grafică desktop a aplicației")
    
    args = parser.parse_args()
    
    # Singleton DatabaseManager usage
    db = DatabaseManager('echoprint.db')
    
    if args.gui or (args.mode is None):
        # Launch graphical user interface
        print("[*] Se lansează interfața grafică desktop (GUI)...")
        from gui import EchoPrintGUI
        gui_app = EchoPrintGUI(db)
        gui_app.run()
        db.close()
        return
    
    if args.mode == 'learn':
        if not args.dir:
            print("[-] Trebuie să specifici un director folosind --dir")
            sys.exit(1)
        if not os.path.isdir(args.dir):
            print(f"[-] Directorul {args.dir} nu există.")
            sys.exit(1)
        learn_directory(args.dir, db)
        
    elif args.mode == 'listen':
        # Select Strategy (Strategy Design Pattern)
        strategy = None
        source_name = "Microfon"
        if args.file:
            if not os.path.isfile(args.file):
                print(f"[-] Fișierul {args.file} nu există.")
                sys.exit(1)
            strategy = FileInputStrategy(args.file)
            source_name = f"Fișier: {os.path.basename(args.file)}"
        elif args.mock:
            strategy = MockInputStrategy()
            source_name = "Mock Audio"
        else:
            strategy = MicrophoneInputStrategy()
            
        recognize_audio(args.duration, db, strategy=strategy, source_name=source_name)
        
    db.close()

if __name__ == "__main__":
    main()
