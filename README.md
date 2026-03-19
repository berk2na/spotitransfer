# Spotitransfer

> 🇹🇷 Türkçe açıklama aşağıda mevcuttur.

A web application that transfers your Spotify playlists to YouTube Music. It authenticates with both platforms via OAuth 2.0, fetches your Spotify playlists, searches for each track on YouTube, and creates a matching playlist on your YouTube account.

## Features

- Spotify & YouTube OAuth 2.0 login
- Browse and preview your Spotify playlists
- Real-time transfer progress tracking
- Multi-user support with per-user token isolation
- Handles large playlists with pagination
- Retries failed requests with exponential backoff
- Prioritizes official YouTube Music "Topic" channel results

## Tech Stack

- **Backend:** Python, Flask
- **APIs:** Spotify Web API, YouTube Data API v3
- **Auth:** OAuth 2.0 (Spotify + Google)
- **Frontend:** HTML/CSS/JS

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/spotitransfer.git
cd spotitransfer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the root directory:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback/spotify

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/callback/youtube

SECRET_KEY=your_random_secret_key
```

### 4. Spotify Setup

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add `http://127.0.0.1:5000/callback/spotify` to **Redirect URIs**
4. Copy your **Client ID** and **Client Secret** into `.env`
5. Under **User Management**, add the Spotify email addresses of anyone who will use the app (required while in Development Mode)

### 5. Google / YouTube Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **YouTube Data API v3**
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**
5. Select **Web application**
6. Add `http://127.0.0.1:5000/callback/youtube` to **Authorized redirect URIs**
7. Copy your **Client ID** and **Client Secret** into `.env`
8. Go to **OAuth consent screen → Test users** and add the Google accounts that will use the app

### 6. Run the app

```bash
python app.py
```

## Usage

1. Click **Connect with Spotify** and log in
2. Click **Connect with YouTube** and log in
3. Browse your playlists and select one
4. Click **Preview** to see the tracks
5. Click **Transfer to YouTube Music**
6. Wait for the transfer to complete — a new private playlist will appear in your YouTube account

## Notes

- YouTube Data API v3 has a daily quota of **10,000 units**. Each song search costs ~100 units, so roughly 95 songs can be transferred per day per Google Cloud project.
- Tokens are stored in memory — restarting the server will require users to log in again. For production use, replace with a database or Redis.
- To use with more than 25 Spotify users or 100 Google users, the respective apps need to go through platform verification.


# Spotitransfer (Türkçe)

Spotify playlistlerini YouTube Music'e aktaran bir web uygulaması. Her iki platform için OAuth 2.0 ile kimlik doğrulaması yapar, Spotify playlistlerini çeker, her şarkıyı YouTube'da arar ve YouTube hesabında eşleşen bir playlist oluşturur.

## Özellikler

- Spotify ve YouTube OAuth 2.0 girişi
- Spotify playlistlerini önizleme
- Gerçek zamanlı aktarım takibi
- Kullanıcı başına token izolasyonuyla çoklu kullanıcı desteği
- Büyük playlistlerde sayfalama desteği
- Başarısız isteklerde exponential backoff ile yeniden deneme
- Resmi YouTube Music "Topic" kanalı sonuçlarını önceliklendirir

## Teknolojiler

- **Backend:** Python, Flask
- **API'ler:** Spotify Web API, YouTube Data API v3
- **Kimlik Doğrulama:** OAuth 2.0 (Spotify + Google)
- **Frontend:** HTML/CSS/JS

## Kurulum

### 1. Repoyu klonla

```bash
git clone https://github.com/YOUR_USERNAME/spotitransfer.git
cd spotitransfer
```

### 2. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
```

### 3. Ortam değişkenlerini ayarla

Proje klasöründe bir `.env` dosyası oluştur:

```env
SPOTIFY_CLIENT_ID=spotify_client_id
SPOTIFY_CLIENT_SECRET=spotify_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:5000/callback/spotify

GOOGLE_CLIENT_ID=google_client_id
GOOGLE_CLIENT_SECRET=google_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:5000/callback/youtube

SECRET_KEY=rastgele_uzun_bir_anahtar
```

### 4. Spotify Kurulumu

1. [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) adresine git
2. Yeni bir uygulama oluştur
3. **Redirect URIs** kısmına `http://127.0.0.1:5000/callback/spotify` ekle
4. **Client ID** ve **Client Secret**'ı `.env` dosyasına yapıştır
5. **User Management** kısmına uygulamayı kullanacak kişilerin Spotify email adreslerini ekle (Development Mode'da zorunlu)

### 5. Google / YouTube Kurulumu

1. [Google Cloud Console](https://console.cloud.google.com) adresine git
2. Yeni bir proje oluştur
3. **YouTube Data API v3**'ü etkinleştir
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID** yolunu izle
5. **Web application** seç
6. **Authorized redirect URIs** kısmına `http://127.0.0.1:5000/callback/youtube` ekle
7. **Client ID** ve **Client Secret**'ı `.env` dosyasına yapıştır
8. **OAuth consent screen → Test users** kısmına uygulamayı kullanacak Google hesaplarını ekle

### 6. Uygulamayı çalıştır

```bash
python app.py
```

## Kullanım

1. **Spotify ile Bağlan** butonuna tıkla ve giriş yap
2. **YouTube ile Bağlan** butonuna tıkla ve giriş yap
3. Playlistlerini gözat ve birini seç
4. **Önizle** butonuna tıklayarak şarkıları gör
5. **YouTube Music'e Aktar** butonuna tıkla
6. Aktarım tamamlanana kadar bekle — YouTube hesabında yeni bir özel playlist oluşacak

## Notlar

- YouTube Data API v3'ün günlük **10.000 unit** kotası vardır. Her şarkı araması ~100 unit harcadığından günlük yaklaşık 95 şarkı aktarılabilir.
- Token'lar bellekte saklanır — sunucu yeniden başlatılırsa kullanıcıların tekrar giriş yapması gerekir. Production ortamı için veritabanı veya Redis kullanılması önerilir.
- 25'ten fazla Spotify kullanıcısı veya 100'den fazla Google kullanıcısı için ilgili platformların doğrulama süreçlerinden geçilmesi gerekir.
