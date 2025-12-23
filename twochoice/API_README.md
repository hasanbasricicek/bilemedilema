# bilemedilema REST API Documentation

## 🚀 API Kurulumu

### 1. Gerekli Paketleri Yükle

```bash
pip install -r requirements.txt
```

### 2. Veritabanı Migration

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Sunucuyu Başlat

```bash
python manage.py runserver
```

---

## 📚 API Endpoints

### Base URL
```
http://localhost:8000/api/v1/
```

### API Dokümantasyonu
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

---

## 🔐 Authentication (Kimlik Doğrulama)

### 1. Kayıt Ol (Register)

**Endpoint:** `POST /api/v1/auth/register/`

**Request Body:**
```json
{
  "username": "ahmet123",
  "email": "ahmet@example.com",
  "password": "güçlüşifre123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "ahmet123",
    "email": "ahmet@example.com",
    "date_joined": "2025-12-23T00:00:00Z"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 2. Giriş Yap (Login)

**Endpoint:** `POST /api/v1/auth/login/`

**Request Body:**
```json
{
  "username": "ahmet123",
  "password": "güçlüşifre123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "ahmet123",
    "email": "ahmet@example.com"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 3. Token Yenile (Refresh Token)

**Endpoint:** `POST /api/v1/auth/token/refresh/`

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:**
```json
{
  "access": "yeni_access_token..."
}
```

---

## 📊 Polls (Anketler)

### 1. Anket Listesi (Sonsuz Kaydırma)

**Endpoint:** `GET /api/v1/posts/`

**Query Parameters:**
- `page`: Sayfa numarası (default: 1)
- `page_size`: Sayfa başına kayıt (default: 10, max: 100)
- `topic`: Konu filtresi (technology, lifestyle, entertainment, sports, education, general)
- `sort`: Sıralama (new, popular, trend)
- `search`: Arama terimi

**Headers:**
```
Authorization: Bearer {access_token}
```

**Örnek Request:**
```
GET /api/v1/posts/?page=1&page_size=10&sort=popular&topic=technology
```

**Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/v1/posts/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Hangisi daha iyi?",
      "description": "Sizce hangisi?",
      "topic": "technology",
      "author": {
        "id": 1,
        "username": "ahmet123"
      },
      "poll_options": [
        {
          "id": 1,
          "option_text": "Seçenek A",
          "vote_count": 45
        },
        {
          "id": 2,
          "option_text": "Seçenek B",
          "vote_count": 30
        }
      ],
      "vote_count": 75,
      "comment_count": 12,
      "created_at": "2025-12-23T00:00:00Z",
      "user_voted": true,
      "user_vote_option": 1
    }
  ]
}
```

---

### 2. Anket Detayı

**Endpoint:** `GET /api/v1/posts/{id}/`

**Response:**
```json
{
  "id": 1,
  "title": "Hangisi daha iyi?",
  "poll_options": [...],
  "comments": [
    {
      "id": 1,
      "author": {
        "id": 2,
        "username": "zeynep99"
      },
      "content": "Harika anket!",
      "created_at": "2025-12-23T00:00:00Z"
    }
  ]
}
```

---

### 3. Oy Ver

**Endpoint:** `POST /api/v1/posts/{id}/vote/`

**Request Body:**
```json
{
  "option_id": 1
}
```

**Response:**
```json
{
  "message": "Oy kaydedildi",
  "post": {
    "id": 1,
    "title": "Hangisi daha iyi?",
    "poll_options": [...]
  }
}
```

---

### 4. Anket Sonuçları

**Endpoint:** `GET /api/v1/posts/{id}/results/`

**Response:**
```json
{
  "total_votes": 75,
  "results": [
    {
      "option": {
        "id": 1,
        "option_text": "Seçenek A"
      },
      "vote_count": 45,
      "percentage": 60.0
    },
    {
      "option": {
        "id": 2,
        "option_text": "Seçenek B"
      },
      "vote_count": 30,
      "percentage": 40.0
    }
  ]
}
```

---

## 🔔 Notifications (Bildirimler)

### 1. Bildirim Listesi

**Endpoint:** `GET /api/v1/notifications/`

**Response:**
```json
{
  "count": 25,
  "results": [
    {
      "id": 1,
      "actor": {
        "id": 2,
        "username": "zeynep99"
      },
      "verb": "anketine oy verdi",
      "post_title": "Hangisi daha iyi?",
      "post": 1,
      "is_read": false,
      "created_at": "2025-12-23T00:00:00Z"
    }
  ]
}
```

---

### 2. Bildirimi Okundu İşaretle

**Endpoint:** `POST /api/v1/notifications/{id}/mark_read/`

**Response:**
```json
{
  "message": "Bildirim okundu olarak işaretlendi"
}
```

---

### 3. Tüm Bildirimleri Okundu İşaretle

**Endpoint:** `POST /api/v1/notifications/mark_all_read/`

---

### 4. Okunmamış Bildirim Sayısı

**Endpoint:** `GET /api/v1/notifications/unread_count/`

**Response:**
```json
{
  "unread_count": 5
}
```

---

## 👤 User (Kullanıcı)

### Kullanıcı Profili

**Endpoint:** `GET /api/v1/users/{username}/`

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "ahmet123",
    "email": "ahmet@example.com"
  },
  "stats": {
    "posts": 15,
    "votes": 120
  }
}
```

---

## 📱 Push Notifications (FCM)

### FCM Token Kaydet

**Endpoint:** `POST /api/v1/fcm/register/`

**Request Body:**
```json
{
  "token": "fcm_device_token_here",
  "device_type": "android"
}
```

**Response:**
```json
{
  "message": "FCM token kaydedildi",
  "token": "fcm_device_token_here"
}
```

---

## 🔒 Authentication Header

Tüm korumalı endpoint'ler için:

```
Authorization: Bearer {access_token}
```

---

## 📱 Mobil Uygulama Örnek Kullanım

### React Native ile Login

```javascript
const login = async (username, password) => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/auth/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username, password }),
    });
    
    const data = await response.json();
    
    // Token'ı kaydet
    await AsyncStorage.setItem('access_token', data.tokens.access);
    await AsyncStorage.setItem('refresh_token', data.tokens.refresh);
    
    return data;
  } catch (error) {
    console.error('Login error:', error);
  }
};
```

---

### Anket Listesi Çekme

```javascript
const fetchPolls = async (page = 1) => {
  try {
    const token = await AsyncStorage.getItem('access_token');
    
    const response = await fetch(
      `http://localhost:8000/api/v1/posts/?page=${page}&page_size=10`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );
    
    const data = await response.json();
    return data.results;
  } catch (error) {
    console.error('Fetch polls error:', error);
  }
};
```

---

### Oy Verme

```javascript
const vote = async (postId, optionId) => {
  try {
    const token = await AsyncStorage.getItem('access_token');
    
    const response = await fetch(
      `http://localhost:8000/api/v1/posts/${postId}/vote/`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ option_id: optionId }),
      }
    );
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Vote error:', error);
  }
};
```

---

## 🎯 Özellikler

✅ JWT Authentication
✅ Sonsuz Kaydırma (Infinite Scroll)
✅ Filtreleme ve Sıralama
✅ Real-time Bildirimler
✅ Push Notification Desteği
✅ CORS Desteği
✅ API Dokümantasyonu (Swagger)
✅ Mobil Uygulama Hazır

---

## 🔧 Geliştirme Notları

### Token Süresi
- Access Token: 7 gün
- Refresh Token: 30 gün

### Rate Limiting
Şu anda aktif değil, production'da eklenecek.

### CORS
Development modunda tüm origin'lere izin var.
Production'da sadece belirli domain'lere izin verilecek.

---

## 📞 Destek

API ile ilgili sorularınız için:
- Email: info@bilemedilema.com
- API Docs: http://localhost:8000/api/docs/
