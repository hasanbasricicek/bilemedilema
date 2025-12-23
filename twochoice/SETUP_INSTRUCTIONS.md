# 🚀 bilemedilema - Kurulum ve Kullanım Talimatları

## 📋 Gereksinimler

- Python 3.8+
- pip
- virtualenv (önerilir)

---

## 🔧 Kurulum Adımları

### 1. Sanal Ortam Oluştur (Önerilir)

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

---

### 2. Gerekli Paketleri Yükle

```bash
pip install -r requirements.txt
```

**Yüklenen Paketler:**
- Django 4.2+
- Django REST Framework
- Django REST Framework SimpleJWT
- Django CORS Headers
- drf-yasg (Swagger/OpenAPI)
- Pillow (Görsel işleme)
- FCM Django (Push notifications)

---

### 3. Veritabanı Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 4. Superuser Oluştur (Opsiyonel)

```bash
python manage.py createsuperuser
```

---

### 5. Sunucuyu Başlat

```bash
python manage.py runserver
```

**Sunucu Adresleri:**
- Web: `http://localhost:8000/`
- Admin: `http://localhost:8000/admin/`
- API Docs: `http://localhost:8000/api/docs/`
- API: `http://localhost:8000/api/v1/`

---

## 📱 Mobil Uygulama İçin API Kullanımı

### API Endpoint'leri

Tüm API endpoint'leri için detaylı dokümantasyon:
- **Swagger UI:** `http://localhost:8000/api/docs/`
- **ReDoc:** `http://localhost:8000/api/redoc/`
- **API README:** `API_README.md` dosyasına bakın

---

### Hızlı Başlangıç

#### 1. Kayıt Ol

```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com",
    "password": "test123456"
  }'
```

#### 2. Giriş Yap

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "password": "test123456"
  }'
```

**Response:**
```json
{
  "user": {...},
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

#### 3. Anket Listesi

```bash
curl -X GET http://localhost:8000/api/v1/posts/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🎯 Yeni Özellikler

### ✅ Tamamlanan Özellikler

1. **REST API Altyapısı**
   - Django REST Framework
   - JWT Authentication
   - Token-based auth
   - 7 gün access token
   - 30 gün refresh token

2. **API Endpoints**
   - Auth (register, login, logout, refresh)
   - Posts (list, detail, vote, results)
   - Notifications (list, mark read, unread count)
   - User (profile, stats)
   - Image Upload (optimize, compress)
   - FCM Token (register)

3. **Sonsuz Kaydırma (Infinite Scroll)**
   - Pagination desteği
   - Sayfa başına 10 kayıt
   - Max 100 kayıt
   - Next/Previous linkler

4. **Görsel Yükleme & Optimizasyon**
   - Otomatik resize (max 1920px)
   - JPEG compression (quality 85%)
   - Format dönüştürme (PNG → JPEG)
   - Boyut optimizasyonu

5. **Push Notification Altyapısı**
   - FCM token kayıt
   - Device type desteği (iOS/Android)
   - Bildirim gönderme hazır

6. **API Dokümantasyonu**
   - Swagger UI
   - ReDoc
   - Interactive API testing

7. **CORS Desteği**
   - Mobil uygulama için
   - Development modunda tüm origin'ler
   - Production için konfigüre edilebilir

---

## 📱 Mobil Uygulama Geliştirme

### React Native ile Başlangıç

#### 1. Expo Projesi Oluştur

```bash
npx create-expo-app bilemedilema-mobile
cd bilemedilema-mobile
```

#### 2. Gerekli Paketleri Yükle

```bash
npm install axios @react-native-async-storage/async-storage
npm install @react-navigation/native @react-navigation/stack
npm install react-native-screens react-native-safe-area-context
```

#### 3. API Service Oluştur

`services/api.js`:
```javascript
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const API_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token interceptor
api.interceptors.request.use(async (config) => {
  const token = await AsyncStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  register: (data) => api.post('/auth/register/', data),
  login: (data) => api.post('/auth/login/', data),
  logout: (data) => api.post('/auth/logout/', data),
};

export const pollsAPI = {
  list: (params) => api.get('/posts/', { params }),
  detail: (id) => api.get(`/posts/${id}/`),
  vote: (id, optionId) => api.post(`/posts/${id}/vote/`, { option_id: optionId }),
  results: (id) => api.get(`/posts/${id}/results/`),
};

export default api;
```

---

## 🔐 Güvenlik

### Production Ayarları

`settings.py` dosyasında:

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://app.yourdomain.com",
]

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

---

## 🧪 Test

### API Test

```bash
# Postman veya cURL ile test edin
# Swagger UI kullanarak interactive test yapın
```

### Unit Test

```bash
python manage.py test
```

---

## 📊 Özellik Listesi

### Tamamlanan (42 Özellik)

1-39. Önceki özellikler
40. Poll Expiry Countdown
41. Post Embed System
42. Premium UI Framework
43. **REST API Infrastructure** 🆕
44. **JWT Authentication** 🆕
45. **Infinite Scroll API** 🆕
46. **Image Upload & Optimization** 🆕
47. **Push Notification Infrastructure** 🆕

---

## 🚀 Sonraki Adımlar

### Mobil Uygulama

1. React Native projesi oluştur
2. API entegrasyonu yap
3. UI/UX tasarımı
4. Push notification entegrasyonu
5. Test
6. App Store / Play Store yayınla

### Backend

1. Push notification gönderme sistemi
2. Rate limiting
3. Caching (Redis)
4. Production deployment
5. Monitoring

---

## 📞 Destek

Sorularınız için:
- API Docs: `http://localhost:8000/api/docs/`
- API README: `API_README.md`

---

## 🎉 Başarılar!

API'niz hazır! Artık mobil uygulama geliştirebilirsiniz! 🚀📱
