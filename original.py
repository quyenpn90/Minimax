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
import stat
import psutil
import shutil

def get_app_root_dir():
    """Lấy thư mục gốc của ứng dụng (hoạt động cho cả .py và .exe)"""  # inserted
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def debug_print(message):
    """In debug message cho cả .py và .exe mode"""  # inserted
    try:
        print(message)
    except UnicodeEncodeError:
        pass
    try:
        with open('debug.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()}: {message}\n')
    except:
        return None

def safe_traceback():
    """Chỉ in traceback khi KHÔNG chạy trong exe mode"""  # inserted
    if not IS_EXE_MODE:
        import traceback
        traceback.print_exc()

def get_resource_path(relative_path):
    """\n    Lấy đường dẫn tài nguyên chính xác, hoạt động cho cả chế độ .py và .exe.\n    PHIÊN BẢN ĐÃ SỬA LỖI\n    """  # inserted
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath('.')
    return os.path.join(base_path, relative_path)
GOOGLE_SHEET_CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vRSov25a2w4uqF68dJNz6U6ql2pOVoFImJLpE6HC_YUux6BzVVocI9R907rpJK4B3lr3u0fdwyi2lLl/pub?output=tsv'
DEFAULT_PASSWORD = '221504'
PROFILES_JSON_PATH = 'profiles.json'
PROFILES_DIR = 'profiles'
SCRIPT_PATH = get_resource_path('script.js')
MAX_PROFILES = 5
OPERA_PATH_FILE = 'brave_config.json'

class LicenseFileMonitor:
    def __init__(self, callback):
        self.callback = callback
        self.last_modified = None
        self.license_path = None
        self.running = False
        self.thread = None

    def start_monitoring(self):
        """Bắt đầu theo dõi file license"""  # inserted
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        debug_print('[MONITOR] Bắt đầu theo dõi file license...')

    def stop_monitoring(self):
        """Dừng theo dõi file license"""  # inserted
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        debug_print('[MONITOR] Dừng theo dõi file license...')

    def _monitor_loop(self):
        """Vòng lặp theo dõi file"""  # inserted
        while self.running:
            try:
                current_dir_license = os.path.join(os.path.abspath('.'), 'license.dat')
                if os.path.exists(current_dir_license):
                    mtime = os.path.getmtime(current_dir_license)
                    if self.last_modified is None:
                        self.last_modified = mtime
                        self.license_path = current_dir_license
                        debug_print(f'[MONITOR] Phát hiện file license: {current_dir_license}')
                    else:  # inserted
                        if mtime!= self.last_modified:
                            debug_print(f'[MONITOR] File license đã thay đổi: {current_dir_license}')
                            self.last_modified = mtime
                            self.license_path = current_dir_license
                            if self.callback:
                                self.callback()
                time.sleep(2)
            except Exception as e:
                debug_print(f'[MONITOR] Lỗi theo dõi file: {e}')
                time.sleep(5)

class SecurityManager:
    def get_appdata_path(self):
        """Lấy đường dẫn AppData\\Roaming an toàn cho cache"""  # inserted
        try:
            appdata = os.getenv('APPDATA')
            if appdata:
                appdata_dir = os.path.join(appdata, 'MinimaxTool')
                os.makedirs(appdata_dir, exist_ok=True)
                return appdata_dir
        except Exception:
            pass
        return os.path.abspath('.')

    def _filter_garbage(self, value):
        """Lọc các giá trị rác phổ biến"""  # inserted
        if not value:
            return ''
        value = str(value).strip()
        garbage_values = ['', 'none', 'null', '00000000', '00000000-0000-0000-0000-000000000000', 'ffffffff', 'ffffffff-ffff-ffff-ffff-ffffffffffff', 'to be filled by o.e.m.', 'to be filled by o.e.m', 'to be filled by oem', 'to be filled by o.e.m', 'system serial number', 'default string', 'default', 'unknown', 'n/a', 'na', 'not available', 'not specified', 'xxxxxxxx', 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx', '12345678', '12345678-1234-1234-1234-123456789012']
        if value.lower() in [g.lower() for g in garbage_values]:
            return ''
        if value.replace('0', '').replace('f', '').replace('-', '').replace(':', '').strip() == '':
            return ''
        if len(value) < 4:
            return ''
        return value

    def get_machine_id(self):
        """Hàm lấy mã máy ổn định - PHIÊN BẢN MỚI (Luôn kết hợp WMI + Fallback)"""  # inserted
        wmi_string = ''
        fallback_string = ''
        try:
            uuid = self._get_uuid()
            bios_serial = self._get_serial()
            cpu_id = self._get_cpu_id()
            mainboard_serial = self._get_mainboard_serial()
            disk_serial = self._get_disk_serial()
            wmi_string = f'UUID:{uuid}|BIOS:{bios_serial}|CPU:{cpu_id}|BOARD:{mainboard_serial}|DISK:{disk_serial}'
            debug_print(f'[MACHINE_ID] Chuỗi WMI: {wmi_string[:50]}...')
        except Exception as e:
            debug_print(f'[MACHINE_ID] Lỗi khi lấy WMI: {e}')
            wmi_string = 'UUID:|BIOS:|CPU:|BOARD:|DISK:'
        try:
            fallback_string = self._get_fallback_string()
            debug_print(f'[MACHINE_ID] Chuỗi Fallback: {fallback_string[:50]}...')
        except Exception as e:
            debug_print(f'[MACHINE_ID] Lỗi khi lấy Fallback: {e}')
            fallback_string = 'FALLBACK_V2:ERROR|ERROR|ERROR'
        try:
            combined_string = wmi_string + fallback_string
            debug_print(f'[MACHINE_ID] Chuỗi tổng hợp: {combined_string[:100]}...')
            hashed_id = hashlib.sha256(combined_string.encode()).hexdigest()
            debug_print(f'[MACHINE_ID] Hashed ID (gốc): {hashed_id[:16]}...')
            final_machine_id = f'{hashed_id}_mnmv_10'
            debug_print(f'[MACHINE_ID] ID cuối cùng (có suffix): {final_machine_id[:26]}...')
            return final_machine_id
        except Exception as e:
            debug_print(f'[MACHINE_ID] Lỗi nghiêm trọng khi tạo hash: {e}')
            return 'error_machine_mnmv_10'

    def _get_uuid(self):
        """Lấy UUID của máy"""  # inserted
        try:
            result = subprocess.check_output('wmic csproduct get uuid', shell=True, stderr=subprocess.DEVNULL).decode()
            uuid_str = result.split('\n')[1].strip()
            filtered_uuid = self._filter_garbage(uuid_str)
            if filtered_uuid:
                debug_print(f'[MACHINE_ID] UUID: {filtered_uuid[:16]}...')
                return filtered_uuid
            return ''
        except Exception as e:
            debug_print(f'[MACHINE_ID] Không thể lấy UUID: {e}')
            return ''

    def _get_serial(self):
        """Lấy Serial Number của máy"""  # inserted
        try:
            result = subprocess.check_output('wmic bios get serialnumber', shell=True, stderr=subprocess.DEVNULL).decode()
            serial_str = result.split('\n')[1].strip()
            filtered_serial = self._filter_garbage(serial_str)
            if filtered_serial:
                debug_print(f'[MACHINE_ID] Serial: {filtered_serial[:16]}...')
                return filtered_serial
            return ''
        except Exception as e:
            debug_print(f'[MACHINE_ID] Không thể lấy Serial: {e}')
            return ''

    def _get_cpu_id(self):
        """Lấy CPU ID của máy"""  # inserted
        try:
            result = subprocess.check_output('wmic cpu get processorid', shell=True, stderr=subprocess.DEVNULL).decode()
            cpu_str = result.split('\n')[1].strip()
            filtered_cpu = self._filter_garbage(cpu_str)
            if filtered_cpu:
                debug_print(f'[MACHINE_ID] CPU ID: {filtered_cpu[:16]}...')
                return filtered_cpu
            return ''
        except Exception as e:
            debug_print(f'[MACHINE_ID] Không thể lấy CPU ID: {e}')
            return ''

    def _get_mac_address(self):
        """Lấy MAC Address của máy"""  # inserted
        try:
            mac_str = ':'.join(['{:02x}'.format(uuid.getnode() >> i & 255) for i in range(0, 48, 8)][::(-1)])
            debug_print(f'[MACHINE_ID] MAC: {mac_str[:16]}...')
            return mac_str
        except Exception as e:
            debug_print(f'[MACHINE_ID] Không thể lấy MAC Address: {e}')
            return ''

    def _get_mainboard_serial(self):
        """Lấy Serial Number của Mainboard"""  # inserted
        try:
            result = subprocess.check_output('wmic baseboard get serialnumber', shell=True, stderr=subprocess.DEVNULL).decode()
            mainboard_str = result.split('\n')[1].strip()
            filtered_mainboard = self._filter_garbage(mainboard_str)
            if filtered_mainboard:
                debug_print(f'[MACHINE_ID] Mainboard Serial: {filtered_mainboard[:16]}...')
                return filtered_mainboard
            return ''
        except Exception as e:
            debug_print(f'[MACHINE_ID] Không thể lấy Mainboard Serial: {e}')
            return ''

    def _get_disk_serial(self):
        """Lấy Serial Number của ổ đĩa chính (thay thế MAC) với phương án dự phòng"""  # inserted
        try:
            result = subprocess.check_output('wmic diskdrive where index=0 get serialnumber', shell=True, stderr=subprocess.DEVNULL).decode()
            disk_str = result.split('\n')[1].strip()
            filtered_disk = self._filter_garbage(disk_str)
            if filtered_disk:
                debug_print(f'[MACHINE_ID] Disk Serial (Physical): {filtered_disk[:16]}...')
                return filtered_disk
            debug_print('[MACHINE_ID] Physical disk serial failed, trying volume serial...')
            result = subprocess.check_output('wmic logicaldisk where \"DeviceID=\'C:\'\" get VolumeSerialNumber', shell=True, stderr=subprocess.DEVNULL).decode()
            volume_str = result.split('\n')[1].strip()
            filtered_volume = self._filter_garbage(volume_str)
            if filtered_volume:
                debug_print(f'[MACHINE_ID] Disk Serial (Volume): {filtered_volume[:16]}...')
                return filtered_volume
            return ''
        except Exception as e:
            debug_print(f'[MACHINE_ID] Không thể lấy Disk Serial: {e}')
            return ''

    def _get_fallback_string(self):
        """Lấy chuỗi fallback (Phương án C) mà không tạo hash"""  # inserted
        try:
            debug_print('[MACHINE_ID] Lấy chuỗi Fallback - Không dùng WMI')
            disk_serial = self._get_fallback_disk_serial()
            computer_name = self._get_fallback_computer_name()
            cpu_id = self._get_fallback_cpu_id()
            fallback_string = f'FALLBACK_V2:{disk_serial}|{computer_name}|{cpu_id}'
            debug_print(f'[MACHINE_ID] Chuỗi dự phòng: {fallback_string[:50]}...')
            return fallback_string
        except Exception as e:
            debug_print(f'[MACHINE_ID] Lỗi trong Phương án C: {e}')
            return 'FALLBACK_V2:ERROR|ERROR|ERROR'

    def _get_fallback_machine_id(self):
        """Phương án C: Tạo mã máy dự phòng khi WMI hoàn toàn hỏng"""  # inserted
        try:
            debug_print('[MACHINE_ID] Kích hoạt Phương án C - Không dùng WMI')
            fallback_string = self._get_fallback_string()
            final_machine_id = hashlib.sha256(fallback_string.encode()).hexdigest()
            debug_print(f'[MACHINE_ID] ID cuối cùng (Fallback): {final_machine_id[:16]}...')
            return final_machine_id
        except Exception as e:
            debug_print(f'[MACHINE_ID] Lỗi trong Phương án C: {e}')
            return 'error_fallback'

    def _get_fallback_disk_serial(self):
        """Lấy Serial Number của ổ đĩa vật lý bằng PowerShell (mạnh và ổn định)"""  # inserted
        try:
            ps_script = '$csys = Get-WmiObject Win32_OperatingSystem | Select-Object -ExpandProperty SystemDrive; $drive = Get-Partition | Where-Object {$_.DriveLetter -eq $csys.Substring(0,1)} | Select-Object -ExpandProperty DiskNumber; Get-PhysicalDisk | Where-Object {$_.DeviceID -eq $drive} | Select-Object -ExpandProperty SerialNumber'
            result = subprocess.check_output(f'powershell -Command \"{ps_script}\"', shell=True, stderr=subprocess.DEVNULL).decode().strip()
            if result:
                filtered_serial = self._filter_garbage(result)
                if filtered_serial:
                    debug_print(f'[MACHINE_ID] Fallback Disk Serial (OS Physical): {filtered_serial[:16]}...')
                    return filtered_serial
        except Exception as e:
            debug_print(f'[MACHINE_ID] PowerShell lỗi, thử phương án cũ vol C:: {e}')
            try:
                result = subprocess.check_output('vol C:', shell=True, stderr=subprocess.DEVNULL).decode()
                for line in result.split('\n'):
                    if 'Volume Serial Number' in line:
                        parts = line.split()
                        for part in parts:
                            if '-' in part and len(part) == 9:
                                filtered_serial = self._filter_garbage(part)
                                if filtered_serial:
                                    debug_print(f'[MACHINE_ID] Fallback Disk Serial (vol C:): {filtered_serial}')
                                    return filtered_serial
                        else:  # inserted
                            break
            except Exception as e2:
                debug_print(f'[MACHINE_ID] Cả PowerShell và vol C: đều lỗi: {e2}')
        debug_print('[MACHINE_ID] Fallback Disk Serial (Default): empty')
        return ''

    def _get_fallback_computer_name(self):
        """Lấy tên máy tính từ biến môi trường COMPUTERNAME"""  # inserted
        try:
            computer_name = os.environ.get('COMPUTERNAME', '')
            if computer_name:
                filtered_name = self._filter_garbage(computer_name)
                if filtered_name:
                    debug_print(f'[MACHINE_ID] Fallback Computer Name: {filtered_name}')
                    return filtered_name
        except Exception as e:
            debug_print(f'[MACHINE_ID] Không thể lấy Fallback Computer Name: {e}')
        debug_print('[MACHINE_ID] Fallback Computer Name (Default): empty')
        return ''

    def _get_fallback_cpu_id(self):
        """Lấy mã CPU từ biến môi trường PROCESSOR_IDENTIFIER"""  # inserted
        try:
            cpu_id = os.environ.get('PROCESSOR_IDENTIFIER', '')
            if cpu_id:
                filtered_cpu = self._filter_garbage(cpu_id)
                if filtered_cpu:
                    debug_print(f'[MACHINE_ID] Fallback CPU ID: {filtered_cpu[:20]}...')
                    return filtered_cpu
        except Exception as e:
            debug_print(f'[MACHINE_ID] Không thể lấy Fallback CPU ID: {e}')
        debug_print('[MACHINE_ID] Fallback CPU ID (Default): empty')
        return ''

class App(customtkinter.CTk):
    def __init__(self, security_manager):
        try:
            debug_print('[DEBUG] Khởi tạo App...')
            super().__init__()
            self.sm = security_manager
            self.is_authenticated = False
            self.profiles = {}
            self.running_browsers = {}
            self.profile_widgets = {}
            self.my_machine_id = ''
            self.api_url = 'https://script.google.com/macros/s/AKfycbxSBnm8_y7AMpEgcLWfhfB6WFMYjMelc2gkA8coZHyB7g3UpdvElyAnyTpegXdaSco/exec'
            self.current_quota = 0
            self.quota_lock = threading.Lock()
            self.license_monitor = LicenseFileMonitor(self.reload_license)
            debug_print('[DEBUG] Thiết lập giao diện...')
            self.title('Profile Manager & Browser Tool (Secured & Full Feature + Enhanced Anti-F12 Multi-Layer Protection)')
            self.geometry('800x600')
            self.protocol('WM_DELETE_WINDOW', self.on_closing)
        except Exception as e:
            debug_print(f'[ERROR] Lỗi khởi tạo App: {e}')
            import traceback
            safe_traceback()
            raise
        self.security_frame = customtkinter.CTkFrame(self, fg_color='transparent')
        self.security_frame.pack(pady=10, padx=10, fill='x')
        self.auth_status_label = customtkinter.CTkLabel(self.security_frame, text='Trạng thái: Đang kiểm tra...', text_color='orange')
        self.auth_status_label.pack(side='left')
        self.license_created_label = customtkinter.CTkLabel(self.security_frame, text='', text_color='gray', font=customtkinter.CTkFont(size=10))
        self.license_created_label.pack(side='left', padx=(10, 0))
        self.trial_status_label = customtkinter.CTkLabel(self.security_frame, text='', text_color='blue', font=customtkinter.CTkFont(size=10))
        self.trial_status_label.pack(side='left', padx=(10, 0))
        button_frame = customtkinter.CTkFrame(self.security_frame, fg_color='transparent')
        button_frame.pack(side='right')
        self.delete_id_button = customtkinter.CTkButton(button_frame, text='Xóa ID Máy', command=self.prompt_delete_id)
        self.delete_id_button.pack(side='left', padx=5)
        self.main_content = customtkinter.CTkFrame(self, fg_color='transparent')
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(1, weight=1)
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
        control_frame = customtkinter.CTkFrame(self.main_content)
        control_frame.grid(row=1, column=0, padx=0, pady=(0, 5), sticky='ew')
        add_profile_button = customtkinter.CTkButton(control_frame, text='➕ Thêm Profile', command=self.add_profile)
        add_profile_button.pack(side='left', padx=5, pady=5)
        delete_profile_button = customtkinter.CTkButton(control_frame, text='🗑️ Xóa Profile', command=self.delete_profile, fg_color='#D32F2F', hover_color='#B71C1C')
        delete_profile_button.pack(side='left', padx=5, pady=5)
        start_button = customtkinter.CTkButton(control_frame, text='▶️ Khởi động Profile đã chọn', command=self.start_selected_profiles)
        start_button.pack(side='left', padx=5, pady=5)
        stop_all_button = customtkinter.CTkButton(control_frame, text='⏹️ Dừng tất cả', command=self.stop_all_browsers, fg_color='#D32F2F', hover_color='#B71C1C')
        stop_all_button.pack(side='left', padx=5, pady=5)
        reset_violations_button = customtkinter.CTkButton(control_frame, text='🔓 Reset Vi Phạm', command=self.reset_violations, fg_color='#FF9800', hover_color='#F57C00')
        reset_violations_button.pack(side='left', padx=5, pady=5)
        audio_sync_button = customtkinter.CTkButton(control_frame, text='🎵 SRT (Audio-SRT Sync)', command=self.open_audio_srt_sync, fg_color='#673AB7', hover_color='#5E35B1')
        audio_sync_button.pack(side='left', padx=10, pady=5)
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.main_content, label_text='Danh sách Profile')
        self.scrollable_frame.grid(row=2, column=0, padx=0, pady=5, sticky='nsew')
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        self.main_status_label = customtkinter.CTkLabel(self.main_content, text='Sẵn sàng')
        self.main_status_label.grid(row=3, column=0, padx=0, pady=(5, 0), sticky='w')
        security_notice = customtkinter.CTkLabel(self.main_content, text='🔒 Hệ thống bảo mật nâng cao: Multi-Layer Protection - Chống F12, DevTools, Console, Copy/Paste, Screenshot - Lần 1: Cảnh báo, Lần 2: Khóa 24h', text_color='#FF9800', font=customtkinter.CTkFont(size=12, weight='bold'))
        security_notice.grid(row=4, column=0, padx=0, pady=(5, 0), sticky='w')
        try:
            debug_print('[DEBUG] Thiết lập timer...')
            self.after(100, self.run_online_license_check)
            debug_print('[DEBUG] Khởi tạo App hoàn tất!')
        except Exception as e:
            debug_print(f'[ERROR] Lỗi thiết lập timer: {e}')
            import traceback
            safe_traceback()

    def start_license_monitor(self):
        """Khởi động license monitor"""  # inserted
        try:
            self.license_monitor.start_monitoring()
            debug_print('[DEBUG] License monitor đã khởi động')
        except Exception as e:
            debug_print(f'[ERROR] Lỗi khởi động license monitor: {e}')

    def reload_license(self):
        """Reload license khi file thay đổi"""  # inserted
        try:
            debug_print('[MONITOR] Reloading license...')
            self.after(100, self.check_license_immediately)
            self.after(200, self.check_trial_expired_immediately)
            debug_print('[MONITOR] License reloaded!')
        except Exception as e:
            debug_print(f'[ERROR] Lỗi reload license: {e}')

    def cleanup_trial_files(self):
        """Dọn dẹp các file trial lỗi"""  # inserted
        try:
            if os.path.exists(TRIAL_STATE_FILE):
                try:
                    with open(TRIAL_STATE_FILE, 'r', encoding='utf-8') as f:
                        data = f.read().strip()
                        if not data:
                            os.remove(TRIAL_STATE_FILE)
                            debug_print('Đã xóa file trial_state.dat rỗng')
                            return
                        json.loads(data)
                        debug_print('File trial_state.dat hợp lệ')
                except Exception as e:
                    debug_print(f'File trial_state.dat lỗi: {e}')
                    try:
                        os.remove(TRIAL_STATE_FILE)
                        debug_print('Đã xóa file trial_state.dat lỗi')
                    except:
                        return
        except Exception as e:
            debug_print(f'Lỗi dọn dẹp trial files: {e}')

    def is_first_run(self):
        """Kiểm tra có phải lần đầu chạy thật sự không"""  # inserted
        try:
            if os.path.exists('admin_reset.dat'):
                debug_print('[SECURITY] File admin_reset.dat tồn tại - admin đã xóa ID máy')
                return True
            if os.path.exists(HIDDEN_AUTH_FILE):
                debug_print('[SECURITY] File ẩn tồn tại - không phải lần đầu chạy')
                return False
            if os.path.exists(LOCAL_KEY_FILE):
                debug_print('[SECURITY] File local tồn tại - không phải lần đầu chạy')
                return False
            marker_files = ['first_run_marker.dat', 'tool_initialized.dat', 'machine_verified.dat']
            for marker_file in marker_files:
                if os.path.exists(marker_file):
                    debug_print(f'[SECURITY] File marker {marker_file} tồn tại - không phải lần đầu chạy')
                    return False
            else:  # inserted
                license_files = ['license.dat', 'key_activated_*.dat', 'trial_state.dat']
                for license_file in license_files:
                    if '*' in license_file:
                        import glob
                        matching_files = glob.glob(license_file)
                        if matching_files:
                            debug_print(f'[SECURITY] File license {license_file} tồn tại - không phải lần đầu chạy')
                            return False
                    else:  # inserted
                        if os.path.exists(license_file):
                            debug_print(f'[SECURITY] File license {license_file} tồn tại - không phải lần đầu chạy')
                            return False
                else:  # inserted
                    if os.path.exists(HIDDEN_AUTH_DIR):
                        debug_print('[SECURITY] Thư mục ẩn tồn tại - không phải lần đầu chạy')
                        return False
                    debug_print('[SECURITY] Không tìm thấy file nào - đây là lần đầu chạy thật sự')
                    return True
        except Exception as e:
            debug_print(f'[SECURITY] Lỗi kiểm tra lần đầu chạy: {e}')
            return False

    def run_security_check(self):
        """Kiểm tra bảo mật - chỉ xác thực một lần, ghi nhớ máy"""  # inserted
        try:
            debug_print('[SECURITY] Bắt đầu kiểm tra bảo mật...')
            if self.sm.verify_license():
                debug_print('[SECURITY] License hợp lệ - cho phép sử dụng')
                self.authenticate_success()
            else:  # inserted
                debug_print('[SECURITY] License không hợp lệ - kiểm tra trường hợp...')
                if self.is_first_run():
                    debug_print('[SECURITY] Lần đầu chạy thật sự hoặc admin đã reset - tạo license mới')
                    self.sm.create_license()
                    if self.sm.verify_license():
                        debug_print('[SECURITY] Đã tạo license thành công')
                        self.authenticate_success()
                    else:  # inserted
                        debug_print('[SECURITY] Lỗi tạo license')
                        self.authenticate_fail('Lỗi khi tạo file bản quyền.')
                else:  # inserted
                    debug_print('[SECURITY] Phát hiện chuyển máy hoặc tool đã được sử dụng trước đó')
                    self.authenticate_fail('PHÁT HIỆN CHUYỂN MÁY HOẶC TOOL ĐÃ ĐƯỢC SỬ DỤNG!')
                    self.prompt_delete_id()
        except Exception as e:
            debug_print(f'[SECURITY] Lỗi kiểm tra bảo mật: {e}')
            self.authenticate_fail('Lỗi kiểm tra bảo mật')

    def authenticate_success(self):
        self.is_authenticated = True
        self.load_profiles()

    def check_and_show_main_interface(self):
        """Kiểm tra và hiển thị giao diện chính nếu cần"""  # inserted
        try:
            trial_info = self.sm.check_trial_status()
            if trial_info['has_trial']:
                if 'remaining' in trial_info and trial_info['remaining'] > 0:
                    self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                    return
                if 'expired' in trial_info and trial_info['expired']:
                    license_info = self.sm.check_license_security()
                    if not license_info['expired']:
                        self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                        return
            if not trial_info['has_trial']:
                license_info = self.sm.check_license_security()
                if not license_info['expired']:
                    self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
        except Exception as e:
            debug_print(f'Lỗi kiểm tra hiển thị giao diện: {e}')

    def authenticate_fail(self, message):
        self.is_authenticated = False
        self.auth_status_label.configure(text=f'Trạng thái: {message}', text_color='red')

    def run_online_license_check(self):
        """Hàm kiểm tra license online MỚI (Tích hợp Quota)."""  # inserted
        try:
            my_machine_id = self.sm.get_machine_id()
            self.my_machine_id = my_machine_id
        except Exception as e:
            self.authenticate_fail(f'Lỗi nghiêm trọng: Không thể lấy Mã máy.\n{e}')
            messagebox.showerror('Lỗi Mã Máy', f'Không thể lấy Mã máy: {e}')
            self.destroy()
            return None
        try:
            headers = {'Cache-Control': 'no-cache', 'Pragma': 'no-cache'}
            params = {'id': my_machine_id}
            debug_print(f'[LICENSE] Đang gọi API: {self.api_url} với ID: {my_machine_id[:10]}...')
            response = requests.get(self.api_url, headers=headers, params=params, timeout=15)
            if response.status_code!= 200:
                msg = f'Lỗi: Không thể kết nối máy chủ License (Code: {response.status_code}).'
                self.authenticate_fail(msg)
                messagebox.showerror('Lỗi Mạng', 'Không thể kết nối máy chủ License. Vui lòng kiểm tra Internet.')
                self.destroy()
                return
            data = response.json()
            debug_print(f'[LICENSE] Nhận được dữ liệu: {data}')
            if 'error' in data:
                self.authenticate_fail(f"Máy chưa được cấp phép (Lỗi: {data['error']}).")
                self.show_machine_id_dialog(my_machine_id)
                self.destroy()
                return
            status = data.get('status', 'BANNED').strip().upper()
            if status == 'BANNED' or status!= 'ACTIVE':
                self.authenticate_fail('License của bạn đã bị Admin khóa hoặc không hoạt động!')
                messagebox.showerror('Đã Khóa', 'License của bạn đã bị Admin khóa. Vui lòng liên hệ hỗ trợ.')
                self.destroy()
                return
            expiry_date_str = data.get('expiry_date')
            expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            today = datetime.date.today()
            if expiry_date < today:
                self.authenticate_fail(f'License đã hết hạn ngày: {expiry_date_str}')
                messagebox.showerror('Hết Hạn', f'License của bạn đã hết hạn vào ngày {expiry_date_str}.')
                self.destroy()
                return
            server_quota = int(data.get('remaining_chars', 0))
            local_quota = (-2)
            try:
                cache_file = os.path.join(self.sm.get_appdata_path(), 'quota_cache.json')
                if os.path.exists(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                        if cache_data.get('machine_id') == self.my_machine_id:
                            local_quota = cache_data.get('remaining_quota', (-2))
            except Exception as e:
                debug_print(f'[QUOTA] Lỗi đọc cache cục bộ: {e}')
            with self.quota_lock:
                if server_quota == (-1):
                    self.current_quota = (-1)
                else:  # inserted
                    if local_quota!= (-2):
                        self.current_quota = min(server_quota, local_quota)
                    else:  # inserted
                        self.current_quota = server_quota
            debug_print(f'[QUOTA] Server: {server_quota}, Local: {local_quota}, Đã chốt: {self.current_quota} ký tự')
            days_left = (expiry_date - today).days
            quota_display = 'Không giới hạn' if self.current_quota == (-1) else f'{self.current_quota:,}'
            self.auth_status_label.configure(text=f'License: Còn {days_left} ngày | Ký tự: {quota_display}', text_color='green')
            self.authenticate_success()
            self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
        except requests.exceptions.RequestException:
            self.authenticate_fail('Không có kết nối mạng.')
            messagebox.showerror('Lỗi Mạng', 'Không có kết nối mạng. Vui lòng kiểm tra Internet và mở lại tool.')
            self.destroy()
        except Exception as e:
            debug_print(f'[LICENSE ERROR] {e}')
            safe_traceback()
            self.authenticate_fail(f'Lỗi dữ liệu License: {e}')
            messagebox.showerror('Lỗi Dữ Liệu', f'Phát hiện lỗi dữ liệu License từ máy chủ. Vui lòng báo Admin: {e}')
            self.destroy()

    def show_machine_id_dialog(self, machine_id):
        """\n        Hiển thị dialog tùy chỉnh để báo lỗi Mã máy và cho phép sao chép.\n        """  # inserted
        dialog = customtkinter.CTkToplevel(self)
        dialog.title('Chưa Kích Hoạt')
        dialog.geometry('500x200')
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(False, False)
        msg = 'Máy chưa được cấp phép.\n\nVui lòng copy và gửi Mã máy này cho Admin:'
        label = customtkinter.CTkLabel(dialog, text=msg, font=customtkinter.CTkFont(size=14))
        label.pack(pady=10, padx=20)
        id_entry = customtkinter.CTkEntry(dialog, width=400, font=customtkinter.CTkFont(size=12))
        id_entry.insert(0, machine_id)
        id_entry.configure(state='readonly')
        id_entry.pack(pady=5, padx=20)

        def copy_id_to_clipboard():
            try:
                self.clipboard_clear()
                self.clipboard_append(machine_id)
                copy_btn.configure(text='Đã sao chép! ✅', fg_color='green')
                debug_print(f'Đã sao chép: {machine_id}')
            except Exception as e:
                debug_print(f'Lỗi sao chép: {e}')
                copy_btn.configure(text='Lỗi sao chép')
        copy_btn = customtkinter.CTkButton(dialog, text='Sao chép Mã máy', command=copy_id_to_clipboard)
        copy_btn.pack(pady=10)
        ok_btn = customtkinter.CTkButton(dialog, text='Đã hiểu (Thoát)', command=dialog.destroy, fg_color='gray')
        ok_btn.pack(pady=5)
        dialog.wait_window()

    def api_report_usage(self, chars_used):
        """Báo cáo \"âm thầm\" số ký tự đã dùng lên server (chạy trong Thread)."""  # inserted
        try:
            payload = {'machine_id': self.my_machine_id, 'chars_used': int(chars_used)}
            requests.post(self.api_url, json=payload, timeout=10)
            debug_print(f'[QUOTA] Đã báo cáo {chars_used} ký tự lên server.')
        except Exception as e:
            debug_print(f'[QUOTA] Lỗi báo cáo server (không nghiêm trọng): {e}')

    def prompt_activation(self):
        password = self.create_password_dialog('Phát hiện vi phạm. Vui lòng nhập mật khẩu để kích hoạt lại:', 'Kích hoạt')
        if password == DEFAULT_PASSWORD:
            self.sm.create_license()
            self.run_security_check()
        else:  # inserted
            self.auth_status_label.configure(text='Trạng thái: Sai mật khẩu. Vui lòng thoát.', text_color='red')

    def prompt_delete_id(self):
        """Xử lý trường hợp chuyển máy - yêu cầu nhập mật khẩu để xóa ID máy cũ"""  # inserted
        password = self.create_password_dialog('Phát hiện chuyển máy!\n\nNhập mật khẩu quản trị để xóa ID máy cũ và nhận diện máy mới:', 'Xóa ID Máy Cũ')
        if password == DEFAULT_PASSWORD:
            debug_print('[ADMIN] Admin đã xác thực - xóa ID máy cũ')
            self.sm.delete_license()
            self.sm.create_license()
            if self.sm.verify_license():
                debug_print('[ADMIN] Đã tạo license mới thành công cho máy mới')
                self.authenticate_success()
            else:  # inserted
                debug_print('[ADMIN] Lỗi tạo license mới')
                self.authenticate_fail('Lỗi tạo license cho máy mới')
        else:  # inserted
            debug_print('[ADMIN] Sai mật khẩu admin')
            self.auth_status_label.configure(text='Trạng thái: Sai mật khẩu admin. Tool bị khóa.', text_color='red')

    def check_trial_and_license_status(self):
        """Kiểm tra trạng thái dùng thử và license - LOGIC TUẦN TỰ"""  # inserted
        try:
            trial_info = self.sm.check_trial_status()
            debug_print(f'[DEBUG] Trial info: {trial_info}')
            if trial_info['has_trial']:
                if 'expired' in trial_info and trial_info['expired']:
                    self.trial_status_label.configure(text='Dùng thử: Đã hết hạn', text_color='red')
                    license_info = self.sm.check_license_security()
                    if license_info.get('need_key'):
                        self.main_content.pack_forget()
                        debug_print('[SECURITY] Trial hết hạn - license cần nhập key')
                        self.show_license_expired_dialog(license_info['message'], None)
                    else:  # inserted
                        if license_info.get('valid'):
                            days_left = license_info.get('days_left', 0)
                            expiry_date = license_info.get('expiry_date', '')
                            today = license_info.get('today', '')
                            self.license_status_label.configure(text=f'License: Key còn {days_left} ngày', text_color='green')
                            self.license_created_label.configure(text=f'Hết hạn: {expiry_date} | Hôm nay: {today}')
                            if self.is_authenticated:
                                self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                        else:  # inserted
                            self.main_content.pack_forget()
                            debug_print('[SECURITY] Trial hết hạn - license không hợp lệ')
                            self.show_license_expired_dialog(license_info.get('message', 'Lỗi kiểm tra license'), None)
                else:  # inserted
                    if 'remaining' in trial_info:
                        remaining = trial_info['remaining']
                        if remaining <= 0:
                            self.trial_status_label.configure(text='Dùng thử: Đã hết hạn', text_color='red')
                            license_info = self.sm.check_license_security()
                            if license_info.get('need_key'):
                                self.main_content.pack_forget()
                                debug_print('[SECURITY] Trial hết hạn (remaining <= 0) - license cần nhập key')
                                self.show_license_expired_dialog(license_info['message'], None)
                            else:  # inserted
                                if license_info.get('valid'):
                                    days_left = license_info.get('days_left', 0)
                                    expiry_date = license_info.get('expiry_date', '')
                                    today = license_info.get('today', '')
                                    self.license_status_label.configure(text=f'License: Key còn {days_left} ngày', text_color='green')
                                    self.license_created_label.configure(text=f'Hết hạn: {expiry_date} | Hôm nay: {today}')
                                    if self.is_authenticated:
                                        self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                                else:  # inserted
                                    self.main_content.pack_forget()
                                    debug_print('[SECURITY] Trial hết hạn (remaining <= 0) - license không hợp lệ')
                                    self.show_license_expired_dialog(license_info.get('message', 'Lỗi kiểm tra license'), None)
                        else:  # inserted
                            if remaining <= 5:
                                self.trial_status_label.configure(text=f'Dùng thử: Còn {remaining} phút', text_color='red')
                                self.license_status_label.configure(text='License: Chưa kích hoạt', text_color='gray')
                                self.license_created_label.configure(text='')
                                if self.is_authenticated:
                                    self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                            else:  # inserted
                                self.trial_status_label.configure(text=f'Dùng thử: Còn {remaining} phút', text_color='blue')
                                self.license_status_label.configure(text='License: Chưa kích hoạt', text_color='gray')
                                self.license_created_label.configure(text='')
                                if self.is_authenticated:
                                    self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                    else:  # inserted
                        self.trial_status_label.configure(text='Dùng thử: Chưa kích hoạt', text_color='orange')
                        self.license_status_label.configure(text='License: Chưa kích hoạt', text_color='gray')
                        self.license_created_label.configure(text='')
                        if self.is_authenticated and (not self.is_trial_activated()):
                            self.main_content.pack_forget()
                            debug_print('[DEBUG] Hiển thị dialog kích hoạt trial TRƯỚC - KHÔNG kiểm tra license')
                            self.show_trial_activation_dialog(trial_info['trial_key'], trial_info['duration'])
                        else:  # inserted
                            if self.is_authenticated and self.is_trial_activated():
                                self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
            else:  # inserted
                if 'expired' in trial_info and trial_info['expired']:
                    self.trial_status_label.configure(text='Dùng thử: Đã hết hạn', text_color='red')
                    license_info = self.sm.check_license_security()
                    if license_info.get('need_key'):
                        self.main_content.pack_forget()
                        debug_print('[SECURITY] Trial hết hạn (has_trial=False) - license cũng hết hạn')
                        self.show_license_expired_dialog(license_info['message'], None)
                    else:  # inserted
                        days_left = license_info.get('days_left', 0)
                        expiry_date = license_info.get('expiry_date', '')
                        today = license_info.get('today', '')
                        self.license_status_label.configure(text=f'License: Key còn {days_left} ngày', text_color='green')
                        self.license_created_label.configure(text=f'Hết hạn: {expiry_date} | Hôm nay: {today}')
                        if self.is_authenticated:
                            self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                else:  # inserted
                    self.trial_status_label.configure(text='', text_color='blue')
                    license_info = self.sm.check_license_security()
                    if license_info.get('valid'):
                        days_left = license_info.get('days_left', 0)
                        expiry_date = license_info.get('expiry_date', '')
                        today = license_info.get('today', '')
                        self.license_status_label.configure(text=f'License: Key còn {days_left} ngày', text_color='green')
                        self.license_created_label.configure(text=f'Hết hạn: {expiry_date} | Hôm nay: {today}')
                        if self.is_authenticated:
                            self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                    else:  # inserted
                        if license_info.get('need_key'):
                            self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='red')
                            self.license_created_label.configure(text='')
                            self.main_content.pack_forget()
                            self.show_license_expired_dialog(license_info['message'], None)
        except Exception as e:
            self.trial_status_label.configure(text='Dùng thử: Lỗi kiểm tra', text_color='red')
            self.license_status_label.configure(text='License: Lỗi kiểm tra', text_color='red')
            self.license_created_label.configure(text='')

    def check_license_on_startup(self):
        """Kiểm tra license ngay khi khởi động - CHỈ CẬP NHẬT GUI"""  # inserted
        try:
            license_info = self.sm.check_license_security()
            if license_info.get('need_key'):
                debug_print(f"[SECURITY] Cần nhập key ngay khi khởi động: {license_info['message']}")
                self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='red')
                self.license_created_label.configure(text='')
            else:  # inserted
                if license_info.get('valid'):
                    days_left = license_info.get('days_left', 0)
                    expiry_date = license_info.get('expiry_date', '')
                    today = license_info.get('today', '')
                    self.license_status_label.configure(text=f'License: Key còn {days_left} ngày', text_color='green')
                    self.license_created_label.configure(text=f'Hết hạn: {expiry_date} | Hôm nay: {today}')
        except Exception as e:
            debug_print(f'[SECURITY] Lỗi kiểm tra license khi khởi động: {e}')

    def open_audio_srt_sync(self):
        """Mở cửa sổ chức năng Audio-SRT Sync (Nhạc)."""  # inserted
        try:
            win = customtkinter.CTkToplevel(self)
            win.title('Audio-SRT Sync Tool (Nhạc)')
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
                            else:  # inserted
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
                            else:  # inserted
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
                            else:  # inserted
                                if gap_duration_ms < (-5):
                                    log_message(f'CẢNH BÁO: [{i}/{total_subs}] SRT chồng chéo! (overlap {abs(gap_duration_ms)}ms)')
                                    if len(final_audio) >= abs(gap_duration_ms):
                                        final_audio = final_audio[:gap_duration_ms]
                                        log_message(f'    -> Đã cắt bớt {abs(gap_duration_ms)}ms của audio trước.')
                                    else:  # inserted
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
                            else:  # inserted
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
                                    else:  # inserted
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
                                            else:  # inserted
                                                if processed_duration < required_duration_ms - 20:
                                                    pad_ms = required_duration_ms - processed_duration
                                                    log_message(f'    -> Tinh chỉnh: Bù thêm {pad_ms}ms')
                                                    processed_segment += AudioSegment.silent(duration=pad_ms)
                                        else:  # inserted
                                            padding_ms = required_duration_ms - actual_duration_ms
                                            log_message(f'    -> Ngắn ({actual_duration_ms}ms < {required_duration_ms}ms). Thêm {padding_ms}ms im lặng')
                                            processed_segment = audio_segment + AudioSegment.silent(duration=padding_ms)
                                    if processed_segment is not None:
                                        final_audio += processed_segment
                                    else:  # inserted
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
                    finally:  # inserted
                        progress.stop()
                progress.start()
                threading.Thread(target=worker, daemon=True).start()
            start_btn = customtkinter.CTkButton(frame, text='Bắt đầu Xử lý', command=process)
            start_btn.grid(row=4, column=0, columnspan=3, pady=10)
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
        """Kiểm tra license ngay lập tức - CHỈ CẬP NHẬT GUI"""  # inserted
        try:
            restart_flag_file = os.path.join(os.path.abspath('.'), 'restart_flag.tmp')
            if os.path.exists(restart_flag_file):
                debug_print('[DEBUG] Phát hiện flag restart, delay kiểm tra license...')
                try:
                    os.remove(restart_flag_file)
                except:
                    pass
                self.after(2000, self.check_license_immediately)
            else:  # inserted
                debug_print('[SECURITY] Kiểm tra license ngay lập tức...')
                license_info = self.sm.check_license_security()
                if license_info.get('need_key'):
                    debug_print(f"[SECURITY] Cần nhập key - cập nhật GUI: {license_info['message']}")
                    self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='red')
                    self.license_created_label.configure(text='')
                else:  # inserted
                    if license_info.get('valid'):
                        debug_print(f"[SECURITY] License hợp lệ: {license_info['message']}")
                        days_left = license_info.get('days_left', 0)
                        expiry_date = license_info.get('expiry_date', '')
                        today = license_info.get('today', '')
                        if days_left <= 7:
                            self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='orange')
                        else:  # inserted
                            self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='green')
                        self.license_created_label.configure(text=f'Hết hạn: {expiry_date} | Hôm nay: {today}')
                        if self.is_authenticated:
                            self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                    else:  # inserted
                        debug_print(f"[SECURITY] License không hợp lệ: {license_info.get('message', 'Lỗi')}")
                        self.license_status_label.configure(text=f"License: {license_info.get('message', 'Lỗi')}", text_color='red')
                        self.license_created_label.configure(text='')
        except Exception as e:
            debug_print(f'[SECURITY] Lỗi kiểm tra license ngay lập tức: {e}')
            import traceback
            safe_traceback()
            self.license_status_label.configure(text='License: Lỗi kiểm tra', text_color='red')
            self.license_created_label.configure(text='')

    def check_trial_expired_immediately(self):
        """Kiểm tra trial hết hạn ngay lập tức và chặn tool"""  # inserted
        try:
            debug_print('[SECURITY] Kiểm tra trial hết hạn ngay lập tức...')
            trial_info = self.sm.check_trial_status()
            if trial_info.get('expired'):
                debug_print(f"[SECURITY] Trial hết hạn - kiểm tra license: {trial_info['message']}")
                license_info = self.sm.check_license_security()
                if license_info.get('need_key'):
                    debug_print(f"[SECURITY] License cần nhập key - chặn tool: {license_info['message']}")
                    self.main_content.pack_forget()
                    self.show_license_expired_dialog(license_info['message'], None)
                else:  # inserted
                    if license_info.get('valid'):
                        debug_print(f"[SECURITY] License hợp lệ - không chặn tool: {license_info['message']}")
                        days_left = license_info.get('days_left', 0)
                        if days_left <= 7:
                            self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='orange')
                        else:  # inserted
                            self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='green')
                        self.license_created_label.configure(text=f'Key còn {days_left} ngày')
                        if self.is_authenticated:
                            self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                    else:  # inserted
                        debug_print(f"[SECURITY] License không hợp lệ - chặn tool: {license_info.get('message', 'Lỗi')}")
                        self.main_content.pack_forget()
                        self.show_license_expired_dialog(license_info.get('message', 'Lỗi kiểm tra license'), None)
            else:  # inserted
                debug_print(f"[SECURITY] Trial hợp lệ: {trial_info.get('message', 'OK')}")
                if trial_info['has_trial']:
                    if 'remaining' in trial_info:
                        remaining = trial_info['remaining']
                        if remaining <= 5:
                            self.trial_status_label.configure(text=f'Dùng thử: Còn {remaining} phút', text_color='red')
                        else:  # inserted
                            self.trial_status_label.configure(text=f'Dùng thử: Còn {remaining} phút', text_color='blue')
                    else:  # inserted
                        self.trial_status_label.configure(text='Dùng thử: Chưa kích hoạt', text_color='orange')
                else:  # inserted
                    self.trial_status_label.configure(text='', text_color='blue')
        except Exception as e:
            debug_print(f'[SECURITY] Lỗi kiểm tra trial hết hạn ngay lập tức: {e}')

    def check_license_status(self):
        """Kiểm tra trạng thái license - LOGIC MỚI"""  # inserted
        try:
            license_info = self.sm.check_license_security()
            if license_info.get('need_key'):
                self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='red')
                self.license_created_label.configure(text='')
                debug_print(f"[SECURITY] Cần nhập key: {license_info['message']}")
                self.show_license_expired_dialog(license_info['message'], None)
            else:  # inserted
                if license_info.get('valid'):
                    days_left = license_info.get('days_left', 0)
                    if days_left <= 7:
                        self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='orange')
                    else:  # inserted
                        self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='green')
                    self.license_created_label.configure(text=f'Key còn {days_left} ngày')
                    if self.is_authenticated:
                        self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                else:  # inserted
                    self.license_status_label.configure(text=f"License: {license_info.get('message', 'Lỗi kiểm tra')}", text_color='red')
                    self.license_created_label.configure(text='')
        except Exception as e:
            self.license_status_label.configure(text='License: Lỗi kiểm tra', text_color='red')
            self.license_created_label.configure(text='')

    def is_license_activated(self):
        """Kiểm tra xem license đã được kích hoạt chưa - LOGIC MỚI"""  # inserted
        try:
            license_info = self.sm.check_license_security()
            if license_info.get('need_key'):
                debug_print('[SECURITY] Cần nhập key - chưa được kích hoạt')
                return False
            if license_info.get('valid'):
                debug_print('[SECURITY] License hợp lệ và chưa hết hạn')
                return True
            debug_print('[SECURITY] License không hợp lệ')
            return False
        except Exception as e:
            debug_print(f'[SECURITY] Lỗi kiểm tra license activation: {e}')
            return False

    def is_trial_activated(self):
        """Kiểm tra xem trial đã được kích hoạt chưa"""  # inserted
        try:
            if not os.path.exists(TRIAL_STATE_FILE):
                return False
            with open(TRIAL_STATE_FILE, 'r', encoding='utf-8') as f:
                trial_state = json.load(f)
            if trial_state.get('activated') and trial_state.get('start_time'):
                start_time = trial_state.get('start_time')
                duration = trial_state.get('duration', 30)
                start_datetime = datetime.datetime.fromtimestamp(start_time)
                end_datetime = start_datetime + datetime.timedelta(minutes=duration)
                now = datetime.datetime.now()
                if now <= end_datetime:
                    return True
            return False
        except Exception as e:
            debug_print(f'Lỗi kiểm tra trial activated: {e}')
            return False

    def periodic_check(self):
        """Kiểm tra định kỳ - CHỈ CẬP NHẬT GUI, KHÔNG TẠO DIALOG"""  # inserted
        try:
            license_info = self.sm.check_license_security()
            if license_info.get('need_key'):
                debug_print(f"[PERIODIC] Key hết hạn, cập nhật GUI: {license_info['message']}")
                self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='red')
                self.license_created_label.configure(text='')
                self.main_content.pack_forget()
            else:  # inserted
                if license_info.get('valid'):
                    days_left = license_info.get('days_left', 0)
                    if days_left <= 7:
                        self.license_status_label.configure(text=f'License: Key còn {days_left} ngày', text_color='orange')
                    else:  # inserted
                        self.license_status_label.configure(text=f'License: Key còn {days_left} ngày', text_color='green')
                    self.license_created_label.configure(text=f'Key còn {days_left} ngày')
                    if self.is_authenticated and (not self.main_content.winfo_viewable()):
                        self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
            self.check_trial_and_license_status()
            self.after(30000, self.periodic_check)
        except Exception as e:
            debug_print(f'Lỗi kiểm tra định kỳ: {e}')
            self.after(30000, self.periodic_check)

    def show_license_expired_dialog(self, message, next_key_info=None):
        """Hiển thị dialog license hết hạn với ô nhập key gia hạn"""  # inserted
        try:
            debug_print(f'[DEBUG] Hiển thị dialog license hết hạn: {message}')
            if hasattr(self, '_license_expired_dialog') and self._license_expired_dialog.winfo_exists():
                debug_print('[DEBUG] Dialog đã tồn tại, bỏ qua')
                return
            debug_print('[DEBUG] Tạo dialog mới...')
            dialog = customtkinter.CTkToplevel(self)
            self._license_expired_dialog = dialog
            dialog.title('⚠️ LICENSE HẾT HẠN - CẦN GIA HẠN')
            dialog.geometry('700x500')
            dialog.resizable(False, False)
            dialog.transient(self)
            dialog.grab_set()
            dialog.protocol('WM_DELETE_WINDOW', lambda: None)
            dialog.lift()
            dialog.attributes('-topmost', True)
            dialog.after(100, lambda: dialog.attributes('-topmost', False))
            dialog.update_idletasks()
            x = dialog.winfo_screenwidth() // 2 - 350
            y = dialog.winfo_screenheight() // 2 - 250
            dialog.geometry(f'700x500+{x}+{y}')
            debug_print('[DEBUG] Dialog đã được tạo và hiển thị')
        except Exception as e:
            debug_print(f'[ERROR] Lỗi tạo dialog license hết hạn: {e}')
            import traceback
            safe_traceback()
        title_label = customtkinter.CTkLabel(dialog, text='⚠️ LICENSE HẾT HẠN', font=customtkinter.CTkFont(size=20, weight='bold'), text_color='red')
        title_label.pack(pady=20)
        message_label = customtkinter.CTkLabel(dialog, text=message, font=customtkinter.CTkFont(size=14), text_color='orange')
        message_label.pack(pady=10)
        key_frame = customtkinter.CTkFrame(dialog)
        key_frame.pack(pady=20, padx=20, fill='x')
        if next_key_info:
            key_info_label = customtkinter.CTkLabel(key_frame, text=f"🔑 Cần key gia hạn tháng {next_key_info['month']}:", font=customtkinter.CTkFont(size=14, weight='bold'), text_color='blue')
            key_info_label.pack(pady=5)
            key_display_label = customtkinter.CTkLabel(key_frame, text=next_key_info['key'], font=customtkinter.CTkFont(size=12, family='Courier'), text_color='green', bg_color='gray20')
            key_display_label.pack(pady=5)
        key_label = customtkinter.CTkLabel(key_frame, text='Nhập key gia hạn:', font=customtkinter.CTkFont(size=14, weight='bold'))
        key_label.pack(pady=10)
        placeholder_text = 'Nhập key gia hạn để tiếp tục sử dụng'
        if next_key_info:
            placeholder_text = f"Nhập key tháng {next_key_info['month']} ở trên"
        self.extend_key_entry = customtkinter.CTkEntry(key_frame, placeholder_text=placeholder_text, height=35, font=customtkinter.CTkFont(size=12), show='*')
        self.extend_key_entry.pack(pady=10, padx=20, fill='x')
        self.extend_key_entry.focus()
        button_frame = customtkinter.CTkFrame(dialog, fg_color='transparent')
        button_frame.pack(pady=20)

        def extend_license():
            key = self.extend_key_entry.get()
            if not key:
                messagebox.showerror('Lỗi', 'Vui lòng nhập key gia hạn!')
                return
            if self.check_extend_key(key):
                dialog.destroy()
                messagebox.showinfo('Thành công', 'Gia hạn thành công! Tool đã được cập nhật.')
                self.after(100, self.update_license_status_after_renewal)
            else:  # inserted
                messagebox.showerror('Lỗi', 'Key gia hạn không hợp lệ hoặc đã sử dụng!')

        def exit_app():
            dialog.destroy()
            import sys
            sys.exit(0)
        extend_button = customtkinter.CTkButton(button_frame, text='🔑 GIA HẠN', command=extend_license, height=40, fg_color='#4CAF50', hover_color='#45a049')
        extend_button.pack(side='left', padx=10)
        exit_button = customtkinter.CTkButton(button_frame, text='❌ Thoát', command=exit_app, height=40, fg_color='#D32F2F', hover_color='#B71C1C')
        exit_button.pack(side='left', padx=10)

        def on_enter(event):
            extend_license()
        self.extend_key_entry.bind('<Return>', on_enter)

    def show_trial_activation_dialog(self, trial_key, duration):
        """Hiển thị dialog kích hoạt dùng thử"""  # inserted
        if hasattr(self, '_trial_dialog') and self._trial_dialog.winfo_exists():
            return
        dialog = customtkinter.CTkToplevel(self)
        self._trial_dialog = dialog
        dialog.title('Kích Hoạt Dùng Thử')
        dialog.geometry('600x400')
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.protocol('WM_DELETE_WINDOW', lambda: None)
        dialog.update_idletasks()
        x = dialog.winfo_screenwidth() // 2 - 300
        y = dialog.winfo_screenheight() // 2 - 200
        dialog.geometry(f'600x400+{x}+{y}')
        title_label = customtkinter.CTkLabel(dialog, text='🎯 KÍCH HOẠT DÙNG THỬ', font=customtkinter.CTkFont(size=20, weight='bold'), text_color='blue')
        title_label.pack(pady=20)
        info_label = customtkinter.CTkLabel(dialog, text=f'Bạn có {duration} phút để dùng thử tool', font=customtkinter.CTkFont(size=14), text_color='green')
        info_label.pack(pady=10)
        key_frame = customtkinter.CTkFrame(dialog)
        key_frame.pack(pady=20, padx=20, fill='x')
        key_label = customtkinter.CTkLabel(key_frame, text='Nhập key dùng thử:', font=customtkinter.CTkFont(size=14, weight='bold'))
        key_label.pack(pady=10)
        self.trial_key_entry = customtkinter.CTkEntry(key_frame, placeholder_text='Nhập key dùng thử để bắt đầu', height=35, font=customtkinter.CTkFont(size=12), show='*')
        self.trial_key_entry.pack(pady=10, padx=20, fill='x')
        self.trial_key_entry.focus()
        button_frame = customtkinter.CTkFrame(dialog, fg_color='transparent')
        button_frame.pack(pady=20)

        def activate_trial():
            key = self.trial_key_entry.get()
            if not key:
                messagebox.showerror('Lỗi', 'Vui lòng nhập key dùng thử!')
                return
            if self.sm.activate_trial(key):
                dialog.destroy()
                self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                messagebox.showinfo('Thành công', f'Kích hoạt dùng thử thành công!\nBạn có {duration} phút để sử dụng tool.')
                self.check_trial_and_license_status()
            else:  # inserted
                messagebox.showerror('Lỗi', 'Key dùng thử không hợp lệ!')

        def exit_app():
            dialog.destroy()
            self.destroy()
        activate_button = customtkinter.CTkButton(button_frame, text='🎯 KÍCH HOẠT DÙNG THỬ', command=activate_trial, height=40, fg_color='#4CAF50', hover_color='#45a049')
        activate_button.pack(side='left', padx=10)
        exit_button = customtkinter.CTkButton(button_frame, text='❌ Thoát', command=exit_app, height=40, fg_color='#D32F2F', hover_color='#B71C1C')
        exit_button.pack(side='left', padx=10)

        def on_enter(event):
            activate_trial()
        self.trial_key_entry.bind('<Return>', on_enter)

    def show_license_activation_dialog(self):
        """Hiển thị dialog kích hoạt license chính"""  # inserted
        if hasattr(self, '_license_dialog') and self._license_dialog.winfo_exists():
            return
        dialog = customtkinter.CTkToplevel(self)
        self._license_dialog = dialog
        dialog.title('Kích Hoạt License')
        dialog.geometry('600x400')
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()
        dialog.protocol('WM_DELETE_WINDOW', lambda: None)
        dialog.update_idletasks()
        x = dialog.winfo_screenwidth() // 2 - 300
        y = dialog.winfo_screenheight() // 2 - 200
        dialog.geometry(f'600x400+{x}+{y}')
        title_label = customtkinter.CTkLabel(dialog, text='🔑 KÍCH HOẠT LICENSE', font=customtkinter.CTkFont(size=20, weight='bold'), text_color='green')
        title_label.pack(pady=20)
        info_label = customtkinter.CTkLabel(dialog, text='Thời gian dùng thử đã hết. Vui lòng nhập key license để tiếp tục sử dụng.', font=customtkinter.CTkFont(size=14), text_color='orange')
        info_label.pack(pady=10)
        key_frame = customtkinter.CTkFrame(dialog)
        key_frame.pack(pady=20, padx=20, fill='x')
        key_label = customtkinter.CTkLabel(key_frame, text='Nhập key license:', font=customtkinter.CTkFont(size=14, weight='bold'))
        key_label.pack(pady=10)
        self.license_key_entry = customtkinter.CTkEntry(key_frame, placeholder_text='Nhập key license để kích hoạt', height=35, font=customtkinter.CTkFont(size=12), show='*')
        self.license_key_entry.pack(pady=10, padx=20, fill='x')
        self.license_key_entry.focus()
        button_frame = customtkinter.CTkFrame(dialog, fg_color='transparent')
        button_frame.pack(pady=20)

        def activate_license():
            key = self.license_key_entry.get()
            if not key:
                messagebox.showerror('Lỗi', 'Vui lòng nhập key license!')
            else:  # inserted
                if key == 'LICENSE123':
                    dialog.destroy()
                    self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                    messagebox.showinfo('Thành công', 'Kích hoạt license thành công!')
                    self.license_status_label.configure(text='License: Đã kích hoạt', text_color='green')
                    self.license_created_label.configure(text='Tạo: Hôm nay')
                else:  # inserted
                    messagebox.showerror('Lỗi', 'Key license không hợp lệ!')

        def open_manager():
            dialog.destroy()
            self.open_license_manager()

        def exit_app():
            dialog.destroy()
            self.destroy()
        activate_button = customtkinter.CTkButton(button_frame, text='🔑 KÍCH HOẠT LICENSE', command=activate_license, height=40, fg_color='#4CAF50', hover_color='#45a049')
        activate_button.pack(side='left', padx=10)
        manager_button = customtkinter.CTkButton(button_frame, text='🔐 License Manager', command=open_manager, height=40)
        manager_button.pack(side='left', padx=10)
        exit_button = customtkinter.CTkButton(button_frame, text='❌ Thoát', command=exit_app, height=40, fg_color='#D32F2F', hover_color='#B71C1C')
        exit_button.pack(side='left', padx=10)

        def on_enter(event):
            activate_license()
        self.license_key_entry.bind('<Return>', on_enter)

    def check_extend_key(self, key):
        """Kiểm tra key gia hạn - LOGIC MỚI"""  # inserted
        try:
            debug_print(f'[DEBUG] Kiểm tra key gia hạn: {key}')
            return self.sm.validate_and_activate_key(key)
        except Exception as e:
            debug_print(f'Lỗi kiểm tra key gia hạn: {e}')
            return False

    def encrypt_data(self, data):
        """Mã hóa dữ liệu (copy từ SecurityManager)"""  # inserted
        try:
            json_str = json.dumps(data)
            encoded = base64.b64encode(json_str.encode()).decode()
            signature = hashlib.sha256(f'{encoded}{LICENSE_SECRET_KEY}'.encode()).hexdigest()
            return {'data': encoded, 'signature': signature}
        except Exception:
            return None

    def restart_application(self):
        """Khởi động lại ứng dụng"""  # inserted
        try:
            import sys
            import subprocess
            import os
            debug_print('[DEBUG] Bắt đầu khởi động lại ứng dụng...')
            self.destroy()
            import time
            time.sleep(0.5)
            restart_flag_file = os.path.join(os.path.abspath('.'), 'restart_flag.tmp')
            with open(restart_flag_file, 'w') as f:
                f.write('restarted')
            if getattr(sys, 'frozen', False):
                subprocess.Popen([sys.executable])
            else:  # inserted
                subprocess.Popen([sys.executable, __file__])
            debug_print('[DEBUG] Đã khởi động lại ứng dụng')
        except Exception as e:
            debug_print(f'Lỗi khởi động lại: {e}')
            import traceback
            safe_traceback()

    def create_password_dialog(self, text, title):
        """Tạo dialog nhập mật khẩu với field ẩn"""  # inserted
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
        if hasattr(self, 'license_monitor'):
            self.license_monitor.stop_monitoring()
        self.save_brave_path()
        self.stop_all_browsers()
        self.destroy()

    def browse_brave_path(self):
        """Mở dialog chọn file Brave Browser"""  # inserted
        from tkinter import filedialog
        brave_path = filedialog.askopenfilename(title='Chọn file Brave Browser', filetypes=[('Brave Executable', 'brave.exe'), ('Executable Files', '*.exe'), ('All Files', '*.*')])
        if brave_path:
            self.brave_path_entry.delete(0, 'end')
            self.brave_path_entry.insert(0, brave_path)
            self.save_brave_path()

    def load_brave_path(self):
        """Tải đường dẫn Brave Browser đã lưu"""  # inserted
        try:
            brave_config_file = 'brave_config.json'
            if os.path.exists(brave_config_file):
                with open(brave_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    brave_path = config.get('brave_path', '')
                    if brave_path and os.path.exists(brave_path):
                        self.brave_path_entry.insert(0, brave_path)
                    else:  # inserted
                        debug_print('Đường dẫn Brave Browser đã lưu không tồn tại, bỏ qua')
        except Exception as e:
            debug_print(f'Lỗi tải cấu hình Brave Browser: {e}')

    def save_brave_path(self):
        """Lưu đường dẫn Brave Browser vào file cấu hình"""  # inserted
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
        """Chờ trang tải xong (document.readyState == \'complete\')."""  # inserted
        try:
            WebDriverWait(driver, timeout).until(lambda d: d.execute_script('return document.readyState') == 'complete')
        except Exception as e:
            debug_print(f'[Minimax] Hết thời gian chờ trang load: {e}')

    def _has_minimax_403_error(self, driver):
        """Kiểm tra toast/lỗi 403 trên trang Minimax."""  # inserted
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
        """\n        Tự động reload nếu gặp lỗi 403 cho đến khi hết lỗi.\n        Đã sửa lỗi bị kẹt (hang) bằng cách bỏ \'wait_for_page_loaded\'.\n        """  # inserted
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
        """Lấy đường dẫn Brave Browser theo thứ tự ưu tiên: Tùy chỉnh -> Tự động tìm"""  # inserted
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
        else:  # inserted
            debug_print('Không tìm thấy Brave Browser ở bất kỳ đâu.')

    def validate_brave_path(self, brave_path):
        """Kiểm tra đường dẫn Brave Browser có hợp lệ không"""  # inserted
        try:
            if not os.path.exists(brave_path):
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
        """Test đường dẫn Brave Browser và hiển thị kết quả"""  # inserted
        brave_path = self.brave_path_entry.get().strip()
        if not brave_path:
            self.main_status_label.configure(text='⚠️ Vui lòng nhập đường dẫn Brave Browser trước khi test', text_color='orange')
            return
        if self.validate_brave_path(brave_path):
            self.main_status_label.configure(text=f'✅ Đường dẫn Brave Browser hợp lệ: {brave_path}', text_color='green')
            self.save_brave_path()
        else:  # inserted
            self.main_status_label.configure(text=f'❌ Đường dẫn Brave Browser không hợp lệ: {brave_path}', text_color='red')

    def get_driver_lock(self, profile_name):
        """Trả về Lock theo profile để đồng bộ gọi WebDriver giữa các luồng."""  # inserted
        if not hasattr(self, '_driver_locks'):
            self._driver_locks = {}
        if profile_name not in self._driver_locks:
            self._driver_locks[profile_name] = threading.Lock()
        return self._driver_locks[profile_name]

    def monitor_devtools(self, driver, profile_name, anti_devtools_script):
        """Chạy trong một luồng riêng để giám sát DevTools - PHIÊN BẢN ĐƠN GIẢN."""  # inserted
        debug_print(f'[Anti-DevTools] Bắt đầu giám sát đơn giản cho profile \'{profile_name}\'')
        signal = '!!!---DEVTOOLS-DETECTED---!!!'
        while profile_name in self.running_browsers:
            try:
                lock = self.get_driver_lock(profile_name)
                with lock:
                    driver.execute_script(anti_devtools_script)
                with lock:
                    current_title = driver.title
                if current_title == signal:
                    debug_print('[Anti-DevTools] PHÁT HIỆN DEVTOOLS! Tải lại trang...')
                    with lock:
                        driver.refresh()
                time.sleep(0.5)
            except Exception as e:
                debug_print(f'[Anti-DevTools] Lỗi kết nối tới profile \'{profile_name}\': {e}')
        debug_print(f'[Anti-DevTools] Đã dừng giám sát profile \'{profile_name}\'')

    def load_profiles(self):
        if os.path.exists(PROFILES_JSON_PATH):
            with open(PROFILES_JSON_PATH, 'r') as f:
                self.profiles = json.load(f)
        os.makedirs(PROFILES_DIR, exist_ok=True)
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
        if current_profile_count >= MAX_PROFILES:
            password_dialog = customtkinter.CTkInputDialog(text=f'Đã đạt giới hạn tối đa {MAX_PROFILES} profile.\nNhập mật khẩu để tiếp tục tạo profile mới:', title='Xác thực mật khẩu')
            entered_password = password_dialog.get_input()
            if entered_password!= DEFAULT_PASSWORD:
                self.main_status_label.configure(text='Lỗi: Mật khẩu không đúng!', text_color='red')
                return
            self.main_status_label.configure(text='Mật khẩu đúng, cho phép tạo profile mới.', text_color='green')
        dialog = customtkinter.CTkInputDialog(text='Nhập tên cho profile mới:', title='Thêm Profile')
        new_name = dialog.get_input()
        if new_name and new_name not in self.profiles:
            profile_path = os.path.join(PROFILES_DIR, new_name.strip())
            os.makedirs(profile_path, exist_ok=True)
            self.profiles[new_name] = {'path': profile_path}
            self.save_profiles()
            self.update_profile_list_ui()
            self.main_status_label.configure(text=f'Đã tạo profile \'{new_name}\' thành công.', text_color='green')
        else:  # inserted
            if new_name in self.profiles:
                self.main_status_label.configure(text=f'Lỗi: Profile \'{new_name}\' đã tồn tại.', text_color='red')

    def delete_profile(self):
        """Xóa profile đã chọn với xác nhận"""  # inserted
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
        else:  # inserted
            self.main_status_label.configure(text='Không thể xóa profile nào.', text_color='red')

    def start_selected_profiles(self):
        if not self.is_authenticated:
            return
        for name, widgets in self.profile_widgets.items():
            if widgets['checkbox'].get() == 1 and name not in self.running_browsers:
                thread = threading.Thread(target=self.launch_browser, args=(name,))
                thread.daemon = True
                thread.start()

    def launch_browser(self, profile_name):
        self.after(0, self.update_profile_status, profile_name, 'Đang khởi động...', 'orange')
        driver = None
        browser_pid = None
        try:
            profile_path = self.profiles[profile_name]['path']
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
            brave_path = self.get_brave_path()
            try:
                original_driver_path = get_resource_path(os.path.join('drivers', 'chromedriver.exe'))
                if not os.path.exists(original_driver_path):
                    raise FileNotFoundError('Không tìm thấy chromedriver.exe trong thư mục /drivers')
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
            finally:  # inserted
                pass  # postinserted
            try:
                debug_print(f'Thử khởi động Brave với binary của Brave Browser: {brave_path}')
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
                    _ = driver.window_handles
                    break
                except Exception:
                    if time.time() - ready_start > max_wait_seconds:
                        pass
                    else:  # inserted
                        time.sleep(0.2)
                        pass
            time.sleep(2)
            driver.get('https://www.minimax.io/audio/voices-cloning')
            try:
                self.auto_reload_until_ok(driver, profile_name)
            except Exception as e:
                debug_print(f'[Minimax] Lỗi khi chạy cơ chế auto-reload: {e}')
            self.running_browsers[profile_name] = driver
            self.after(0, self.update_profile_status, profile_name, 'Đang chạy', 'green')
            try:
                with self.quota_lock:
                    quota_to_inject = self.current_quota
                driver.execute_script(f'\n                    window.REMAINING_CHARS = {quota_to_inject};\n                    window.MY_UNIQUE_MACHINE_ID = \'{self.my_machine_id}\'; \n                ')
                debug_print(f'[{profile_name}] Đã tiêm Quota: {quota_to_inject} ký tự')
            except Exception as e:
                debug_print(f'[{profile_name}] Lỗi tiêm Quota: {e}')
            try:
                script_path = get_resource_path('script_chong_devtools.js')
                with open(script_path, 'r', encoding='utf-8') as f:
                    anti_devtools_script_code = f.read()
                monitor_thread = threading.Thread(target=self.monitor_devtools, args=(driver, profile_name, anti_devtools_script_code), daemon=True)
                monitor_thread.start()
                debug_print(f'[Anti-DevTools] Đã khởi động giám sát cho profile \'{profile_name}\'')
            except Exception as e:
                debug_print(f'[Anti-DevTools] LỖI NGHIÊM TRỌNG: Không thể tải hoặc khởi động giám sát: {e}')
                safe_traceback()
            if browser_pid:
                debug_print(f'Watchdog đang giám sát Browser PID: {browser_pid} cho profile \'{profile_name}\'')
                while psutil.pid_exists(browser_pid):
                    try:
                        _ = driver.window_handles
                        time.sleep(1)
                    except Exception:
                        debug_print(f'Driver không phản hồi, dừng giám sát cho profile {profile_name}')
                        break
                debug_print(f'Tiến trình Chrome (PID: {browser_pid}) cho profile \'{profile_name}\' đã không còn tồn tại.')
            else:  # inserted
                debug_print(f'Không thể lấy PID, Watchdog chuyển sang chế độ cũ cho profile \'{profile_name}\'.')
                while True:
                    try:
                        _ = driver.window_handles
                        time.sleep(1)
                    except Exception:
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
            else:  # inserted
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
        if not self.is_authenticated:
            return
        password = self.create_password_dialog('Nhập mật khẩu quản trị để reset vi phạm:', 'Reset Vi Phạm')
        if password == DEFAULT_PASSWORD:
            for name, driver in self.running_browsers.items():
                try:
                    driver.execute_script('\n                        localStorage.removeItem(\'f12_violation_count\');\n                        localStorage.removeItem(\'f12_locked_status\');\n                        localStorage.removeItem(\'f12_lock_time\');\n                        localStorage.removeItem(\'f12_warning_shown\');\n                        alert(\'✅ Đã reset trạng thái vi phạm cho profile này!\');\n                    ')
                except Exception as e:
                    debug_print(f'Lỗi khi reset vi phạm cho {name}: {e}')
            self.main_status_label.configure(text='✅ Đã reset tất cả trạng thái vi phạm!', text_color='green')
        else:  # inserted
            self.main_status_label.configure(text='❌ Sai mật khẩu!', text_color='red')

    def toggle_script(self, profile_name):
        if not self.is_authenticated:
            return
        if profile_name not in self.running_browsers:
            return
        widgets = self.profile_widgets[profile_name]
        is_script_on = widgets['script_on']
        if not is_script_on:
            widgets['script_on'] = True
            widgets['script_button'].configure(text='Tắt Script', fg_color='#D32F2F', hover_color='#B71C1C')
            self.main_status_label.configure(text=f'Đã BẬT chế độ giám sát cho \'{profile_name}\'.', text_color='green')
            thread = threading.Thread(target=self.tampermonkey_engine, args=(profile_name,))
            thread.daemon = True
            thread.start()
        else:  # inserted
            widgets['script_on'] = False
            widgets['script_button'].configure(text='Bật Script', fg_color=('#3B8ED0', '#1F6AA5'))
            self.main_status_label.configure(text=f'Đã TẮT chế độ giám sát cho \'{profile_name}\'.', text_color='gray')
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
        """\n        Hàm này được gọi từ luồng giám sát để yêu cầu xác nhận từ người dùng.\n        Nó sẽ điều phối việc tạo UI trên luồng chính và chờ kết quả.\n        """  # inserted
        import threading
        result_container = {'choice': 'stop'}
        dialog_closed_event = threading.Event()
        self.after(0, self._create_error_dialog_ui, profile_name, result_container, dialog_closed_event)
        dialog_closed_event.wait()
        return result_container['choice']

    def tampermonkey_engine(self, profile_name):
        debug_print(f'Bắt đầu engine giám sát cho profile: {profile_name}')
        if not hasattr(self, '_script_code'):
            try:
                script_path = get_resource_path('script.js')
                if not os.path.exists(script_path):
                    error_msg = 'Lỗi: Không tìm thấy script.js'
                    print(error_msg)
                    self.after(0, self.main_status_label.configure, {'text': error_msg, 'text_color': 'red'})
                    return
                with open(script_path, 'r', encoding='utf-8') as f:
                    self._script_code = f.read()
            except Exception as e:
                error_msg = f'Lỗi đọc script.js: {e}'
                print(error_msg)
                self.after(0, self.main_status_label.configure, {'text': error_msg, 'text_color': 'red'})
                return None
        consecutive_error_count = 0
        max_consecutive_errors = 5
        script_injected = False
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
                        with self.quota_lock:
                            quota_to_inject = self.current_quota
                        driver.execute_script(f'\n                            window.REMAINING_CHARS = {quota_to_inject};\n                            window.MY_UNIQUE_MACHINE_ID = \'{self.my_machine_id}\'; \n                            window.myScriptInjected = true;\n                        ')
                        driver.execute_script(self._script_code)
                    script_injected = True
                    debug_print(f'Đã tiêm script và quota {quota_to_inject} cho \'{profile_name}\'')
                current_title = ''
                with lock:
                    current_title = driver.title
                if current_title.startswith('MMX_REPORT:'):
                    try:
                        chars_used_str = current_title.split(':')[1]
                        chars_used = int(chars_used_str)
                        debug_print(f'[{profile_name}] Nhận tín hiệu: Trừ {chars_used} ký tự')
                        new_quota = 0
                        with self.quota_lock:
                            if self.current_quota == (-1):
                                new_quota = (-1)
                                debug_print(f'[{profile_name}] User không giới hạn. Bỏ qua trừ quota.')
                            else:  # inserted
                                self.current_quota -= chars_used
                                new_quota = self.current_quota
                        debug_print(f'[{profile_name}] Ngân hàng còn: {new_quota} ký tự')
                        try:
                            cache_file = os.path.join(self.sm.get_appdata_path(), 'quota_cache.json')
                            cache_data = {'machine_id': self.my_machine_id, 'remaining_quota': new_quota}
                            with open(cache_file, 'w', encoding='utf-8') as f:
                                json.dump(cache_data, f)
                            debug_print(f'[QUOTA] Đã lưu quota mới ({new_quota}) vào cache cục bộ.')
                        except Exception as e:
                            debug_print(f'[QUOTA] Lỗi ghi cache cục bộ: {e}')
                        with lock:
                            driver.execute_script(f'window.REMAINING_CHARS = {new_quota};')
                            driver.execute_script('document.title = \'Minimax\';')
                        quota_display = 'Không giới hạn' if new_quota == (-1) else f'{new_quota:,}'
                        current_text = self.auth_status_label.cget('text')
                        if '|' in current_text:
                            days_part = current_text.split('|')[0].strip()
                            self.after(0, self.auth_status_label.configure, {'text': f'{days_part} | Ký tự: {quota_display}'})
                        else:  # inserted
                            self.after(0, self.auth_status_label.configure, {'text': f'Ký tự: {quota_display}'})
                        threading.Thread(target=self.api_report_usage, args=(chars_used,), daemon=True).start()
                    except Exception as e_report:
                        debug_print(f'[{profile_name}] Lỗi xử lý tín hiệu MMX_REPORT: {e_report}')
                        with lock:
                            driver.execute_script('document.title = \'Minimax\';')
                if consecutive_error_count > 0:
                    self.after(0, self.main_status_label.configure, {'text': f'✅ Đã kết nối lại thành công với \'{profile_name}\'', 'text_color': 'green'})
                consecutive_error_count = 0
                time.sleep(1.0)
            except Exception as e:
                consecutive_error_count += 1
                debug_print(f'Lỗi giám sát (lần {consecutive_error_count}/{max_consecutive_errors}): {e}')
                script_injected = False
                if consecutive_error_count >= max_consecutive_errors:
                    debug_print('Đã đạt giới hạn lỗi. Hỏi người dùng...')
                    user_choice = self.prompt_user_on_error(profile_name)
                    if user_choice == 'retry':
                        debug_print('Người dùng chọn thử lại. Reset bộ đếm lỗi.')
                        consecutive_error_count = 0
                        self.after(0, self.main_status_label.configure, {'text': f'Đang thử kết nối lại với \'{profile_name}\'...', 'text_color': 'blue'})
                    else:  # inserted
                        debug_print('Người dùng chọn dừng giám sát.')
                        if profile_name in self.profile_widgets:
                            self.profile_widgets[profile_name]['script_on'] = False
                        self.after(0, self.update_profile_status, profile_name, 'Đã dừng (Lỗi)', 'gray')
                time.sleep(3)
        if profile_name in self.profile_widgets:
            self.profile_widgets[profile_name]['script_on'] = False
        debug_print(f'Đã dừng engine giám sát cho profile: {profile_name}')

    def restart_engine_for_profile(self, profile_name):
        """Khởi động lại engine cho profile cụ thể"""  # inserted
        try:
            if profile_name in self.profile_widgets and self.profile_widgets[profile_name]['script_on']:
                debug_print(f'Khởi động lại engine cho profile: {profile_name}')
                thread = threading.Thread(target=self.tampermonkey_engine, args=(profile_name,))
                thread.daemon = True
                thread.start()
                self.main_status_label.configure(text=f'🔄 Đã khởi động lại engine cho \'{profile_name}\'', text_color='blue')
        except Exception as e:
            debug_print(f'Lỗi khởi động lại engine cho \'{profile_name}\': {e}')

    def update_license_status_after_renewal(self):
        """Cập nhật trạng thái license sau khi gia hạn thành công - LOGIC ĐÃ SỬA"""  # inserted
        try:
            debug_print('[DEBUG] Cập nhật trạng thái license sau gia hạn...')
            import time
            time.sleep(0.2)
            license_info = self.sm.check_license_security()
            if license_info.get('need_key'):
                debug_print(f"[DEBUG] Vẫn cần nhập key: {license_info['message']}")
                self.show_license_expired_dialog(license_info['message'], None)
            else:  # inserted
                if license_info.get('valid'):
                    debug_print(f"[DEBUG] License đã được gia hạn thành công: {license_info['message']}")
                    days_left = license_info.get('days_left', 0)
                    expiry_date = license_info.get('expiry_date', '')
                    today = license_info.get('today', '')
                    if days_left <= 7:
                        self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='orange')
                    else:  # inserted
                        self.license_status_label.configure(text=f"License: {license_info['message']}", text_color='green')
                    self.license_created_label.configure(text=f'Hết hạn: {expiry_date} | Hôm nay: {today}')
                    if self.is_authenticated:
                        self.main_content.pack(pady=(0, 10), padx=10, fill='both', expand=True)
                        debug_print('[DEBUG] Đã hiển thị giao diện chính sau gia hạn')
                else:  # inserted
                    debug_print(f"[DEBUG] License không hợp lệ: {license_info.get('message', 'Lỗi')}")
                    self.show_license_expired_dialog(license_info.get('message', 'Lỗi kiểm tra license'), None)
        except Exception as e:
            debug_print(f'[ERROR] Lỗi cập nhật trạng thái license: {e}')
            import traceback
            safe_traceback()
if __name__ == '__main__':
    try:
        debug_print('[DEBUG] Khởi động ứng dụng...')
        security_manager = SecurityManager()
        debug_print('[DEBUG] SecurityManager đã tạo')
        app = App(security_manager)
        debug_print('[DEBUG] App đã tạo, bắt đầu mainloop...')
        app.mainloop()
    except Exception as e:
        debug_print(f'[ERROR] Lỗi khởi động ứng dụng: {e}')
        import traceback
        safe_traceback()
        input('Nhấn Enter để thoát...')