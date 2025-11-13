# Phien ban da duoc cap nhat de tim tai nguyen trong thu muc 'Resource'

import customtkinter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
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
from tkinter import filedialog, messagebox
import sys
import stat
import psutil

# --- CAC HAM TIEN ICH CO BAN ---
def get_app_root_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def debug_print(message):
    print(message)
    try:
        with open('debug.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()}: {message}\n')
    except:
        pass

def safe_traceback():
    if not (getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')):
        import traceback
        traceback.print_exc()

# --- HAM GET_RESOURCE_PATH DA DUOC CHINH SUA ---
def get_resource_path(relative_path):
    """
    Lay duong dan tai nguyen chinh xac, hoat dong cho ca che do .py va .exe.
    PHAN TICH: Tim file trong thu muc con 'Resource'.
    """
    try:
        # Che do chay file .EXE
        base_path = sys._MEIPASS
    except Exception:
        # Che do chay file .PY
        base_path = os.path.abspath('.')
    
    # Noi duong dan co so voi thu muc 'Resource' roi moi den ten file
    resource_dir = os.path.join(base_path, 'Resource')
    return os.path.join(resource_dir, relative_path)


# --- CAC HANG SO CUA UNG DUNG ---
PROFILES_JSON_PATH = 'profiles.json'
PROFILES_DIR = 'profiles'
SCRIPT_PATH = get_resource_path('script.js')
DEFAULT_PASSWORD = '221504'

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        debug_print('[DEBUG] Khoi tao App...')
        self.is_authenticated = True
        self.profiles = {}
        self.running_browsers = {}
        self.profile_widgets = {}
        
        self.title('Profile Manager & Browser Tool (Core Function)')
        self.geometry('800x600')
        self.protocol('WM_DELETE_WINDOW', self.on_closing)

        self.main_content = customtkinter.CTkFrame(self, fg_color='transparent')
        self.main_content.pack(pady=10, padx=10, fill='both', expand=True)
        self.main_content.grid_columnconfigure(0, weight=1)
        self.main_content.grid_rowconfigure(2, weight=1)

        chrome_config_frame = customtkinter.CTkFrame(self.main_content)
        chrome_config_frame.grid(row=0, column=0, padx=0, pady=(0, 5), sticky='ew')
        
        chrome_path_label = customtkinter.CTkLabel(chrome_config_frame, text='Duong dan Chrome (tuy chon):', font=customtkinter.CTkFont(size=12, weight='bold'))
        chrome_path_label.pack(side='left', padx=(10, 5), pady=5)
        self.chrome_path_entry = customtkinter.CTkEntry(chrome_config_frame, placeholder_text='De trong de tu dong tim Chrome', width=300, height=30)
        self.chrome_path_entry.pack(side='left', padx=5, pady=5)
        self.chrome_path_entry.bind('<FocusOut>', lambda e: self.save_chrome_path())
        self.chrome_path_entry.bind('<Return>', lambda e: self.save_chrome_path())
        browse_chrome_button = customtkinter.CTkButton(chrome_config_frame, text='📁 Chon Chrome', command=self.browse_chrome_path, width=120, height=30)
        browse_chrome_button.pack(side='left', padx=5, pady=5)
        test_chrome_button = customtkinter.CTkButton(chrome_config_frame, text='🔍 Test', command=self.test_chrome_path, width=80, height=30, fg_color='#4CAF50', hover_color='#45a049')
        test_chrome_button.pack(side='left', padx=5, pady=5)
        self.load_chrome_path()

        control_frame = customtkinter.CTkFrame(self.main_content)
        control_frame.grid(row=1, column=0, padx=0, pady=(0, 5), sticky='ew')
        add_profile_button = customtkinter.CTkButton(control_frame, text='➕ Them Profile', command=self.add_profile)
        add_profile_button.pack(side='left', padx=5, pady=5)
        delete_profile_button = customtkinter.CTkButton(control_frame, text='🗑️ Xoa Profile', command=self.delete_profile, fg_color='#D32F2F', hover_color='#B71C1C')
        delete_profile_button.pack(side='left', padx=5, pady=5)
        start_button = customtkinter.CTkButton(control_frame, text='▶️ Khoi dong Profile da chon', command=self.start_selected_profiles)
        start_button.pack(side='left', padx=5, pady=5)
        stop_all_button = customtkinter.CTkButton(control_frame, text='⏹️ Dung tat ca', command=self.stop_all_browsers, fg_color='#D32F2F', hover_color='#B71C1C')
        stop_all_button.pack(side='left', padx=5, pady=5)
        reset_violations_button = customtkinter.CTkButton(control_frame, text='🔓 Reset Vi Pham', command=self.reset_violations, fg_color='#FF9800', hover_color='#F57C00')
        reset_violations_button.pack(side='left', padx=5, pady=5)
        
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.main_content, label_text='Danh sach Profile')
        self.scrollable_frame.grid(row=2, column=0, padx=0, pady=5, sticky='nsew')
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        
        self.main_status_label = customtkinter.CTkLabel(self.main_content, text='San sang')
        self.main_status_label.grid(row=3, column=0, padx=0, pady=(5, 0), sticky='w')
        
        security_notice = customtkinter.CTkLabel(self.main_content, text='🔒 Chuc nang giam sat va chong F12 van hoat dong khi kich ban duoc bat.', text_color='#FF9800', font=customtkinter.CTkFont(size=12, weight='bold'))
        security_notice.grid(row=4, column=0, padx=0, pady=(5, 0), sticky='w')

        self.after(100, self.load_profiles)
        debug_print('[DEBUG] Khoi tao App hoan tat!')
        
    def create_password_dialog(self, text, title):
        dialog = customtkinter.CTkInputDialog(text=text, title=title)
        return dialog.get_input()

    def on_closing(self):
        debug_print('Dang dong ung dung, don dep cac trinh duyet...')
        self.save_chrome_path()
        self.stop_all_browsers()
        self.destroy()

    def browse_chrome_path(self):
        chrome_path = filedialog.askopenfilename(title='Chon file Chrome', filetypes=[('Chrome Executable', 'chrome.exe'), ('All Files', '*.*')])
        if chrome_path:
            self.chrome_path_entry.delete(0, 'end')
            self.chrome_path_entry.insert(0, chrome_path)
            self.save_chrome_path()

    def load_chrome_path(self):
        try:
            config_file = 'chrome_config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    path = config.get('chrome_path', '')
                    if path and os.path.exists(path):
                        self.chrome_path_entry.insert(0, path)
        except Exception as e:
            debug_print(f'Loi tai cau hinh Chrome: {e}')

    def save_chrome_path(self):
        try:
            path = self.chrome_path_entry.get().strip()
            config_file = 'chrome_config.json'
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump({'chrome_path': path}, f, indent=2)
            debug_print(f'Da luu duong dan Chrome: {path}')
        except Exception as e:
            debug_print(f'Loi luu cau hinh Chrome: {e}')
    
    def validate_chrome_path(self, chrome_path):
        if not chrome_path or not os.path.exists(chrome_path) or not os.path.isfile(chrome_path):
            return False
        return 'chrome' in os.path.basename(chrome_path).lower() and chrome_path.endswith('.exe')

    def get_chrome_path(self):
        custom_path = self.chrome_path_entry.get().strip()
        if self.validate_chrome_path(custom_path):
            debug_print(f'Su dung duong dan Chrome tuy chinh: {custom_path}')
            return custom_path
        
        possible_paths = [
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
            os.path.join(os.getenv('LOCALAPPDATA'), 'Google\\Chrome\\Application\\chrome.exe')
        ]
        for path in possible_paths:
            if self.validate_chrome_path(path):
                debug_print(f'Tu dong tim thay Chrome tai: {path}')
                return path
        
        debug_print('Khong tim thay Chrome tu dong.')
        return None

    def test_chrome_path(self):
        chrome_path = self.get_chrome_path()
        if chrome_path:
            self.main_status_label.configure(text=f'✅ Tim thay Chrome: {chrome_path}', text_color='green')
        else:
            self.main_status_label.configure(text='❌ Khong tim thay Chrome. Vui long chon duong dan thu cong.', text_color='red')

    def load_profiles(self):
        if os.path.exists(PROFILES_JSON_PATH):
            with open(PROFILES_JSON_PATH, 'r', encoding='utf-8') as f:
                self.profiles = json.load(f)
        os.makedirs(PROFILES_DIR, exist_ok=True)
        self.update_profile_list_ui()

    def save_profiles(self):
        with open(PROFILES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(self.profiles, f, indent=4)

    def update_profile_list_ui(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.profile_widgets.clear()
        
        for profile_name in sorted(self.profiles.keys()):
            is_running = profile_name in self.running_browsers
            row_frame = customtkinter.CTkFrame(self.scrollable_frame)
            row_frame.pack(fill='x', padx=5, pady=5, expand=True)
            row_frame.grid_columnconfigure(0, weight=1)
            
            checkbox = customtkinter.CTkCheckBox(row_frame, text=profile_name, font=customtkinter.CTkFont(size=14))
            checkbox.grid(row=0, column=0, sticky='w', padx=5)
            
            action_frame = customtkinter.CTkFrame(row_frame, fg_color='transparent')
            action_frame.grid(row=0, column=1, sticky='e')
            
            status_text = 'Dang chay' if is_running else 'Da dung'
            status_color = 'green' if is_running else 'gray'
            status_label = customtkinter.CTkLabel(action_frame, text=status_text, text_color=status_color, width=100)
            status_label.pack(side='left', padx=10)
            
            script_button = customtkinter.CTkButton(action_frame, text='Bat Script', command=lambda name=profile_name: self.toggle_script(name), state='normal' if is_running else 'disabled')
            script_button.pack(side='left', padx=5)
            
            self.profile_widgets[profile_name] = {'checkbox': checkbox, 'status_label': status_label, 'script_button': script_button, 'script_on': False}

    def add_profile(self):
        dialog = customtkinter.CTkInputDialog(text='Nhap ten cho profile moi:', title='Them Profile')
        new_name = dialog.get_input()
        if new_name and new_name not in self.profiles:
            profile_path = os.path.join(PROFILES_DIR, new_name.strip())
            os.makedirs(profile_path, exist_ok=True)
            self.profiles[new_name] = {'path': profile_path}
            self.save_profiles()
            self.update_profile_list_ui()
            self.main_status_label.configure(text=f'Da tao profile \'{new_name}\'.', text_color='green')
        elif new_name in self.profiles:
            self.main_status_label.configure(text=f'Loi: Profile \'{new_name}\' da ton tai.', text_color='red')

    def delete_profile(self):
        selected_profiles = [name for name, widgets in self.profile_widgets.items() if widgets['checkbox'].get() == 1]
        if not selected_profiles:
            messagebox.showwarning("Chua chon profile", "Vui long chon it nhat mot profile de xoa.")
            return
        
        confirm = messagebox.askyesno("Xac nhan xoa", f"Ban co chac chan muon xoa {len(selected_profiles)} profile da chon khong?")
        if not confirm:
            return
            
        for name in selected_profiles:
            if name in self.running_browsers:
                try: self.running_browsers[name].quit()
                except: pass
                del self.running_browsers[name]
            
            try:
                import shutil
                shutil.rmtree(self.profiles[name]['path'])
                del self.profiles[name]
            except Exception as e:
                debug_print(f"Loi khi xoa profile '{name}': {e}")

        self.save_profiles()
        self.update_profile_list_ui()

    def start_selected_profiles(self):
        for name, widgets in self.profile_widgets.items():
            if widgets['checkbox'].get() == 1 and name not in self.running_browsers:
                threading.Thread(target=self.launch_browser, args=(name,), daemon=True).start()

    def launch_browser(self, profile_name):
        self.after(0, self.update_profile_status, profile_name, 'Dang khoi dong...', 'orange')
        
        chromedriver_path = get_resource_path('chromedriver.exe')
        if not os.path.exists(chromedriver_path):
            self.after(0, self.update_profile_status, profile_name, 'Loi: Thieu chromedriver.exe', 'red')
            debug_print(f"Loi: Khong tim thay chromedriver.exe trong thu muc Resource.")
            return
        
        chrome_path = self.get_chrome_path()
        if not chrome_path:
            self.after(0, self.update_profile_status, profile_name, 'Loi: Khong tim thay Chrome', 'red')
            debug_print("Loi: Khong tim thay chrome.exe. Vui long chon duong dan thu cong.")
            return

        driver = None
        try:
            profile_path = self.profiles[profile_name]['path']
            
            debug_print(f'Khoi dong profile {profile_name} voi undetected-chromedriver...')
            driver = uc.Chrome(
                user_data_dir=os.path.abspath(profile_path),
                headless=False,
                driver_executable_path=chromedriver_path,
                browser_executable_path=chrome_path,
                no_sandbox=True
            )

            self.running_browsers[profile_name] = driver
            self.after(0, self.update_profile_status, profile_name, 'Dang chay', 'green')
            
            driver.get('https://www.minimax.io/audio/voices-cloning')

            while True:
                try:
                    _ = driver.window_handles
                    time.sleep(1)
                except Exception:
                    debug_print(f"Profile '{profile_name}' da duoc dong.")
                    break
        
        except Exception as e:
            debug_print(f'Loi nghiem trong khi chay profile {profile_name}: {e}')
            safe_traceback()
            self.after(0, self.update_profile_status, profile_name, 'Loi Driver/Chrome', 'red')
        
        finally:
            if profile_name in self.running_browsers:
                del self.running_browsers[profile_name]
            self.after(0, self.update_profile_status, profile_name, 'Da dung', 'gray')

    def update_profile_status(self, profile_name, text, color):
        if profile_name in self.profile_widgets:
            widgets = self.profile_widgets[profile_name]
            widgets['status_label'].configure(text=text, text_color=color)
            widgets['script_button'].configure(state='normal' if text == 'Dang chay' else 'disabled')
            if text != 'Dang chay':
                widgets['script_on'] = False
                widgets['script_button'].configure(text='Bat Script', fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])

    def stop_all_browsers(self):
        for driver in list(self.running_browsers.values()):
            try: driver.quit()
            except: pass
        self.running_browsers.clear()
        self.after(100, self.update_profile_list_ui)

    def reset_violations(self):
        password = self.create_password_dialog('Nhap mat khau quan tri de reset vi pham:', 'Reset Vi Pham')
        if password == DEFAULT_PASSWORD:
            for name, driver in self.running_browsers.items():
                try:
                    driver.execute_script("localStorage.clear(); alert('Da xoa sach localStorage cho profile nay!');")
                except Exception as e:
                    debug_print(f'Loi khi reset vi pham cho {name}: {e}')
            self.main_status_label.configure(text='✅ Da reset tat ca trang thai vi pham!', text_color='green')
        elif password is not None:
            self.main_status_label.configure(text='❌ Sai mat khau!', text_color='red')

    def toggle_script(self, profile_name):
        if profile_name not in self.running_browsers: return
        
        widgets = self.profile_widgets[profile_name]
        is_on = widgets.get('script_on', False)
        
        if not is_on:
            widgets['script_on'] = True
            widgets['script_button'].configure(text='Tat Script', fg_color='#D32F2F', hover_color='#B71C1C')
            threading.Thread(target=self.tampermonkey_engine, args=(profile_name,), daemon=True).start()
        else:
            widgets['script_on'] = False
            widgets['script_button'].configure(text='Bat Script', fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
            try: self.running_browsers[profile_name].refresh()
            except: pass

    def tampermonkey_engine(self, profile_name):
        debug_print(f'Bat dau engine giam sat cho profile: {profile_name}')
        
        try:
            with open(SCRIPT_PATH, 'r', encoding='utf-8') as f:
                script_code = f.read()
        except Exception as e:
            debug_print(f'Loi doc script.js: {e}')
            self.after(0, self.update_profile_status, profile_name, 'Loi script.js', 'red')
            return

        while self.profile_widgets.get(profile_name, {}).get('script_on', False):
            try:
                driver = self.running_browsers.get(profile_name)
                if not driver: break
                
                is_injected = driver.execute_script('return window.myScriptInjected === true;')
                if not is_injected:
                    driver.execute_script('window.myScriptInjected = true;\n' + script_code)
                    debug_print(f'Da tiem script cho \'{profile_name}\'.')
                
                time.sleep(2)
            except Exception as e:
                debug_print(f'Loi giam sat cho profile {profile_name}: {e}. Dung giam sat.')
                self.after(0, lambda: self.main_status_label.configure(text=f'⚠️ Mat ket noi script voi \'{profile_name}\'.', text_color='orange'))
                break
        
        debug_print(f'Da dung engine giam sat cho profile: {profile_name}')
        if profile_name in self.profile_widgets:
            self.profile_widgets[profile_name]['script_on'] = False
            self.after(0, self.update_profile_status, profile_name, self.profile_widgets[profile_name]['status_label'].cget("text"), self.profile_widgets[profile_name]['status_label'].cget("text_color"))


if __name__ == '__main__':
    try:
        debug_print('--- KHOI DONG UNG DUNG ---')
        app = App()
        app.mainloop()
    except Exception as e:
        debug_print(f'[ERROR] Loi nghiem trong: {e}')
        safe_traceback()
        input('Ung dung gap loi nghiem trong. Nhan Enter de thoat...')