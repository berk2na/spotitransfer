from flask import Flask, redirect, request, session, jsonify, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
import time, os, threading, json, secrets
from dotenv import load_dotenv

load_dotenv()

if os.path.exists(".cache"):
    os.remove(".cache")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your_secret_key")

# ─── CONFIG ───
SPOTIFY_CLIENT_ID     = os.environ.get("SPOTIFY_CLIENT_ID", "your_spotify_client_id")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "your_spotify_client_secret")
SPOTIFY_REDIRECT_URI  = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback/spotify")

YT_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID", "your_google_client_id")
YT_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "your_google_client_secret")
YT_REDIRECT_URI  = os.environ.get("GOOGLE_REDIRECT_URI", "http://127.0.0.1:5000/callback/youtube")
YT_SCOPES        = ["https://www.googleapis.com/auth/youtube"]

# Kullanıcı başına YouTube token'larını bellekte sakla
# (Production'da Redis/DB kullanılmalı)
yt_tokens = {}

transfer_status = {}
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"  # localhost için

# ─── HELPERS ───

def get_user_id():
    """Session'dan kullanıcı ID'sini döner"""
    return session.get("spotify_user_id")

def get_youtube_for_user(user_id):
    """Kullanıcıya ait YouTube client'ı döner, token'ı gerekirse yeniler"""
    token_data = yt_tokens.get(user_id)
    if not token_data:
        return None

    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        client_id=YT_CLIENT_ID,
        client_secret=YT_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=YT_SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        yt_tokens[user_id]["access_token"] = creds.token

    return build("youtube", "v3", credentials=creds)


def search_youtube(youtube, track_name, artist_name):
    """YouTube'da şarkıyı arar, topic kanalını tercih eder"""
    query = f"{track_name} {artist_name}"
    try:
        result = youtube.search().list(
            part="snippet",
            q=query,
            type="video",
            videoCategoryId="10",
            maxResults=3
        ).execute()

        items = result.get("items", [])
        if not items:
            return None

        for item in items:
            if "- Topic" in item["snippet"].get("channelTitle", ""):
                return item["id"]["videoId"]

        return items[0]["id"]["videoId"]

    except HttpError:
        return None


def add_to_playlist_with_retry(youtube, playlist_id, video_id, max_retries=3):
    """Retry + exponential backoff ile playlist'e şarkı ekler"""
    for attempt in range(max_retries):
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={"snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id}
                }}
            ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 409:
                return True
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    return False


# ─── ROUTES ───

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/logout/spotify")
def logout_spotify():
    user_id = session.get("spotify_user_id")
    yt_token = yt_tokens.get(user_id)
    
    session.clear()
    
    if yt_token:
        session["yt_token_temp"] = yt_token
    
    if os.path.exists(".spotify_cache"):
        os.remove(".spotify_cache")
    
    return redirect("/")

@app.route("/logout/youtube")
def logout_youtube():
    user_id = get_user_id()
    if user_id and user_id in yt_tokens:
        del yt_tokens[user_id]
    session.pop("yt_connected", None)
    return redirect("/")

# ── Spotify OAuth ──

@app.route("/login/spotify")
def login_spotify():
    sp_oauth = SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=SPOTIFY_REDIRECT_URI,
        scope="playlist-read-private playlist-read-collaborative",
        cache_path=None
    )
    auth_url = sp_oauth.get_authorize_url()
    auth_url += "&show_dialog=true&prompt=login"
    return redirect(auth_url)


@app.route("/callback/spotify")
def callback_spotify():
    import requests as req
    code = request.args.get("code")
    
    token_res = req.post("https://accounts.spotify.com/api/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": SPOTIFY_REDIRECT_URI,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET
    })
    
    token_info = token_res.json()
    session["spotify_token"] = token_info["access_token"]
    
    sp = spotipy.Spotify(auth=session["spotify_token"])
    user = sp.current_user()
    session["spotify_user_id"] = user["id"]
    session["spotify_user_name"] = user["display_name"]
    
    if "yt_token_temp" in session:
        yt_tokens[user["id"]] = session.pop("yt_token_temp")
        session["yt_connected"] = True
    
    return redirect("/")

# ── YouTube OAuth ──

@app.route("/login/youtube")
def login_youtube():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": YT_CLIENT_ID,
                "client_secret": YT_CLIENT_SECRET,
                "redirect_uris": [YT_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=YT_SCOPES,
        redirect_uri=YT_REDIRECT_URI
    )
    auth_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent"
    )
    session["yt_state"] = state
    return redirect(auth_url)


@app.route("/callback/youtube")
def callback_youtube():
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": YT_CLIENT_ID,
                "client_secret": YT_CLIENT_SECRET,
                "redirect_uris": [YT_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=YT_SCOPES,
        redirect_uri=YT_REDIRECT_URI,
        state=session.get("yt_state")
    )
    flow.fetch_token(authorization_response=request.url)
    creds = flow.credentials

    user_id = get_user_id()
    if user_id:
        yt_tokens[user_id] = {
            "access_token": creds.token,
            "refresh_token": creds.refresh_token,
        }
        session["yt_connected"] = True

    return redirect("/")


@app.route("/api/auth/status")
def auth_status():
    user_id = get_user_id()
    yt_ok = bool(
        (user_id and yt_tokens.get(user_id)) or 
        session.get("yt_token_temp")
    )
    return jsonify({
        "spotify": bool(session.get("spotify_token")),
        "youtube": yt_ok,
        "spotify_user": session.get("spotify_user_name")
    })


# ── Spotify API ──

@app.route("/api/playlists")
def api_playlists():
    if not session.get("spotify_token"):
        return jsonify({"error": "not_authenticated"}), 401

    sp = spotipy.Spotify(auth=session["spotify_token"])
    playlists = []

    try:
        results = sp.current_user_playlists(limit=50)
        while results:
            for item in results["items"]:
                if item and item["owner"]["id"] == session.get("spotify_user_id"):
                    tracks_info = item.get("tracks", {})
                    track_count = tracks_info.get("total", 0) if isinstance(tracks_info, dict) else 0
                    playlists.append({
                        "id": item["id"],
                        "name": item["name"],
                        "track_count": track_count,
                        "image": item["images"][0]["url"] if item.get("images") else None,
                        "owner": item["owner"]["display_name"]
                    })
            results = sp.next(results) if results["next"] else None

        return jsonify({
            "playlists": playlists,
            "user": session.get("spotify_user_name")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/playlist/<playlist_id>/tracks")
def api_tracks(playlist_id):
    if not session.get("spotify_token"):
        return jsonify({"error": "not_authenticated"}), 401

    sp = spotipy.Spotify(auth=session["spotify_token"])
    tracks = []

    try:
        results = sp.playlist_tracks(playlist_id)
        while results:
            for item in results["items"]:
                track = item.get("item") or item.get("track")
                if track and isinstance(track, dict):
                    tracks.append({
                        "name": track["name"],
                        "artist": track["artists"][0]["name"],
                        "album": track["album"]["name"],
                        "duration": track["duration_ms"]
                    })
            results = sp.next(results) if results["next"] else None

    except Exception as e:
        return jsonify({"error": str(e), "tracks": []}), 403

    return jsonify({"tracks": tracks})


# ── Transfer ──

def do_transfer(job_id, user_id, playlist_name, tracks):
    transfer_status[job_id] = {
        "status": "running",
        "total": len(tracks),
        "done": 0,
        "not_found": [],
        "playlist_id": None
    }

    try:
        youtube = get_youtube_for_user(user_id)
        if not youtube:
            raise Exception("YouTube bağlantısı bulunamadı. Lütfen tekrar bağlanın.")

        # Playlist oluştur
        playlist = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": playlist_name,
                    "description": f"Spotify'dan aktarıldı: {playlist_name}"
                },
                "status": {"privacyStatus": "private"}
            }
        ).execute()

        playlist_id = playlist["id"]
        transfer_status[job_id]["playlist_id"] = playlist_id

        for track in tracks:
            video_id = search_youtube(youtube, track["name"], track["artist"])

            if video_id:
                success = add_to_playlist_with_retry(youtube, playlist_id, video_id)
                if not success:
                    transfer_status[job_id]["not_found"].append(
                        f"{track['name']} — {track['artist']}"
                    )
            else:
                transfer_status[job_id]["not_found"].append(
                    f"{track['name']} — {track['artist']}"
                )

            transfer_status[job_id]["done"] += 1
            time.sleep(0.3)

        transfer_status[job_id]["status"] = "done"

    except HttpError as e:
        if e.resp.status == 403 and "quotaExceeded" in str(e):
            transfer_status[job_id]["status"] = "error"
            transfer_status[job_id]["error"] = "YouTube API günlük quota aşıldı. Yarın tekrar deneyin."
        else:
            transfer_status[job_id]["status"] = "error"
            transfer_status[job_id]["error"] = str(e)
    except Exception as e:
        transfer_status[job_id]["status"] = "error"
        transfer_status[job_id]["error"] = str(e)


@app.route("/api/transfer", methods=["POST"])
def api_transfer():
    if not session.get("spotify_token"):
        return jsonify({"error": "not_authenticated"}), 401

    user_id = get_user_id()
    if not yt_tokens.get(user_id):
        return jsonify({"error": "youtube_not_connected"}), 401

    data = request.json
    playlist_name = data.get("playlist_name")
    tracks = data.get("tracks", [])
    job_id = f"job_{user_id}_{int(time.time())}"

    thread = threading.Thread(
        target=do_transfer,
        args=(job_id, user_id, playlist_name, tracks)
    )
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/transfer/status/<job_id>")
def api_transfer_status(job_id):
    status = transfer_status.get(job_id)
    if not status:
        return jsonify({"error": "job not found"}), 404
    return jsonify(status)


if __name__ == "__main__":
    import webbrowser
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
