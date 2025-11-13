# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: main.py
# Bytecode version: 3.10.0rc2 (3439)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

import customtkinter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
import os
import json
import threading
import time
import subprocess
import uuid
import hashlib
import datetime
import base64
from tkinter import messagebox, filedialog
import tkinter as tk
from tkinter import ttk, scrolledtext
import requests
try:
    import pysrt
except Exception:
    pass
if os.name == 'nt':
    try:
        os.environ['PYDUB_HIDE_CONSOLE'] = '1'
    except Exception:
        pass
import sys
import re
import shutil

# --- Regex & constants ---
_SENT_END = re.compile(r'[\.!\?…。！？]+')
_NEWLINE = '\n'

def smart_split_by_chars(text: str, max_chars: int = 1000, soft_margin: int = 200) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    chunks, i, n = [], 0, len(text)
    while i < n:
        target = min(i + max_chars, n)
        if n - i <= max_chars + soft_margin:
            chunk = text[i:].strip()
            if chunk: chunks.append(chunk)
            break
        window_end = min(i + max_chars + soft_margin, n)
        window_txt = text[i:window_end]
        cut_pos = None
        for m in _SENT_END.finditer(window_txt):
            pos = i + m.end()
            if pos >= target - soft_margin:
                cut_pos = pos
        if cut_pos is None:
            last_nl = window_txt.rfind(_NEWLINE)
            if last_nl != -1 and (i + last_nl) >= (target - soft_margin):
                cut_pos = i + last_nl + 1
        if cut_pos is None or cut_pos <= i:
            cut_pos = target
        chunk = text[i:cut_pos].strip()
        if chunk: chunks.append(chunk)
        i = cut_pos
    if len(chunks) >= 2 and len(chunks[-1]) < max(100, max_chars // 5):
        chunks[-2] = (chunks[-2] + "\n" + chunks[-1]).strip()
        chunks.pop()
    return chunks

def get_app_root_dir():
    """Lấy thư mục gốc của ứng dụng (hoạt động cho cả .py và .exe)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

import base64, os

def download_blob_to_path(driver, blob_url: str, dest_path: str, ensure_dir=True, timeout_ms=120000):
    """
    Tải nội dung từ blob:... (cùng origin trang hiện tại) rồi lưu ra dest_path.
    Trả về (ok: bool, msg: str).
    """
    try:
        if ensure_dir:
            os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)

        # Dùng async_script để không bị giới hạn thời gian ngắn
        result = driver.execute_async_script("""
            const url = arguments[0];
            const cb  = arguments[arguments.length - 1];

            (async () => {
                try {
                    // fetch blob:... (phải cùng origin với trang)
                    const res = await fetch(url);
                    if (!res.ok) throw new Error('HTTP ' + res.status);
                    
                    // Đọc stream thành Uint8Array hợp nhất
                    const reader = res.body.getReader();
                    const chunks = [];
                    let total = 0;
                    while (true) {
                        const {done, value} = await reader.read();
                        if (done) break;
                        chunks.push(value);
                        total += value.length;
                    }
                    const merged = new Uint8Array(total);
                    let offset = 0;
                    for (const c of chunks) { merged.set(c, offset); offset += c.length; }

                    // Chuyển Uint8Array -> base64 theo CHUNK để tránh vượt giới hạn JSON
                    function toBase64(u8) {
                        const chunkSize = 0x8000; // ~32KB
                        let binary = '';
                        for (let i = 0; i < u8.length; i += chunkSize) {
                            const sub = u8.subarray(i, i + chunkSize);
                            binary += String.fromCharCode.apply(null, sub);
                        }
                        return btoa(binary);
                    }

                    const b64 = toBase64(merged);
                    const OUT_CHUNK = 5_000_000; // 5MB base64/đoạn
                    const parts = [];
                    for (let i = 0; i < b64.length; i += OUT_CHUNK) {
                        parts.push(b64.slice(i, i + OUT_CHUNK));
                    }
                    cb({ ok: true, chunks: parts, size: merged.length });
                } catch (e) {
                    cb({ ok: false, error: String(e) });
                }
            })();
        """, blob_url)

        if not result or not result.get("ok"):
            return (False, f"JS error: {result.get('error') if result else 'unknown'}")

        with open(dest_path, "wb") as f:
            for part in result["chunks"]:
                f.write(base64.b64decode(part))
        return (True, f"Saved {result.get('size', 0)} bytes → {dest_path}")
    except Exception as e:
        return (False, f"Python error: {e}")

def debug_print(message):
    """In debug message cho cả .py và .exe mode"""
    try:
        print(message)
    except UnicodeEncodeError:
        pass
    try:
        with open('debug.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()}: {message}\n')
    except:
        pass
    try:
        if hasattr(App, '_instance') and App._instance is not None:
            App._instance._log_from_thread(str(message))
    except:
        pass

def safe_traceback():
    """Chỉ in traceback khi KHÔNG chạy trong exe mode"""
    if not IS_EXE_MODE:
        import traceback
        traceback.print_exc()

def get_gemini_language_list():
    return [
        "Vietnamese", "English", "Arabic", "Cantonese", "Chinese (Mandarin)",
        "Dutch", "French", "German", "Indonesian", "Italian", "Japanese",
        "Korean", "Portuguese", "Russian", "Spanish", "Turkish", "Ukrainian",
        "Thai", "Polish", "Romanian", "Greek", "Czech", "Finnish", "Hindi",
        "Bulgarian", "Danish", "Hebrew", "Malay", "Persian", "Slovak",
        "Swedish", "Croatian", "Filipino", "Hungarian", "Norwegian",
        "Slovenian", "Catalan", "Nynorsk", "Tamil", "Afrikaans"
    ]

def get_resource_path(relative_path):
    """
    Lấy đường dẫn tài nguyên chính xác, hoạt động cho cả chế độ .py và .exe.
    PHIÊN BẢN ĐÃ SỬA LỖI
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)
PROFILES_JSON_PATH = 'profiles.json'
PROFILES_DIR = 'profiles'
SCRIPT_PATH = get_resource_path('script.js')
MAX_PROFILES = 5
OPERA_PATH_FILE = 'brave_config.json'

class SecurityManagerStub:
    """Lớp giả lập SecurityManager để loại bỏ logic License/Activation/Quota"""

    def get_appdata_path(self):
        """Lấy đường dẫn AppData\\Roaming an toàn cho cache"""
        try:
            appdata = os.getenv('APPDATA')
            if appdata:
                appdata_dir = os.path.join(appdata, 'MinimaxTool')
                os.makedirs(appdata_dir, exist_ok=True)
                return appdata_dir
        except Exception:
            pass
        return os.path.abspath('.')

    def get_machine_id(self):
        """Hàm giả lập lấy mã máy - chỉ để tránh lỗi"""
        return 'free_mnmv_10'

    def verify_license(self):
        """Giả lập: Luôn trả về True (luôn xác thực thành công)"""
        return True

    def check_license_security(self):
        """Giả lập: Luôn trả về True và hợp lệ"""
        return {'valid': True, 'expired': False, 'need_key': False, 'days_left': 9999, 'message': 'Miễn phí'}

class App(customtkinter.CTk):
    def __init__(self, security_manager):
        try:
            debug_print('[DEBUG] Khởi tạo App...')
            super().__init__()
            try:
                App._instance = self
            except Exception:
                pass
            self.sm = security_manager
            self.is_authenticated = False
            self.profiles = {}
            self.running_browsers = {}
            self.profile_widgets = {}
            self.my_machine_id = ''

            # Trạng thái batch
            self._batch_thread = None
            self._batch_stop = threading.Event()
            self.source_status = {}   # {filepath: {"status": "...", "progress": "..."}}
            self._batch_running = False

            # File selectors (MP3 + TEXT)
            self.mp3_path = ""
            self.text_path = ""
            self.language = "Vietnamese"  # mặc định

            # Loại bỏ các hằng số liên quan đến License/API
            self.current_quota = -1 # Luôn là không giới hạn
            self.quota_lock = threading.Lock()
            # Loại bỏ License monitor
            debug_print('[DEBUG] Thiết lập giao diện...')
            self.title('Profile Manager & Browser Tool (FREE Edition)') # Đổi tiêu đề
            self.geometry('1200x800')
            self.protocol('WM_DELETE_WINDOW', self.on_closing)
        except Exception as e:
            debug_print(f'[ERROR] Lỗi khởi tạo App: {e}')
            import traceback
            safe_traceback()
            raise
        
        # Thay thế security_frame
        self.security_frame = customtkinter.CTkFrame(self, fg_color='transparent')
        self.security_frame.pack(pady=10, padx=10, fill='x')
        self.auth_status_label = customtkinter.CTkLabel(self.security_frame, text='Trạng thái: Đã kích hoạt (Miễn phí)', text_color='green')
        self.auth_status_label.pack(side='left')
        self.license_created_label = customtkinter.CTkLabel(self.security_frame, text='License: Miễn phí', text_color='gray', font=customtkinter.CTkFont(size=10))
        self.license_created_label.pack(side='left', padx=(10, 0))
        self.trial_status_label = customtkinter.CTkLabel(self.security_frame, text='Quota: Không giới hạn', text_color='blue', font=customtkinter.CTkFont(size=10))
        self.trial_status_label.pack(side='left', padx=(10, 0))

        # Loại bỏ nút Xóa ID Máy
        # self.delete_id_button = customtkinter.CTkButton(button_frame, text='Xóa ID Máy', command=self.prompt_delete_id)
        # self.delete_id_button.pack(side='left', padx=5)

        self.main_content = customtkinter.CTkFrame(self, fg_color='transparent')
        self.main_content.grid_columnconfigure(0, weight=1)
        # Chỉ cho danh sách profile và log giãn theo chiều dọc
        try:
            self.main_content.grid_rowconfigure(0, weight=0)
            self.main_content.grid_rowconfigure(1, weight=0)
            self.main_content.grid_rowconfigure(2, weight=1)
            self.main_content.grid_rowconfigure(3, weight=0)
        except Exception:
            pass
        # Hiển thị phần nội dung chính ngay từ đầu để tránh phụ thuộc authenticate_success
        try:
            self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
        except Exception:
            pass
        
        brave_config_frame = customtkinter.CTkFrame(self.main_content)
        brave_config_frame.grid(row=0, column=0, padx=0, pady=(0, 5), sticky='ew')
        brave_path_label = customtkinter.CTkLabel(brave_config_frame, text='Đường dẫn Brave Browser (bắt buộc):', font=customtkinter.CTkFont(size=12, weight='bold'))
        brave_path_label.pack(side='left', padx=(10, 5), pady=5)
        self.brave_path_entry = customtkinter.CTkEntry(brave_config_frame, placeholder_text='Nhập đường dẫn brave.exe', width=300, height=30)
        self.brave_path_entry.pack(side='left', padx=5, pady=5)
        self.brave_path_entry.bind('<FocusOut>', lambda e: self.save_brave_path())
        self.brave_path_entry.bind('<Return>', lambda e: self.save_brave_path())
        browse_brave_button = customtkinter.CTkButton(brave_config_frame, text='📁 Chọn Brave Browser', command=self.browse_brave_path, width=120, height=30)
        browse_brave_button.pack(side='left', padx=5, pady=5)
        test_brave_button = customtkinter.CTkButton(brave_config_frame, text='🔍 Test', command=self.test_brave_path, width=80, height=30, fg_color='#4CAF50', hover_color='#45a049')
        test_brave_button.pack(side='left', padx=5, pady=5)
        self.load_brave_path()
        try:
            self.bind('<Control-Shift-A>', lambda e: self.open_auto_settings())
        except Exception:
            pass
        
        control_frame = customtkinter.CTkFrame(self.main_content)
        control_frame.grid(row=1, column=0, padx=0, pady=(0, 5), sticky='ew')
        add_profile_button = customtkinter.CTkButton(control_frame, text='➕ Thêm Profile', command=self.add_profile)
        add_profile_button.pack(side='left', padx=5, pady=5)
        auto_btn = customtkinter.CTkButton(control_frame, text='⚙️ Thiết lập AUTO', command=self.open_auto_settings, fg_color='#2E7D32', hover_color='#1B5E20')
        auto_btn.pack(side='left', padx=5, pady=5)
        delete_profile_button = customtkinter.CTkButton(control_frame, text='🗑️ Xóa Profile', command=self.delete_profile, fg_color='#D32F2F', hover_color='#B71C1C')
        delete_profile_button.pack(side='left', padx=5, pady=5)
        start_button = customtkinter.CTkButton(control_frame, text='▶️ Khởi động Profile đã chọn', command=self.start_selected_profiles)
        start_button.pack(side='left', padx=5, pady=5)
        # stop_all_button = customtkinter.CTkButton(control_frame, text='⏹️ Dừng tất cả', command=self.stop_all_browsers, fg_color='#D32F2F', hover_color='#B71C1C')
        # stop_all_button.pack(side='left', padx=5, pady=5)
        # Loại bỏ nút Reset Vi Phạm (vì đã bỏ cơ chế vi phạm)
        # reset_violations_button = customtkinter.CTkButton(control_frame, text='🔓 Reset Vi Phạm', command=self.reset_violations, fg_color='#FF9800', hover_color='#F57C00')
        # reset_violations_button.pack(side='left', padx=5, pady=5)
        
        audio_sync_button = customtkinter.CTkButton(control_frame, text='🎵 SRT (Audio-SRT Sync)', command=self.open_audio_srt_sync, fg_color='#673AB7', hover_color='#5E35B1')
        audio_sync_button.pack(side='left', padx=10, pady=5)
        
        # === SPLIT PANE (2 CỘT) ===
        # Row 2 trước đây có scrollable_frame + log_frame, giờ thay bằng 2 cột
        split_pane = customtkinter.CTkFrame(self.main_content, fg_color="transparent")
        split_pane.grid(row=2, column=0, padx=0, pady=5, sticky="nsew")

        # 2 cột: trái (profiles + files), phải (log)
        split_pane.grid_columnconfigure(0, weight=1, minsize=250)  # Bên trái
        split_pane.grid_columnconfigure(1, weight=4)               # Bên phải
        split_pane.grid_rowconfigure(0, weight=1)

        left_pane  = customtkinter.CTkFrame(split_pane)     # Bên trái
        right_pane = customtkinter.CTkFrame(split_pane)     # Bên phải
        left_pane.grid(row=0, column=0, sticky="nsew", padx=(0,6))
        right_pane.grid(row=0, column=1, sticky="nsew", padx=(6,0))

        # === LEFT PANE: Profiles (trên) + Source files (dưới) ===
        left_pane.grid_rowconfigure(0, weight=0, minsize=220)  # Profiles cao cố định
        left_pane.grid_rowconfigure(1, weight=1)               # Files giãn phần còn lại
        left_pane.grid_columnconfigure(0, weight=1)

        # Danh sách Profile (giữ nguyên, chỉ đổi parent & grid)
        self.scrollable_frame = customtkinter.CTkScrollableFrame(
            left_pane,
            label_text='Danh sách Profile',
            height=150
        )
        self.scrollable_frame.grid(row=0, column=0, padx=0, pady=5, sticky='ew')

        # ===== Danh sách file nguồn (.txt) =====
        source_wrap = customtkinter.CTkFrame(left_pane)
        source_wrap.grid(row=1, column=0, sticky="nsew", padx=0, pady=5)
        source_wrap.grid_rowconfigure(1, weight=1)   # list chiếm
        source_wrap.grid_columnconfigure(0, weight=1)

        # Header: Label + Refresh ở cùng một hàng
        src_header = customtkinter.CTkFrame(source_wrap, fg_color="transparent")
        src_header.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        src_header.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(
            src_header,
            text="Danh sách file source (input) [.txt]",
            font=customtkinter.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        customtkinter.CTkButton(
            src_header,
            text="🔄 Làm mới danh sách",
            command=self.refresh_source_file_list,
            width=140
        ).grid(row=0, column=1, sticky="e", padx=(8, 8))
        self.btn_run_all = customtkinter.CTkButton(
            src_header,
            text="▶️ Chạy tất cả",
            command=self.start_batch_on_sources,
            width=140,
            state="disabled",          # ✅ mặc định tắt ngay khi tạo
        )
        self.btn_run_all.grid(row=0, column=2, sticky="w", padx=(0, 8))

        self.btn_stop_batch = customtkinter.CTkButton(
            src_header,
            text="⏹ Dừng batch",
            command=self.stop_batch,
            width=140,
            fg_color="#D32F2F",
            hover_color="#B71C1C",
            state="disabled",          # ✅ mặc định tắt
        )
        self.btn_stop_batch.grid(row=0, column=3, sticky="w")

        # Khung list + scrollbar
        list_container = customtkinter.CTkFrame(source_wrap, fg_color="transparent")
        list_container.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        list_container.grid_columnconfigure(0, weight=1)
        list_container.grid_rowconfigure(0, weight=1)

        # --- Treeview: KHAI BÁO CỘT MỘT LẦN DUY NHẤT ---
        self.source_tree = ttk.Treeview(
            list_container,
            columns=("name", "status", "progress"),  # <-- đủ 3 cột ngay từ đầu
            show="headings",
            selectmode="extended",
            height=12
        )
        self.source_tree.grid(row=0, column=0, sticky="nsew")

        # Headings
        self.source_tree.heading("name", text="Tên file")
        self.source_tree.heading("status", text="Trạng thái")
        self.source_tree.heading("progress", text="Tiến độ")

        # Kích thước & căn lề
        self.source_tree.column("name", anchor="w", width=250, stretch=True)
        self.source_tree.column("status", anchor="center", width=120, stretch=False)
        self.source_tree.column("progress", anchor="center", width=100, stretch=False)

        # Scrollbar
        src_scroll = tk.Scrollbar(list_container, orient="vertical", command=self.source_tree.yview)
        src_scroll.grid(row=0, column=1, sticky="ns")
        self.source_tree.configure(yscrollcommand=src_scroll.set)

        # === RIGHT PANE: Log (giữ như cũ, chỉ đổi parent) ===
        right_pane.grid_rowconfigure(1, weight=1)
        right_pane.grid_columnconfigure(0, weight=1)

        log_header = customtkinter.CTkFrame(right_pane, fg_color='transparent')
        log_header.grid(row=0, column=0, sticky='ew', padx=8, pady=(6, 0))
        customtkinter.CTkLabel(log_header, text='Log chạy').pack(side='left')
        customtkinter.CTkButton(
            log_header, text='🧹 Xóa log',
            width=100, fg_color='#D32F2F', hover_color='#B71C1C',
            command=self.clear_log
        ).pack(side='right')

        self.log_text = customtkinter.CTkTextbox(right_pane, height=180, wrap='word')
        self.log_text.grid(row=1, column=0, sticky='nsew', padx=8, pady=(6, 8))
        
        self.main_status_label = customtkinter.CTkLabel(self.main_content, text='Sẵn sàng')
        self.main_status_label.grid(row=3, column=0, padx=0, pady=(5, 0), sticky='w')

        # Loại bỏ Security Notice
        # security_notice = customtkinter.CTkLabel(self.main_content, text='🔒 Hệ thống bảo mật nâng cao: Multi-Layer Protection - Chống F12, DevTools, Console, Copy/Paste, Screenshot - Lần 1: Cảnh báo, Lần 2: Khóa 24h', text_color='#FF9800', font=customtkinter.CTkFont(size=12, weight='bold'))
        # security_notice.grid(row=4, column=0, padx=0, pady=(5, 0), sticky='w')
        
        # Log chạy (đặt dưới danh sách profile)
        debug_print('[DEBUG] Thiết lập timer...')

        self.load_auto_config()

        self.refresh_source_file_list()
        
        style = ttk.Style(self)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        # Chuyển sang logic xác thực đơn giản
        self.authenticate_success() 
        debug_print('[DEBUG] Khởi tạo App hoàn tất!')

    def load_auto_config(self):
        """Đọc auto_config.json và set self.mp3_path, self.text_path từ đó."""
        try:
            cfg = {}
            if os.path.exists('auto_config.json'):
                with open('auto_config.json', 'r', encoding='utf-8') as f:
                    cfg = json.load(f) or {}
            self.auto_config = cfg

            # Lấy folder_path và mp3_path từ file
            folder_path = cfg.get('folder_path', '') or ''
            mp3_path = cfg.get('mp3_path', '') or ''
            language = (cfg.get('language') or '').strip()

            self.mp3_path = mp3_path
            debug_print(f"[AUTO-Config] voice_path mặc định: {self.mp3_path}")

            # set language (nếu chưa có thì để Vietnamese)
            valid_languages = get_gemini_language_list()
            if language in valid_languages:
                self.language = language
            else:
                self.language = "Vietnamese"
            debug_print(f"[AUTO-Config] ngôn ngữ mặc định: {self.language}")

            # Tự động chọn text_path = file .txt đầu tiên trong folder_path (nếu có)
            self.text_path = ""
            if folder_path and os.path.isdir(folder_path):
                try:
                    for name in os.listdir(folder_path):
                        if name.lower().endswith('.txt'):
                            self.text_path = os.path.join(folder_path, name)
                            break
                    if self.text_path:
                        debug_print(f"[AUTO-Config] text_path mặc định: {self.text_path}")
                    else:
                        debug_print("[AUTO-Config] Không tìm thấy file .txt trong folder_path để set text_path.")
                except Exception as e:
                    debug_print(f"[AUTO-Config] Lỗi khi scan folder_path lấy text_path: {e}")
            else:
                if folder_path:
                    debug_print(f"[AUTO-Config] folder_path không tồn tại: {folder_path}")
        except Exception as e:
            debug_print(f"[AUTO-Config] Lỗi load_auto_config: {e}")

    def get_download_dir(self, profile_name=None):
        """Trả về thư mục download cho trình duyệt (ưu tiên cấu hình AUTO)."""
        try:
            cfg = getattr(self, 'auto_config', {}) or {}
            download_path = (cfg.get('download_path') or '').strip()
            if download_path and os.path.isdir(download_path):
                return os.path.abspath(download_path)

            folder_path = (cfg.get('folder_path') or '').strip()
            if folder_path and os.path.isdir(folder_path):
                return os.path.abspath(folder_path)
        except Exception as e:
            debug_print(f"[AUTO] get_download_dir error: {e}")

        # Fallback: thư mục downloads riêng trong profile
        try:
            if profile_name and profile_name in self.profiles:
                base = self.profiles[profile_name]['path']
                dl = os.path.join(base, 'downloads')
                os.makedirs(dl, exist_ok=True)
                return os.path.abspath(dl)
        except Exception:
            pass

        # Fallback cuối
        return os.path.abspath('.')

    def start_license_monitor(self):
        self.main_status_label = customtkinter.CTkLabel(self.main_content, text='Sẵn sàng')
        pass

    def reload_license(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def authenticate_success(self):
        self.is_authenticated = True
        try:
            self.load_profiles()
        except Exception as e:
            debug_print(f"[ERROR] authenticate_success/load_profiles: {e}")

    def _log_from_thread(self, message):
        try:
            if not hasattr(self, 'log_text'):
                return
            def _append():
                try:
                    ts = time.strftime('%H:%M:%S')
                    self.log_text.insert('end', f'[{ts}] {message}\n')
                    self.log_text.see('end')
                except Exception:
                    pass
            self.after(0, _append)
        except Exception:
            pass

    def save_log(self):
        try:
            from tkinter import filedialog
            if not hasattr(self, 'log_text'):
                return
            path = filedialog.asksaveasfilename(title='Lưu log', defaultextension='.txt', filetypes=[('Text files','*.txt'),('All files','*.*')])
            if path:
                data = self.log_text.get('1.0','end')
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(data)
                debug_print(f'Đã lưu log: {path}')
        except Exception as e:
            debug_print(f'Lỗi lưu log: {e}')

    def clear_log(self):
        try:
            if hasattr(self, 'log_text'):
                self.log_text.delete('1.0','end')
        except Exception:
            pass

    def open_auto_settings(self):
        try:
            win = customtkinter.CTkToplevel(self)
            win.title('Cấu hình AUTO')
            win.geometry('620x260')
            win.transient(self)
            win.grab_set()

            frm = customtkinter.CTkFrame(win)
            frm.pack(fill='both', expand=True, padx=12, pady=12)
            frm.grid_columnconfigure(1, weight=1)

            # Load cấu hình hiện tại
            cfg = {}
            try:
                if os.path.exists('auto_config.json'):
                    with open('auto_config.json', 'r', encoding='utf-8') as f:
                        cfg = json.load(f) or {}
            except Exception:
                cfg = {}

            # ========== DÒNG 1: THƯ MỤC NGUỒN ==========
            customtkinter.CTkLabel(frm, text='Thư mục nguồn (text/segment):').grid(
                row=0, column=0, sticky='w', padx=6, pady=8
            )
            var_folder = customtkinter.StringVar(value=cfg.get('folder_path', ''))
            ent_folder = customtkinter.CTkEntry(frm, textvariable=var_folder)
            ent_folder.grid(row=0, column=1, sticky='ew', padx=6, pady=8)

            def browse_folder():
                path = filedialog.askdirectory(title='Chọn thư mục nguồn')
                if path:
                    var_folder.set(path)

            customtkinter.CTkButton(
                frm, text='Chọn...', command=browse_folder, width=90
            ).grid(row=0, column=2, padx=6, pady=8)

            # ========== DÒNG 2: FILE MP3 ==========
            customtkinter.CTkLabel(frm, text='File MP3 nền (tuỳ chọn):').grid(
                row=1, column=0, sticky='w', padx=6, pady=8
            )
            var_mp3 = customtkinter.StringVar(value=cfg.get('mp3_path', ''))
            ent_mp3 = customtkinter.CTkEntry(frm, textvariable=var_mp3)
            ent_mp3.grid(row=1, column=1, sticky='ew', padx=6, pady=8)

            def browse_mp3():
                path = filedialog.askopenfilename(
                    title='Chọn file MP3',
                    filetypes=[('MP3 files', '*.mp3'), ('All files', '*.*')]
                )
                if path:
                    var_mp3.set(path)

            customtkinter.CTkButton(
                frm, text='Chọn...', command=browse_mp3, width=90
            ).grid(row=1, column=2, padx=6, pady=8)

            # ========== DÒNG 3: THƯ MỤC LƯU FILE TẢI VỀ ==========
            customtkinter.CTkLabel(frm, text='Thư mục lưu file (auto download):').grid(
                row=2, column=0, sticky='w', padx=6, pady=8
            )
            var_download = customtkinter.StringVar(value=cfg.get('download_path', ''))
            ent_download = customtkinter.CTkEntry(frm, textvariable=var_download)
            ent_download.grid(row=2, column=1, sticky='ew', padx=6, pady=8)

            def browse_download():
                path = filedialog.askdirectory(title='Chọn thư mục lưu file')
                if path:
                    var_download.set(path)

            customtkinter.CTkButton(
                frm, text='Chọn...', command=browse_download, width=90
            ).grid(row=2, column=2, padx=6, pady=8)

            # ========== DÒNG 4: NGÔN NGỮ GEMINI ==========
            customtkinter.CTkLabel(frm, text='Ngôn ngữ (Gemini language):').grid(
                row=3, column=0, sticky='w', padx=6, pady=8
            )
            languages = get_gemini_language_list()
            current_lang = cfg.get('language', self.language if hasattr(self, 'language') else 'Vietnamese')
            if current_lang not in languages:
                current_lang = "Vietnamese"

            var_lang = customtkinter.StringVar(value=current_lang)
            lang_menu = customtkinter.CTkOptionMenu(
                frm,
                variable=var_lang,
                values=languages,
                width=180
            )
            lang_menu.grid(row=3, column=1, sticky='w', padx=6, pady=8)

            # ========== STATUS ==========
            status = customtkinter.CTkLabel(frm, text='', text_color='green')
            status.grid(row=4, column=0, columnspan=3, sticky='w', padx=6, pady=(4, 0))

            # ========== NÚT LƯU / ĐÓNG ==========
            btns = customtkinter.CTkFrame(frm, fg_color='transparent')
            btns.grid(row=4, column=0, columnspan=3, sticky='e', padx=6, pady=(10, 0))

            def on_save():
                try:
                    folder = var_folder.get().strip()
                    mp3 = var_mp3.get().strip()
                    download_path = var_download.get().strip()
                    lang = var_lang.get().strip()

                    cfg_new = {
                        'folder_path': folder,
                        'mp3_path': mp3,
                        'download_path': download_path,
                        'language': lang
                    }

                    with open('auto_config.json', 'w', encoding='utf-8') as f:
                        json.dump(cfg_new, f, ensure_ascii=False, indent=2)

                    self.auto_config = cfg_new
                    self.mp3_path = mp3
                    self.language = lang

                    # Auto cập nhật text_path (file .txt đầu tiên trong folder)
                    self.text_path = ""
                    if folder and os.path.isdir(folder):
                        try:
                            for name in os.listdir(folder):
                                if name.lower().endswith('.txt'):
                                    self.text_path = os.path.join(folder, name)
                                    break
                        except Exception as ex_scan:
                            debug_print(f"AUTO: Lỗi scan folder_path khi set text_path: {ex_scan}")

                    status.configure(text='Đã lưu cấu hình AUTO.', text_color='green')
                    try:
                        self.main_status_label.configure(
                            text='AUTO: Đã lưu cấu hình',
                            text_color='blue'
                        )
                    except Exception:
                        pass

                    debug_print(
                        f"AUTO: Đã lưu cấu hình. "
                        f"folder_path={folder}, mp3_path={mp3}, download_path={download_path}, text_path={self.text_path}"
                    )
                except Exception as ex:
                    status.configure(text=f'Lỗi lưu cấu hình: {ex}', text_color='red')
                    debug_print(f'AUTO: Lỗi lưu cấu hình: {ex}')

            customtkinter.CTkButton(btns, text='Lưu', command=on_save, width=110).pack(side='right', padx=6)
            customtkinter.CTkButton(
                btns, text='Đóng', command=win.destroy,
                width=110, fg_color='#6C757D', hover_color='#5A6268'
            ).pack(side='right', padx=6)

        except Exception as e:
            debug_print(f'Lỗi mở Cấu hình AUTO: {e}')



    def authenticate_fail(self, message):
        self.is_authenticated = False
        self.auth_status_label.configure(text=f'Trạng thái: {message}', text_color='red')

    def run_online_license_check(self):
        """Đã loại bỏ - Chỉ để trống"""
        self.authenticate_success()

    def show_machine_id_dialog(self, machine_id):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def api_report_usage(self, chars_used):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def prompt_activation(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def prompt_delete_id(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def check_trial_and_license_status(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def check_license_on_startup(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def open_audio_srt_sync(self):
        """Mở cửa sổ chức năng Audio-SRT Sync (Nhạc)."""
        try:
            # Logic Audio-SRT Sync Tool
            # ... (Giữ nguyên logic Audio-SRT Sync Tool vì không liên quan đến License)
            win = customtkinter.CTkToplevel(self)
            win.title('Cấu hình AUTO')
            win.geometry('820x640')
            win.grab_set()
            frame = customtkinter.CTkFrame(win)
            frame.pack(fill='both', expand=True, padx=10, pady=10)
            srt_label = customtkinter.CTkLabel(frame, text='File SRT:')
            srt_label.grid(row=0, column=0, sticky='w', padx=5, pady=5)
            srt_var = customtkinter.StringVar()
            srt_entry = customtkinter.CTkEntry(frame, textvariable=srt_var, width=420)
            srt_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=5)

            def browse_srt():
                path = filedialog.askopenfilename(title='Chọn file SRT', filetypes=[('SRT files', '*.srt'), ('All files', '*.*')])
                if path:
                    srt_var.set(path)
            srt_btn = customtkinter.CTkButton(frame, text='Chọn...', command=browse_srt, width=100)
            srt_btn.grid(row=0, column=2, padx=5, pady=5)
            ad_label = customtkinter.CTkLabel(frame, text='Thư mục Âm thanh:')
            ad_label.grid(row=1, column=0, sticky='w', padx=5, pady=5)
            ad_var = customtkinter.StringVar()
            ad_entry = customtkinter.CTkEntry(frame, textvariable=ad_var, width=420)
            ad_entry.grid(row=1, column=1, sticky='ew', padx=5, pady=5)

            def browse_ad():
                path = filedialog.askdirectory(title='Chọn thư mục chứa file âm thanh')
                if path:
                    ad_var.set(path)
            ad_btn = customtkinter.CTkButton(frame, text='Chọn...', command=browse_ad, width=100)
            ad_btn.grid(row=1, column=2, padx=5, pady=5)
            outd_label = customtkinter.CTkLabel(frame, text='Thư mục Lưu File:')
            outd_label.grid(row=2, column=0, sticky='w', padx=5, pady=5)
            outd_var = customtkinter.StringVar()
            outd_entry = customtkinter.CTkEntry(frame, textvariable=outd_var, width=420)
            outd_entry.grid(row=2, column=1, sticky='ew', padx=5, pady=5)

            def browse_outd():
                path = filedialog.askdirectory(title='Chọn thư mục lưu file kết quả')
                if path:
                    outd_var.set(path)
            outd_btn = customtkinter.CTkButton(frame, text='Chọn...', command=browse_outd, width=100)
            outd_btn.grid(row=2, column=2, padx=5, pady=5)
            outname_label = customtkinter.CTkLabel(frame, text='Tên File Xuất:')
            outname_label.grid(row=3, column=0, sticky='w', padx=5, pady=5)
            outname_var = customtkinter.StringVar(value='output_synced.mp3')
            outname_entry = customtkinter.CTkEntry(frame, textvariable=outname_var, width=420)
            outname_entry.grid(row=3, column=1, sticky='ew', padx=5, pady=5)
            log_box = customtkinter.CTkTextbox(frame, height=300)
            log_box.grid(row=5, column=0, columnspan=3, sticky='nsew', padx=5, pady=(10, 5))
            frame.grid_rowconfigure(5, weight=1)
            frame.grid_columnconfigure(1, weight=1)
            progress = customtkinter.CTkProgressBar(frame, mode='indeterminate')
            progress.grid(row=6, column=0, columnspan=3, sticky='ew', padx=5, pady=5)

            def log_message(msg):
                ts = time.strftime('%H:%M:%S')
                log_box.insert('end', f'[{ts}] {msg}\n')
                log_box.see('end')

            def process():
                import threading
                if not srt_var.get() or not os.path.exists(srt_var.get()):
                    messagebox.showerror('Lỗi', 'File SRT không hợp lệ!')
                    return
                if not ad_var.get() or not os.path.exists(ad_var.get()):
                    messagebox.showerror('Lỗi', 'Thư mục âm thanh không hợp lệ!')
                    return

                def worker():
                    try:
                        os.environ['PYDUB_HIDE_CONSOLE'] = '1'
                        import pysrt
                        from pydub import AudioSegment
                        try:
                            if os.name == 'nt':
                                import subprocess as _subp
                                from pydub import utils as _pydub_utils

                                def _hidden_popen(*args, **kwargs):
                                    startupinfo = kwargs.get('startupinfo')
                                    creationflags = kwargs.get('creationflags', 0)
                                    if startupinfo is None:
                                        startupinfo = _subp.STARTUPINFO()
                                    startupinfo.dwFlags |= _subp.STARTF_USESHOWWINDOW
                                    startupinfo.wShowWindow = 0
                                    creationflags |= getattr(_subp, 'CREATE_NO_WINDOW', 0)
                                    kwargs['startupinfo'] = startupinfo
                                    kwargs['creationflags'] = creationflags
                                    return _subp.Popen(*args, **kwargs)
                                _pydub_utils.Popen = _hidden_popen
                        except Exception:
                            pass

                        def find_executable(name):
                            base_path = get_app_root_dir()
                            local_path = os.path.join(base_path, f'{name}.exe')
                            if os.path.exists(local_path):
                                return local_path
                            for path_dir in os.environ.get('PATH', '').split(os.pathsep):
                                exe_path = os.path.join(path_dir, f'{name}.exe')
                                if os.path.exists(exe_path):
                                    return exe_path
                            else:
                                raise FileNotFoundError(f'\'{name}.exe\' not found')

                        def find_ffmpeg():
                            return find_executable('ffmpeg')

                        def find_ffprobe():
                            return find_executable('ffprobe')
                        ffmpeg_path = find_ffmpeg()
                        AudioSegment.converter = ffmpeg_path
                        AudioSegment.ffprobe = find_ffprobe()
                        AudioSegment.silent(duration=10)
                        log_message(f'Đang sử dụng FFmpeg tại: {AudioSegment.converter}')
                        try:
                            srt_file = pysrt.open(srt_var.get(), encoding='utf-8')
                        except Exception:
                            srt_file = pysrt.open(srt_var.get(), encoding='latin-1')
                        total_subs = len(srt_file)
                        log_message(f'Tìm thấy {total_subs} dòng thoại')
                        final_audio = AudioSegment.empty()
                        last_end_time_ms = 0
                        audio_folder = os.path.abspath(ad_var.get())
                        audio_extensions = ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac', '.opus']

                        def speed_change(sound, speed=1.0):
                            if speed <= 0:
                                return sound
                            if abs(speed - 1.0) < 0.001:
                                return sound
                            atempo_filters = []
                            safe_speed = max(0.5, min(100.0, speed))
                            if safe_speed > 1.0:
                                current_speed = safe_speed
                                while current_speed > 2.0:
                                    atempo_filters.append('atempo=2.0')
                                    current_speed /= 2.0
                                if current_speed > 1.0001:
                                    atempo_filters.append(f'atempo={current_speed:.4f}')
                            else:
                                current_speed = safe_speed
                                while current_speed < 0.5:
                                    atempo_filters.append('atempo=0.5')
                                    current_speed /= 0.5
                                if current_speed < 0.9999:
                                    atempo_filters.append(f'atempo={current_speed:.4f}')
                            filter_str = ','.join(atempo_filters) if atempo_filters else f'atempo={safe_speed:.4f}'
                            try:
                                command = [ffmpeg_path, '-f', 's16le', '-ar', str(sound.frame_rate), '-ac', str(sound.channels), '-i', '-', '-filter:a', filter_str, '-vn', '-f', 's16le', '-ar', str(sound.frame_rate), '-ac', str(sound.channels), '-']
                                import subprocess
                                startupinfo = None
                                creationflags = 0
                                if os.name == 'nt':
                                    startupinfo = subprocess.STARTUPINFO()
                                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                    startupinfo.wShowWindow = 0
                                    creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                                proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=startupinfo, creationflags=creationflags)
                                new_sound_data, err = proc.communicate(input=sound.raw_data)
                                if proc.returncode!= 0:
                                    raise Exception(f"ffmpeg exited {proc.returncode}: {err.decode(errors='ignore')[:400]}")
                                if not new_sound_data:
                                    raise Exception('FFmpeg atempo empty output')
                                return AudioSegment(data=new_sound_data, sample_width=sound.sample_width, frame_rate=sound.frame_rate, channels=sound.channels)
                            except Exception as e:
                                log_message(f'LỖI FFmpeg khi thay đổi tốc độ ({safe_speed:.3f}x): {e}')
                                return sound
                        for i, sub in enumerate(srt_file, 1):
                            start_time_ms = sub.start.ordinal
                            end_time_ms = sub.end.ordinal
                            required_duration_ms = end_time_ms - start_time_ms
                            if required_duration_ms <= 0:
                                log_message(f'CẢNH BÁO: [{i}/{total_subs}] Dòng SRT có thời lượng 0ms. Bỏ qua.')
                                last_end_time_ms = end_time_ms
                                continue
                            gap_duration_ms = start_time_ms - last_end_time_ms
                            if gap_duration_ms > 5:
                                log_message(f'[{i}/{total_subs}] Thêm khoảng lặng {gap_duration_ms}ms')
                                final_audio += AudioSegment.silent(duration=gap_duration_ms)
                            else:
                                if gap_duration_ms < (-5):
                                    log_message(f'CẢNH BÁO: [{i}/{total_subs}] SRT chồng chéo! (overlap {abs(gap_duration_ms)}ms)')
                                    if len(final_audio) >= abs(gap_duration_ms):
                                        final_audio = final_audio[:gap_duration_ms]
                                        log_message(f'    -> Đã cắt bớt {abs(gap_duration_ms)}ms của audio trước.')
                                    else:
                                        final_audio = AudioSegment.empty()
                                    last_end_time_ms = start_time_ms
                            audio_file = None
                            for ext in audio_extensions:
                                candidate = os.path.join(audio_folder, f'{i}{ext}')
                                if os.path.exists(candidate):
                                    audio_file = candidate
                                    break
                            if not audio_file:
                                log_message(f'LỖI: [{i}/{total_subs}] Không tìm thấy file {i}.(mp3/wav...)!')
                                final_audio += AudioSegment.silent(duration=required_duration_ms)
                                last_end_time_ms = end_time_ms
                            else:
                                log_message(f'[{i}/{total_subs}] Đang xử lý: {os.path.basename(audio_file)}')
                                try:
                                    audio_segment = AudioSegment.from_file(audio_file)
                                    actual_duration_ms = len(audio_segment)
                                    processed_segment = None
                                    did_speed_up = False
                                    if actual_duration_ms <= 1:
                                        log_message(f'LỖI: [{i}/{total_subs}] File {os.path.basename(audio_file)} quá ngắn hoặc lỗi đọc.')
                                        final_audio += AudioSegment.silent(duration=required_duration_ms)
                                        last_end_time_ms = end_time_ms
                                        continue
                                    if actual_duration_ms == required_duration_ms:
                                        log_message(f'    -> Vừa khớp ({actual_duration_ms}ms). Giữ nguyên.')
                                        processed_segment = audio_segment
                                    else:
                                        if actual_duration_ms > required_duration_ms:
                                            speed_ratio = actual_duration_ms / required_duration_ms
                                            log_message(f'    -> Dài ({actual_duration_ms}ms > {required_duration_ms}ms). Tăng tốc {speed_ratio:.4f}x')
                                            processed_segment = speed_change(audio_segment, speed_ratio)
                                            did_speed_up = True
                                            processed_duration = len(processed_segment)
                                            log_message(f'    -> Thời lượng sau tăng tốc: {processed_duration}ms (Yêu cầu: {required_duration_ms}ms)')
                                            if processed_duration > required_duration_ms + 20:
                                                log_message(f'    -> Tinh chỉnh: Cắt bớt {processed_duration - required_duration_ms}ms')
                                                processed_segment = processed_segment[:required_duration_ms]
                                            else:
                                                if processed_duration < required_duration_ms - 20:
                                                    pad_ms = required_duration_ms - processed_duration
                                                    log_message(f'    -> Tinh chỉnh: Bù thêm {pad_ms}ms')
                                                    processed_segment += AudioSegment.silent(duration=pad_ms)
                                        else:
                                            padding_ms = required_duration_ms - actual_duration_ms
                                            log_message(f'    -> Ngắn ({actual_duration_ms}ms < {required_duration_ms}ms). Thêm {padding_ms}ms im lặng')
                                            processed_segment = audio_segment + AudioSegment.silent(duration=padding_ms)
                                    if processed_segment is not None:
                                        final_audio += processed_segment
                                    else:
                                        log_message(f'LỖI: [{i}/{total_subs}] Không thể xử lý segment. Thêm khoảng lặng thay thế.')
                                        final_audio += AudioSegment.silent(duration=required_duration_ms)
                                    last_end_time_ms = end_time_ms
                                except Exception as e:
                                    log_message(f'LỖI khi xử lý file {os.path.basename(audio_file)}: {e}')
                                    final_audio += AudioSegment.silent(duration=required_duration_ms)
                                    last_end_time_ms = end_time_ms
                        out_dir = outd_var.get().strip() or os.path.dirname(os.path.abspath(srt_var.get()))
                        out_name = outname_var.get().strip() or 'output_synced.mp3'
                        if not out_name.lower().endswith(('.mp3', '.wav', '.flac', '.ogg')):
                            out_name += '.mp3'
                        output_path = os.path.join(out_dir, out_name)
                        output_format = os.path.splitext(output_path)[1][1:]
                        AudioSegment.converter = ffmpeg_path
                        final_audio.export(output_path, format=output_format)
                        log_message(f'Hoàn thành! File xuất: {output_path}')
                        messagebox.showinfo('Thành công', f'Đã hoàn thành!\nFile xuất: {output_path}')
                    except Exception as e:
                        log_message(f'LỖI NGHIÊM TRỌNG: {e}')
                    finally:
                        progress.stop()
                progress.start()
                threading.Thread(target=worker, daemon=True).start()
            start_btn = customtkinter.CTkButton(frame, text='Bắt đầu Xử lý', command=process)
            start_btn.grid(row=4, column=0, columnspan=3, pady=10)
            
            # Logic Tách SRT
            split_label = customtkinter.CTkLabel(frame, text='Xử lý SRT (tách lời thoại)', font=customtkinter.CTkFont(size=14, weight='bold'))
            split_label.grid(row=7, column=0, columnspan=3, sticky='w', padx=5, pady=(10, 5))
            split_srt_var = customtkinter.StringVar()
            split_entry = customtkinter.CTkEntry(frame, textvariable=split_srt_var, width=420)
            split_entry.grid(row=8, column=1, sticky='ew', padx=5, pady=5)
            customtkinter.CTkLabel(frame, text='File SRT:').grid(row=8, column=0, sticky='w', padx=5, pady=5)

            def browse_split_srt():
                path = filedialog.askopenfilename(title='Chọn file SRT', filetypes=[('SRT files', '*.srt'), ('All files', '*.*')])
                if path:
                    split_srt_var.set(path)
            customtkinter.CTkButton(frame, text='Chọn...', command=browse_split_srt, width=100).grid(row=8, column=2, padx=5, pady=5)
            split_output = customtkinter.CTkTextbox(frame, height=180)
            split_output.grid(row=9, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)
            frame.grid_rowconfigure(9, weight=1)

            def split_srt_text():
                try:
                    path = split_srt_var.get().strip()
                    if not path or not os.path.exists(path):
                        messagebox.showerror('Lỗi', 'Vui lòng chọn file SRT để tách!')
                        return
                    try:
                        subs = pysrt.open(path, encoding='utf-8')
                    except Exception:
                        subs = pysrt.open(path, encoding='latin-1')
                    import re as _re
                    lines = []
                    for item in subs:
                        text = item.text.replace('\r', '\n')
                        parts = [t.strip() for t in _re.split('[\\n]+', text) if t.strip()]
                        merged = ' '.join(parts)
                        if merged:
                            lines.append(merged)
                    split_output.delete('1.0', 'end')
                    split_output.insert('end', '\n\n'.join(lines))
                    log_message(f'[Xử lý SRT] Đã tách {len(lines)} dòng lời thoại')
                except Exception as e:
                    messagebox.showerror('Lỗi đọc SRT', f'Không thể đọc file SRT: {e}')

            def save_split_text():
                content = split_output.get('1.0', 'end').strip()
                if not content:
                    messagebox.showerror('Lỗi', 'Không có dữ liệu để lưu!')
                    return
                default_name = 'srt_split.txt'
                save_path = filedialog.asksaveasfilename(title='Lưu kết quả', defaultextension='.txt', initialfile=default_name, filetypes=[('Text files', '*.txt'), ('All files', '*.*')])
                if save_path:
                    try:
                        with open(save_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        log_message(f'[Xử lý SRT] Đã lưu: {save_path}')
                        messagebox.showinfo('Thành công', f'Đã lưu: {save_path}')
                    except Exception as e:
                        messagebox.showerror('Lỗi', f'Không thể lưu file: {e}')
            split_btn = customtkinter.CTkButton(frame, text='Tách', command=split_srt_text)
            split_btn.grid(row=10, column=0, padx=5, pady=5, sticky='w')
            save_btn = customtkinter.CTkButton(frame, text='Lưu .txt', command=save_split_text)
            save_btn.grid(row=10, column=1, padx=5, pady=5, sticky='w')
        except Exception as e:
            messagebox.showerror('Lỗi', f'Không thể mở Audio-SRT Sync: {e}')

    def check_license_immediately(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def check_trial_expired_immediately(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def check_license_status(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def is_license_activated(self):
        """Đã loại bỏ - Chỉ để trống"""
        return True

    def is_trial_activated(self):
        """Đã loại bỏ - Chỉ để trống"""
        return True

    def periodic_check(self):
        """Đã loại bỏ - Chỉ để trống"""
        self.after(30000, self.periodic_check)

    def show_license_expired_dialog(self, message, next_key_info=None):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def show_trial_activation_dialog(self, trial_key, duration):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def show_license_activation_dialog(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def check_extend_key(self, key):
        """Đã loại bỏ - Chỉ để trống"""
        return True

    def encrypt_data(self, data):
        """Đã loại bỏ - Chỉ để trống"""
        return {'data': base64.b64encode(json.dumps(data).encode()).decode(), 'signature': 'free'}

    def restart_application(self):
        """Khởi động lại ứng dụng"""
        try:
            import sys
            import subprocess
            import os
            debug_print('[DEBUG] Bắt đầu khởi động lại ứng dụng...')
            self.destroy()
            import time
            time.sleep(0.5)
            if getattr(sys, 'frozen', False):
                subprocess.Popen([sys.executable])
            else:
                subprocess.Popen([sys.executable, __file__])
            debug_print('[DEBUG] Đã khởi động lại ứng dụng')
        except Exception as e:
            debug_print(f'Lỗi khởi động lại: {e}')
            import traceback
            safe_traceback()

    def create_password_dialog(self, text, title):
        """Tạo dialog nhập mật khẩu với field ẩn"""
        dialog = customtkinter.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry('400x200')
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.update_idletasks()
        x = dialog.winfo_screenwidth() // 2 - 200
        y = dialog.winfo_screenheight() // 2 - 100
        dialog.geometry(f'400x200+{x}+{y}')
        result = {'password': None}
        label = customtkinter.CTkLabel(dialog, text=text, font=customtkinter.CTkFont(size=14))
        label.pack(pady=20)
        password_entry = customtkinter.CTkEntry(dialog, show='*', width=250, height=35, font=customtkinter.CTkFont(size=14))
        password_entry.pack(pady=10)
        password_entry.focus()
        button_frame = customtkinter.CTkFrame(dialog, fg_color='transparent')
        button_frame.pack(pady=20)

        def ok_clicked():
            result['password'] = password_entry.get()
            dialog.destroy()

        def cancel_clicked():
            result['password'] = None
            dialog.destroy()
        ok_button = customtkinter.CTkButton(button_frame, text='OK', command=ok_clicked, width=100, height=35)
        ok_button.pack(side='left', padx=10)
        cancel_button = customtkinter.CTkButton(button_frame, text='Cancel', command=cancel_clicked, width=100, height=35, fg_color='#6C757D', hover_color='#5A6268')
        cancel_button.pack(side='left', padx=10)

        def on_enter(event):
            ok_clicked()
        password_entry.bind('<Return>', on_enter)
        dialog.wait_window()
        return result['password']

    def on_closing(self):
        debug_print('Đang đóng ứng dụng, dọn dẹp các trình duyệt...')
        # Loại bỏ license_monitor
        self.save_brave_path()
        self.stop_all_browsers()
        self.destroy()

    def browse_brave_path(self):
        """Mở dialog chọn file Brave Browser"""
        from tkinter import filedialog
        brave_path = filedialog.askopenfilename(title='Chọn file Brave Browser', filetypes=[('Brave Executable', 'brave.exe'), ('Executable Files', '*.exe'), ('All Files', '*.*')])
        if brave_path:
            self.brave_path_entry.delete(0, 'end')
            self.brave_path_entry.insert(0, brave_path)
            self.save_brave_path()

    def load_brave_path(self):
        """Tải đường dẫn Brave Browser đã lưu"""
        try:
            brave_config_file = 'brave_config.json'
            if os.path.exists(brave_config_file):
                with open(brave_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    brave_path = config.get('brave_path', '')
                    if brave_path and os.path.exists(brave_path):
                        self.brave_path_entry.insert(0, brave_path)
                    else:
                        debug_print('Đường dẫn Brave Browser đã lưu không tồn tại, bỏ qua')
        except Exception as e:
            debug_print(f'Lỗi tải cấu hình Brave Browser: {e}')

    def save_brave_path(self):
        """Lưu đường dẫn Brave Browser vào file cấu hình"""
        try:
            brave_path = self.brave_path_entry.get().strip()
            brave_config_file = 'brave_config.json'
            config = {'brave_path': brave_path}
            with open(brave_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            debug_print(f'Đã lưu đường dẫn Brave Browser: {brave_path}')
        except Exception as e:
            debug_print(f'Lỗi lưu cấu hình Brave Browser: {e}')

    def _wait_for_page_loaded(self, driver, timeout=30):
        """Chờ trang tải xong (document.readyState == 'complete')."""
        try:
            WebDriverWait(driver, timeout).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        except Exception as e:
            debug_print(f'[Minimax] Hết thời gian chờ trang load: {e}')

    def _has_minimax_403_error(self, driver):
        """Kiểm tra toast/lỗi 403 trên trang Minimax."""
        try:
            page = driver.page_source or ''
            if 'Request failed with status code 403' in page:
                return True
            try:
                elements = driver.find_elements(By.XPATH, '//*[contains(text(),\'Request failed with status code 403\')]')
                if elements:
                    return True
                return False
            except Exception:
                return False
        except Exception as e:
            debug_print(f'[Minimax] Lỗi khi kiểm tra 403: {e}')
            return False

    def auto_reload_until_ok(self, driver, profile_name, max_attempts=20, wait_between=0.0):
        """
        Tự động reload nếu gặp lỗi 403 cho đến khi hết lỗi.
        Đã sửa lỗi bị kẹt (hang) bằng cách bỏ 'wait_for_page_loaded'.
        """
        attempt = 0
        while True:
            attempt += 1
            try:
                debug_print(f'[Minimax] Lần {attempt}: Đang chờ Cloudflare/Verify...')
                WebDriverWait(driver, 10).until_not(lambda d: 'verifying you are human' in (d.page_source or '').lower())
                debug_print(f'[Minimax] Lần {attempt}: Đã qua Cloudflare/Verify.')
            except Exception as e:
                debug_print(f'[Minimax] Lần {attempt}: Lỗi chờ Cloudflare: {e}')
            if not self._has_minimax_403_error(driver):
                if attempt > 1:
                    debug_print(f'[Minimax] Hết lỗi 403 sau {attempt - 1} lần reload.')
                return None
            debug_print(f'[Minimax] Phát hiện lỗi 403. Reload lần {attempt}...')
            self.after(0, self.update_profile_status, profile_name, f'Đang tự reset ({attempt})...', 'orange')
            try:
                driver.refresh()
            except Exception as e:
                debug_print(f'[Minimax] Lỗi khi refresh: {e}')
                return None
            if wait_between and wait_between > 0:
                time.sleep(wait_between)
            if max_attempts is not None and attempt >= max_attempts:
                debug_print('[Minimax] Đạt giới hạn số lần reload. Dừng lại.')
                break

    def get_brave_path(self):
        """Lấy đường dẫn Brave Browser theo thứ tự ưu tiên: Tùy chỉnh -> Tự động tìm"""
        brave_path_from_ui = self.brave_path_entry.get().strip()
        if self.validate_brave_path(brave_path_from_ui):
            debug_print(f'Sử dụng đường dẫn Brave Browser tùy chỉnh từ giao diện: {brave_path_from_ui}')
            return brave_path_from_ui
        debug_print('Không tìm thấy đường dẫn Brave Browser tùy chỉnh. Tự động tìm trên hệ thống...')
        username = os.getenv('USERNAME')
        possible_paths = ['C:\\\\Program Files\\\\BraveSoftware\\\\Brave-Browser\\\\Application\\\\brave.exe', 'C:\\\\Program Files (x86)\\\\BraveSoftware\\\\Brave-Browser\\\\Application\\\\brave.exe', f'C:\\\\Users\\\\{username}\\\\AppData\\\\Local\\\\BraveSoftware\\\\Brave-Browser\\\\Application\\\\brave.exe']
        for path in possible_paths:
            if os.path.exists(path):
                debug_print(f'Tìm thấy Brave Browser tại: {path}')
                return path
        else:
            debug_print('Không tìm thấy Brave Browser ở bất kỳ đâu.')
            return None # Thêm giá trị trả về None nếu không tìm thấy

    def validate_brave_path(self, brave_path):
        """Kiểm tra đường dẫn Brave Browser có hợp lệ không"""
        try:
            if not brave_path or not os.path.exists(brave_path):
                return False
            if not os.path.isfile(brave_path):
                return False
            filename = os.path.basename(brave_path).lower()
            if filename!= 'brave.exe':
                return False
            if not os.access(brave_path, os.R_OK):
                return False
            return True
        except Exception as e:
            debug_print(f'Lỗi kiểm tra đường dẫn Brave Browser: {e}')
            return False

    def test_brave_path(self):
        """Test đường dẫn Brave Browser và hiển thị kết quả"""
        brave_path = self.brave_path_entry.get().strip()
        if not brave_path:
            self.main_status_label.configure(text='⚠️ Vui lòng nhập đường dẫn Brave Browser trước khi test', text_color='orange')
            return
        if self.validate_brave_path(brave_path):
            self.main_status_label.configure(text=f'✅ Đường dẫn Brave Browser hợp lệ: {brave_path}', text_color='green')
            self.save_brave_path()
        else:
            self.main_status_label.configure(text=f'❌ Đường dẫn Brave Browser không hợp lệ: {brave_path}', text_color='red')

    def get_driver_lock(self, profile_name):
        """Trả về Lock theo profile để đồng bộ gọi WebDriver giữa các luồng."""
        if not hasattr(self, '_driver_locks'):
            self._driver_locks = {}
        if profile_name not in self._driver_locks:
            self._driver_locks[profile_name] = threading.Lock()
        return self._driver_locks[profile_name]

    def monitor_devtools(self, driver, profile_name, anti_devtools_script):
        """Đã loại bỏ - Giữ nguyên tên hàm nhưng không có logic Anti-DevTools."""
        debug_print(f'[Anti-DevTools] Giám sát đã bị loại bỏ cho profile \'{profile_name}\'')
        pass 

    def load_profiles(self):
        try:
            if os.path.exists(PROFILES_JSON_PATH):
                with open(PROFILES_JSON_PATH, 'r', encoding='utf-8') as f:
                    try:
                        self.profiles = json.load(f) or {}
                    except json.JSONDecodeError:
                        debug_print(f"[WARN] profiles.json không hợp lệ. Khởi tạo rỗng.")
                        self.profiles = {}
            else:
                self.profiles = {}
            os.makedirs(PROFILES_DIR, exist_ok=True)
        except Exception as e:
            debug_print(f"[ERROR] load_profiles: {e}")
            self.profiles = {}
        self.update_profile_list_ui()

    def save_profiles(self):
        with open(PROFILES_JSON_PATH, 'w') as f:
            json.dump(self.profiles, f, indent=4)

    def update_profile_list_ui(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.profile_widgets.clear()
        for profile_name in self.profiles.keys():
            is_running = profile_name in self.running_browsers
            row_frame = customtkinter.CTkFrame(self.scrollable_frame)
            row_frame.pack(fill='x', padx=5, pady=5, expand=True)
            row_frame.grid_columnconfigure(0, weight=1)
            name_frame = customtkinter.CTkFrame(row_frame, fg_color='transparent')
            name_frame.grid(row=0, column=0, sticky='w')
            checkbox = customtkinter.CTkCheckBox(name_frame, text=profile_name, font=customtkinter.CTkFont(size=14))
            checkbox.pack(side='left')
            action_frame = customtkinter.CTkFrame(row_frame, fg_color='transparent')
            action_frame.grid(row=0, column=1, sticky='e')
            status_text = 'Đang chạy' if is_running else 'Đã dừng'
            status_color = 'green' if is_running else 'gray'
            status_label = customtkinter.CTkLabel(action_frame, text=status_text, text_color=status_color, width=100)
            status_label.pack(side='left', padx=10)
            script_button = customtkinter.CTkButton(action_frame, text='Bật Script', command=lambda name=profile_name: self.toggle_script(name), state='normal' if is_running else 'disabled')
            script_button.pack(side='left', padx=5)
            self.profile_widgets[profile_name] = {'checkbox': checkbox, 'status_label': status_label, 'script_button': script_button, 'script_on': False}

    def add_profile(self):
        current_profile_count = len(self.profiles)
        # Loại bỏ logic giới hạn MAX_PROFILES và mật khẩu
        
        dialog = customtkinter.CTkInputDialog(text='Nhập tên cho profile mới:', title='Thêm Profile')
        new_name = dialog.get_input()
        if new_name and new_name not in self.profiles:
            profile_path = os.path.join(PROFILES_DIR, new_name.strip())
            os.makedirs(profile_path, exist_ok=True)
            self.profiles[new_name] = {'path': profile_path}
            self.save_profiles()
            self.update_profile_list_ui()
            self.main_status_label.configure(text=f'Đã tạo profile \'{new_name}\' thành công.', text_color='green')
        else:
            if new_name in self.profiles:
                self.main_status_label.configure(text=f'Lỗi: Profile \'{new_name}\' đã tồn tại.', text_color='red')

    def delete_profile(self):
        """Xóa profile đã chọn với xác nhận"""
        selected_profiles = []
        for name, widgets in self.profile_widgets.items():
            if widgets['checkbox'].get() == 1:
                selected_profiles.append(name)
        if not selected_profiles:
            self.main_status_label.configure(text='Vui lòng chọn ít nhất một profile để xóa.', text_color='orange')
            return
        profile_list = '\n'.join([f'• {name}' for name in selected_profiles])
        confirm_dialog = customtkinter.CTkInputDialog(text=f'Bạn có chắc chắn muốn xóa {len(selected_profiles)} profile sau?\n\n{profile_list}\n\nNhập \'XÓA\' để xác nhận:', title='Xác nhận xóa Profile')
        confirmation = confirm_dialog.get_input()
        if confirmation!= 'XÓA':
            self.main_status_label.configure(text='Đã hủy việc xóa profile.', text_color='gray')
            return
        deleted_count = 0
        for profile_name in selected_profiles:
            try:
                if profile_name in self.running_browsers:
                    try:
                        self.running_browsers[profile_name].quit()
                    except:
                        pass
                    del self.running_browsers[profile_name]
                profile_path = self.profiles[profile_name]['path']
                if os.path.exists(profile_path):
                    import shutil
                    shutil.rmtree(profile_path)
                del self.profiles[profile_name]
                deleted_count += 1
            except Exception as e:
                debug_print(f'Lỗi khi xóa profile \'{profile_name}\': {e}')
        self.save_profiles()
        self.update_profile_list_ui()
        if deleted_count > 0:
            self.main_status_label.configure(text=f'Đã xóa thành công {deleted_count} profile.', text_color='green')
        else:
            self.main_status_label.configure(text='Không thể xóa profile nào.', text_color='red')

    def start_selected_profiles(self):
        if not self.is_authenticated:
            return
        for name, widgets in self.profile_widgets.items():
            if widgets['checkbox'].get() == 1 and name not in self.running_browsers:
                thread = threading.Thread(target=self.launch_browser, args=(name,))
                thread.daemon = True
                thread.start()

    def apply_profile_download_prefs(self, profile_path, download_dir):
        """Merge các key cần thiết vào file Preferences của profile Brave."""
        try:
            pref_file = os.path.join(profile_path, "Default", "Preferences")
            os.makedirs(os.path.dirname(pref_file), exist_ok=True)
            data = {}
            if os.path.exists(pref_file):
                with open(pref_file, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                    except Exception:
                        data = {}

            # Merge tối thiểu cho auto-download
            data.setdefault("download", {})
            data["download"]["default_directory"]   = download_dir.replace("\\", "/")
            data["download"]["prompt_for_download"] = False
            data["download"]["directory_upgrade"]   = True

            data.setdefault("profile", {})
            data["profile"].setdefault("default_content_setting_values", {})
            data["profile"]["default_content_setting_values"]["automatic_downloads"] = 1

            data.setdefault("safebrowsing", {})
            data["safebrowsing"]["enabled"] = True

            # Tắt popups
            data.setdefault("profile", {}).setdefault("default_content_settings", {})
            data["profile"]["default_content_settings"]["popups"] = 0

            # Lưu lại
            with open(pref_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            debug_print(f"[Prefs] Lỗi ghi Preferences: {e}")

    def launch_browser(self, profile_name):
        self.after(0, self.update_profile_status, profile_name, 'Đang khởi động...', 'orange')
        driver = None

        download_dir = self.get_download_dir(profile_name)
        debug_print(f"[{profile_name}] Sử dụng thư mục download: {download_dir}")
        os.makedirs(download_dir, exist_ok=True)
        profile_path = self.profiles[profile_name]['path']

        # Ghi Preferences trước để tắt Save As
        self.apply_profile_download_prefs(profile_path, download_dir)

        try:
            import undetected_chromedriver as uc

            # DÙNG UC OPTIONS (không dùng webdriver.ChromeOptions)
            options = uc.ChromeOptions()

            # Hồ sơ Brave
            options.add_argument(f'--user-data-dir={os.path.abspath(profile_path)}')

            # Các flags an toàn/ổn định
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-ipc-flooding-protection')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--no-first-run')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')
            
            brave_path = self.get_brave_path()
            if not brave_path:
                self.after(0, self.update_profile_status, profile_name, 'Không tìm thấy Brave', 'red')
                return

            # ❌ KHÔNG ép driver_executable_path để tránh mismatch
            driver = uc.Chrome(
                headless=False,
                browser_executable_path=brave_path,
                user_data_dir=os.path.abspath(profile_path)
            )

            self.running_browsers[profile_name] = driver
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)

            self.after(0, self.update_profile_status, profile_name, 'Đang mở Minimax...', 'orange')
            time.sleep(1)
            driver.get('https://www.minimax.io/audio/voices-cloning')

            # Auto xử lý lỗi 403 nếu có
            try:
                self.auto_reload_until_ok(driver, profile_name)
                self.after(0, self.update_profile_status, profile_name, 'Đang chạy', 'green')
            except Exception as e:
                debug_print(f'[Minimax] Lỗi auto-reload: {e}')

            # Giữ vòng đời
            while True:
                try:
                    _ = driver.window_handles
                    time.sleep(1)
                except Exception:
                    debug_print(f"Profile '{profile_name}' đã được đóng.")
                    break

        except Exception as e:
            debug_print(f'Lỗi khi dùng Brave + UC: {e}')
            self.after(0, self.update_profile_status, profile_name, f'Lỗi Brave/UC: {e}', 'red')


    def launch_browser_bk(self, profile_name):
        self.after(0, self.update_profile_status, profile_name, 'Đang khởi động...', 'orange')
        driver = None
        browser_pid = None

        download_dir = self.get_download_dir(profile_name)
        debug_print(f"[{profile_name}] Sử dụng thư mục download: {download_dir}")
        os.makedirs(download_dir, exist_ok=True)

        try:
            profile_path = self.profiles[profile_name]['path']

            #2025-11-11 thêm setting default luu file download
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options = webdriver.ChromeOptions()
            options.add_argument(f'--user-data-dir={os.path.abspath(profile_path)}')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_experimental_option('detach', True)
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-features=VizDisplayCompositor')
            options.add_argument('--disable-ipc-flooding-protection')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-features=TranslateUI')
            options.add_argument('--disable-component-extensions-with-background-pages')
            options.add_argument('--disable-default-apps')
            options.add_argument('--disable-sync')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_experimental_option("prefs", prefs) #2025-11-11 add setting download folder output
            brave_path = self.get_brave_path()
            try:
                original_driver_path = get_resource_path(os.path.join('Resource', 'chromedriver.exe'))
                if not os.path.exists(original_driver_path):
                    raise FileNotFoundError('Không tìm thấy chromedriver.exe trong thư mục /Resource')
                temp_profile_dir = self.profiles[profile_name]['path']
                os.makedirs(temp_profile_dir, exist_ok=True)
                safe_profile_name = ''.join((c for c in profile_name if c.isalnum() or c in ['-', '_'])).rstrip()
                temp_driver_name = f'chromedriver_{safe_profile_name}.exe'
                temp_driver_path = os.path.join(temp_profile_dir, temp_driver_name)
                debug_print(f'[{profile_name}] Tạo driver riêng: {temp_driver_name}')
                shutil.copy2(original_driver_path, temp_driver_path)
                chromedriver_path = temp_driver_path
            except Exception as e:
                debug_print(f'[{profile_name}] Lỗi nghiêm trọng khi tạo driver riêng: {e}')
                self.after(0, self.update_profile_status, profile_name, f'Lỗi tạo driver: {e}', 'red')
                return
            finally:
                pass
            
            try:
                debug_print(f'Thử khởi động Brave với binary của Brave Browser: {brave_path}')
                debug_print(f'Sử dụng chromedriver_path: {chromedriver_path}')
                driver = uc.Chrome(user_data_dir=os.path.abspath(profile_path), headless=False, driver_executable_path=chromedriver_path, browser_executable_path=brave_path)
                browser_pid = driver.browser_pid
                debug_print(f'Sử dụng undetected-chromedriver với Brave Browser thành công cho profile {profile_name}')
            except Exception as e:
                debug_print(f'Lỗi khi dùng Brave + Brave Browser. Fallback về Selenium tiêu chuẩn: {e}')
                debug_print('CẢNH BÁO: Chế độ Fallback sẽ bị phát hiện!')
                safe_traceback()
                self.after(0, self.update_profile_status, profile_name, f'Lỗi Brave+Brave Browser: {e}', 'red')
                return
            
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            self.after(0, self.update_profile_status, profile_name, 'Đang mở Minimax...', 'orange')
            ready_start = time.time()
            max_wait_seconds = 15
            while True:
                try:
                    # Kiểm tra xem trình duyệt đã sẵn sàng chưa
                    _ = driver.window_handles
                    debug_print('[DEBUG] Driver đã phản hồi và sẵn sàng.')
                    break # THOÁT KHI THÀNH CÔNG
                except Exception:
                    if time.time() - ready_start > max_wait_seconds:
                        break # THOÁT KHI HẾT THỜI GIAN CHỜ (15 giây)
                    time.sleep(0.2) # Nghỉ 200ms trước khi thử lại
                
            time.sleep(2)
            driver.get('https://www.minimax.io/audio/voices-cloning')
            try:
                self.auto_reload_until_ok(driver, profile_name)
            except Exception as e:
                debug_print(f'[Minimax] Lỗi khi chạy cơ chế auto-reload: {e}')
                
            #2025-11-12 thêm đọc setting ngôn ngữ từ config
            try:
                self.apply_language_setting(driver)
            except Exception as e:
                debug_print(f"[AUTO] Không thể áp dụng ngôn ngữ cho {profile_name}: {e}")

            self.running_browsers[profile_name] = driver
            self.after(0, self.update_profile_status, profile_name, 'Đang chạy', 'green')
           
            while True:
                try:
                    _ = driver.window_handles
                    time.sleep(1)
                except Exception:
                    debug_print(f"Profile '{profile_name}' da duoc dong.")
                    break
        except Exception as e:
            debug_print(f'Lỗi nghiêm trọng khi chạy profile {profile_name}: {e}')
            self.after(0, self.update_profile_status, profile_name, 'Lỗi', 'red')

    def update_profile_status(self, profile_name, text, color):
        if profile_name in self.profile_widgets:
            widgets = self.profile_widgets[profile_name]
            widgets['status_label'].configure(text=text, text_color=color)
            if text == 'Đang chạy':
                widgets['script_button'].configure(state='normal')
            else:
                widgets['script_on'] = False
                widgets['script_button'].configure(state='disabled', text='Bật Script', fg_color=('#3B8ED0', '#1F6AA5'))

    def stop_all_browsers(self):
        for name, driver in list(self.running_browsers.items()):
            try:
                driver.quit()
            except Exception as e:
                debug_print(f'Lỗi khi đóng profile {name}: {e}')
        self.running_browsers.clear()

    def reset_violations(self):
        """Đã loại bỏ - Giữ lại hàm để tránh lỗi nhưng loại bỏ logic"""
        if not self.is_authenticated:
            return
        # Loại bỏ logic mật khẩu và reset local storage
        self.main_status_label.configure(text='Cơ chế vi phạm đã bị vô hiệu hóa.', text_color='blue')

    def toggle_script(self, profile_name):
        if profile_name not in self.running_browsers: return

        widgets = self.profile_widgets[profile_name]
        is_on = widgets.get('script_on', False)

        if not is_on:
            widgets['script_on'] = True
            widgets['script_button'].configure(text='Tắt Script', fg_color='#D32F2F', hover_color='#B71C1C')
            self.main_status_label.configure(text=f'Đã BẬT chế độ giám sát cho \'{profile_name}\'.', text_color='green')
            self.update_run_all_state()   # <-- thêm dòng này
            thread = threading.Thread(target=self.tampermonkey_engine, args=(profile_name,))
            thread.daemon = True
            thread.start()
        else:
            widgets['script_on'] = False
            widgets['script_button'].configure(text='Bật Script', fg_color=('#3B8ED0', '#1F6AA5'))
            self.main_status_label.configure(text=f'Đã TẮT chế độ giám sát cho \'{profile_name}\'.', text_color='gray')
            self.update_run_all_state()   # <-- thêm dòng này
            try:
                driver = self.running_browsers[profile_name]
                driver.refresh()
            except Exception as e:
                debug_print(f'Không thể làm mới trang: {e}')

    def _create_error_dialog_ui(self, profile_name, result_container, dialog_closed_event):
        """\n        Hàm này TẠO GIAO DIỆN trên luồng chính. Không gọi trực tiếp từ luồng phụ.\n        """  # inserted
        try:
            dialog = customtkinter.CTkToplevel(self)
            dialog.title('⚠️ Cảnh Báo Lỗi Giám Sát')
            dialog.geometry('450x200')
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()
            dialog.after(10, lambda: dialog.lift())
            x = self.winfo_x() + self.winfo_width() // 2 - 225
            y = self.winfo_y() + self.winfo_height() // 2 - 100
            dialog.geometry(f'450x200+{x}+{y}')
            message = f'Tool đã mất kết nối với profile \'{profile_name}\' sau nhiều lần thử.\n\nBạn muốn làm gì?'
            label = customtkinter.CTkLabel(dialog, text=message, font=customtkinter.CTkFont(size=14), wraplength=400)
            label.pack(pady=20, padx=20)
            button_frame = customtkinter.CTkFrame(dialog, fg_color='transparent')
            button_frame.pack(pady=10)

            def on_retry():
                result_container['choice'] = 'retry'
                dialog.destroy()

            def on_stop():
                result_container['choice'] = 'stop'
                dialog.destroy()
            retry_button = customtkinter.CTkButton(button_frame, text='🔄 Thử lại', command=on_retry, width=150, height=40)
            retry_button.pack(side='left', padx=10)
            stop_button = customtkinter.CTkButton(button_frame, text='⏹️ Dừng giám sát', command=on_stop, fg_color='#D32F2F', hover_color='#B71C1C', width=150, height=40)
            stop_button.pack(side='left', padx=10)
            dialog.protocol('WM_DELETE_WINDOW', on_stop)
            self.wait_window(dialog)
        finally:  # inserted
            dialog_closed_event.set()

    def prompt_user_on_error(self, profile_name):
        """Đã loại bỏ - Chỉ để trống"""
        return 'stop'

    def tampermonkey_engine(self, profile_name):
        """
        Engine giám sát đã được làm sạch: 
        - Loại bỏ logic Quota (thay thế bằng giá trị -1 (Không giới hạn)).
        - Loại bỏ logic báo cáo API và ghi cache.
        - Loại bỏ logic hỏi người dùng (prompt_user_on_error).
        """
        debug_print(f'Bắt đầu engine giám sát làm sạch cho profile: {profile_name}')
        
        # --- 1. Tải Script (Giữ lại logic này) ---
        if not hasattr(self, '_script_code'):
            debug_print(f'Đang tải script cho \'{profile_name}\'...')
            try:
                script_path = get_resource_path('script.js')
                debug_print(f'Đường dẫn script: {script_path}')
                if not os.path.exists(script_path):
                    error_msg = 'Lỗi: Không tìm thấy script.js'
                    debug_print(error_msg)
                    self.after(0, self.main_status_label.configure, {'text': error_msg, 'text_color': 'red'})
                    self.profile_widgets[profile_name]['script_on'] = False
                    return
                with open(script_path, 'r', encoding='utf-8') as f:
                    self._script_code = f.read()
            except Exception as e:
                error_msg = f'Lỗi đọc script.js: {e}'
                debug_print(f'Lỗi đọc script.js: {e}')
                self.after(0, self.main_status_label.configure, {'text': error_msg, 'text_color': 'red'})
                self.profile_widgets[profile_name]['script_on'] = False
                return

        consecutive_error_count = 0
        max_consecutive_errors = 5 # Vẫn giữ logic lỗi kết nối
        script_injected = False
            
        # --- 2. Vòng lặp Giám sát ---
        debug_print(f'Bắt đầu giám sát cho profile: {profile_name}')
        while self.profile_widgets.get(profile_name, {}).get('script_on'):
            try:
                driver = self.running_browsers.get(profile_name)
                if not driver:
                    debug_print('Driver không tồn tại, dừng engine')
                    break

                lock = self.get_driver_lock(profile_name)
                if not script_injected:
                    debug_print(f'Đang tiêm script cho \'{profile_name}\'...')
                    with lock:
                        # Tiêm Quota và ID máy (Sử dụng giá trị Không giới hạn -1)
                        quota_to_inject = -1 # Giả lập: Luôn là Không giới hạn
                        driver.execute_script(f'\n                            window.REMAINING_CHARS = {quota_to_inject};\n                            window.MY_UNIQUE_MACHINE_ID = \'{self.my_machine_id}\'; \n                            window.myScriptInjected = true;\n                        ')
                        driver.execute_script(self._script_code)
                    script_injected = True
                    debug_print(f'Đã tiêm script và quota {quota_to_inject} (FREE) cho \'{profile_name}\'')

                # --- 3. Logic Đọc Tín hiệu Title (Giữ lại để tiêm lại script) ---
                current_title = ''
                with lock:
                    current_title = driver.title
                    
                if current_title.startswith('MMX_REPORT:'):
                    # Nếu nhận được tín hiệu MMX_REPORT, chỉ cần reset title
                    debug_print(f'[{profile_name}] Nhận tín hiệu MMX_REPORT, bỏ qua xử lý Quota.')
                    with lock:
                        driver.execute_script('document.title = \'Minimax\';')
                        # Buộc tiêm lại script trong lần lặp tiếp theo
                        script_injected = False 
                
                if consecutive_error_count > 0:
                    self.after(0, self.main_status_label.configure, {'text': f'✅ Đã kết nối lại thành công với \'{profile_name}\'', 'text_color': 'green'})
                
                consecutive_error_count = 0
                time.sleep(1.0)
                
            except Exception as e:
                consecutive_error_count += 1
                debug_print(f'Lỗi giám sát (lần {consecutive_error_count}/{max_consecutive_errors}): {e}')
                script_injected = False
                
                if consecutive_error_count >= max_consecutive_errors:
                    debug_print('Đã đạt giới hạn lỗi kết nối. Tự động dừng giám sát.')
                    
                    # TỰ ĐỘNG DỪNG (Không hỏi người dùng)
                    if profile_name in self.profile_widgets:
                        self.profile_widgets[profile_name]['script_on'] = False
                    self.after(0, self.update_profile_status, profile_name, 'Đã dừng (Lỗi kết nối)', 'gray')
                    break 
                
                time.sleep(3)
                
        if profile_name in self.profile_widgets:
            self.profile_widgets[profile_name]['script_on'] = False
        debug_print(f'Đã dừng engine giám sát cho profile: {profile_name}')
        self.after(0, self.update_run_all_state)

    def restart_engine_for_profile(self, profile_name):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    def update_license_status_after_renewal(self):
        """Đã loại bỏ - Chỉ để trống"""
        pass

    #START-AUTO
    def auto_create_voice(self, profile_name):
        driver = self.running_browsers.get(profile_name)
        if not driver:
            debug_print(f"[{profile_name}] Không có driver")
            return False
        self._ensure_on_tab(driver, "minimax.io", timeout=3)
        debug_print(f"[{profile_name}] URL hiện tại: {driver.current_url}")
        self._inject_helpers_js(driver)

        driver.execute_script("""
            if (window.taskState) {
                window.taskState.status = 'idle';
                window.taskState.message = '';
                window.taskState.progress = 0;
                window.taskState.errors = [];
            }
        """)
        self.run_audio_creation_flow_full(profile_name, driver, self.text_path, timeout=300, poll_interval=2)
        return True

    def upload_and_wait_status_cauhinh(self, profile_name, file_path=None, timeout=30, iframe_index=None):
        debug_print("Start upload_and_wait_status_cauhinh..")
        driver = self.running_browsers.get(profile_name)
        if not driver: return (False, "No driver for this profile")

        # Áp ngôn ngữ nếu cấu hình
        try:
            self.apply_language_setting(driver)
        except Exception as e:
            debug_print(f"[AUTO] Không thể áp dụng ngôn ngữ cho {profile_name}: {e}")

        if iframe_index is not None:
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            if iframe_index >= len(iframes):
                return (False, f"iframe index {iframe_index} out of range")
            driver.switch_to.frame(iframes[iframe_index])

        try:
            if file_path:
                file_path = os.path.abspath(file_path)
                try:
                    file_input = driver.find_element(By.ID, 'gemini-file-input')
                    file_input.send_keys(file_path)
                except Exception:
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, 'gemini-file-input')))
                    driver.find_element(By.ID, 'gemini-file-input').send_keys(file_path)

            upload_btn = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "gemini-upload-btn")))
            driver.execute_script("arguments[0].click();", upload_btn)

            t0 = time.time()
            last = ""
            while time.time() - t0 < timeout:
                status_text = driver.execute_script(
                    "var n=document.getElementById('gemini-upload-status');"
                    "return n && n.textContent ? n.textContent.trim() : '';"
                ) or ""
                if status_text and status_text != last:
                    print(f"[{profile_name}] status: {status_text}")
                    last = status_text
                    lower = status_text.lower()
                    if "thành công" in lower or "success" in lower or "configured" in lower:
                        return (True, status_text)
                    if "lỗi" in lower or "error" in lower or "fail" in lower:
                        return (False, status_text)
                time.sleep(0.5)

            return (False, last or "Timeout waiting for status")
        finally:
            if iframe_index is not None:
                driver.switch_to.default_content()

    def run_audio_creation_flow_full(self, profile_name, driver, text_file_path, timeout=300, poll_interval=2):
        with open(text_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        base_filename = os.path.splitext(os.path.basename(text_file_path))[0]
        total = 1
        idx = 1
        self.update_source_row(text_file_path, status="Đang chạy", progress=f"{idx}/{total}")
        js_insert = """
        const el = document.getElementById('gemini-main-textarea');
        if(!el) return false;
        const desc = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');
        if (desc && typeof desc.set === 'function') desc.set.call(el, arguments[0]);
        else el.value = arguments[0];
        el.dispatchEvent(new Event('input', {bubbles:true}));
        el.dispatchEvent(new Event('change', {bubbles:true}));
        return true;
        """
        ok = driver.execute_script(js_insert, content)
        if not ok:
            debug_print("❌ Không tìm thấy textarea!")
            return

        try:
            time.sleep(5)
            start_btn = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "gemini-merge-btn")))
            driver.execute_script("arguments[0].click();", start_btn)
            debug_print("▶️  Đã click 'Ghép đoạn hội thoại'")
        except Exception as e:
            debug_print("❌ Không tìm thấy nút Ghép đoạn hội thoại:", e)
            return

        try:
            time.sleep(5)
            start_btn = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "gemini-start-queue-btn")))
            driver.execute_script("arguments[0].click();", start_btn)
            debug_print("▶️  Đã click 'Bắt đầu tạo âm thanh'")
        except Exception as e:
            debug_print("❌ Không tìm thấy nút tạo âm thanh:", e)
            return

        debug_print("⏳ Đang chờ tạo âm thanh...")
        t0 = time.time()
        last_status = ""
        while time.time() - t0 < timeout:
            state = driver.execute_script("return window.taskState || {};")
            status = state.get("status", "")
            msg = state.get("message", "")
            progress = state.get("progress", 0)

            if status != last_status:
                debug_print(f"[{status.upper():>7}] {progress:3d}% - {msg}")
                last_status = status

            dl_visible = driver.execute_script("""
                var el = document.getElementById('gemini-download-merged-btn');
                return el && el.offsetParent !== null;
            """)
            if status in ["done", "error", "skipped"] or dl_visible:
                break
            time.sleep(poll_interval)

        filename = f"{base_filename}.mp3"
        WebDriverWait(driver, 60).until(
            lambda d: d.execute_script("""
                var a = document.getElementById('gemini-download-merged-btn');
                return a && a.href && a.href.startsWith('blob:');
            """)
        )

        # Lấy href của thẻ <a id="gemini-download-merged-btn" ...>
        blob_url = driver.execute_script("""
            const a = document.getElementById('gemini-download-merged-btn');
            return a && a.href ? a.href : null;
        """)
        if not blob_url or not str(blob_url).startswith("blob:"):
            debug_print("❌ Không thấy blob href hợp lệ")
        else:
            # Tự đặt tên file đích
            dest_dir = self.get_download_dir(profile_name)  # thư mục tải tự chọn
            debug_print(f'dest_dir: {dest_dir}')
            dest_path = os.path.join(dest_dir, filename)
            debug_print(f'dest_path: {dest_path}')

            ok, msg = download_blob_to_path(driver, blob_url, dest_path)
            debug_print(("✅ " if ok else "❌ ") + msg)
        time.sleep(5)
        debug_print("\n🎯 Hoàn tất toàn bộ quy trình tạo âm thanh & tải file.")

    def run_audio_creation_flow(self, profile_name, driver, text_file_path, timeout=300, poll_interval=2):
        with open(text_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        chunks = smart_split_by_chars(content, max_chars=1000, soft_margin=200)
        debug_print(f"Số đoạn: {len(chunks)}")
        base_filename = os.path.splitext(os.path.basename(text_file_path))[0]
        debug_print(f"📄 Đang xử lý file: {base_filename}. Tổng {len(chunks)} đoạn.")
        total = len(chunks)
        for idx, chunk in enumerate(chunks, start=1):
            if self._batch_stop.is_set():
                debug_print("Batch dừng theo yêu cầu.")
                return
            self.update_source_row(text_file_path, status="Đang chạy", progress=f"{idx}/{total}")
            debug_print(f"--- Đang xử lý ({idx}/{total}): {os.path.basename(text_file_path)}")
            
            if not self.profile_widgets.get(profile_name, {}).get('script_on', False):
                debug_print(f"[{profile_name}] Stop requested → abort at chunk {idx}/{len(chunks)}")
                return

            js_insert = """
            const el = document.getElementById('gemini-main-textarea');
            if(!el) return false;
            const desc = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value');
            if (desc && typeof desc.set === 'function') desc.set.call(el, arguments[0]);
            else el.value = arguments[0];
            el.dispatchEvent(new Event('input', {bubbles:true}));
            el.dispatchEvent(new Event('change', {bubbles:true}));
            return true;
            """
            ok = driver.execute_script(js_insert, chunk)
            if not ok:
                debug_print("❌ Không tìm thấy textarea!")
                return

            try:
                time.sleep(5)
                start_btn = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "gemini-merge-btn")))
                driver.execute_script("arguments[0].click();", start_btn)
                debug_print("▶️  Đã click 'Ghép đoạn hội thoại'")
            except Exception as e:
                debug_print("❌ Không tìm thấy nút Ghép đoạn hội thoại:", e)
                return

            try:
                time.sleep(5)
                start_btn = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID, "gemini-start-queue-btn")))
                driver.execute_script("arguments[0].click();", start_btn)
                debug_print("▶️  Đã click 'Bắt đầu tạo âm thanh'")
            except Exception as e:
                debug_print("❌ Không tìm thấy nút tạo âm thanh:", e)
                return

            debug_print("⏳ Đang chờ tạo âm thanh...")
            t0 = time.time()
            last_status = ""
            while time.time() - t0 < timeout:
                state = driver.execute_script("return window.taskState || {};")
                status = state.get("status", "")
                msg = state.get("message", "")
                progress = state.get("progress", 0)

                if status != last_status:
                    debug_print(f"[{status.upper():>7}] {progress:3d}% - {msg}")
                    last_status = status

                dl_visible = driver.execute_script("""
                    var el = document.getElementById('gemini-download-merged-btn');
                    return el && el.offsetParent !== null;
                """)
                if status in ["done", "error", "skipped"] or dl_visible:
                    break
                time.sleep(poll_interval)

            filename = f"{base_filename}_{idx}.mp3"
            WebDriverWait(driver, 60).until(
                lambda d: d.execute_script("""
                    var a = document.getElementById('gemini-download-merged-btn');
                    return a && a.href && a.href.startsWith('blob:');
                """)
            )

            # Lấy href của thẻ <a id="gemini-download-merged-btn" ...>
            blob_url = driver.execute_script("""
                const a = document.getElementById('gemini-download-merged-btn');
                return a && a.href ? a.href : null;
            """)
            if not blob_url or not str(blob_url).startswith("blob:"):
                debug_print("❌ Không thấy blob href hợp lệ")
            else:
                # Tự đặt tên file đích
                dest_dir = self.get_download_dir(profile_name)  # thư mục tải tự chọn
                debug_print(f'dest_dir: {dest_dir}')
                dest_path = os.path.join(dest_dir, filename)
                debug_print(f'dest_path: {dest_path}')

                ok, msg = download_blob_to_path(driver, blob_url, dest_path)
                debug_print(("✅ " if ok else "❌ ") + msg)
            time.sleep(5)

        debug_print("\n🎯 Hoàn tất toàn bộ quy trình tạo âm thanh & tải file.")

    # --- Selenium helpers ---
    def _ensure_on_tab(self, driver, url_substr: str, timeout=5) -> bool:
        end = time.time() + timeout
        url_substr = (url_substr or "").lower()
        while time.time() < end:
            for h in driver.window_handles:
                try:
                    driver.switch_to.window(h)
                    if url_substr in driver.current_url.lower():
                        return True
                except Exception:
                    pass
            time.sleep(0.2)
        return False

    def _inject_helpers_js(self, driver):
        js = """
        return (function(){
        try {
            if (window.__mini_helpers_version >= 1) {
                return { ok: true, note: 'already' };
            }
            if (!window.__mini_setValue) {
                window.__mini_setValue = function(sel, text) {
                    try {
                        var el = document.querySelector(sel);
                        if (!el) return { ok:false, reason: 'not found: ' + sel };
                        var proto = null;
                        if (el.tagName === 'TEXTAREA') proto = HTMLTextAreaElement && HTMLTextAreaElement.prototype;
                        else if (el.tagName === 'INPUT') proto = HTMLInputElement && HTMLInputElement.prototype;
                        if (proto) {
                            var desc = Object.getOwnPropertyDescriptor(proto, 'value');
                            if (desc && typeof desc.set === 'function') { desc.set.call(el, text); }
                            else { el.value = text; }
                            el.dispatchEvent(new Event('input',  { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        } else {
                            el.textContent = text;
                            el.dispatchEvent(new Event('input',  { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                        }
                        return { ok:true };
                    } catch (e) { return { ok:false, reason: String(e) }; }
                };
            }
            window.__mini_helpers_version = 1;
            return { ok:true, note:'injected' };
        } catch (e) {
            return { ok:false, reason: String(e) };
        }
        })();
        """
        try:
            res = driver.execute_script(js)
            debug_print(f"[inject_helpers_js] result: {res}")
            return bool(res and res.get('ok'))
        except Exception as e:
            debug_print(f"[inject_helpers_js] Selenium JS error: {e}")
            return False
        
    def apply_language_setting(self, driver):
        """Chọn ngôn ngữ trên dropdown gemini-language-select theo self.language."""
        try:
            lang = getattr(self, 'language', 'Vietnamese')
            if not lang:
                return

            script = r"""
            (function(lang) {
                try {
                    var sel = document.getElementById('gemini-language-select');
                    if (!sel) return false;
                    for (var i = 0; i < sel.options.length; i++) {
                        if (sel.options[i].value === lang || sel.options[i].text === lang) {
                            sel.selectedIndex = i;
                            sel.dispatchEvent(new Event('change', { bubbles: true }));
                            return true;
                        }
                    }
                    return false;
                } catch (e) {
                    console.error('apply_language_setting error', e);
                    return false;
                }
            })(arguments[0]);
            """

            ok = driver.execute_script(script, lang)
            debug_print(f"[AUTO] Set language='{lang}' result={ok}")
        except Exception as e:
            debug_print(f"[AUTO] Lỗi set ngôn ngữ: {e}")

    def get_input_folder(self):
        """Lấy folder input từ auto_config (folder_path)."""
        try:
            cfg = getattr(self, 'auto_config', {}) or {}
            folder = (cfg.get('folder_path') or '').strip()
            if folder and os.path.isdir(folder):
                return folder
        except Exception as e:
            debug_print(f"[AUTO] get_input_folder error: {e}")
        return None

    def list_txt_files_level1(self, folder):
        """Liệt kê file .txt cấp 1 trong folder (không đệ quy)."""
        out = []
        try:
            for name in os.listdir(folder):
                p = os.path.join(folder, name)
                if os.path.isfile(p) and name.lower().endswith(".txt"):
                    out.append(p)
            # Sắp xếp alpha cho dễ đọc
            out.sort(key=lambda s: s.lower())
        except Exception as e:
            debug_print(f"[AUTO] list_txt_files_level1 error: {e}")
        return out

    def refresh_source_file_list(self):
        try:
            # Xoá Treeview cũ
            for iid in self.source_tree.get_children():
                self.source_tree.delete(iid)
            self.source_status.clear()

            folder = (getattr(self, "auto_config", {}) or {}).get("folder_path")
            if not folder or not os.path.isdir(folder):
                self._log_from_thread("⚠️ Chưa cấu hình 'Thư mục nguồn' trong AUTO.")
                return

            # Tạo sẵn RUN_DONE (để người dùng nhìn thấy trong thư mục)
            self.get_run_done_dir(folder)

            files = []
            for name in os.listdir(folder):
                fp = os.path.join(folder, name)
                # BỎ QUA thư mục RUN_DONE và các thư mục khác
                if os.path.isdir(fp):
                    continue
                if os.path.isfile(fp) and name.lower().endswith(".txt"):
                    files.append(fp)

            files.sort(key=lambda p: os.path.basename(p).lower())

            for fp in files:
                self.source_status[fp] = {"status": "Chờ", "progress": ""}
                self.source_tree.insert("", "end", iid=fp,
                                        values=(os.path.basename(fp), "Chờ", ""))

            self._log_from_thread(f"Đã nạp {len(files)} file .txt trong thư mục nguồn.")
        except Exception as e:
            self._log_from_thread(f"Lỗi refresh_source_file_list: {e}")

    
    def update_source_row(self, filepath, status=None, progress=None):
        try:
            if filepath not in self.source_status:
                return
            if status is not None:
                self.source_status[filepath]["status"] = status
            if progress is not None:
                self.source_status[filepath]["progress"] = progress

            name = os.path.basename(filepath)
            st = self.source_status[filepath]["status"]
            pg = self.source_status[filepath]["progress"]

            def _do():
                if self.source_tree.exists(filepath):
                    self.source_tree.item(filepath, values=(name, st, pg))
            self.after(0, _do)
        except Exception:
            pass
    
    def start_batch_on_sources(self):
        if self._batch_thread and self._batch_thread.is_alive():
            debug_print("Batch đang chạy...")
            return
        # yêu cầu phải có ít nhất 1 profile đang mở (để Bật Script hoạt động)
        prof = self.get_first_checked_profile_name()
        if not prof:
            self._log_from_thread("⚠️ Vui lòng tick chọn 1 profile ở danh sách bên trên.")
            return
        if prof not in self.running_browsers:
            self._log_from_thread("⚠️ Hãy khởi động profile đã chọn trước (nút 'Khởi động Profile đã chọn').")
            return
        
        ok, msg = self.upload_and_wait_status_cauhinh(prof, self.mp3_path, timeout=45)
        if ok:
            time.sleep(5)
            self._batch_stop.clear()
            self._batch_running = True
            if getattr(self, "btn_run_all", None):
                self.btn_run_all.configure(state="disabled")
            if getattr(self, "btn_stop_batch", None):
                self.btn_stop_batch.configure(state="normal")
            self._batch_thread = threading.Thread(target=self._batch_worker, args=(prof,), daemon=True)
            self._batch_thread.start()
            debug_print("▶️ Bắt đầu batch cho toàn bộ file .txt")
            
        else:
            debug_print(f"[{prof}] Upload/Cấu hình thất bại: {msg}")

    def stop_batch(self):
        self._batch_stop.set()
        self._batch_running = False
        debug_print("🛑 Đã yêu cầu dừng batch.")

        # UI: tắt Stop, cập nhật lại Run All theo trạng thái Script
        if hasattr(self, "btn_stop_batch"):
            self.btn_stop_batch.configure(state="disabled")
        self.update_run_all_state()


    def _batch_worker(self, profile_name):
        try:
            items = list(self.source_tree.get_children())
            total = len(items)
            done = 0
            for idx, iid in enumerate(items, 1):
                if self._batch_stop.is_set():
                    debug_print("Batch dừng theo yêu cầu.")
                    break

                filepath = iid  # mình set iid = full path
                ok = self._run_one_source_file(filepath, profile_name)

                done += 1
                if ok:
                    try:
                        # xác định folder input hiện tại
                        input_folder = self.get_input_folder() or os.path.dirname(filepath)
                        run_done_dir  = self.get_run_done_dir(input_folder)

                        base = os.path.basename(filepath)
                        dest = os.path.join(run_done_dir, base)

                        # nếu trùng tên thì thêm timestamp cho an toàn
                        if os.path.exists(dest):
                            ts = time.strftime("%Y%m%d_%H%M%S")
                            name, ext = os.path.splitext(base)
                            dest = os.path.join(run_done_dir, f"{name}_{ts}{ext}")

                        shutil.move(filepath, dest)
                        self._log_from_thread(f"✅ Đã chuyển '{base}' vào thư mục RUN_DONE.")
                        self.update_source_row(filepath, status="Done", progress="✅")

                    except Exception as e:
                        self._log_from_thread(f"⚠️ Không thể chuyển file vào RUN_DONE: {e}")
                else:
                    self.update_source_row(filepath, status="Lỗi", progress="✖")
        except Exception as e:
            debug_print(f"Lỗi batch: {e}")
        finally:
            self._batch_running = False
            # Cập nhật UI về lại trạng thái sau batch
            self.after(0, lambda: (
                hasattr(self, "btn_stop_batch") and self.btn_stop_batch.configure(state="disabled"),
                self.update_run_all_state()
            ))

    def get_first_checked_profile_name(self):
        for name, widgets in self.profile_widgets.items():
            try:
                if widgets["checkbox"].get() == 1:
                    return name
            except Exception:
                pass
        return None

    def _run_one_source_file(self, filepath, profile_name) -> bool:
        """
        Trả về True nếu xử lý ok, False nếu fail.
        Ở đây mình set self.text_path = filepath rồi gọi pipeline cũ.
        Nếu pipeline cũ là đồng bộ/blocking -> dùng trực tiếp.
        Nếu pipeline cũ chạy nền -> cần chờ tín hiệu hoàn thành (bạn có thể tự set event).
        """
        try:
            # 1) set đường dẫn file txt hiện tại
            self._hilight_running(filepath)
            self.text_path = filepath
            self.auto_create_voice(profile_name)
           
            return True
        except Exception as e:
            self._log_from_thread(f"Lỗi xử lý {os.path.basename(filepath)}: {e}")
            return False


    def _hilight_running(self, filepath):
        def _do():
            try:
                for iid in self.source_tree.get_children():
                    self.source_tree.item(iid, tags=())
                self.source_tree.item(filepath, tags=("running",))
                self.source_tree.tag_configure("running", background="#fff6e6")
            except Exception:
                pass
        self.after(0, _do)

    def update_run_all_state(self):
        """Bật 'Chạy tất cả' khi có ít nhất 1 profile đang bật Script và batch không chạy."""
        try:
            any_on = any(w.get('script_on', False) for w in self.profile_widgets.values())
            if getattr(self, "btn_run_all", None) is not None:
                if getattr(self, "_batch_running", False):
                    self.btn_run_all.configure(state="disabled")
                else:
                    self.btn_run_all.configure(state=("normal" if any_on else "disabled"))
        except Exception:
            pass
    def get_run_done_dir(self, base_folder: str) -> str:
        """
        Trả về đường dẫn thư mục RUN_DONE trong base_folder; tự tạo nếu chưa có.
        """
        try:
            run_done_dir = os.path.join(base_folder, "RUN_DONE")
            os.makedirs(run_done_dir, exist_ok=True)
            return run_done_dir
        except Exception as e:
            debug_print(f"[AUTO] get_run_done_dir error: {e}")
            # fallback: ngay trong base_folder
            return base_folder


if __name__ == '__main__':
    try:
        debug_print('[DEBUG] Khởi động ứng dụng...')
        # Thay thế SecurityManager bằng SecurityManagerStub
        security_manager = SecurityManagerStub() 
        debug_print('[DEBUG] SecurityManager đã tạo')
        app = App(security_manager)
        debug_print('[DEBUG] App đã tạo, bắt đầu mainloop...')
        app.mainloop()
    except Exception as e:
        debug_print(f'[ERROR] Lỗi khởi động ứng dụng: {e}')
        import traceback
        safe_traceback()
        input('Nhấn Enter để thoát...')





















