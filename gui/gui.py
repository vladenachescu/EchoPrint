import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import time
import numpy as np
import hashlib

# Add static FFmpeg binaries to PATH dynamically
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except ImportError:
    pass

# Import core business logic modules
from collections import Counter
from db.db_manager import DatabaseManager
from audio.audio_processor import AudioProcessor
from audio.recorder import AudioRecorder
from audio.audio_source import MicrophoneInputStrategy, FileInputStrategy, MockInputStrategy
from ai.ai_noise_agent import AINoiseAgent
from ai.ai_recommendation_agent import AIRecommendationAgent
from ai.ai_trivia_agent import AIMusicTriviaAgent
from ai.ai_lyrics_agent import AILyricsAgent

# Color Palette (Premium Dark Theme)
BG_MAIN = "#121216"       # Deep dark background
BG_CARD = "#1C1C24"       # Dark grey for cards
BG_FIELD = "#282833"      # Lighter grey for input fields
FG_MAIN = "#FFFFFF"       # White text
FG_MUTED = "#8E8E9F"      # Muted grey text
COLOR_ACCENT = "#0088FF"   # Modern Neon Neon Blue
COLOR_TEAL = "#00E5FF"     # Neon Teal
COLOR_GREEN = "#00E676"    # Success Green
COLOR_RED = "#FF3366"      # Soft Red for danger/delete
FONT_TITLE = ("Outfit", 16, "bold")
FONT_SUBTITLE = ("Outfit", 12, "bold")
FONT_BODY = ("Outfit", 10)
FONT_CONSOLE = ("Consolas", 9)

class EchoPrintGUI:
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.root = tk.Tk()
        self.root.title("EchoPrint - Audio Recognition MDS")
        self.root.geometry("850x650")
        self.root.minsize(800, 600)
        self.root.configure(bg=BG_MAIN)
        
        # Keep track of active tasks/recording
        self.is_processing = False
        self.selected_file_path = None
        
        self.setup_styles()
        self.create_widgets()
        self.load_database_songs()
        self.load_search_history()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Configure Notebook (Tabs)
        self.style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=BG_CARD, foreground=FG_MUTED, borderwidth=0, padding=(15, 8), font=FONT_SUBTITLE)
        self.style.map("TNotebook.Tab", 
                       background=[("selected", COLOR_ACCENT)], 
                       foreground=[("selected", FG_MAIN)])
        
        # Configure Treeview (Tables)
        self.style.configure("Treeview", background=BG_CARD, foreground=FG_MAIN, fieldbackground=BG_CARD, borderwidth=0, font=FONT_BODY, rowheight=25)
        self.style.configure("Treeview.Heading", background=BG_FIELD, foreground=FG_MAIN, borderwidth=1, font=FONT_BODY)
        self.style.map("Treeview", background=[("selected", COLOR_ACCENT)], foreground=[("selected", FG_MAIN)])
        
        # Configure Progressbar
        self.style.configure("TProgressbar", thickness=10, troughcolor=BG_FIELD, background=COLOR_ACCENT)

    def create_widgets(self):
        # Create Notebook (Tab controller)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 4 Tabs
        self.tab_recognition = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_database = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_history = tk.Frame(self.notebook, bg=BG_MAIN)
        self.tab_learning = tk.Frame(self.notebook, bg=BG_MAIN)
        
        self.notebook.add(self.tab_recognition, text="🔎 Recognition")
        self.notebook.add(self.tab_database, text="📁 Database")
        self.notebook.add(self.tab_history, text="📜 Search History")
        self.notebook.add(self.tab_learning, text="⚙️ Learn Songs")
        
        # Build widgets for each tab
        self.build_tab_recognition()
        self.build_tab_database()
        self.build_tab_history()
        self.build_tab_learning()

    # ==========================================
    # TAB 1: RECOGNITION WIDGETS
    # ==========================================
    def build_tab_recognition(self):
        # Left Panel (Controls)
        panel_left = tk.Frame(self.tab_recognition, bg=BG_CARD, width=320)
        panel_left.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), pady=10)
        panel_left.pack_propagate(False)
        
        lbl_control = tk.Label(panel_left, text="Recognition Options", font=FONT_TITLE, fg=FG_MAIN, bg=BG_CARD)
        lbl_control.pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        # Source Selection Strategy
        lbl_source = tk.Label(panel_left, text="Audio Source Input:", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD)
        lbl_source.pack(anchor=tk.W, padx=15, pady=(10, 2))
        
        self.input_source_var = tk.StringVar(value="Microphone")
        sources = ["Microphone", "Audio File (.mp3, .wav, .m4a)", "Mock Simulation (Test Signal)"]
        for s in sources:
            r = tk.Radiobutton(panel_left, text=s, variable=self.input_source_var, value=s, 
                               bg=BG_CARD, fg=FG_MAIN, selectcolor=BG_FIELD, activebackground=BG_CARD, 
                               activeforeground=FG_MAIN, font=FONT_BODY, command=self.on_source_changed)
            r.pack(anchor=tk.W, padx=20, pady=4)
            
        # File selector frame (initially hidden/disabled)
        self.file_frame = tk.Frame(panel_left, bg=BG_CARD)
        self.file_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.btn_select_file = tk.Button(self.file_frame, text="Choose Audio File...", bg=BG_FIELD, fg=FG_MAIN, 
                                         activebackground=BG_FIELD, activeforeground=FG_MAIN, borderwidth=0, 
                                         font=FONT_BODY, cursor="hand2", command=self.select_audio_file)
        self.btn_select_file.pack(fill=tk.X, pady=5)
        self.lbl_selected_file = tk.Label(self.file_frame, text="No file selected", font=FONT_BODY, 
                                          fg=FG_MUTED, bg=BG_CARD, wraplength=280, justify=tk.LEFT)
        self.lbl_selected_file.pack(fill=tk.X)
        self.file_frame.pack_forget() # Hide by default (microphone selected)
        
        # Listening duration slider
        lbl_duration = tk.Label(panel_left, text="Listening Duration (seconds):", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD)
        lbl_duration.pack(anchor=tk.W, padx=15, pady=(15, 2))
        self.slider_duration = tk.Scale(panel_left, from_=3, to=20, orient=tk.HORIZONTAL, bg=BG_CARD, fg=FG_MAIN,
                                        troughcolor=BG_FIELD, highlightthickness=0, borderwidth=0, font=FONT_BODY)
        self.slider_duration.set(10)
        self.slider_duration.pack(fill=tk.X, padx=20, pady=5)
        
        # Action button (IDENTIFY)
        self.btn_identify = tk.Button(panel_left, text="🔍 IDENTIFY NOW", font=("Outfit", 12, "bold"), 
                                    bg=COLOR_ACCENT, fg=FG_MAIN, activebackground=COLOR_ACCENT, activeforeground=FG_MAIN,
                                    borderwidth=0, cursor="hand2", command=self.start_recognition_thread)
        self.btn_identify.pack(fill=tk.X, side=tk.BOTTOM, padx=20, pady=20, ipady=8)
        
        # Right Panel (Results & AI Reports)
        panel_right = tk.Frame(self.tab_recognition, bg=BG_MAIN)
        panel_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, pady=10)
        
        # Quality report card
        card_quality = tk.Frame(panel_right, bg=BG_CARD)
        card_quality.pack(fill=tk.X, pady=(0, 10))
        
        lbl_q_title = tk.Label(card_quality, text="AI Quality Agent Report", font=FONT_SUBTITLE, fg=COLOR_TEAL, bg=BG_CARD)
        lbl_q_title.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        self.lbl_q_status = tk.Label(card_quality, text="Ready for Analysis", font=("Outfit", 11, "bold"), fg=FG_MUTED, bg=BG_CARD)
        self.lbl_q_status.pack(anchor=tk.W, padx=20, pady=2)
        
        self.lbl_q_details = tk.Label(card_quality, text="SNR: -- dB | Clipping: --% | Volume (RMS): --", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD)
        self.lbl_q_details.pack(anchor=tk.W, padx=20, pady=(2, 15))
        
        # Main result card
        card_result = tk.Frame(panel_right, bg=BG_CARD)
        card_result.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        lbl_res_title = tk.Label(card_result, text="Recognition Result", font=FONT_SUBTITLE, fg=COLOR_ACCENT, bg=BG_CARD)
        lbl_res_title.pack(anchor=tk.W, padx=15, pady=(15, 10))
        
        self.progress_bar = ttk.Progressbar(card_result, orient=tk.HORIZONTAL, mode='determinate', style="TProgressbar")
        self.progress_bar.pack(fill=tk.X, padx=20, pady=5)
        self.progress_bar.pack_forget() # Hide initially
        
        self.lbl_song_result = tk.Label(card_result, text="Press the IDENTIFY NOW button to start audio analysis.", 
                                        font=("Outfit", 13, "bold"), fg=FG_MUTED, bg=BG_CARD, wraplength=450)
        self.lbl_song_result.pack(padx=20, pady=10, fill=tk.BOTH)
        
        self.lbl_score_result = tk.Label(card_result, text="", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD)
        self.lbl_score_result.pack(padx=20, pady=2, fill=tk.X)
        
        # Sub-notebook for AI analysis and recommendations
        self.ai_notebook = ttk.Notebook(card_result)
        self.ai_notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 15))
        
        # Tab 1: Recommendations
        self.tab_recs = tk.Frame(self.ai_notebook, bg=BG_CARD)
        self.ai_notebook.add(self.tab_recs, text="🎵 Recommendations")
        
        self.lbl_recs_list = tk.Label(self.tab_recs, text="Similar songs will be recommended here based on BPM and spectral features.", 
                                      font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD, justify=tk.LEFT, wraplength=420)
        self.lbl_recs_list.pack(anchor=tk.W, padx=15, pady=15, fill=tk.BOTH, expand=True)
        
        # Tab 2: Trivia & Bio
        self.tab_trivia = tk.Frame(self.ai_notebook, bg=BG_CARD)
        self.ai_notebook.add(self.tab_trivia, text="💡 Trivia & Biography")
        
        self.txt_trivia = tk.Text(self.tab_trivia, bg=BG_CARD, fg=FG_MAIN, insertbackground=FG_MAIN, borderwidth=0, font=FONT_BODY, wrap=tk.WORD)
        self.txt_trivia.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        self.txt_trivia.insert(tk.END, "Informațiile despre artist și trivia vor apărea aici după recunoaștere.")
        self.txt_trivia.configure(state=tk.DISABLED)
        
        # Tab 3: Meaning & Lyrics
        self.tab_lyrics = tk.Frame(self.ai_notebook, bg=BG_CARD)
        self.ai_notebook.add(self.tab_lyrics, text="📝 Lyrics & Meaning")
        
        self.txt_lyrics = tk.Text(self.tab_lyrics, bg=BG_CARD, fg=FG_MAIN, insertbackground=FG_MAIN, borderwidth=0, font=FONT_BODY, wrap=tk.WORD)
        self.txt_lyrics.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        self.txt_lyrics.insert(tk.END, "Analiza mesajului piesei și rezumatul versurilor vor apărea aici după recunoaștere.")
        self.txt_lyrics.configure(state=tk.DISABLED)

    def on_source_changed(self):
        source = self.input_source_var.get()
        if source == "Audio File (.mp3, .wav, .m4a)":
            self.file_frame.pack(fill=tk.X, padx=15, pady=10)
        else:
            self.file_frame.pack_forget()

    def select_audio_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav *.ogg *.flac *.m4a")])
        if file_path:
            self.selected_file_path = file_path
            self.lbl_selected_file.configure(text=os.path.basename(file_path))

    # ==========================================
    # TAB 2: DATABASE CRUD WIDGETS
    # ==========================================
    def build_tab_database(self):
        # Top filter bar
        frame_top = tk.Frame(self.tab_database, bg=BG_MAIN)
        frame_top.pack(fill=tk.X, pady=(10, 5))
        
        lbl_search = tk.Label(frame_top, text="Filter by name:", font=FONT_BODY, fg=FG_MAIN, bg=BG_MAIN)
        lbl_search.pack(side=tk.LEFT, padx=10)
        
        self.db_search_var = tk.StringVar()
        self.db_search_var.trace_add("write", self.filter_database_songs)
        
        self.entry_search = tk.Entry(frame_top, textvariable=self.db_search_var, bg=BG_FIELD, fg=FG_MAIN, 
                                     insertbackground=FG_MAIN, borderwidth=0, font=FONT_BODY, width=35)
        self.entry_search.pack(side=tk.LEFT, padx=5, ipady=4)
        
        # Treeview (Table of Songs)
        frame_table = tk.Frame(self.tab_database, bg=BG_MAIN)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scroll_y = tk.Scrollbar(frame_table, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Columns: ID, Song Name, Fingerprint Count
        self.tree_songs = ttk.Treeview(frame_table, columns=("id", "name", "fingerprints"), show="headings", yscrollcommand=scroll_y.set)
        self.tree_songs.heading("id", text="Song ID")
        self.tree_songs.heading("name", text="Song File Name")
        self.tree_songs.heading("fingerprints", text="Fingerprints Stored")
        
        self.tree_songs.column("id", width=100, anchor=tk.CENTER)
        self.tree_songs.column("name", width=450, anchor=tk.W)
        self.tree_songs.column("fingerprints", width=150, anchor=tk.CENTER)
        
        self.tree_songs.pack(fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.tree_songs.yview)
        
        # Control Buttons for CRUD
        frame_controls = tk.Frame(self.tab_database, bg=BG_MAIN)
        frame_controls.pack(fill=tk.X, pady=(5, 15), padx=10)
        
        self.btn_edit_song = tk.Button(frame_controls, text="✏️ Rename Song", font=FONT_BODY, bg=BG_CARD, fg=FG_MAIN, 
                                       activebackground=BG_CARD, activeforeground=FG_MAIN, borderwidth=0, 
                                       cursor="hand2", padx=15, pady=8, command=self.modify_selected_song)
        self.btn_edit_song.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_delete_song = tk.Button(frame_controls, text="🗑️ Delete Song", font=FONT_BODY, bg=COLOR_RED, fg=FG_MAIN, 
                                         activebackground=COLOR_RED, activeforeground=FG_MAIN, borderwidth=0, 
                                         cursor="hand2", padx=15, pady=8, command=self.delete_selected_song)
        self.btn_delete_song.pack(side=tk.LEFT)

    def load_database_songs(self):
        # Clear treeview
        for item in self.tree_songs.get_children():
            self.tree_songs.delete(item)
            
        # Get songs from DB
        self.songs_cache = self.db.get_all_songs_metadata()
        for s_id, s_name, fp_count in self.songs_cache:
            self.tree_songs.insert("", tk.END, values=(s_id, s_name, fp_count))

    def filter_database_songs(self, *args):
        query = self.db_search_var.get().lower()
        for item in self.tree_songs.get_children():
            self.tree_songs.delete(item)
            
        for s_id, s_name, fp_count in self.songs_cache:
            if query in s_name.lower():
                self.tree_songs.insert("", tk.END, values=(s_id, s_name, fp_count))

    def modify_selected_song(self):
        selected = self.tree_songs.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a song from the table to modify.")
            return
            
        values = self.tree_songs.item(selected[0], "values")
        song_id = int(values[0])
        old_name = values[1]
        
        # Simple Popup Window for Edit Name
        dialog = tk.Toplevel(self.root)
        dialog.title("Modify Song Name")
        dialog.geometry("450x180")
        dialog.configure(bg=BG_CARD)
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        lbl_info = tk.Label(dialog, text="Enter new name for the song:", font=FONT_BODY, fg=FG_MAIN, bg=BG_CARD)
        lbl_info.pack(anchor=tk.W, padx=20, pady=(20, 5))
        
        entry_name = tk.Entry(dialog, bg=BG_FIELD, fg=FG_MAIN, insertbackground=FG_MAIN, borderwidth=0, font=FONT_BODY)
        entry_name.insert(0, old_name)
        entry_name.pack(fill=tk.X, padx=20, pady=5, ipady=4)
        
        def save():
            new_name = entry_name.get().strip()
            if not new_name:
                messagebox.showerror("Error", "The name cannot be empty.", parent=dialog)
                return
            if self.db.update_song_name(song_id, new_name):
                dialog.destroy()
                self.load_database_songs()
                messagebox.showinfo("Success", "The song name was successfully updated.")
            else:
                messagebox.showerror("Error", "The update failed.", parent=dialog)
                
        btn_save = tk.Button(dialog, text="Save", font=FONT_BODY, bg=COLOR_ACCENT, fg=FG_MAIN, borderwidth=0, 
                             cursor="hand2", padx=15, pady=6, command=save)
        btn_save.pack(side=tk.RIGHT, padx=20, pady=20)
        
        btn_cancel = tk.Button(dialog, text="Cancel", font=FONT_BODY, bg=BG_FIELD, fg=FG_MAIN, borderwidth=0, 
                               cursor="hand2", padx=15, pady=6, command=dialog.destroy)
        btn_cancel.pack(side=tk.RIGHT, pady=20)

    def delete_selected_song(self):
        selected = self.tree_songs.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a song from the table to delete.")
            return
            
        values = self.tree_songs.item(selected[0], "values")
        song_id = int(values[0])
        song_name = values[1]
        
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the song '{song_name}'?\nThis action will delete all its fingerprints from the database.")
        if confirm:
            if self.db.delete_song(song_id):
                self.load_database_songs()
                self.load_search_history() # Reload history as references might be set to NULL
                messagebox.showinfo("Success", f"Song '{song_name}' was deleted from the database.")
            else:
                messagebox.showerror("Error", "Song deletion failed.")

    # ==========================================
    # TAB 3: SEARCH HISTORY WIDGETS
    # ==========================================
    def build_tab_history(self):
        frame_table = tk.Frame(self.tab_history, bg=BG_MAIN)
        frame_table.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scroll_y = tk.Scrollbar(frame_table, orient=tk.VERTICAL)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Columns: ID, Time, Source, Result, SNR, Score
        self.tree_history = ttk.Treeview(frame_table, columns=("id", "time", "source", "result", "snr", "score"), show="headings", yscrollcommand=scroll_y.set)
        self.tree_history.heading("id", text="History ID")
        self.tree_history.heading("time", text="Date / Time")
        self.tree_history.heading("source", text="Input Source")
        self.tree_history.heading("result", text="Identified Song")
        self.tree_history.heading("snr", text="Estimated SNR")
        self.tree_history.heading("score", text="Confidence Score")
        
        self.tree_history.column("id", width=80, anchor=tk.CENTER)
        self.tree_history.column("time", width=150, anchor=tk.CENTER)
        self.tree_history.column("source", width=150, anchor=tk.W)
        self.tree_history.column("result", width=250, anchor=tk.W)
        self.tree_history.column("snr", width=100, anchor=tk.CENTER)
        self.tree_history.column("score", width=100, anchor=tk.CENTER)
        
        self.tree_history.pack(fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.tree_history.yview)
        
        # Control Buttons
        frame_controls = tk.Frame(self.tab_history, bg=BG_MAIN)
        frame_controls.pack(fill=tk.X, pady=(5, 15), padx=10)
        
        self.btn_clear_history = tk.Button(frame_controls, text="🧹 Clear Search History", font=FONT_BODY, bg=COLOR_RED, fg=FG_MAIN, 
                                           activebackground=COLOR_RED, activeforeground=FG_MAIN, borderwidth=0, 
                                           cursor="hand2", padx=15, pady=8, command=self.clear_search_history)
        self.btn_clear_history.pack(side=tk.LEFT)

    def load_search_history(self):
        for item in self.tree_history.get_children():
            self.tree_history.delete(item)
            
        history = self.db.get_history()
        # Row layout: history_id, search_time, input_source, song_name, snr, confidence_score
        for h_id, h_time, h_source, h_result, h_snr, h_score in history:
            res_str = h_result if h_result else "[No song recognized]"
            snr_str = f"{h_snr:.1f} dB" if h_snr is not None else "--"
            score_str = str(h_score) if h_score > 0 else "--"
            self.tree_history.insert("", tk.END, values=(h_id, h_time, h_source, res_str, snr_str, score_str))

    def clear_search_history(self):
        if not self.tree_history.get_children():
            return
        confirm = messagebox.askyesno("Confirm Clear History", "Are you sure you want to delete all search history from the database?")
        if confirm:
            if self.db.clear_history():
                self.load_search_history()
                messagebox.showinfo("Success", "The search history was cleared.")
            else:
                messagebox.showerror("Error", "Clearing history failed.")

    # ==========================================
    # TAB 4: LEARNING & DIRECTORY WIDGETS
    # ==========================================
    def build_tab_learning(self):
        # Settings area for Gemini API Key
        frame_settings = tk.Frame(self.tab_learning, bg=BG_CARD)
        frame_settings.pack(fill=tk.X, padx=10, pady=(10, 0))
        
        lbl_settings_title = tk.Label(frame_settings, text="⚙️ Google Gemini API Configuration", font=FONT_TITLE, fg=FG_MAIN, bg=BG_CARD)
        lbl_settings_title.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        lbl_settings_desc = tk.Label(frame_settings, text="Enter your Gemini API key to enable intelligent trivia generation and real-time lyrics analysis.", 
                                     font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD)
        lbl_settings_desc.pack(anchor=tk.W, padx=15, pady=(2, 10))
        
        frame_key_input = tk.Frame(frame_settings, bg=BG_CARD)
        frame_key_input.pack(fill=tk.X, padx=15, pady=(5, 15))
        
        lbl_key = tk.Label(frame_key_input, text="Gemini API Key:", font=FONT_BODY, fg=FG_MAIN, bg=BG_CARD)
        lbl_key.pack(side=tk.LEFT, padx=(0, 10))
        
        self.entry_api_key = tk.Entry(frame_key_input, bg=BG_FIELD, fg=FG_MAIN, insertbackground=FG_MAIN, borderwidth=0, font=FONT_BODY, width=50, show="*")
        self.entry_api_key.pack(side=tk.LEFT, padx=(0, 10), ipady=5)
        
        # Load existing key
        existing_key = self.db.get_config_value("gemini_api_key") or ""
        self.entry_api_key.insert(0, existing_key)
        
        btn_save_key = tk.Button(frame_key_input, text="Save Key", font=("Outfit", 10, "bold"), bg=COLOR_TEAL, fg=BG_MAIN, borderwidth=0, 
                                 cursor="hand2", padx=15, command=self.save_gemini_api_key)
        btn_save_key.pack(side=tk.LEFT, ipady=2)

        # Folder selection area
        frame_dir = tk.Frame(self.tab_learning, bg=BG_CARD)
        frame_dir.pack(fill=tk.X, padx=10, pady=10)
        
        lbl_dir_title = tk.Label(frame_dir, text="Learn files from folder", font=FONT_TITLE, fg=FG_MAIN, bg=BG_CARD)
        lbl_dir_title.pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        lbl_dir_desc = tk.Label(frame_dir, text="The application will process the audio files in the folder, generate fingerprints and AI features, and save them in the database.", 
                                font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD, wraplength=700, justify=tk.LEFT)
        lbl_dir_desc.pack(anchor=tk.W, padx=15, pady=(2, 10))
        
        frame_picker = tk.Frame(frame_dir, bg=BG_CARD)
        frame_picker.pack(fill=tk.X, padx=15, pady=(5, 15))
        
        self.entry_dir_path = tk.Entry(frame_picker, bg=BG_FIELD, fg=FG_MAIN, insertbackground=FG_MAIN, borderwidth=0, font=FONT_BODY, width=60)
        self.entry_dir_path.pack(side=tk.LEFT, padx=(0, 10), ipady=5, expand=True, fill=tk.X)
        
        btn_browse_dir = tk.Button(frame_picker, text="Choose Folder...", font=FONT_BODY, bg=BG_FIELD, fg=FG_MAIN, borderwidth=0, 
                                   cursor="hand2", command=self.browse_learning_directory)
        btn_browse_dir.pack(side=tk.LEFT, padx=(0, 10), ipady=2)
        
        self.btn_start_learn = tk.Button(frame_picker, text="🚀 Learn Songs", font=("Outfit", 10, "bold"), bg=COLOR_ACCENT, fg=FG_MAIN, borderwidth=0, 
                                         cursor="hand2", padx=15, command=self.start_learning_thread)
        self.btn_start_learn.pack(side=tk.LEFT, ipady=2)
        
        # Real-time processing logs
        frame_logs = tk.Frame(self.tab_learning, bg=BG_MAIN)
        frame_logs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        lbl_log = tk.Label(frame_logs, text="Log de procesare în timp real:", font=FONT_BODY, fg=FG_MUTED, bg=BG_MAIN)
        lbl_log.pack(anchor=tk.W, pady=2)
        
        # Text log widget with Scrollbar
        self.txt_console = tk.Text(frame_logs, bg=BG_CARD, fg=COLOR_TEAL, insertbackground=FG_MAIN, borderwidth=0, font=FONT_CONSOLE, wrap=tk.WORD)
        self.txt_console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scroll_txt = tk.Scrollbar(frame_logs, command=self.txt_console.yview)
        scroll_txt.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_console.config(yscrollcommand=scroll_txt.set)
        
        self.log_console("Ready for processing. Select a folder to start.")

    def browse_learning_directory(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.entry_dir_path.delete(0, tk.END)
            self.entry_dir_path.insert(0, dir_path)

    def log_console(self, text):
        self.txt_console.configure(state=tk.NORMAL)
        self.txt_console.insert(tk.END, f"{text}\n")
        self.txt_console.see(tk.END)
        self.txt_console.configure(state=tk.DISABLED)

    # ==========================================
    # WORKER THREAD FOR LEARNING SONGS
    # ==========================================
    def start_learning_thread(self):
        if self.is_processing:
            return
            
        dir_path = self.entry_dir_path.get().strip()
        if not dir_path or not os.path.isdir(dir_path):
            messagebox.showerror("Error", "The specified folder is invalid or does not exist.")
            return
            
        self.is_processing = True
        self.btn_start_learn.configure(state=tk.DISABLED, bg=BG_FIELD)
        
        # Launch background processing thread to keep Tkinter responsive
        t = threading.Thread(target=self.bg_learning_task, args=(dir_path,), daemon=True)
        t.start()

    def bg_learning_task(self, dir_path):
        self.log_console("\n" + "="*50)
        self.log_console(f"[*] Searching for audio files in {dir_path}...")
        valid_extensions = ('.mp3', '.wav', '.ogg', '.flac', '.m4a')
        
        # Scan folder first
        audio_files = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.lower().endswith(valid_extensions):
                    audio_files.append(os.path.join(root, file))
                    
        if not audio_files:
            self.log_console("[-] No supported audio files found (.mp3, .wav, .ogg, .flac, .m4a).")
            self.learning_task_finished()
            return
            
        self.log_console(f"[+] Found {len(audio_files)} audio files. Initiating processing...")
        
        for i, file_path in enumerate(audio_files, 1):
            file_name = os.path.basename(file_path)
            self.log_console(f"[{i}/{len(audio_files)}] Processing: {file_name}...")
            
            file_hash = ""
            try:
                # Fast hash generation
                hasher = hashlib.md5()
                with open(file_path, 'rb') as f:
                    buf = f.read(65536)
                    while len(buf) > 0:
                        hasher.update(buf)
                        buf = f.read(65536)
                file_hash = hasher.hexdigest()
            except Exception as he:
                self.log_console(f"    [-] Error generating hash: {he}")
                continue
                
            # Check db
            if self.db.find_song_by_file_hash(file_hash):
                self.log_console(f"    [*] Skipping (already in database)")
                continue
                
            try:
                # Fingerprint
                hashes = AudioProcessor.fingerprint_file(file_path)
                song_id = self.db.insert_song(file_name, file_hash)
                
                if song_id:
                    db_hashes = [(h[0], song_id, h[1]) for h in hashes]
                    self.db.insert_fingerprints(db_hashes)
                    self.log_console(f"    [+] Added to DB ({len(db_hashes)} fingerprints)")
                    
                    # Extract features
                    try:
                        features = AIRecommendationAgent.extract_features(file_path)
                        self.db.insert_features(
                            song_id,
                            features['bpm'],
                            features['spectral_centroid'],
                            features['spectral_flatness'],
                            features['zero_crossing_rate']
                        )
                        self.log_console(f"    [+] AI Features saved: BPM={features['bpm']:.1f}, Centroid={features['spectral_centroid']:.1f}")
                    except Exception as fe:
                        self.log_console(f"    [-] Error extracting AI features: {fe}")
            except Exception as e:
                self.log_console(f"    [-] Error processing: {e}")
                
        self.log_console("[*] Processing complete.")
        self.log_console("="*50 + "\n")
        
        # Callback to update GUI in main thread
        self.root.after(0, self.learning_task_finished)

    def learning_task_finished(self):
        self.is_processing = False
        self.btn_start_learn.configure(state=tk.NORMAL, bg=COLOR_ACCENT)
        self.load_database_songs() # Reload db tab treeview
        messagebox.showinfo("Success", "Folder scanning and processing completed.")

    # ==========================================
    # WORKER THREAD FOR AUDIO RECOGNITION
    # ==========================================
    def start_recognition_thread(self):
        if self.is_processing:
            return
            
        source = self.input_source_var.get()
        
        # Check source inputs
        if source == "Audio File (.mp3, .wav, .m4a)":
            if not self.selected_file_path or not os.path.isfile(self.selected_file_path):
                messagebox.showerror("Error", "Please select a valid audio file from your computer.")
                return
                
        self.is_processing = True
        self.btn_identify.configure(state=tk.DISABLED, bg=BG_FIELD, text="🔍 PROCESSING...")
        
        # Show Progress elements
        self.progress_bar.pack(fill=tk.X, padx=20, pady=5)
        self.progress_bar.configure(value=0)
        self.lbl_song_result.configure(text="Preparing recording/audio reading...", fg=FG_MAIN)
        self.lbl_score_result.configure(text="")
        self.lbl_recs_list.configure(text="Waiting for recognition result...")
        
        # Start background search
        t = threading.Thread(target=self.bg_recognition_task, daemon=True)
        t.start()

    def bg_recognition_task(self):
        source = self.input_source_var.get()
        duration = self.slider_duration.get()
        
        # Initialize Audio Strategy (Strategy Pattern)
        strategy = None
        source_name = "Microphone"
        
        if source == "Audio File (.mp3, .wav, .m4a)":
            strategy = FileInputStrategy(self.selected_file_path)
            source_name = f"Fișier: {os.path.basename(self.selected_file_path)}"
        elif source == "Mock Simulation (Test Signal)":
            strategy = MockInputStrategy()
            source_name = "Mock Audio"
        else:
            strategy = MicrophoneInputStrategy()
            source_name = "Microphone"
            
        try:
            # UI animation simulate for duration
            def update_progress():
                step = 100 / (duration * 10)
                for _ in range(int(duration * 10)):
                    if not self.is_processing:
                        break
                    time.sleep(0.1)
                    self.root.after(0, lambda: self.progress_bar.step(step))

            # Start loading/recording
            self.root.after(0, lambda: self.lbl_song_result.configure(text=f"Listening/Loading track ({duration}s)..."))
            
            # Run progressbar in separate thread
            prog_thread = threading.Thread(target=update_progress, daemon=True)
            prog_thread.start()
            
            # Load audio data
            recorder = AudioRecorder(strategy=strategy, sample_rate=22050)
            audio_data = recorder.record(duration_seconds=duration)
            
            # 1. Quality assess
            self.root.after(0, lambda: self.lbl_song_result.configure(text="Evaluating audio quality with AI Agent..."))
            noise_agent = AINoiseAgent(sample_rate=22050)
            quality = noise_agent.assess_quality(audio_data)
            
            # Update Quality view
            q_color = COLOR_GREEN if quality['rating'] == 'EXCELLENT' else (COLOR_RED if quality['rating'] in ['TOO_LOW', 'DISTORTED'] else "#FFAA00")
            self.root.after(0, lambda: self.lbl_q_status.configure(text=f"Rating: {quality['rating']}", fg=q_color))
            self.root.after(0, lambda: self.lbl_q_details.configure(
                text=f"SNR: {quality['snr']:.1f} dB | Clipping: {quality['clipping']:.2f}% | RMS: {quality['rms']:.4f}\nRecomandare: {quality['reason']}"
            ))
            
            if quality['rating'] == 'TOO_LOW':
                self.root.after(0, lambda: self.recognition_failed("The audio signal is too weak (microphone muted).", source_name, quality['snr'], 0))
                return
                
            # 2. Denoising
            self.root.after(0, lambda: self.lbl_song_result.configure(text="AI Agent: Applying spectral denoising..."))
            audio_clean = noise_agent.denoise(audio_data)
            
            # 3. Fingerprinting
            self.root.after(0, lambda: self.lbl_song_result.configure(text="Calculating spectrogram fingerprints..."))
            hashes = AudioProcessor.fingerprint_audio_data(audio_clean)
            
            if not hashes:
                self.root.after(0, lambda: self.recognition_failed("Could not generate fingerprints from the signal.", source_name, quality['snr'], 0))
                return
                
            self.root.after(0, lambda: self.lbl_song_result.configure(text="Querying database..."))
            hash_strings = [h[0] for h in hashes]
            matches = self.db.find_matches(hash_strings)
            
            if not matches:
                self.root.after(0, lambda: self.recognition_failed("Song was not found in the database.", source_name, quality['snr'], 0))
                return
                
            # Align
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
                self.root.after(0, lambda: self.recognition_failed("Fingerprint temporal alignment error.", source_name, quality['snr'], 0))
                return
                
            # Score
            scores = {}
            for song_id, diffs in song_diffs.items():
                binned_diffs = [d - (d % 2) for d in diffs]
                counter = Counter(binned_diffs)
                best_diff, max_count = counter.most_common(1)[0]
                scores[song_id] = max_count
                
            best_song_id = max(scores, key=scores.get)
            best_score = scores[best_song_id]
            
            if best_score < 5:
                self.root.after(0, lambda: self.recognition_failed(f"Signal too weak to be certain (Score: {best_score} matches)", source_name, quality['snr'], best_score))
                return
                
            song_name = self.db.get_song_by_id(best_song_id)
            
            # Save to DB history
            self.db.insert_history(source_name, best_song_id, quality['snr'], best_score)
            
            # Load recommendations
            recommender = AIRecommendationAgent(self.db)
            recs = recommender.recommend_for_song(best_song_id, top_n=3)
            
            # Call AI LLM agents to fetch trivia and lyrics in background
            self.root.after(0, lambda: self.lbl_song_result.configure(text=f"🎵 Recognized: {song_name}\nQuerying LLM agents..."))
            
            from ai.llm_client import GeminiLLMClient
            llm_client = GeminiLLMClient(db_manager=self.db)
            trivia_agent = AIMusicTriviaAgent(llm_client=llm_client)
            lyrics_agent = AILyricsAgent(llm_client=llm_client)
            
            trivia_text = trivia_agent.get_trivia(song_name)
            lyrics_text = lyrics_agent.get_lyrics_analysis(song_name)
            
            # Trigger UI update
            self.root.after(0, lambda: self.recognition_success(song_name, best_score, recs, trivia_text, lyrics_text))
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.root.after(0, lambda: self.recognition_failed(f"Internal error: {str(e)}", source_name, quality.get('snr', 0.0) if 'quality' in locals() else 0.0, 0))

    def recognition_success(self, song_name, score, recs, trivia_text, lyrics_text):
        self.is_processing = False
        self.btn_identify.configure(state=tk.NORMAL, bg=COLOR_ACCENT, text="🔍 IDENTIFY NOW")
        self.progress_bar.pack_forget()
        
        self.lbl_song_result.configure(text=f"🎵 RECOGNIZED SONG:\n{song_name}", fg=COLOR_TEAL)
        self.lbl_score_result.configure(text=f"Confidence score: {score} fingerprint matches", fg=COLOR_GREEN)
        
        # Update Recommendations list
        if recs:
            rec_text = ""
            for i, rec in enumerate(recs, 1):
                rec_text += f"{i}. {rec['song_name']} (Distance: {rec['distance']:.3f})\n"
            self.lbl_recs_list.configure(text=rec_text.strip(), fg=FG_MAIN)
        else:
            self.lbl_recs_list.configure(text="No other songs found in the database for recommendations.", fg=FG_MUTED)
            
        # Update LLM Text boxes
        self.update_text_widget(self.txt_trivia, trivia_text)
        self.update_text_widget(self.txt_lyrics, lyrics_text)
        
        self.load_search_history() # Reload history list in Tab 3

    def recognition_failed(self, reason, source_name, snr, score):
        self.is_processing = False
        self.btn_identify.configure(state=tk.NORMAL, bg=COLOR_ACCENT, text="🔍 IDENTIFY NOW")
        self.progress_bar.pack_forget()
        
        self.lbl_song_result.configure(text=reason, fg=COLOR_RED)
        self.lbl_score_result.configure(text="")
        self.lbl_recs_list.configure(text="Identification failed. No recommendations available.", fg=FG_MUTED)
        
        # Clear LLM text boxes
        self.update_text_widget(self.txt_trivia, "Artist biography and trivia will appear here after recognition.")
        self.update_text_widget(self.txt_lyrics, "Song message analysis and lyrics summary will appear here after recognition.")
        
        # Save failed query to history
        self.db.insert_history(source_name, None, snr, score)
        self.load_search_history() # Reload history list in Tab 3

    def save_gemini_api_key(self):
        key_val = self.entry_api_key.get().strip()
        if self.db.set_config_value("gemini_api_key", key_val):
            messagebox.showinfo("Success", "Gemini API key saved successfully!")
        else:
            messagebox.showerror("Error", "Failed to save the key to the database.")

    def update_text_widget(self, widget, text):
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)
        widget.configure(state=tk.DISABLED)

    # ==========================================
    # APP EXECUTION
    # ==========================================
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    db = DatabaseManager('echoprint.db')
    app = EchoPrintGUI(db)
    app.run()
