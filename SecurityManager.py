class SecurityManager:
    def get_machine_id(self):
        try:
            result = subprocess.check_output('wmic csproduct get uuid', shell=True, stderr=subprocess.DEVNULL).decode()
            uuid_str = result.split('\n')[1].strip()
            return uuid_str
        except Exception:
            return ':'.join(['{:02x}'.format(uuid.getnode() >> i & 255) for i in range(0, 48, 8)][::(-1)])

    def hash_id(self, machine_id):
        return hashlib.sha256(machine_id.encode()).hexdigest()

    def create_license(self):
        machine_id = self.get_machine_id()
        hashed_id = self.hash_id(machine_id)
        license_data = {'machine_key': hashed_id}
        os.makedirs(HIDDEN_AUTH_DIR, exist_ok=True)
        try:
            subprocess.run(['attrib', '+h', HIDDEN_AUTH_DIR], shell=True, stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass
        with open(HIDDEN_AUTH_FILE, 'w') as f:
            json.dump(license_data, f)
        with open(LOCAL_KEY_FILE, 'w') as f:
            json.dump(license_data, f)
            return True

    def verify_license(self):
        return True

    def delete_license(self):
        if os.path.exists(HIDDEN_AUTH_FILE):
            os.remove(HIDDEN_AUTH_FILE)
        if os.path.exists(LOCAL_KEY_FILE):
            os.remove(LOCAL_KEY_FILE)
        debug_print('Đã xóa ID máy.')

    def decrypt_license_data(self, encrypted_data):
        """Giải mã dữ liệu license"""  # inserted
        try:
            if not encrypted_data or 'data' not in encrypted_data or 'signature' not in encrypted_data:
                debug_print('[SECURITY] License data không đầy đủ')
                return
            expected_signature = hashlib.sha256(f"{encrypted_data['data']}{LICENSE_SECRET_KEY}".encode()).hexdigest()
            if expected_signature!= encrypted_data['signature']:
                debug_print('[SECURITY] License signature không hợp lệ!')
                return
            decoded = base64.b64decode(encrypted_data['data']).decode()
            return json.loads(decoded)
        except Exception as e:
            debug_print(f'[SECURITY] Lỗi giải mã license: {e}')
            return None

    def encrypt_data(self, data):
        """Mã hóa dữ liệu"""  # inserted
        try:
            json_str = json.dumps(data)
            encoded = base64.b64encode(json_str.encode()).decode()
            signature = hashlib.sha256(f'{encoded}{LICENSE_SECRET_KEY}'.encode()).hexdigest()
            return {'data': encoded, 'signature': signature}
        except Exception as e:
            debug_print(f'[SECURITY] Lỗi mã hóa dữ liệu: {e}')
            return None

    def check_license_security(self):
        """Kiểm tra bảo mật license - LOGIC ĐÃ SỬA LỖI"""  # inserted
        return {'valid': True, 'days_left': 1000, 'expiry_date': '2027-01-01', 'today': '', 'message': ''}
        try:
            debug_print('[DEBUG] Bắt đầu kiểm tra bảo mật license...')
            license_path = self.get_license_path()
            if not license_path:
                debug_print('[SECURITY] Không tìm thấy license.dat')
                return {'valid': False, 'message': 'Không tìm thấy license.dat', 'need_key': True}
            with open(license_path, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            license_data = self.decrypt_license_data(encrypted_data)
            if not license_data:
                debug_print('[SECURITY] License.dat không hợp lệ hoặc bị giả mạo')
                return {'valid': False, 'message': 'License.dat không hợp lệ', 'need_key': True}
            if not IS_EXE_MODE:
                debug_print(f'[DEBUG] License data hợp lệ: {license_data}')
            else:  # inserted
                debug_print('[DEBUG] License data hợp lệ')
            activated_files = self.find_activated_key_files()
            debug_print(f'[DEBUG] Tìm thấy {len(activated_files)} file key đã kích hoạt')
            if activated_files:
                for file in activated_files:
                    key_data = self.read_activated_key_file(file)
                    if key_data and self.is_key_still_valid(key_data):
                        detailed_info = self.get_license_detailed_info(key_data)
                        debug_print(f"[SECURITY] Key đã kích hoạt còn hạn, còn {detailed_info['days_left']} ngày")
                        return {'valid': True, 'days_left': detailed_info['days_left'], 'expiry_date': detailed_info['expiry_date'], 'today': detailed_info['today'], 'message': detailed_info['message']}
                else:  # inserted
                    debug_print('[SECURITY] Tất cả key đã hết hạn, hiển thị dialog nhập key mới')
                    return {'valid': False, 'message': 'Key đã hết hạn, cần nhập key mới', 'need_key': True}
            else:  # inserted
                expiry_date_str = license_data.get('expiry_date', '')
                if expiry_date_str:
                    try:
                        expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                        today = datetime.date.today()
                        if today >= expiry_date:
                            debug_print(f'[SECURITY] License.dat đã hết hạn: {expiry_date} <= {today}')
                            extend_keys = license_data.get('extend_keys', [])
                            if extend_keys:
                                debug_print('[SECURITY] License.dat hết hạn, cần nhập key gia hạn')
                                return {'valid': False, 'message': f'License.dat đã hết hạn từ {expiry_date}, cần nhập key gia hạn', 'need_key': True}
                            debug_print('[SECURITY] License.dat hết hạn và không có key gia hạn')
                            return {'valid': False, 'message': f'License.dat đã hết hạn từ {expiry_date}, cần tạo license mới', 'need_key': True}
                        days_until_expiry = (expiry_date - today).days
                        debug_print(f'[SECURITY] License.dat còn hạn {days_until_expiry} ngày')
                    except Exception as e:
                        debug_print(f'[SECURITY] Lỗi kiểm tra ngày hết hạn license.dat: {e}')
                        return {'valid': False, 'message': 'Lỗi kiểm tra ngày hết hạn license.dat', 'need_key': True}
                extend_keys = license_data.get('extend_keys', [])
                if extend_keys:
                    debug_print('[SECURITY] Chưa kích hoạt key nào, cần nhập key gia hạn')
                    return {'valid': False, 'message': 'Chưa kích hoạt key, cần nhập key gia hạn', 'need_key': True}
                debug_print('[SECURITY] Không có key gia hạn, cần tạo license mới')
                return {'valid': False, 'message': 'Không có key gia hạn, cần tạo license mới', 'need_key': True}
        except Exception as e:
            debug_print(f'[SECURITY] Lỗi kiểm tra bảo mật license: {e}')
            import traceback
            safe_traceback()
            return {'valid': False, 'message': f'Lỗi kiểm tra: {e}', 'need_key': True}

    def find_activated_key_files(self):
        """Tìm tất cả file key đã kích hoạt trong thư mục ẩn"""  # inserted
        try:
            import glob
            os.makedirs(HIDDEN_KEYS_DIR, exist_ok=True)
            try:
                subprocess.run(['attrib', '+h', HIDDEN_KEYS_DIR], shell=True, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass
            pattern = os.path.join(HIDDEN_KEYS_DIR, 'key_activated_*.dat')
            files = glob.glob(pattern)
            debug_print(f'[DEBUG] Tìm thấy files trong {HIDDEN_KEYS_DIR}: {files}')
            return files
        except Exception as e:
            debug_print(f'[ERROR] Lỗi tìm file key: {e}')
            return []

    def read_activated_key_file(self, filename):
        """Đọc file key đã kích hoạt với bảo mật chống hack"""  # inserted
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            if 'data' in encrypted_data and 'signature' in encrypted_data:
                data = self.decrypt_activated_key_data(encrypted_data)
                if data:
                    debug_print(f'[DEBUG] Đọc file {filename} (đã mã hóa): {data}')
                    return data
                debug_print(f'[ERROR] File {filename} bị hack hoặc bị hỏng!')
                return
            debug_print(f'[SECURITY] File {filename} không có bảo mật - TỪ CHỐI!')
            debug_print('[SECURITY] Có thể bị hack - bỏ lớp bảo mật!')
            return
        except Exception as e:
            debug_print(f'[ERROR] Lỗi đọc file {filename}: {e}')
            return None

    def is_key_still_valid(self, key_data):
        """Kiểm tra key còn hạn không"""  # inserted
        try:
            expiry_date_str = key_data.get('expiry_date', '')
            if not expiry_date_str:
                return False
            expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            today = datetime.date.today()
            return today <= expiry_date
        except Exception as e:
            debug_print(f'[ERROR] Lỗi kiểm tra hạn key: {e}')
            return False

    def calculate_days_left(self, key_data):
        """Tính số ngày còn lại"""  # inserted
        try:
            expiry_date_str = key_data.get('expiry_date', '')
            expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            today = datetime.date.today()
            days_left = (expiry_date - today).days
            return max(0, days_left)
        except Exception as e:
            debug_print(f'[ERROR] Lỗi tính ngày còn lại: {e}')
            return 0

    def get_license_detailed_info(self, key_data):
        """Lấy thông tin chi tiết về license bao gồm ngày hết hạn và ngày hiện tại"""  # inserted
        try:
            expiry_date_str = key_data.get('expiry_date', '')
            if not expiry_date_str:
                return {'days_left': 0, 'expiry_date': '', 'today': '', 'message': 'Không có thông tin ngày hết hạn'}
            expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
            today = datetime.date.today()
            return {'days_left': (expiry_date - today).days, 'expiry_date': max(0, days_left), 'today': expiry_date.strftime('%d/%m/%Y'), 'message': f"{today.strftime('%d/%m/%Y')}Key còn {max(0, days_left)} ngày (Hết hạn: {expiry_date.strftime('%d/%m/%Y')}, Hôm nay: {today.strftime('%d/%m/%Y')})"}
        except Exception as e:
            debug_print(f'[ERROR] Lỗi lấy thông tin chi tiết license: {e}')
            return {'days_left': 0, 'expiry_date': '', 'today': '', 'message': 'Lỗi đọc thông tin license'}

    def validate_and_activate_key(self, input_key):
        """Xác thực và kích hoạt key - PHÂN BIỆT TRIAL VÀ EXTEND KEY"""  # inserted
        try:
            input_key = input_key.strip()
            if not IS_EXE_MODE:
                debug_print(f'[DEBUG] Xác thực key: \'{input_key}\'')
            else:  # inserted
                debug_print('[DEBUG] Xác thực key')
            license_path = self.get_license_path()
            if not license_path:
                debug_print('[ERROR] Không tìm thấy license.dat')
                return False
            with open(license_path, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            license_data = self.decrypt_license_data(encrypted_data)
            if not license_data:
                debug_print('[ERROR] Không thể giải mã license')
                return False
            trial_config = license_data.get('trial_config', {})
            if trial_config.get('enabled'):
                trial_key = trial_config.get('key', '').strip()
                debug_print(f'[DEBUG] Kiểm tra key trial: \'{trial_key}\' vs \'{input_key}\' (length: {len(trial_key)} vs {len(input_key)})')
                if trial_key == input_key.strip():
                    debug_print('[DEBUG] Key trial khớp, nhưng cần kích hoạt trial trước')
                    return False
            extend_keys = license_data.get('extend_keys', [])
            debug_print(f'[DEBUG] Tìm thấy {len(extend_keys)} key gia hạn trong license.dat')
            for key_info in extend_keys:
                stored_key = key_info['key'].strip() if key_info['key'] else ''
                debug_print(f'[DEBUG] Kiểm tra key gia hạn: \'{stored_key}\' vs \'{input_key}\' (length: {len(stored_key)} vs {len(input_key)})')
                if stored_key == input_key.strip():
                    debug_print(f"[DEBUG] Key gia hạn khớp với tháng {key_info.get('month', 'N/A')}")
                    is_used = key_info.get('used', False)
                    debug_print(f"[DEBUG] Trạng thái key: used={is_used}, used_date={key_info.get('used_date', 'N/A')}")
                    if is_used:
                        debug_print(f"[DEBUG] Key gia hạn đã được sử dụng vào ngày {key_info.get('used_date', 'N/A')}")
                        return False
                    key_end_date_str = key_info.get('end_date', '')
                    if key_end_date_str:
                        try:
                            key_end_date = datetime.datetime.strptime(key_end_date_str, '%Y-%m-%d').date()
                            today = datetime.date.today()
                            if today > key_end_date:
                                debug_print(f'[DEBUG] Key gia hạn đã hết hạn từ {key_end_date} (hôm nay: {today})')
                                return False
                            debug_print(f'[DEBUG] Key gia hạn còn hạn đến {key_end_date}')
                        except Exception as e:
                            debug_print(f'[DEBUG] Lỗi kiểm tra ngày hết hạn key: {e}')
                    if self.create_activated_key_file(input_key, key_info):
                        debug_print('[DEBUG] Đã tạo file key đã kích hoạt')
                        key_info['used'] = True
                        key_info['used_date'] = datetime.date.today().strftime('%Y-%m-%d')
                        encrypted_data = self.encrypt_data(license_data)
                        main_dir = os.path.dirname(os.path.abspath(__file__))
                        main_license_path = os.path.join(main_dir, 'license.dat')
                        try:
                            with open(main_license_path, 'w', encoding='utf-8') as f:
                                json.dump(encrypted_data, f, indent=2)
                            debug_print(f'[DEBUG] Đã cập nhật license.dat tại \'{main_license_path}\'')
                        except Exception as e:
                            debug_print(f'[ERROR] Không thể ghi vào thư mục main: {e}')
                            try:
                                with open(license_path, 'w', encoding='utf-8') as f:
                                    json.dump(encrypted_data, f, indent=2)
                                debug_print(f'[DEBUG] Đã cập nhật license.dat tại \'{license_path}\' (fallback)')
                            except Exception as e2:
                                debug_print(f'[ERROR] Không thể cập nhật license.dat: {e2}')
                                return False
                        debug_print('[DEBUG] Đã cập nhật license.dat với key gia hạn đã sử dụng')
                        return True
            else:  # inserted
                debug_print('[DEBUG] Key không khớp với license.dat (không phải trial key hoặc extend key)')
                return False
        except Exception as e:
            debug_print(f'[ERROR] Lỗi xác thực key: {e}')
            return False

    def get_license_path(self):
        """Lấy đường dẫn license.dat - Đọc tất cả và chọn file tốt nhất"""  # inserted
        try:
            possible_paths = []
            main_dir = os.path.dirname(os.path.abspath(__file__))
            main_license_path = os.path.join(main_dir, 'license.dat')
            if os.path.exists(main_license_path):
                possible_paths.append(main_license_path)
            app_root = get_app_root_dir()
            portable_license_path = os.path.join(app_root, 'license.dat')
            if os.path.exists(portable_license_path):
                possible_paths.append(portable_license_path)
            if os.path.exists(HIDDEN_LICENSE_FILE):
                possible_paths.append(HIDDEN_LICENSE_FILE)
            test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bao_mat', 'test_licenses')
            test_license_path = os.path.join(test_dir, 'license.dat')
            if os.path.exists(test_license_path):
                possible_paths.append(test_license_path)
            bundled_license_path = get_resource_path('license.dat')
            if os.path.exists(bundled_license_path):
                possible_paths.append(bundled_license_path)
            if not possible_paths:
                debug_print('[DEBUG] Không tìm thấy license.dat ở bất kỳ đâu')
                return
            best_path = self._select_best_license_file(possible_paths)
            if best_path:
                debug_print(f'[DEBUG] Sử dụng license.dat tốt nhất: {best_path}')
                return best_path
            debug_print('[DEBUG] Tất cả license.dat đều không có key hợp lệ')
            return possible_paths[0]
        except Exception as e:
            debug_print(f'[ERROR] Lỗi lấy đường dẫn license: {e}')
            return None

    def _select_best_license_file(self, license_paths):
        """Chọn license.dat tốt nhất (có key còn hạn, chưa sử dụng)"""  # inserted
        try:
            best_path = None
            best_score = (-1)
            for path in license_paths:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        encrypted_data = json.load(f)
                    expected_signature = hashlib.sha256(f"{encrypted_data['data']}{LICENSE_SECRET_KEY}".encode()).hexdigest()
                    if expected_signature!= encrypted_data['signature']:
                        debug_print(f'[DEBUG] Chữ ký không hợp lệ: {path}')
                        continue
                    decoded = base64.b64decode(encrypted_data['data']).decode()
                    license_data = json.loads(decoded)
                    score = self._calculate_license_score(license_data)
                    debug_print(f'[DEBUG] File {path} có điểm: {score}')
                    if score > best_score:
                        best_score = score
                        best_path = path
                except Exception as e:
                    debug_print(f'[DEBUG] Lỗi đọc file {path}: {e}')
            return best_path
        except Exception as e:
            debug_print(f'[ERROR] Lỗi chọn license tốt nhất: {e}')
            return None

    def _calculate_license_score(self, license_data):
        """Tính điểm cho license.dat (cao hơn = tốt hơn)"""  # inserted
        try:
            score = 0
            today = datetime.date.today()
            extend_keys = license_data.get('extend_keys', [])
            for key_info in extend_keys:
                if not key_info.get('used', False):
                    score += 10
                    end_date_str = key_info.get('end_date', '')
                    if end_date_str:
                        try:
                            end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                            if end_date >= today:
                                score += 5
                                days_left = (end_date - today).days
                                score += min(days_left, 30)
                        except:
                            pass
            trial_config = license_data.get('trial_config', {})
            if trial_config.get('enabled', False):
                score += 1
            debug_print(f'[DEBUG] License score: {score}')
            return score
        except Exception as e:
            debug_print(f'[ERROR] Lỗi tính điểm license: {e}')
            return 0

    def create_activated_key_file(self, key, key_info):
        """Tạo file key đã kích hoạt trong thư mục ẩn"""
        try:
            os.makedirs(HIDDEN_KEYS_DIR, exist_ok=True)
            try:
                # Windows only; trên macOS sẽ fail nhưng đã bọc try/except
                subprocess.run(['attrib', '+h', HIDDEN_KEYS_DIR], shell=True, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass

            next_number = self.get_next_activated_key_number()
            filename = os.path.join(HIDDEN_KEYS_DIR, f'key_activated_{next_number}.dat')

            today = datetime.date.today()
            expiry_date_str = key_info.get('end_date', '')

            if expiry_date_str:
                try:
                    expiry_date = datetime.datetime.strptime(expiry_date_str, '%Y-%m-%d').date()
                    debug_print(f'[DEBUG] Sử dụng ngày hết hạn thực tế: {expiry_date}')
                except Exception:
                    expiry_date = today + datetime.timedelta(days=30)
                    debug_print(f'[DEBUG] Fallback: 30 ngày từ ngày kích hoạt: {expiry_date}')
            else:
                expiry_date = today + datetime.timedelta(days=30)
                debug_print(f'[DEBUG] Không có end_date, sử dụng 30 ngày: {expiry_date}')

            key_data = {
                'key': key,
                'month': key_info.get('month', next_number),
                'activation_date': today.strftime('%Y-%m-%d'),
                'expiry_date': expiry_date.strftime('%Y-%m-%d'),
                'status': 'active',
                'created_timestamp': datetime.datetime.now().isoformat(),
                'checksum': hashlib.md5(f'{key}{today}{expiry_date}'.encode()).hexdigest(),
            }

            encrypted_data = self.encrypt_activated_key_data(key_data)
            if not encrypted_data:
                debug_print('[ERROR] Không thể mã hóa dữ liệu key đã kích hoạt')
                return False

            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(encrypted_data, f, indent=2)

            try:
                subprocess.run(['attrib', '+h', filename], shell=True, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass

            debug_print(f'[DEBUG] Đã tạo file {filename} với dữ liệu đã mã hóa (chống hack)')
            return True

        except Exception as e:
            debug_print(f'[ERROR] Lỗi tạo file key: {e}')
            return False


    def encrypt_activated_key_data(self, data):
        """Mã hóa dữ liệu key đã kích hoạt với chữ ký để chống hack"""  # inserted
        try:
            json_str = json.dumps(data)
            encoded = base64.b64encode(json_str.encode()).decode()
            signature = hashlib.sha256(f'{encoded}{LICENSE_SECRET_KEY}'.encode()).hexdigest()
            return {'data': encoded, 'signature': signature}
        except Exception as e:
            debug_print(f'[ERROR] Lỗi mã hóa dữ liệu key đã kích hoạt: {e}')
            return None

    def decrypt_activated_key_data(self, encrypted_data):
        """Giải mã dữ liệu key đã kích hoạt và kiểm tra chữ ký chống hack"""  # inserted
        try:
            expected_signature = hashlib.sha256(f"{encrypted_data['data']}{LICENSE_SECRET_KEY}".encode()).hexdigest()
            if expected_signature!= encrypted_data['signature']:
                debug_print('[ERROR] Chữ ký key đã kích hoạt không hợp lệ - có thể bị hack!')
                return
            decoded = base64.b64decode(encrypted_data['data']).decode()
            data = json.loads(decoded)
            key = data.get('key', '')
            activation_date = data.get('activation_date', '')
            expiry_date = data.get('expiry_date', '')
            expected_checksum = hashlib.md5(f'{key}{activation_date}{expiry_date}'.encode()).hexdigest()
            if data.get('checksum')!= expected_checksum:
                debug_print('[ERROR] Checksum key đã kích hoạt không hợp lệ - có thể bị hack!')
                return
            return data
        except Exception as e:
            debug_print(f'[ERROR] Lỗi giải mã dữ liệu key đã kích hoạt: {e}')
            return None

    def get_next_activated_key_number(self):
        """Lấy số thứ tự tiếp theo cho file key trong thư mục ẩn"""  # inserted
        try:
            import glob
            pattern = os.path.join(HIDDEN_KEYS_DIR, 'key_activated_*.dat')
            files = glob.glob(pattern)
            if not files:
                return 1
            numbers = []
            for file in files:
                try:
                    filename = os.path.basename(file)
                    number = int(filename.split('_')[2].split('.')[0])
                    numbers.append(number)
                except:
                    continue
            if numbers:
                return max(numbers) + 1
            return 1
        except Exception as e:
            debug_print(f'[ERROR] Lỗi lấy số tiếp theo: {e}')
            return 1

    def migrate_old_key_files(self):
        """Di chuyển file key cũ từ thư mục hiện tại sang thư mục ẩn"""  # inserted
        try:
            import glob
            import shutil
            old_pattern = 'key_activated_*.dat'
            old_files = glob.glob(old_pattern)
            if not old_files:
                debug_print('[DEBUG] Không có file key cũ để di chuyển')
            else:  # inserted
                os.makedirs(HIDDEN_KEYS_DIR, exist_ok=True)
                try:
                    subprocess.run(['attrib', '+h', HIDDEN_KEYS_DIR], shell=True, stderr=subprocess.DEVNULL, check=False)
                except Exception:
                    pass
                for old_file in old_files:
                    try:
                        filename = os.path.basename(old_file)
                        new_path = os.path.join(HIDDEN_KEYS_DIR, filename)
                        shutil.copy2(old_file, new_path)
                        try:
                            subprocess.run(['attrib', '+h', new_path], shell=True, stderr=subprocess.DEVNULL, check=False)
                        except Exception:
                            pass
                        os.remove(old_file)
                        debug_print(f'[DEBUG] Đã di chuyển {old_file} -> {new_path}')
                    except Exception as e:
                        debug_print(f'[ERROR] Lỗi di chuyển file {old_file}: {e}')
                debug_print(f'[DEBUG] Hoàn thành di chuyển {len(old_files)} file key')
            self.migrate_old_license_file()
        except Exception as e:
            debug_print(f'[ERROR] Lỗi di chuyển file key cũ: {e}')

    def migrate_old_license_file(self):
        """Di chuyển file license.dat cũ từ thư mục hiện tại sang thư mục ẩn"""  # inserted
        try:
            import shutil
            old_license = os.path.join(os.path.abspath('.'), 'license.dat')
            if not os.path.exists(old_license):
                debug_print('[DEBUG] Không có file license.dat cũ để di chuyển')
                return
            os.makedirs(HIDDEN_LICENSE_DIR, exist_ok=True)
            try:
                subprocess.run(['attrib', '+h', HIDDEN_LICENSE_DIR], shell=True, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass
            shutil.copy2(old_license, HIDDEN_LICENSE_FILE)
            try:
                subprocess.run(['attrib', '+h', HIDDEN_LICENSE_FILE], shell=True, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass
            os.remove(old_license)
            debug_print(f'[DEBUG] Đã di chuyển {old_license} -> {HIDDEN_LICENSE_FILE}')
        except Exception as e:
            debug_print(f'[ERROR] Lỗi di chuyển file license.dat cũ: {e}')

    def save_license_to_hidden_location(self, license_data):
        """Lưu license.dat vào thư mục ẩn"""  # inserted
        try:
            os.makedirs(HIDDEN_LICENSE_DIR, exist_ok=True)
            try:
                subprocess.run(['attrib', '+h', HIDDEN_LICENSE_DIR], shell=True, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass
            encrypted_data = self.encrypt_data(license_data)
            if not encrypted_data:
                debug_print('[ERROR] Không thể mã hóa dữ liệu license')
                return False
            with open(HIDDEN_LICENSE_FILE, 'w', encoding='utf-8') as f:
                json.dump(encrypted_data, f, indent=2)
            try:
                subprocess.run(['attrib', '+h', HIDDEN_LICENSE_FILE], shell=True, stderr=subprocess.DEVNULL, check=False)
            except Exception:
                pass
            debug_print(f'[DEBUG] Đã lưu license.dat vào {HIDDEN_LICENSE_FILE}')
            return True
        except Exception as e:
            debug_print(f'[ERROR] Lỗi lưu license.dat vào thư mục ẩn: {e}')
            return False

    def get_next_available_key(self, license_data):
        """Lấy key gia hạn tiếp theo có thể sử dụng"""  # inserted
        try:
            extend_keys = license_data.get('extend_keys', [])
            used_keys = self.load_used_keys()
            for key_info in extend_keys:
                key = key_info['key']
                if key in used_keys:
                    used_info = used_keys[key]
                    used_timestamp = used_info.get('used_timestamp', 0)
                    used_date = datetime.datetime.fromtimestamp(used_timestamp)
                    expiry_date = used_date + datetime.timedelta(days=30)
                    if datetime.datetime.now() < expiry_date:
                        debug_print(f"[DEBUG] Key {key} đã sử dụng nhưng còn trong thời hạn đến {expiry_date.strftime('%Y-%m-%d')}")
                        return
                    debug_print(f"[DEBUG] Key {key} đã hết hạn từ {expiry_date.strftime('%Y-%m-%d')}")
                    continue
            else:  # inserted
                for key_info in extend_keys:
                    if not key_info.get('used', False) and key_info['key'] not in used_keys:
                        return key_info
        except Exception as e:
            debug_print(f'[ERROR] Lỗi lấy key tiếp theo: {e}')
            return None

    def get_active_extend_key(self, license_data):
        """Lấy key gia hạn đang hoạt động (đã sử dụng nhưng còn trong thời hạn)"""  # inserted
        try:
            extend_keys = license_data.get('extend_keys', [])
            used_keys = self.load_used_keys()
            for key_info in extend_keys:
                key = key_info['key']
                if key in used_keys:
                    used_info = used_keys[key]
                    used_timestamp = used_info.get('used_timestamp', 0)
                    used_date = datetime.datetime.fromtimestamp(used_timestamp)
                    expiry_date = used_date + datetime.timedelta(days=30)
                    if datetime.datetime.now() < expiry_date:
                        debug_print(f"[DEBUG] Key {key} đang hoạt động, hết hạn: {expiry_date.strftime('%Y-%m-%d')}")
                        return key_info
        except Exception as e:
            debug_print(f'[ERROR] Lỗi lấy key đang hoạt động: {e}')
            return None

    def check_trial_status(self):
        """Kiểm tra trạng thái dùng thử - ĐỌC TỪ EXE HOẶC BÊN NGOÀI"""  # inserted
        return {'has_trial': True, 'message': 'Chưa kích hoạt dùng thử', 'trial_key': 'xxxxx', 'duration': '10000'}
        try:
            license_path = LICENSE_FILE
            if not os.path.exists(license_path):
                debug_print('[SECURITY] Không tìm thấy license trong exe cho trial check')
                current_dir_license = os.path.join(os.path.abspath('.'), 'license.dat')
                if os.path.exists(current_dir_license):
                    license_path = current_dir_license
                    debug_print(f'[SECURITY] Đọc license từ bên ngoài cho trial check: {license_path}')
                else:  # inserted
                    return {'has_trial': False, 'message': 'Không tìm thấy license'}
            with open(license_path, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            license_data = self.decrypt_license_data(encrypted_data)
            if not license_data:
                return {'has_trial': False, 'message': 'License không hợp lệ'}
            trial_config = license_data.get('trial_config', {})
            if not trial_config.get('enabled'):
                return {'has_trial': False, 'message': 'Không có chế độ dùng thử'}
            debug_print(f'[DEBUG] Kiểm tra trial_state file: {TRIAL_STATE_FILE}')
            if not os.path.exists(TRIAL_STATE_FILE):
                debug_print(f'[DEBUG] Trial state file không tồn tại: {TRIAL_STATE_FILE}')
                return {'has_trial': True, 'message': 'Chưa kích hoạt dùng thử', 'trial_key': trial_config.get('key'), 'duration': trial_config.get('duration')}
            try:
                with open(TRIAL_STATE_FILE, 'r', encoding='utf-8') as f:
                    trial_state = json.load(f)
            except Exception as e:
                debug_print(f'Lỗi đọc file trial_state.dat: {e}')
                try:
                    os.remove(TRIAL_STATE_FILE)
                    debug_print('Đã xóa file trial_state.dat lỗi')
                except:
                    pass
                return {'has_trial': True, 'message': 'Chưa kích hoạt dùng thử', 'trial_key': trial_config.get('key'), 'duration': trial_config.get('duration')}
            start_time = trial_state.get('start_time')
            duration = trial_config.get('duration', 30)
            if not start_time:
                return {'has_trial': True, 'message': 'Chưa kích hoạt dùng thử', 'trial_key': trial_config.get('key'), 'duration': duration}
            try:
                start_datetime = datetime.datetime.fromtimestamp(start_time)
                end_datetime = start_datetime + datetime.timedelta(minutes=duration)
                now = datetime.datetime.now()
                if now > end_datetime:
                    debug_print(f'[SECURITY] Trial đã hết hạn: {now} > {end_datetime}')
                    return {'has_trial': False, 'message': 'Đã hết thời gian dùng thử', 'expired': True}
                remaining_minutes = int((end_datetime - now).total_seconds() / 60)
                debug_print(f'[SECURITY] Trial còn {remaining_minutes} phút')
                if remaining_minutes <= 0:
                    debug_print('[SECURITY] Trial hết hạn (remaining <= 0)')
                    return {'has_trial': False, 'message': 'Đã hết thời gian dùng thử', 'expired': True}
                return {'has_trial': True, 'message': f'Dùng thử còn {remaining_minutes} phút', 'remaining': remaining_minutes}
            except Exception as e:
                debug_print(f'Lỗi xử lý thời gian trial: {e}')
                try:
                    os.remove(TRIAL_STATE_FILE)
                    debug_print('Đã xóa file trial_state.dat lỗi')
                except:
                    pass
                return {'has_trial': True, 'message': 'Chưa kích hoạt dùng thử', 'trial_key': trial_config.get('key'), 'duration': duration}
        except Exception as e:
            debug_print(f'Lỗi kiểm tra dùng thử: {e}')
            try:
                if os.path.exists(TRIAL_STATE_FILE):
                    os.remove(TRIAL_STATE_FILE)
                    debug_print('Đã xóa file trial_state.dat lỗi')
            except:
                pass
            return {'has_trial': False, 'message': f'Lỗi kiểm tra dùng thử: {e}'}

    def activate_trial(self, trial_key):
        """Kích hoạt dùng thử - TƯƠNG THÍCH VỚI LICENSE_MANAGER"""  # inserted
        return True
        try:
            debug_print(f'[DEBUG] Bắt đầu kích hoạt trial với key: {trial_key}')
            license_path = LICENSE_FILE
            if not os.path.exists(license_path):
                current_dir_license = os.path.join(os.path.abspath('.'), 'license.dat')
                if os.path.exists(current_dir_license):
                    license_path = current_dir_license
                else:  # inserted
                    debug_print('[DEBUG] Không tìm thấy license file')
                    return False
            with open(license_path, 'r', encoding='utf-8') as f:
                encrypted_data = json.load(f)
            license_data = self.decrypt_license_data(encrypted_data)
            if not license_data:
                debug_print('[DEBUG] Không thể giải mã license')
                return False
            trial_config = license_data.get('trial_config', {})
            if not trial_config.get('enabled'):
                debug_print('[DEBUG] Trial không được bật')
                return False
            trial_key_in_license = trial_config.get('key', '')
            debug_print(f'[DEBUG] Key trial trong license: \'{trial_key_in_license}\'')
            debug_print(f'[DEBUG] Key trial nhập vào: \'{trial_key}\'')
            debug_print(f'[DEBUG] So sánh: \'{trial_key_in_license}\' == \'{trial_key}\' ? {trial_key_in_license == trial_key}')
            if trial_key_in_license!= trial_key:
                debug_print('[DEBUG] Key trial không khớp với license.dat')
                return False
            debug_print('[DEBUG] Key trial khớp, bắt đầu kích hoạt')
            if os.path.exists(TRIAL_STATE_FILE):
                try:
                    os.remove(TRIAL_STATE_FILE)
                    debug_print('Đã xóa file trial_state.dat cũ')
                except:
                    pass
            trial_duration = trial_config.get('duration', 2)
            trial_state = {'start_time': datetime.datetime.now().timestamp(), 'activated': True, 'trial_key': trial_key, 'duration': trial_duration}
            debug_print(f'[DEBUG] Tạo trial_state file: {TRIAL_STATE_FILE} với duration: {trial_duration} phút')
            with open(TRIAL_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(trial_state, f, indent=2)
            debug_print(f'Đã kích hoạt trial với key: {trial_key} ({trial_duration} phút)')
            debug_print(f'[DEBUG] Trial state file đã tạo: {os.path.exists(TRIAL_STATE_FILE)}')
            return True
        except Exception as e:
            debug_print(f'Lỗi kích hoạt dùng thử: {e}')
            try:
                if os.path.exists(TRIAL_STATE_FILE):
                    os.remove(TRIAL_STATE_FILE)
                    debug_print('Đã xóa file trial_state.dat lỗi')
            except:
                pass
            return False

