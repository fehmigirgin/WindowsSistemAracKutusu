✨ Özellikler
10 kategori altında toplanmış, ~30 sistem komutuna tek tıkla erişim:
🖥️ Sistem Bilgisi	Systeminfo, CPU/BIOS/RAM detayları, DDR modül bilgisi, sürücü listesi
🌐 Ağ ve İnternet	IPConfig, ping, tracert, nslookup, netstat, ARP tablosu, DNS flush
💾 Disk ve Dosya Sistemi	SFC, DISM onarımı, CHKDSK, disk listesi, klasör ağacı
⚙️ İşlem ve Görev Yönetimi	Tasklist, işlem sonlandırma, zamanlanmış görevler
🧹 Temizlik ve Bakım	Temp/cache/Geri Dönüşüm Kutusu temizliği, Disk Temizleme
🔋 Güç Yönetimi	Enerji/pil raporu, güç planları, yeniden başlatma/kapatma
🔒 Güvenlik ve Kullanıcı	Whoami, kullanıcı listesi, Windows Firewall durumu
🔄 Yazılım Güncelleme	winget ile güncelleme listesi ve toplu güncelleme
📡 Ağ Adaptörleri	Wifi/Ethernet adaptörlerini listeleme, etkinleştirme/devre dışı bırakma
🔑 Lisans Bilgileri	Windows aktivasyon durumu, lisans anahtarı, Office lisans kontrolü

Arayüz ve Mimari
•	🎨 CustomTkinter ile modern, koyu/açık tema destekli arayüz
•	🧵 Thread tabanlı komut çalıştırma — uzun süren işlemler (SFC, DISM vb.) arayüzü kilitlemez, çıktı canlı olarak akar
•	📋 Queue tabanlı, thread-safe loglama
•	🔐 Windows UAC entegrasyonu — gerektiğinde otomatik yönetici yükseltmesi
•	⚠️ Riskli işlemler (restart, shutdown, adaptör kapatma, toplu güncelleme, işlem sonlandırma) için onay mekanizması
•	📦 PyInstaller ile bağımsız çalışan tek dosyalık .exe
