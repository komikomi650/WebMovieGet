import os
import sys

# Windows環境での絵文字・特殊文字タイトルによる文字コードエラー（UnicodeEncodeError）を予防
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import threading
import queue
import winreg
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# yt_dlpの自動インストール処理（別のPCでインストールされていない場合用）
try:
    import yt_dlp
except ImportError:
    import subprocess
    # Tkinterメッセージボックスでユーザーに通知
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("初期設定", "初回起動の準備を行います。\n動画保存に必要な部品（yt-dlp）を自動でインストールします。\nこの処理は初回のみです。数秒ほどお待ちください。")
        root.destroy()
    except Exception:
        pass
    
    try:
        # pipを使ってインストール
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"])
        import yt_dlp
    except Exception as e:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("エラー", f"自動インストールに失敗しました。\nインターネット接続を確認の上、再度お試しいただくか、\n「簡単初期設定.bat」を先に実行してください。\n\n詳細: {e}")
            root.destroy()
        except Exception:
            pass
        sys.exit(1)

class YoutubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("かんたん 動画保存")
        self.root.geometry("1020x760")
        self.root.configure(bg="#F1F5F9")  # Soft gray-blue background
        
        # Config file path
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.config_file = os.path.join(base_dir, "config.json")
        
        # Determine save directory (load from config if saved, else Downloads folder)
        self.save_dir = self.load_saved_directory()
        
        # Thread communication queue
        self.queue = queue.Queue()
        
        # App state
        self.is_downloading = False
        self.download_thread = None
        self.urls_to_download = []
        self.current_download_idx = 0
        
        # Load download history
        self.history_data = self.load_history()
        
        # Set up GUI components
        self.create_widgets()
        
        # Draw history items in UI
        self.update_history_ui()
        
        # Start queue polling
        self.poll_queue()

    def load_saved_directory(self):
        """Load saved directory from config.json, fallback to Downloads folder."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved_path = data.get("save_dir", "")
                    if saved_path and os.path.exists(saved_path):
                        return saved_path
            except Exception:
                pass
        return self.get_downloads_folder()

    def save_directory_setting(self, path):
        """Save directory choice to config.json for persistence."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump({"save_dir": path}, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def get_downloads_folder(self):
        """Get the user's Downloads folder path on Windows, with fallbacks."""
        try:
            sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                downloads_dir, _ = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")
                if os.path.exists(downloads_dir):
                    return downloads_dir
        except Exception:
            pass
        
        # Fallback 1: UserProfile/Downloads
        fallback = os.path.join(os.path.expanduser("~"), "Downloads")
        if os.path.exists(fallback):
            return fallback
        
        # Fallback 2: UserProfile/Desktop
        fallback_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(fallback_desktop):
            return fallback_desktop
        
        return os.path.expanduser("~")

    def create_widgets(self):
        # Configure overall styles
        style = ttk.Style()
        style.theme_use("clam")
        
        # Progressbar style
        style.configure("TProgressbar", thickness=25, troughcolor="#E2E8F0", background="#22C55E")
        
        # 1. Header Frame
        header_frame = tk.Frame(self.root, bg="#FFFFFF", bd=0, highlightthickness=0)
        header_frame.pack(fill="x", padx=0, pady=0)
        
        header_label = tk.Label(
            header_frame, 
            text="📥 かんたん 動画保存", 
            font=("MS Gothic", 20, "bold"), 
            bg="#FFFFFF", 
            fg="#1E3A8A",  # Dark Blue
            anchor="w"
        )
        header_label.pack(fill="x", padx=25, pady=(20, 5))
        
        desc_label = tk.Label(
            header_frame, 
            text="WEB動画のURL（アドレス）を貼り付けて「動画の保存を開始する」を押すだけで保存できます。", 
            font=("Yu Gothic", 11), 
            bg="#FFFFFF", 
            fg="#475569",  # Slate gray
            anchor="w"
        )
        desc_label.pack(fill="x", padx=25, pady=(0, 20))
        
        # Separator line
        sep = tk.Frame(self.root, height=1, bg="#E2E8F0")
        sep.pack(fill="x", padx=0, pady=0)
        
        # Main layout frame to split left and right
        main_layout = tk.Frame(self.root, bg="#F1F5F9")
        main_layout.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Left container (for download cards)
        left_container = tk.Frame(main_layout, bg="#F1F5F9")
        left_container.pack(side="left", fill="both", expand=True)
        
        # Card 1: URL Input
        card_url = tk.Frame(left_container, bg="#FFFFFF", bd=1, relief="solid", highlightthickness=0, highlightbackground="#CBD5E1")
        card_url.configure(bd=0)  # remove solid border to style with Frame
        card_url.pack(fill="x", pady=(0, 15))
        
        card_url_inner = tk.Frame(card_url, bg="#FFFFFF", padx=15, pady=15)
        card_url_inner.pack(fill="both", expand=True)
        
        step1_title = tk.Label(
            card_url_inner, 
            text="手順 1： 保存したい動画のアドレス（URL）を貼り付ける", 
            font=("Yu Gothic", 13, "bold"), 
            bg="#FFFFFF", 
            fg="#0F172A",
            anchor="w"
        )
        step1_title.pack(fill="x", pady=(0, 5))
        
        step1_sub = tk.Label(
            card_url_inner, 
            text="※ 複数の動画を一度に保存したい場合は、1行に1つずつ貼り付けてください。", 
            font=("Yu Gothic", 10), 
            bg="#FFFFFF", 
            fg="#64748B",
            anchor="w"
        )
        step1_sub.pack(fill="x", pady=(0, 10))
        
        # URL Text box
        self.url_text = tk.Text(
            card_url_inner, 
            height=6, 
            font=("Consolas", 12), 
            bg="#F8FAFC", 
            fg="#0F172A", 
            insertbackground="#0F172A",
            bd=1, 
            relief="solid",
            highlightthickness=0
        )
        self.url_text.pack(fill="x", pady=(0, 5))
        
        # Context menu (Right-click menu) for URL input
        self.url_context_menu = tk.Menu(self.url_text, tearoff=0, font=("Yu Gothic", 10))
        self.url_context_menu.add_command(label="📋 貼り付け", command=self.paste_from_clipboard)
        self.url_context_menu.add_command(label="✂️ 切り取り", command=lambda: self.url_text.event_generate("<<Cut>>"))
        self.url_context_menu.add_command(label="📄 コピー", command=lambda: self.url_text.event_generate("<<Copy>>"))
        self.url_context_menu.add_separator()
        self.url_context_menu.add_command(label="☑️ すべて選択", command=self.select_all_url_text)
        self.url_context_menu.add_command(label="🧹 クリア", command=lambda: self.url_text.delete("1.0", "end"))
        
        # Bind right-click event
        self.url_text.bind("<Button-3>", self.show_context_menu)
        
        # Card 2: Save Location
        card_dir = tk.Frame(left_container, bg="#FFFFFF", padx=15, pady=15)
        card_dir.pack(fill="x", pady=(0, 15))
        
        step2_title = tk.Label(
            card_dir, 
            text="手順 2： 動画を保存する場所（フォルダ）を確認する", 
            font=("Yu Gothic", 13, "bold"), 
            bg="#FFFFFF", 
            fg="#0F172A",
            anchor="w"
        )
        step2_title.pack(fill="x", pady=(0, 10))
        
        dir_selector_frame = tk.Frame(card_dir, bg="#FFFFFF")
        dir_selector_frame.pack(fill="x")
        
        self.dir_entry_val = tk.StringVar(value=self.save_dir)
        self.dir_entry = tk.Entry(
            dir_selector_frame, 
            textvariable=self.dir_entry_val, 
            font=("Yu Gothic", 11), 
            state="readonly", 
            bg="#F8FAFC",
            readonlybackground="#F8FAFC",
            relief="solid", 
            bd=1
        )
        self.dir_entry.pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 10))
        
        # Change Folder Button
        self.change_dir_btn = tk.Button(
            dir_selector_frame, 
            text="📂 場所を変える", 
            font=("Yu Gothic", 11, "bold"), 
            bg="#E2E8F0", 
            fg="#1E293B", 
            activebackground="#CBD5E1", 
            activeforeground="#1E293B",
            relief="flat", 
            bd=0, 
            command=self.change_save_directory,
            cursor="hand2"
        )
        self.change_dir_btn.pack(side="right", ipady=2, ipadx=10)
        self.make_button_hoverable(self.change_dir_btn, "#CBD5E1", "#E2E8F0")
        
        # Card 3: Download Button
        self.download_btn = tk.Button(
            left_container, 
            text="🚀 動画の保存を開始する（ダウンロード）", 
            font=("Yu Gothic", 16, "bold"), 
            bg="#22C55E", 
            fg="#FFFFFF", 
            activebackground="#16A34A", 
            activeforeground="#FFFFFF",
            relief="flat", 
            bd=0, 
            command=self.start_download_process,
            cursor="hand2"
        )
        self.download_btn.pack(fill="x", ipady=12, pady=(0, 15))
        self.make_button_hoverable(self.download_btn, "#16A34A", "#22C55E")
        
        # Card 4: Progress and Log Card
        self.card_progress = tk.Frame(left_container, bg="#FFFFFF", padx=15, pady=15)
        self.card_progress.pack(fill="both", expand=True)
        
        self.progress_title = tk.Label(
            self.card_progress, 
            text="保存の状況", 
            font=("Yu Gothic", 13, "bold"), 
            bg="#FFFFFF", 
            fg="#0F172A",
            anchor="w"
        )
        self.progress_title.pack(fill="x", pady=(0, 5))
        
        self.status_label = tk.Label(
            self.card_progress, 
            text="待機中：上の入力欄にURLを入れてボタンを押してください。", 
            font=("Yu Gothic", 11), 
            bg="#FFFFFF", 
            fg="#475569", 
            anchor="w"
        )
        self.status_label.pack(fill="x", pady=(0, 8))
        
        # Progress Bar
        self.progress_bar = ttk.Progressbar(
            self.card_progress, 
            orient="horizontal", 
            mode="determinate",
            style="TProgressbar"
        )
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        # Detailed Log text
        log_frame = tk.Frame(self.card_progress, bg="#FFFFFF")
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = tk.Text(
            log_frame, 
            height=8, 
            font=("Yu Gothic", 11), 
            bg="#F8FAFC", 
            fg="#334155", 
            bd=1, 
            relief="solid",
            state="disabled",
            wrap="word"
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        
        # Log scrollbar
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Set up color tags for logs
        self.log_text.tag_configure("info", foreground="#1E3A8A")       # Blue
        self.log_text.tag_configure("success", foreground="#16A34A")    # Green
        self.log_text.tag_configure("error", foreground="#DC2626")      # Red
        self.log_text.tag_configure("warning", font=("Yu Gothic", 11, "bold"))
        
        # 4.5 Right Column for History (added to main_layout)
        vertical_sep = tk.Frame(main_layout, width=1, bg="#CBD5E1")
        vertical_sep.pack(side="left", fill="y", padx=(15, 15))
        
        right_container = tk.Frame(main_layout, bg="#F1F5F9", width=330)
        right_container.pack(side="left", fill="both", expand=False)
        right_container.pack_propagate(False)
        
        history_title = tk.Label(
            right_container, 
            text="📋 保存した履歴 (過去20件)", 
            font=("Yu Gothic", 13, "bold"), 
            bg="#F1F5F9", 
            fg="#0F172A",
            anchor="w"
        )
        history_title.pack(fill="x", pady=(0, 10))
        
        # Scrollable area container
        canvas_border = tk.Frame(right_container, bg="#E2E8F0", padx=1, pady=1)
        canvas_border.pack(fill="both", expand=True)
        
        self.history_canvas = tk.Canvas(canvas_border, bg="#FFFFFF", highlightthickness=0, width=310)
        self.history_canvas.pack(side="left", fill="both", expand=True)
        
        history_scrollbar = ttk.Scrollbar(canvas_border, orient="vertical", command=self.history_canvas.yview)
        history_scrollbar.pack(side="right", fill="y")
        
        self.history_canvas.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_inner_frame = tk.Frame(self.history_canvas, bg="#FFFFFF")
        self.history_canvas_window = self.history_canvas.create_window((0, 0), window=self.history_inner_frame, anchor="nw")
        
        # Bind events for scrolling configuration
        self.history_inner_frame.bind("<Configure>", self.on_history_frame_configure)
        self.history_canvas.bind("<Configure>", self.on_history_canvas_configure)
        
        # Clear History Button
        self.clear_history_btn = tk.Button(
            right_container, 
            text="🧹 履歴をすべて消す", 
            font=("Yu Gothic", 11), 
            bg="#F1F5F9", 
            fg="#64748B", 
            activebackground="#E2E8F0", 
            activeforeground="#475569",
            relief="flat", 
            bd=0, 
            command=self.clear_history,
            cursor="hand2"
        )
        self.clear_history_btn.pack(fill="x", pady=(10, 0), ipady=5)
        self.make_button_hoverable(self.clear_history_btn, "#E2E8F0", "#F1F5F9")
        
        # 5. Footer Actions Frame
        footer_frame = tk.Frame(self.root, bg="#F8FAFC", pady=12)
        footer_frame.pack(fill="x", side="bottom")
        
        # Draw a top border line for the footer
        footer_sep = tk.Frame(footer_frame, height=1, bg="#E2E8F0")
        footer_sep.pack(fill="x", side="top", pady=(0, 10))
        
        footer_buttons_container = tk.Frame(footer_frame, bg="#F8FAFC")
        footer_buttons_container.pack(padx=20)
        
        self.open_dir_btn = tk.Button(
            footer_buttons_container, 
            text="📂 保存したフォルダを開く", 
            font=("Yu Gothic", 12, "bold"), 
            bg="#3B82F6", 
            fg="#FFFFFF", 
            activebackground="#2563EB", 
            activeforeground="#FFFFFF",
            relief="flat", 
            bd=0, 
            command=self.open_save_directory,
            cursor="hand2"
        )
        self.open_dir_btn.pack(side="left", ipadx=15, ipady=8, padx=(0, 15))
        self.make_button_hoverable(self.open_dir_btn, "#2563EB", "#3B82F6")
        
        self.clear_btn = tk.Button(
            footer_buttons_container, 
            text="🧹 入力を消す", 
            font=("Yu Gothic", 12), 
            bg="#94A3B8", 
            fg="#FFFFFF", 
            activebackground="#64748B", 
            activeforeground="#FFFFFF",
            relief="flat", 
            bd=0, 
            command=self.clear_all,
            cursor="hand2"
        )
        self.clear_btn.pack(side="left", ipadx=15, ipady=8)
        self.make_button_hoverable(self.clear_btn, "#64748B", "#94A3B8")

    def make_button_hoverable(self, btn, hover_bg, normal_bg):
        """Bind mouse hover events to change button background colors."""
        btn.bind("<Enter>", lambda e: btn.config(bg=hover_bg) if btn['state'] != "disabled" else None)
        btn.bind("<Leave>", lambda e: btn.config(bg=normal_bg) if btn['state'] != "disabled" else None)

    # 履歴画面イベントハンドラーと管理ロジック
    def on_history_frame_configure(self, event):
        self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))

    def on_history_canvas_configure(self, event):
        self.history_canvas.itemconfig(self.history_canvas_window, width=event.width)

    def load_history(self):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        self.history_file = os.path.join(base_dir, "history.json")
        
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_history(self, title, url, status, filepath=""):
        timestamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
        new_item = {
            "title": title,
            "url": url,
            "status": status,
            "filepath": filepath,
            "timestamp": timestamp
        }
        
        history = self.load_history()
        history = [new_item] + history
        history = history[:20]  # 最大20件
        
        self.history_data = history
        
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
            
        self.root.after(0, self.update_history_ui)

    def clear_history(self):
        if not self.history_data:
            return
        if not messagebox.askyesno("履歴のクリア", "ダウンロード履歴をすべて消去しますか？\n（動画ファイル自体は削除されません）"):
            return
            
        self.history_data = []
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
        except Exception:
            pass
            
        self.update_history_ui()

    def update_history_ui(self):
        # 既存の履歴カードをクリア
        for widget in self.history_inner_frame.winfo_children():
            widget.destroy()
            
        if not self.history_data:
            placeholder = tk.Label(
                self.history_inner_frame, 
                text="保存した履歴はありません。", 
                font=("Yu Gothic", 11), 
                bg="#FFFFFF", 
                fg="#64748B",
                pady=40
            )
            placeholder.pack(fill="x")
            return
            
        for item in self.history_data:
            card = tk.Frame(
                self.history_inner_frame, 
                bg="#F8FAFC", 
                bd=1, 
                relief="solid", 
                highlightthickness=0
            )
            card.pack(fill="x", padx=10, pady=(10, 0))
            
            # 内側に余白を設定
            card_inner = tk.Frame(card, bg="#F8FAFC", padx=10, pady=10)
            card_inner.pack(fill="both", expand=True)
            
            title = item.get("title", "")
            if not title:
                title = item.get("url", "")
                
            title_lbl = tk.Label(
                card_inner, 
                text=title, 
                font=("Yu Gothic", 11, "bold"), 
                bg="#F8FAFC", 
                fg="#0F172A",
                anchor="w", 
                justify="left", 
                wraplength=260
            )
            title_lbl.pack(fill="x", anchor="w", pady=(0, 5))
            
            info_frame = tk.Frame(card_inner, bg="#F8FAFC")
            info_frame.pack(fill="x")
            
            status = item.get("status", "正常")
            if status == "正常":
                status_text = "🟢 正常"
                status_color = "#16A34A"
            else:
                status_text = "🔴 失敗"
                status_color = "#DC2626"
                
            status_lbl = tk.Label(
                info_frame, 
                text=status_text, 
                font=("Yu Gothic", 9, "bold"), 
                bg="#F8FAFC", 
                fg=status_color, 
                anchor="w"
            )
            status_lbl.pack(side="left")
            
            time_lbl = tk.Label(
                info_frame, 
                text=f" ({item.get('timestamp', '')})", 
                font=("Yu Gothic", 9), 
                bg="#F8FAFC", 
                fg="#64748B", 
                anchor="w"
            )
            time_lbl.pack(side="left")
            
            if status == "正常":
                filepath = item.get("filepath", "")
                play_btn = tk.Button(
                    card_inner, 
                    text="▶ 再生する", 
                    font=("Yu Gothic", 10, "bold"), 
                    bg="#E2E8F0", 
                    fg="#1E293B", 
                    activebackground="#CBD5E1", 
                    activeforeground="#1E293B",
                    relief="flat", 
                    bd=0, 
                    command=lambda path=filepath: self.play_video(path),
                    cursor="hand2"
                )
                play_btn.pack(anchor="e", pady=(5, 0), ipadx=8, ipady=2)
                self.make_button_hoverable(play_btn, "#CBD5E1", "#E2E8F0")

    def play_video(self, filepath):
        if not filepath:
            messagebox.showerror("エラー", "保存先のファイルパスが記録されていません。")
            return
            
        if os.path.exists(filepath):
            try:
                os.startfile(filepath)
            except Exception as e:
                messagebox.showerror("エラー", f"動画の再生に失敗しました。\n詳細: {e}")
        else:
            messagebox.showwarning(
                "ファイルが見つかりません", 
                "動画ファイルが見つかりません。\nファイルが移動されたか、削除された可能性があります。\n保存先フォルダをご確認ください。"
            )

    def append_log(self, text, tag=None):
        """Append a colored line to the scrolling log widget."""
        self.log_text.config(state="normal")
        if tag:
            self.log_text.insert("end", text + "\n", tag)
        else:
            self.log_text.insert("end", text + "\n")
        self.log_text.config(state="disabled")
        self.log_text.see("end")

    def show_context_menu(self, event):
        """Show context menu on right click in URL text box."""
        self.url_context_menu.tk_popup(event.x_root, event.y_root)

    def paste_from_clipboard(self):
        """Paste clipboard content into URL text box."""
        try:
            clipboard_text = self.root.clipboard_get()
            self.url_text.insert("insert", clipboard_text)
        except tk.TclError:
            pass

    def select_all_url_text(self):
        """Select all text in URL text box."""
        self.url_text.tag_add("sel", "1.0", "end")
        self.url_text.mark_set("insert", "end")
        return "break"

    def change_save_directory(self):
        """Open a directory selection dialog to update save folder."""
        selected_dir = filedialog.askdirectory(initialdir=self.save_dir, title="保存するフォルダを選択してください")
        if selected_dir:
            self.save_dir = os.path.abspath(selected_dir)
            self.dir_entry_val.set(self.save_dir)
            self.save_directory_setting(self.save_dir)
            self.append_log(f"保存先を {self.save_dir} に変更し、固定しました。", "info")

    def open_save_directory(self):
        """Open the current save folder in Windows Explorer."""
        if os.path.exists(self.save_dir):
            os.startfile(self.save_dir)
        else:
            messagebox.showerror("エラー", "保存先フォルダが見つかりません。")

    def clear_all(self):
        """Clear URL list, input box, and logs."""
        if self.is_downloading:
            messagebox.showwarning("警告", "保存処理中は入力をクリアできません。")
            return
        self.url_text.delete("1.0", "end")
        self.status_label.config(text="待機中：上の入力欄にURLを入れてボタンを押してください。", fg="#475569")
        self.progress_bar['value'] = 0
        
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")
        self.append_log("[準備完了] 保存を開始できます", "success")

    def start_download_process(self):
        """Read URLs and kick off the download thread."""
        if self.is_downloading:
            return
        
        # Extract URLs from Text Box
        raw_text = self.url_text.get("1.0", "end-1c")
        urls = [u.strip() for u in raw_text.split("\n") if u.strip()]
        
        if not urls:
            messagebox.showwarning("入力エラー", "動画のURLが入力されていません。\n手順1の枠内にURLを貼り付けてください。")
            return
        
        self.urls_to_download = urls
        self.current_download_idx = 0
        self.is_downloading = True
        
        # Disable buttons during execution
        self.download_btn.config(state="disabled", bg="#94A3B8", text="保存を実行しています...")
        self.change_dir_btn.config(state="disabled")
        self.clear_btn.config(state="disabled")
        
        # Reset progress bar
        self.progress_bar['value'] = 0
        
        # Start background worker thread
        self.download_thread = threading.Thread(target=self.download_worker, daemon=True)
        self.download_thread.start()

    def download_worker(self):
        """Background thread executing the sequential downloads."""
        total_urls = len(self.urls_to_download)
        success_count = 0
        
        self.queue.put(("LOG", "=== 保存処理を開始します ===", "info"))
        
        for idx, url in enumerate(self.urls_to_download):
            self.queue.put(("START_ITEM", idx, url))
            
            try:
                # 1. Fetch metadata (Title)
                self.queue.put(("LOG", f"[{idx+1}/{total_urls}] 動画の情報を取得しています...", "info"))
                
                # YouTubeのBot認証（Sign in to confirm you're not a bot）対策
                # ブラウザのCookieファイルロックを回避するため、スマホ公式アプリ通信に偽装
                extractor_setting = {
                    'youtube': {
                        'player_client': ['ios', 'android', 'mweb']
                    }
                }

                # Fetching title quickly
                ydl_opts_meta = {
                    'extract_flat': True,
                    'skip_download': True,
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': extractor_setting,
                }
                title = "不明なタイトル"
                with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        title = info.get('title', '動画タイトルを取得できませんでした')
                    except Exception as e:
                        # Continue even if metadata retrieval fails
                        pass
                
                self.queue.put(("TITLE", idx, title))
                self.queue.put(("LOG", f"タイトル: {title}", "info"))
                
                # Progress hook wrapper
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                        downloaded = d.get('downloaded_bytes', 0)
                        speed = d.get('_speed_str', '---')
                        eta = d.get('_eta_str', '---')
                        
                        percent = 0.0
                        if total > 0:
                            percent = (downloaded / total) * 100
                        else:
                            # Parse percent from string fallback
                            pct_str = d.get('_percent_str', '0%').replace('%', '').strip()
                            try:
                                percent = float(pct_str)
                            except ValueError:
                                percent = 0.0
                        
                        self.queue.put(("PROGRESS", idx, percent, speed, eta))
                    elif d['status'] == 'finished':
                        self.queue.put(("MERGING", idx))
                
                # 2. Start download
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': os.path.join(self.save_dir, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_hook],
                    'noplaylist': True,
                    'quiet': True,
                    'no_warnings': True,
                    'extractor_args': extractor_setting,
                }
                
                filepath = ""
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info_real = ydl.extract_info(url, download=False)
                        filepath = ydl.prepare_filename(info_real)
                    except Exception:
                        filepath = os.path.join(self.save_dir, f"{title}.mp4")
                    
                    ydl.download([url])
                
                success_count += 1
                self.queue.put(("SUCCESS_ITEM", idx, title, url, filepath))
                
            except Exception as e:
                # Clean up error messages for user presentation
                err_msg = str(e)
                if "Sign in to confirm you’re not a bot" in err_msg:
                    friendly_err = "YouTubeによるロボット確認（認証制限）が発生しました。"
                elif "Unable to download webpage" in err_msg:
                    friendly_err = "インターネットに接続されていないか、アドレスが間違っています。"
                elif "Incomplete data received" in err_msg:
                    friendly_err = "通信が切断されました。もう一度お試しください。"
                else:
                    # Simplify technical traceback
                    friendly_err = err_msg.split('\n')[0]
                
                self.queue.put(("ERROR_ITEM", idx, friendly_err, url, title))
            
            # Brief delay between videos to be polite and avoid blocking
            threading.Event().wait(1.0)
            
        self.queue.put(("FINISHED_ALL", success_count, total_urls))

    def poll_queue(self):
        """Periodically check the communication queue in the main thread (every 100ms)."""
        while True:
            try:
                msg = self.queue.get_nowait()
            except queue.Empty:
                break
            
            msg_type = msg[0]
            
            if msg_type == "LOG":
                _, text, tag = msg
                self.append_log(text, tag)
                
            elif msg_type == "START_ITEM":
                _, idx, url = msg
                self.current_download_idx = idx
                total = len(self.urls_to_download)
                self.status_label.config(
                    text=f"[{idx+1}/{total}] 動画を保存中... (アドレス: {url[:45]}...)", 
                    fg="#1E3A8A"
                )
                self.append_log(f"\n--- {idx+1}本目の保存処理を開始 ---", "info")
                
            elif msg_type == "TITLE":
                _, idx, title = msg
                self.status_label.config(
                    text=f"[{idx+1}/{len(self.urls_to_download)}] 保存中: {title}", 
                    fg="#1E3A8A"
                )
                
            elif msg_type == "PROGRESS":
                _, idx, percent, speed, eta = msg
                self.progress_bar['value'] = percent
                total = len(self.urls_to_download)
                self.status_label.config(
                    text=f"[{idx+1}/{total}] 保存中: {percent:.1f}% (速度: {speed} | 残り時間: {eta})",
                    fg="#1E293B"
                )
                
            elif msg_type == "MERGING":
                _, idx = msg
                self.progress_bar['value'] = 100
                total = len(self.urls_to_download)
                self.status_label.config(
                    text=f"[{idx+1}/{total}] 画質と音声を綺麗に結合しています... しばらくお待ちください", 
                    fg="#C2410C"
                )
                self.append_log("動画と音声を綺麗に結合しています...", "info")
                
            elif msg_type == "SUCCESS_ITEM":
                _, idx, title, url, filepath = msg
                self.append_log(f"【保存完了】「{title}」を保存しました！", "success")
                self.save_history(title, url, "正常", filepath)
                
            elif msg_type == "ERROR_ITEM":
                _, idx, err, url, title = msg
                self.append_log(f"【保存失敗】エラー内容: {err}", "error")
                self.save_history(title, url, "失敗", "")
                
            elif msg_type == "FINISHED_ALL":
                _, success, total = msg
                self.is_downloading = False
                self.progress_bar['value'] = 100
                
                # Re-enable controls
                self.download_btn.config(state="normal", bg="#22C55E", text="🚀 動画の保存を開始する（ダウンロード）")
                self.change_dir_btn.config(state="normal")
                self.clear_btn.config(state="normal")
                
                # Final Status display
                result_text = f"処理終了： {total}件中 {success}件の保存に成功しました！"
                self.status_label.config(text=result_text, fg="#16A34A" if success == total else "#DC2626")
                self.append_log(f"\n======================================", "info")
                self.append_log(result_text, "success" if success == total else "warning")
                
                if success > 0:
                    self.append_log("下の「保存したフォルダを開く」ボタンを押すと動画を確認できます。", "success")
                    messagebox.showinfo("完了", f"動画の保存が完了しました！\n（成功 {success}件 / 全体 {total}件）")
                else:
                    messagebox.showerror("失敗", "動画の保存に失敗しました。詳細ログを確認してください。")
            
            self.queue.task_done()
            
        # Schedule the next check in 100 milliseconds
        self.root.after(100, self.poll_queue)

if __name__ == "__main__":
    # Windows High DPI support (makes fonts crisp on high-res displays)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            import ctypes
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    root = tk.Tk()
    app = YoutubeDownloaderApp(root)
    # Set default log message
    app.append_log("[準備完了] 保存を開始できます", "success")
    root.mainloop()
