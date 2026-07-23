# -*- coding: utf-8 -*-
"""
Windows Sistem Arac Kutusu - GUI Surumu
Orijinal AracKutusuv4.bat dosyasinin Python + CustomTkinter ile
modern arayuzlu versiyonu.

Derleme: PyInstaller ile .exe yapmak icin BUILD_REHBERI.md dosyasina bakin.
"""

import os
import sys
import ctypes
import queue
import threading
import subprocess
from datetime import datetime

import customtkinter as ctk
from tkinter import messagebox

# ----------------------------------------------------------------------
# Yonetici (Administrator) yetkisi kontrolu ve otomatik yukseltme
# ----------------------------------------------------------------------

def yonetici_mi():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def yonetici_olarak_yeniden_baslat():
    """Uygulamayi 'Yonetici olarak calistir' ile yeniden baslatir."""
    try:
        params = " ".join(f'"{a}"' for a in sys.argv)
        # PyInstaller ile derlenmis .exe calisirken sys.executable exe'nin kendisidir.
        if getattr(sys, "frozen", False):
            exe = sys.executable
            ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        else:
            exe = sys.executable
            script = os.path.abspath(sys.argv[0])
            ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, f'"{script}" {params}', None, 1)
    except Exception as e:
        messagebox.showerror("Hata", f"Yonetici olarak baslatilamadi:\n{e}")
    sys.exit(0)


# ----------------------------------------------------------------------
# Komut tanimlari - orijinal .bat dosyasindaki her kategori ve secenek
# ----------------------------------------------------------------------
# Her komut: dict(
#   ad, aciklama,
#   cmd            -> calistirilacak komut (string), {girdi} yer tutucusu olabilir
#   girdi_iste     -> None ya da kullanicidan istenecek metin
#   onay_iste      -> None ya da onay mesaji (evet/hayir)
#   ozel_fonksiyon -> None ya da python fonksiyonu (cmd yerine calisir)
# )

KATEGORILER = {
    "Sistem Bilgisi": [
        dict(ad="Systeminfo", aciklama="Isletim sistemi, RAM, BIOS bilgileri", cmd="systeminfo"),
        dict(ad="Hostname", aciklama="Bilgisayar adini gosterir", cmd="hostname"),
        dict(ad="Ver", aciklama="Windows surum numarasi", cmd="ver"),
        dict(ad="Islemci Bilgisi", aciklama="CPU model bilgisini gosterir", cmd="wmic cpu get name"),
        dict(ad="RAM Detaylari", aciklama="Bellek modullerinin kapasitesini gosterir", cmd="wmic memorychip get capacity,speed"),
        dict(ad="Driverquery", aciklama="Yuklu suruculeri listeler", cmd="driverquery"),
        dict(ad="DDR RAM Detaylari", aciklama="Bellek modullerinin uretici, hiz, tip bilgisi",
             cmd='powershell -NoProfile -Command "Get-CimInstance Win32_PhysicalMemory | '
                 "Select-Object Manufacturer, BankLabel, @{Name='Capacity(GB)';Expression={$_.Capacity/1GB}}, "
                 "Speed, @{Name='Type';Expression={switch ($_.SMBIOSMemoryType) {20 {'DDR'} 21 {'DDR2'} "
                 "22 {'DDR2 FB-DIMM'} 24 {'DDR3'} 26 {'DDR4'} 34 {'DDR5'} default {'Bilinmeyen'}}}} | "
                 'Format-Table -AutoSize"'),
        dict(ad="BIOS Seri No", aciklama="Anakart/BIOS seri numarasini gosterir",
             cmd='powershell -NoProfile -Command "Get-CimInstance -ClassName Win32_BIOS | Select-Object -ExpandProperty SerialNumber"'),
    ],
    "Ag ve Internet": [
        dict(ad="IPConfig", aciklama="IP adresi ve ag yapilandirmasi", cmd="ipconfig /all"),
        dict(ad="Ping Testi", aciklama="Hedef adrese baglanti/gecikme testi", cmd="ping {girdi}",
             girdi_iste="Adres girin (Ornek: google.com):"),
        dict(ad="NSLookup", aciklama="Alan adinin IP adresini sorgular", cmd="nslookup {girdi}",
             girdi_iste="Alan adi girin:"),
        dict(ad="Netstat", aciklama="Aktif baglantilar ve kullanilan portlar", cmd="netstat -ano"),
        dict(ad="Tracert", aciklama="Hedefe giden ag rotasini izler", cmd="tracert {girdi}",
             girdi_iste="Adres girin:"),
        dict(ad="Getmac", aciklama="Ag adaptorlerinin MAC adresini gosterir", cmd="getmac"),
        dict(ad="ARP Tablosu", aciklama="Yerel agdaki IP-MAC eslesmelerini gosterir", cmd="arp -a"),
        dict(ad="Flush DNS", aciklama="DNS cache'ini temizler", cmd="ipconfig /flushdns"),
    ],
    "Disk ve Dosya Sistemi": [
        dict(ad="SFC Scan", aciklama="Bozuk sistem dosyalarini tarar/onarir", cmd="sfc /scannow"),
        dict(ad="CHKDSK", aciklama="Diskte hata ve bozuk sektor taramasi", cmd="chkdsk {girdi}:",
             girdi_iste="Surucu harfi girin (Ornek: C):"),
        dict(ad="DISM Onarim", aciklama="Windows imajindaki bozukluklari onarir",
             cmd="DISM /Online /Cleanup-Image /RestoreHealth"),
        dict(ad="Disk Listesi", aciklama="Sistemdeki diskleri listeler", cmd="echo list disk | diskpart"),
        dict(ad="Klasor Agaci", aciklama="Bir klasorun alt yapisini gosterir", cmd='tree "{girdi}"',
             girdi_iste="Klasor yolu girin (Ornek: C:\\Users):"),
    ],
    "Islem ve Gorev Yonetimi": [
        dict(ad="Tasklist", aciklama="Calisan tum islemleri listeler", cmd="tasklist"),
        dict(ad="Islem Sonlandir", aciklama="Belirtilen islemi zorla kapatir", cmd="taskkill /IM {girdi} /F",
             girdi_iste="Sonlandirilacak islem adi (Ornek: notepad.exe):",
             onay_iste="Bu islemi zorla sonlandirmak istediginizden emin misiniz?"),
        dict(ad="Zamanlanmis Gorevler", aciklama="Sistemdeki zamanlanmis gorevleri listeler", cmd="schtasks"),
    ],
    "Temizlik ve Bakim": [
        dict(ad="Flush DNS", aciklama="DNS cache'ini temizler", cmd="ipconfig /flushdns"),
        dict(ad="Cache Temizle", aciklama="Gecici dosyalari ve cache'i temizler",
             ozel_fonksiyon="cache_temizle",
             onay_iste="Temp, Prefetch klasorleri ve Geri Donusum Kutusu temizlenecek. Emin misiniz?"),
        dict(ad="Disk Temizleme", aciklama="Windows Disk Temizleme aracini acar", cmd="cleanmgr"),
    ],
    "Guc Yonetimi": [
        dict(ad="Enerji Raporu", aciklama="Enerji verimliligi HTML raporu olusturur (Masaustune kaydedilir)",
             cmd='powercfg -energy -output "%USERPROFILE%\\Desktop\\energy-report.html"'),
        dict(ad="Pil Raporu", aciklama="Batarya kullanim/durum raporu olusturur - dizustu (Masaustune kaydedilir)",
             cmd='powercfg /batteryreport /output "%USERPROFILE%\\Desktop\\battery-report.html"'),
        dict(ad="Guc Planlari", aciklama="Mevcut guc planlarini listeler", cmd="powercfg /list"),
        dict(ad="Yeniden Baslat", aciklama="Bilgisayari yeniden baslatir", cmd="shutdown /r /t 10",
             onay_iste="Bilgisayar 10 saniye icinde yeniden baslatilacak. Emin misiniz?"),
        dict(ad="Kapat", aciklama="Bilgisayari kapatir", cmd="shutdown /s /t 10",
             onay_iste="Bilgisayar 10 saniye icinde kapatilacak. Emin misiniz?"),
    ],
    "Guvenlik ve Kullanici": [
        dict(ad="Whoami", aciklama="Aktif kullanici adini gosterir", cmd="whoami"),
        dict(ad="Whoami Yetkiler", aciklama="Kullanicinin yetkilerini/gruplarini gosterir", cmd="whoami /all"),
        dict(ad="Kullanici Listesi", aciklama="Sistemdeki tum kullanicilari listeler", cmd="net user"),
        dict(ad="Guvenlik Duvari", aciklama="Windows Firewall durumunu gosterir", cmd="netsh advfirewall show allprofiles"),
    ],
    "Yazilim Guncelleme": [
        dict(ad="Guncellemeleri Listele", aciklama="Yuklu olan guncellenebilir programlari gosterir", cmd="winget upgrade"),
        dict(ad="Tumunu Guncelle", aciklama="winget upgrade --all calistirir",
             cmd="winget upgrade --all --accept-source-agreements --accept-package-agreements",
             onay_iste="Tum programlar otomatik olarak en son surume guncellenecek. Devam edilsin mi?"),
    ],
    "Ag Adaptorleri (Wifi/Ethernet)": [
        dict(ad="Adaptorleri Listele", aciklama="Tum ag adaptorlerini ve durumlarini gosterir",
             cmd='powershell -NoProfile -Command "Get-NetAdapter | Format-Table Name, InterfaceDescription, Status, LinkSpeed -AutoSize"'),
        dict(ad="Wifi Devre Disi Birak", aciklama="Kablosuz ag adaptorunu devre disi birakir",
             cmd='powershell -NoProfile -Command "Get-NetAdapter | Where-Object {$_.InterfaceDescription -match \'Wireless|Wi-Fi|802.11\'} | Disable-NetAdapter -Confirm:$false"',
             onay_iste="Wifi adaptoru devre disi birakilacak. Emin misiniz?"),
        dict(ad="Wifi Etkinlestir", aciklama="Kablosuz ag adaptorunu etkinlestirir",
             cmd='powershell -NoProfile -Command "Get-NetAdapter | Where-Object {$_.InterfaceDescription -match \'Wireless|Wi-Fi|802.11\'} | Enable-NetAdapter -Confirm:$false"'),
        dict(ad="Ethernet Devre Disi Birak", aciklama="Ethernet adaptorunu devre disi birakir",
             cmd='powershell -NoProfile -Command "Get-NetAdapter | Where-Object {$_.InterfaceDescription -match \'Ethernet\' -and $_.InterfaceDescription -notmatch \'Virtual|Bluetooth\'} | Disable-NetAdapter -Confirm:$false"',
             onay_iste="Ethernet adaptoru devre disi birakilacak. Emin misiniz?"),
        dict(ad="Ethernet Etkinlestir", aciklama="Ethernet adaptorunu etkinlestirir",
             cmd='powershell -NoProfile -Command "Get-NetAdapter | Where-Object {$_.InterfaceDescription -match \'Ethernet\' -and $_.InterfaceDescription -notmatch \'Virtual|Bluetooth\'} | Enable-NetAdapter -Confirm:$false"'),
    ],
    "Lisans Bilgileri": [
        dict(ad="Windows Lisans Anahtari", aciklama="BIOS'a gomulu OEM anahtarini gosterir (dijital lisansta bos donebilir)",
             cmd='powershell -NoProfile -Command "(Get-CimInstance -ClassName SoftwareLicensingService).OA3xOriginalProductKey"'),
        dict(ad="Windows Aktivasyon Durumu", aciklama="Aktivasyon durumunu detayli gosterir", cmd="slmgr /dli"),
        dict(ad="Office Lisans Durumu", aciklama="Office aktivasyon durumu ve kismi anahtar (son 5 hane)",
             ozel_fonksiyon="office_lisans"),
    ],
}


# ----------------------------------------------------------------------
# Ozel (python-native) fonksiyonlar - .bat icindeki alt-rutinlerin karsiligi
# Her fonksiyon 'log' callback'i alir ve satir satir yazi gonderir.
# ----------------------------------------------------------------------

def cache_temizle(log):
    temp = os.environ.get("TEMP", "")
    log(f"[1/4] Kullanici Temp klasoru temizleniyor... ({temp})")
    _calistir_ve_yaz(f'del /q /f /s "{temp}\\*"', log, sessiz=True)
    _calistir_ve_yaz(f'for /d %i in ("{temp}\\*") do rd /s /q "%i"', log, sessiz=True)

    log("[2/4] Windows Temp klasoru temizleniyor...")
    _calistir_ve_yaz('del /q /f /s "C:\\Windows\\Temp\\*"', log, sessiz=True)
    _calistir_ve_yaz('for /d %i in ("C:\\Windows\\Temp\\*") do rd /s /q "%i"', log, sessiz=True)

    log("[3/4] Prefetch klasoru temizleniyor...")
    _calistir_ve_yaz('del /q /f /s "C:\\Windows\\Prefetch\\*"', log, sessiz=True)

    log("[4/4] Geri Donusum Kutusu bosaltiliyor...")
    _calistir_ve_yaz('rd /s /q "C:\\$Recycle.Bin"', log, sessiz=True)

    log("")
    log("Temizlik tamamlandi.")


def office_lisans(log):
    pf = os.environ.get("ProgramFiles", "C:\\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    adaylar = [
        os.path.join(pf, "Microsoft Office", "Office16", "OSPP.VBS"),
        os.path.join(pf86, "Microsoft Office", "Office16", "OSPP.VBS"),
        os.path.join(pf, "Microsoft Office", "Office15", "OSPP.VBS"),
    ]
    for yol in adaylar:
        if os.path.exists(yol):
            _calistir_ve_yaz(f'cscript //Nologo "{yol}" /dstatus', log)
            return
    log("OSPP.VBS dosyasi bulunamadi. Office kurulu olmayabilir")
    log("veya farkli bir surum/klasor yapisinda olabilir.")


def _calistir_ve_yaz(cmd, log, sessiz=False):
    """Yardimci: tek bir shell komutu calistirir, ciktisini log'a yazar."""
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True,
        )
        for kaynak in (proc.stdout, proc.stderr):
            if kaynak:
                metin = _decode(kaynak)
                if metin.strip() and not sessiz:
                    log(metin.rstrip())
    except Exception as e:
        if not sessiz:
            log(f"[HATA] {e}")


def _decode(b: bytes) -> str:
    for enc in ("utf-8", "cp1254", "cp857", "cp850"):
        try:
            return b.decode(enc)
        except Exception:
            continue
    return b.decode("utf-8", errors="replace")


# ----------------------------------------------------------------------
# Komut calistirma motoru (thread + canli log akisi)
# ----------------------------------------------------------------------

class KomutCalistirici:
    """Bir komutu ayri thread'de calistirip ciktiyi satir satir kuyruga yazar."""

    def __init__(self, log_kuyrugu: queue.Queue):
        self.log_kuyrugu = log_kuyrugu
        self.calisiyor = False

    def _log(self, satir: str):
        self.log_kuyrugu.put(satir)

    def calistir(self, komut: dict, girdi_degeri: str = None, bitince=None):
        thread = threading.Thread(
            target=self._calistir_thread, args=(komut, girdi_degeri, bitince), daemon=True
        )
        thread.start()

    def _calistir_thread(self, komut, girdi_degeri, bitince):
        self.calisiyor = True
        baslik = komut["ad"]
        zaman = datetime.now().strftime("%H:%M:%S")
        self._log(f"\n{'='*70}")
        self._log(f"[{zaman}] ▶ {baslik}")
        self._log(f"{'='*70}")

        try:
            if komut.get("ozel_fonksiyon"):
                fonksiyon = globals()[komut["ozel_fonksiyon"]]
                fonksiyon(self._log)
            else:
                cmd = komut["cmd"]
                if "{girdi}" in cmd:
                    cmd = cmd.replace("{girdi}", girdi_degeri or "")
                self._calistir_akis(cmd)
        except Exception as e:
            self._log(f"[HATA] {e}")
        finally:
            self._log(f"\n[{datetime.now().strftime('%H:%M:%S')}] ✔ Tamamlandi: {baslik}\n")
            self.calisiyor = False
            if bitince:
                bitince()

    def _calistir_akis(self, cmd: str):
        """Komutu calistirir ve ciktiyi satir satir canli olarak log'a basar."""
        proc = subprocess.Popen(
            cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        for satir in iter(proc.stdout.readline, b""):
            self._log(_decode(satir).rstrip("\r\n"))
        proc.stdout.close()
        proc.wait()


# ----------------------------------------------------------------------
# GUI
# ----------------------------------------------------------------------

class AracKutusuApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Windows Sistem Arac Kutusu")
        self.geometry("1150x720")
        self.minsize(950, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.log_kuyrugu = queue.Queue()
        self.calistirici = KomutCalistirici(self.log_kuyrugu)
        self.aktif_kategori = None
        self.calisan_buton = None

        self._arayuz_olustur()
        self._kuyruk_dinle()
        self._admin_durum_goster()

    # ---------------- Arayuz kurulumu ----------------

    def _arayuz_olustur(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sol Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_rowconfigure(99, weight=1)

        ctk.CTkLabel(
            self.sidebar, text="🛠  ARAC KUTUSU",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(24, 4), sticky="w")

        self.admin_label = ctk.CTkLabel(
            self.sidebar, text="", font=ctk.CTkFont(size=12),
            text_color="#8fa"
        )
        self.admin_label.grid(row=1, column=0, padx=20, pady=(0, 16), sticky="w")

        self.kategori_butonlari = {}
        for i, kategori in enumerate(KATEGORILER.keys(), start=2):
            btn = ctk.CTkButton(
                self.sidebar, text=kategori, anchor="w",
                fg_color="transparent", hover_color=("#dce4ee", "#2b2f38"),
                text_color=("black", "white"),
                command=lambda k=kategori: self._kategori_sec(k),
            )
            btn.grid(row=i, column=0, padx=12, pady=3, sticky="ew")
            self.kategori_butonlari[kategori] = btn

        # Alt kisim: tema toggle
        alt_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        alt_frame.grid(row=100, column=0, padx=16, pady=16, sticky="sew")
        ctk.CTkLabel(alt_frame, text="Tema:").pack(side="left", padx=(0, 8))
        self.tema_switch = ctk.CTkSwitch(
            alt_frame, text="Koyu/Acik", command=self._tema_degistir
        )
        self.tema_switch.select()  # varsayilan koyu
        self.tema_switch.pack(side="left")

        # --- Sag Ana Alan ---
        self.ana_alan = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.ana_alan.grid(row=0, column=1, sticky="nsew", padx=16, pady=16)
        self.ana_alan.grid_columnconfigure(0, weight=1)
        self.ana_alan.grid_rowconfigure(1, weight=1)

        self.baslik_label = ctk.CTkLabel(
            self.ana_alan, text="Bir kategori secin",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.baslik_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Komutlar icin kaydirilabilir alan
        self.komut_scroll = ctk.CTkScrollableFrame(self.ana_alan, label_text="")
        self.komut_scroll.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        self.komut_scroll.grid_columnconfigure(0, weight=1)

        # --- Log Paneli ---
        log_frame = ctk.CTkFrame(self.ana_alan)
        log_frame.grid(row=2, column=0, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        self.ana_alan.grid_rowconfigure(2, weight=1)

        ust = ctk.CTkFrame(log_frame, fg_color="transparent")
        ust.grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 0))
        ctk.CTkLabel(ust, text="Konsol / Log", font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkButton(ust, text="Temizle", width=80, command=self._log_temizle).pack(side="right")

        self.log_kutu = ctk.CTkTextbox(
            log_frame, height=260, font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.log_kutu.grid(row=1, column=0, sticky="nsew", padx=8, pady=8)
        log_frame.grid_rowconfigure(1, weight=1)
        self.log_kutu.insert("end", "Hazir. Bir kategori ve komut secin.\n")
        self.log_kutu.configure(state="disabled")

        # ilk kategoriyi ac
        ilk_kategori = next(iter(KATEGORILER))
        self._kategori_sec(ilk_kategori)

    def _admin_durum_goster(self):
        if yonetici_mi():
            self.admin_label.configure(text="✔ Yonetici olarak calisiyor", text_color="#7CFC00")
        else:
            self.admin_label.configure(text="⚠ Yonetici degil", text_color="#FFA500")

    def _tema_degistir(self):
        yeni = "dark" if self.tema_switch.get() else "light"
        ctk.set_appearance_mode(yeni)

    # ---------------- Kategori / komut listesi ----------------

    def _kategori_sec(self, kategori):
        self.aktif_kategori = kategori
        self.baslik_label.configure(text=kategori)

        for k, b in self.kategori_butonlari.items():
            if k == kategori:
                b.configure(fg_color=("#3a7ebf", "#1f538d"))
            else:
                b.configure(fg_color="transparent")

        for w in self.komut_scroll.winfo_children():
            w.destroy()

        for komut in KATEGORILER[kategori]:
            self._komut_satiri_ekle(komut)

    def _komut_satiri_ekle(self, komut):
        satir = ctk.CTkFrame(self.komut_scroll, corner_radius=8)
        satir.grid_columnconfigure(0, weight=1)
        satir.pack(fill="x", pady=5, padx=4)

        metin_frame = ctk.CTkFrame(satir, fg_color="transparent")
        metin_frame.grid(row=0, column=0, sticky="w", padx=12, pady=10)
        ctk.CTkLabel(
            metin_frame, text=komut["ad"], font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            metin_frame, text=komut["aciklama"], font=ctk.CTkFont(size=12),
            text_color=("gray30", "gray70")
        ).pack(anchor="w")

        calistir_btn = ctk.CTkButton(
            satir, text="▶ Calistir", width=110,
            command=lambda k=komut, b_ref=[None]: self._komut_baslat(k, satir)
        )
        calistir_btn.grid(row=0, column=1, padx=12, pady=10)

    # ---------------- Komut calistirma akisi ----------------

    def _komut_baslat(self, komut, satir_widget):
        if self.calistirici.calisiyor:
            messagebox.showinfo("Mesgul", "Su anda baska bir komut calisiyor. Lutfen bitmesini bekleyin.")
            return

        girdi_degeri = None
        if komut.get("girdi_iste"):
            dialog = ctk.CTkInputDialog(text=komut["girdi_iste"], title=komut["ad"])
            girdi_degeri = dialog.get_input()
            if girdi_degeri is None or girdi_degeri.strip() == "":
                return

        if komut.get("onay_iste"):
            onay = messagebox.askyesno("Onay Gerekli", komut["onay_iste"])
            if not onay:
                return

        self._buton_durumu(satir_widget, calisiyor=True)
        self.calistirici.calistir(
            komut, girdi_degeri,
            bitince=lambda: self.after(0, lambda: self._buton_durumu(satir_widget, calisiyor=False))
        )

    def _buton_durumu(self, satir_widget, calisiyor):
        for w in satir_widget.winfo_children():
            if isinstance(w, ctk.CTkButton):
                w.configure(
                    state="disabled" if calisiyor else "normal",
                    text="⏳ Calisiyor..." if calisiyor else "▶ Calistir",
                )

    # ---------------- Log kuyruk dinleme ----------------

    def _kuyruk_dinle(self):
        try:
            while True:
                satir = self.log_kuyrugu.get_nowait()
                self.log_kutu.configure(state="normal")
                self.log_kutu.insert("end", satir + "\n")
                self.log_kutu.see("end")
                self.log_kutu.configure(state="disabled")
        except queue.Empty:
            pass
        self.after(80, self._kuyruk_dinle)

    def _log_temizle(self):
        self.log_kutu.configure(state="normal")
        self.log_kutu.delete("1.0", "end")
        self.log_kutu.configure(state="disabled")


# ----------------------------------------------------------------------
# Giris noktasi
# ----------------------------------------------------------------------

def main():
    # Sadece Windows'ta yonetici kontrolu anlamli; diger platformlarda (test/gelistirme) atla.
    if sys.platform == "win32" and not yonetici_mi():
        # Onay penceresini gostermek icin gecici, gizli bir kok pencere gerekiyor.
        gecici = ctk.CTk()
        gecici.withdraw()
        devam = messagebox.askyesno(
            "Yonetici Yetkisi Gerekli",
            "Bazi araclar (SFC, DISM, ag adaptoru islemleri, chkdsk vb.) yonetici "
            "yetkisi ister.\n\nUygulama simdi yonetici olarak yeniden baslatilsin mi?"
        )
        gecici.destroy()
        if devam:
            yonetici_olarak_yeniden_baslat()
            return
        # Kullanici hayir derse normal (kisitli) modda devam eder

    app = AracKutusuApp()
    app.mainloop()


if __name__ == "__main__":
    main()
