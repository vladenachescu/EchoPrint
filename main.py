import os
import sys

# Force UTF-8 encoding on Windows to prevent UnicodeEncodeError with Romanian diacritics
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

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
from ai.noise_agent import NoiseAgent
from ai.recommendation_agent import RecommendationAgent

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
    print(f"[*] Searching for audio files in {directory_path}...")
    valid_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith(valid_extensions):
                file_path = os.path.join(root, file)
                file_hash = get_file_hash(file_path)
                
                # Check if song is already in db
                if db.find_song_by_file_hash(file_hash):
                    print(f"[*] Skipping {file} (already in database)")
                    continue
                
                print(f"[*] Processing: {file}...")
                try:
                    hashes = AudioProcessor.fingerprint_file(file_path)
                    song_id = db.insert_song(file, file_hash)
                    
                    if song_id:
                        # Format for db insertion: (hash, song_id, offset)
                        db_hashes = [(h[0], song_id, h[1]) for h in hashes]
                        db.insert_fingerprints(db_hashes)
                        
                        # Extract and insert audio features for AI recommendations
                        try:
                            features = RecommendationAgent.extract_features(file_path)
                            db.insert_features(
                                song_id, 
                                features['bpm'], 
                                features['spectral_centroid'], 
                                features['spectral_flatness'], 
                                features['zero_crossing_rate']
                            )
                            print(f"    [+] Features extracted: BPM={features['bpm']:.1f}, Centroid={features['spectral_centroid']:.1f}")
                        except Exception as fe:
                            print(f"    [-] Could not extract AI features: {fe}")
                            
                        print(f"    [+] Successfully added ({len(db_hashes)} fingerprints)")
                except Exception as e:
                    print(f"    [-] Error processing {file}: {e}")

def recognize_audio(duration, db, strategy=None, source_name="Microphone"):
    # Strategy injection (Strategy Design Pattern)
    recorder = AudioRecorder(strategy=strategy, sample_rate=22050)
    audio_data = recorder.record(duration_seconds=duration)
    
    # 1. AI Quality assessment (AI Agent 1)
    noise_agent = NoiseAgent(sample_rate=22050)
    quality = noise_agent.assess_quality(audio_data)
    
    print("\n" + "-"*50)
    print(f"[Quality Report] Signal Quality: {quality['rating']}")
    print(f"[Quality Report] Estimated SNR: {quality['snr']:.1f} dB")
    print(f"[Quality Report] Clipping (distortion): {quality['clipping']:.2f}%")
    print(f"[Quality Report] Recommendation: {quality['reason']}")
    print("-"*50 + "\n")
    
    if quality['rating'] == 'TOO_LOW':
        print("[-] The captured sound is too weak. Recognition canceled.")
        # Log failure to history
        db.insert_history(source_name, None, quality['snr'], 0)
        return
        
    # 2. AI Denoising (Spectral Gating)
    print("[*] Applying background noise removal (denoising)...")
    audio_clean = noise_agent.denoise(audio_data)
    
    print("[*] Generating fingerprints for clean audio...")
    hashes = AudioProcessor.fingerprint_audio_data(audio_clean)
    
    if not hashes:
        print("[-] Could not extract fingerprints from the captured sound. Try again.")
        db.insert_history(source_name, None, quality['snr'], 0)
        return
        
    print(f"[*] Generated {len(hashes)} fingerprints. Searching for matches in database...")
    
    # Extract just the hash strings to search in db
    hash_strings = [h[0] for h in hashes]
    matches = db.find_matches(hash_strings)
    
    if not matches:
        print("[-] No matches found in the database.")
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
        print("[-] No valid alignment found.")
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
        print(f"[-] Match too weak (Score: {best_score}). Song was not recognized with certainty.")
        db.insert_history(source_name, None, quality['snr'], best_score)
        return
        
    song_name = db.get_song_by_id(best_song_id)
    print("\n" + "="*50)
    print(f"[!] RECOGNIZED SONG: {song_name}")
    print(f"[!] CONFIDENCE SCORE: {best_score} matches")
    print("="*50 + "\n")
    
    # Log successful search in history
    db.insert_history(source_name, best_song_id, quality['snr'], best_score)
    
    # 3. AI Music Recommendations (AI Agent 2)
    recommender = RecommendationAgent(db)
    recs = recommender.recommend_for_song(best_song_id, top_n=3)
    if recs:
        print("="*50)
        print("[Recommendation Agent] Recommended similar songs:")
        for i, rec in enumerate(recs, 1):
            print(f"  {i}. {rec['song_name']} (Distance metric: {rec['distance']:.3f})")
        print("="*50 + "\n")

    # 4. LLM Agents (Trivia & Lyrics)
    print("[*] Querying LLM agents for trivia and lyrics...")
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
    parser = argparse.ArgumentParser(description="EchoPrint - Audio Recognition Application with AI Agents (MDS)")
    parser.add_argument('mode', nargs='?', choices=['learn', 'listen'], help="Operation mode: 'learn' (learn songs) or 'listen' (recognize sound)")
    parser.add_argument('--dir', type=str, help="Directory with audio files (required for 'learn')")
    parser.add_argument('--duration', type=int, default=10, help="Listening duration in seconds (for 'listen', default: 10)")
    parser.add_argument('--file', type=str, help="Use an audio file as input (testing option)")
    parser.add_argument('--mock', action='store_true', help="Generate synthetic sound for testing (testing option)")
    parser.add_argument('--gui', action='store_true', help="Launch the desktop graphical user interface")
    
    args = parser.parse_args()
    
    # Singleton DatabaseManager usage
    db = DatabaseManager('echoprint.db')
    
    if args.gui or (args.mode is None):
        # Launch graphical user interface
        print("[*] Launching desktop graphical user interface (GUI)...")
        from gui import EchoPrintGUI
        gui_app = EchoPrintGUI(db)
        gui_app.run()
        db.close()
        return
    
    if args.mode == 'learn':
        if not args.dir:
            print("[-] You must specify a directory using --dir")
            sys.exit(1)
        if not os.path.isdir(args.dir):
            print(f"[-] The directory {args.dir} does not exist.")
            sys.exit(1)
        learn_directory(args.dir, db)
        
    elif args.mode == 'listen':
        # Select Strategy (Strategy Design Pattern)
        strategy = None
        source_name = "Microphone"
        if args.file:
            if not os.path.isfile(args.file):
                print(f"[-] The file {args.file} does not exist.")
                sys.exit(1)
            strategy = FileInputStrategy(args.file)
            source_name = f"File: {os.path.basename(args.file)}"
        elif args.mock:
            strategy = MockInputStrategy()
            source_name = "Mock Audio"
        else:
            strategy = MicrophoneInputStrategy()
            
        recognize_audio(args.duration, db, strategy=strategy, source_name=source_name)
        
    db.close()

if __name__ == "__main__":
    main()
