# 🛠️ Windows Sistem Araç Kutusu

Windows için geliştirilmiş, modern arayüzlü, tek dosyalık (.exe) masaüstü
sistem yönetim uygulaması. Sistem tanılama, ağ testleri, disk bakımı,
güç yönetimi ve daha fazlasını tek bir yerden, tek tıkla çalıştırmanı
sağlar.

![Platform](https://img.shields.io/badge/platform-Windows-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 📸 Ekran Görüntüleri

<!-- Ekran görüntülerini buraya ekle, örnek: -->
<!-- ![Ana Ekran](screenshots/anaekran.png) -->
<!-- ![Ağ Adaptörleri](screenshots/ag-adaptorleri.png) -->

## ✨ Özellikler

10 kategori altında toplanmış, ~30 sistem komutuna tek tıkla erişim:

| Kategori | İçerik |
|---|---|
| 🖥️ **Sistem Bilgisi** | Systeminfo, CPU/BIOS/RAM detayları, DDR modül bilgisi, sürücü listesi |
| 🌐 **Ağ ve İnternet** | IPConfig, ping, tracert, nslookup, netstat, ARP tablosu, DNS flush |
| 💾 **Disk ve Dosya Sistemi** | SFC, DISM onarımı, CHKDSK, disk listesi, klasör ağacı |
| ⚙️ **İşlem ve Görev Yönetimi** | Tasklist, işlem sonlandırma, zamanlanmış görevler |
| 🧹 **Temizlik ve Bakım** | Temp/cache/Geri Dönüşüm Kutusu temizliği, Disk Temizleme |
| 🔋 **Güç Yönetimi** | Enerji/pil raporu, güç planları, yeniden başlatma/kapatma |
| 🔒 **Güvenlik ve Kullanıcı** | Whoami, kullanıcı listesi, Windows Firewall durumu |
| 🔄 **Yazılım Güncelleme** | winget ile güncelleme listesi ve toplu güncelleme |
| 📡 **Ağ Adaptörleri** | Wifi/Ethernet adaptörlerini listeleme, etkinleştirme/devre dışı bırakma |
| 🔑 **Lisans Bilgileri** | Windows aktivasyon durumu, lisans anahtarı, Office lisans kontrolü |

### Arayüz ve Mimari

- 🎨 CustomTkinter ile modern, koyu/açık tema destekli arayüz
- 🧵 Thread tabanlı komut çalıştırma — uzun süren işlemler (SFC, DISM vb.)
  arayüzü kilitlemez, çıktı canlı olarak akar
- 📋 Queue tabanlı, thread-safe loglama
- 🔐 Windows UAC entegrasyonu — gerektiğinde otomatik yönetici yükseltmesi
- ⚠️ Riskli işlemler (restart, shutdown, adaptör kapatma, toplu güncelleme,
  işlem sonlandırma) için onay mekanizması
- 📦 PyInstaller ile bağımsız çalışan tek dosyalık `.exe`

## 🚀 Kurulum

### Hazır .exe ile (önerilen)

[Releases](../../releases) sekmesinden en güncel `AracKutusu.exe`
dosyasını indir, çalıştır. Python kurulumu gerekmez.

### Kaynak koddan çalıştırma

```bash
git clone https://github.com/kullanici-adi/repo-adi.git
cd repo-adi
pip install -r requirements.txt
python main.py
```

### Kendi .exe'ni derlemek istersen

```bash
python -m PyInstaller --onefile --windowed --name AracKutusu --uac-admin main.py
```

Detaylı, adım adım derleme rehberi için `BUILD_REHBERI.md` dosyasına bakabilirsin.

## 🧰 Kullanılan Teknolojiler

- **Python 3.10+**
- **CustomTkinter** — arayüz
- **PyInstaller** — paketleme/dağıtım
- **threading / queue** — asenkron komut çalıştırma ve canlı log akışı
- **subprocess** — Windows komutlarını çalıştırma
- **ctypes** — Windows UAC/yönetici yetkisi kontrolü

## ⚠️ Uyarı

Bu araç gerçek sistem komutları çalıştırır (chkdsk, shutdown, ağ adaptörü
devre dışı bırakma, toplu güncelleme vb.). Riskli işlemler onay penceresi
ile korunsa da, ne yaptığından emin olmadığın komutları çalıştırmadan önce
dikkatli ol.

## 📄 Lisans

MIT License — özgürce kullanabilir, değiştirebilir ve dağıtabilirsin.

## 🤝 Katkı

Pull request'ler ve öneriler memnuniyetle karşılanır. Yeni bir komut
eklemek için `main.py` içindeki `KATEGORILER` sözlüğüne uygun formatta
bir satır eklemen yeterli.
