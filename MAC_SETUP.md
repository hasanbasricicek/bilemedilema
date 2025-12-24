# 🍎 Mac'te Kurulum Rehberi - Bilemedilema

Bu Django projesini Mac bilgisayarınızda çalıştırmak için aşağıdaki adımları takip edin.

## 📋 Ön Gereksinimler

Mac'inizde aşağıdakilerin kurulu olması gerekiyor:
- Python 3.8 veya üzeri
- pip (Python paket yöneticisi)
- Git

### Python Kontrolü
Terminal'i açın ve şu komutu çalıştırın:
```bash
python3 --version
```

## 🚀 Kurulum Adımları

### 1. Projeyi Mac'e Aktarma

**Seçenek A: Git ile (Önerilen)**
```bash
# GitHub'a push ettiyseniz
git clone https://github.com/hasanbasricicek/bilemedilema.git
cd bilemedilema
```

**Seçenek B: Manuel Transfer**
- Projeyi USB, cloud storage veya network üzerinden Mac'e kopyalayın
- Terminal'de proje klasörüne gidin:
```bash
cd ~/Desktop/testapp
```

### 2. Virtual Environment Oluşturma

```bash
# Virtual environment oluştur
python3 -m venv venv

# Virtual environment'ı aktifleştir (Mac/Linux)
source venv/bin/activate
```

Aktivasyon sonrası terminal'inizde `(venv)` görmelisiniz.

### 3. Bağımlılıkları Yükleme

```bash
# twochoice klasörüne git
cd twochoice

# Gerekli paketleri yükle
pip install -r ../requirements.txt
```

### 4. Database Kurulumu

```bash
# Migration'ları çalıştır
python3 manage.py migrate

# Superuser oluştur (admin paneli için)
python3 manage.py createsuperuser
```

Kullanıcı adı, email ve şifre girmeniz istenecek.

### 5. Static Dosyaları Toplama (Opsiyonel)

```bash
python3 manage.py collectstatic --noinput
```

### 6. Sunucuyu Başlatma

```bash
python3 manage.py runserver
```

Tarayıcınızda şu adresi açın: **http://localhost:8000**

## 🔧 Yaygın Sorunlar ve Çözümleri

### Problem: `python3` komutu bulunamıyor
**Çözüm:** Python'u Homebrew ile kurun:
```bash
# Homebrew kurulu değilse önce onu kurun
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Python'u kurun
brew install python3
```

### Problem: pip paket yüklenemiyor
**Çözüm:** pip'i güncelleyin:
```bash
python3 -m pip install --upgrade pip
```

### Problem: Pillow kurulumu hatası
**Çözüm:** Xcode Command Line Tools kurun:
```bash
xcode-select --install
```

### Problem: psycopg hatası (PostgreSQL)
**Çözüm:** Development için SQLite kullanabilirsiniz. `settings.py` dosyasında database ayarlarını kontrol edin.

## 📁 Proje Yapısı

```
testapp/
├── twochoice/                 # Ana Django projesi
│   ├── manage.py             # Django yönetim scripti
│   ├── twochoice/            # Proje ayarları
│   │   └── settings.py       # Konfigürasyon
│   └── twochoice_app/        # Ana uygulama
│       ├── models.py         # Database modelleri
│       ├── views.py          # View fonksiyonları
│       └── templates/        # HTML şablonları
├── requirements.txt          # Python bağımlılıkları
└── venv/                     # Virtual environment (oluşturulacak)
```

## 🎯 Önemli Komutlar

### Virtual Environment
```bash
# Aktifleştir
source venv/bin/activate

# Deaktifleştir
deactivate
```

### Django Komutları
```bash
# Sunucuyu başlat
python3 manage.py runserver

# Migration oluştur
python3 manage.py makemigrations

# Migration'ları uygula
python3 manage.py migrate

# Admin kullanıcısı oluştur
python3 manage.py createsuperuser

# Testleri çalıştır
python3 manage.py test twochoice_app
```

## 🔐 Admin Panel

Admin paneline erişim:
- **URL:** http://localhost:8000/admin/
- **Kullanıcı:** Adım 4'te oluşturduğunuz superuser bilgileri

## 📊 Özellikler

- ✅ Anket oluşturma ve oylama
- ✅ Kullanıcı profilleri
- ✅ Yorum sistemi
- ✅ Bildirimler
- ✅ Hashtag desteği
- ✅ Analytics
- ✅ Rate limiting
- ✅ Cache mekanizması
- ✅ Accessibility (WCAG 2.1 AA)

## 🛠️ Development Ortamı

### VS Code Önerileri
```bash
# VS Code'u açmak için
code .
```

Önerilen VS Code eklentileri:
- Python
- Django
- Pylance
- GitLens

### Debug Modu
`settings.py` dosyasında:
```python
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

## 📚 Ek Dokümantasyon

- **IMPROVEMENTS.md** - Detaylı iyileştirme raporu
- **ACCESSIBILITY.md** - Erişilebilirlik rehberi
- **README_IMPROVEMENTS.md** - İyileştirmeler özeti
- **FEATURE_ROADMAP.md** - Özellik yol haritası

## 🔄 Windows'tan Mac'e Geçiş Notları

### Dosya Yolları
- Windows: `c:\Users\hasan\Desktop\testapp`
- Mac: `~/Desktop/testapp` veya `/Users/[kullanıcıadı]/Desktop/testapp`

### Komut Farklılıkları
| Windows | Mac/Linux |
|---------|-----------|
| `python` | `python3` |
| `venv\Scripts\activate` | `source venv/bin/activate` |
| `dir` | `ls` |
| `cls` | `clear` |

### Line Endings
Git otomatik olarak line ending'leri düzeltir, ancak sorun yaşarsanız:
```bash
git config --global core.autocrlf input
```

## 🚨 Güvenlik Notları

Production'a alırken:
1. `DEBUG = False` yapın
2. `SECRET_KEY`'i değiştirin
3. `ALLOWED_HOSTS`'u güncelleyin
4. PostgreSQL kullanın (SQLite yerine)
5. Redis cache backend kullanın
6. HTTPS kullanın

## 💡 İpuçları

1. **Virtual environment'ı her zaman aktif tutun** çalışırken
2. **Değişiklik yaptıktan sonra** sunucuyu yeniden başlatın (Ctrl+C sonra tekrar `runserver`)
3. **Database değişikliklerinde** migration oluşturmayı unutmayın
4. **Git kullanın** değişikliklerinizi takip etmek için

## 📞 Yardım

Sorun yaşarsanız:
1. Terminal'deki hata mesajlarını okuyun
2. Virtual environment'ın aktif olduğundan emin olun
3. Tüm bağımlılıkların kurulu olduğunu kontrol edin
4. Logları kontrol edin

---

**Son Güncelleme:** 24 Aralık 2024
**Platform:** macOS
**Python Versiyonu:** 3.8+
**Django Versiyonu:** 5.1.4
