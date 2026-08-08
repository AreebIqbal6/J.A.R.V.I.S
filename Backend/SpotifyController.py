import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Wired to your exact .env keys
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.environ.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080/")

def get_spotify_client():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("!! Spotify keys missing from .env")
        return None
    
    # Scopes grant Jarvis permission to read devices and press 'Play'
    scope = "user-modify-playback-state user-read-playback-state"
    
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=scope,
            open_browser=True 
        ))
        return sp
    except Exception as e:
        print(f"!! Spotify Auth Error: {e}")
        return None

def PlaySpotifyTrack(query):
    sp = get_spotify_client()
    if not sp:
        return "Sir, Spotify credentials are missing or invalid."

    # Clean the text to isolate the song name
    clean_query = query.lower().replace("play", "").replace("on spotify", "").strip()

    try:
        # 1. Search the global database for the song
        results = sp.search(q=clean_query, limit=1, type='track')
        if not results['tracks']['items']:
            return f"I couldn't find {clean_query} on Spotify, sir."

        track_uri = results['tracks']['items'][0]['uri']
        track_name = results['tracks']['items'][0]['name']
        artist_name = results['tracks']['items'][0]['artists'][0]['name']

        # 2. Scan your network for active Spotify devices
        devices = sp.devices()
        
        # --- THE WAKE-UP PROTOCOL ---
        if not devices.get('devices'):
            print("\n>> [SPOTIFY]: No active heartbeat detected. Waking up the desktop app...")
            try:
                # Safely forces Windows to open/wake the Spotify app
                os.startfile("spotify:") 
                # Give it 5 seconds to establish a connection to Spotify's cloud
                time.sleep(5) 
                # Scan for devices again now that the app is awake
                devices = sp.devices() 
            except Exception as e:
                print(f"!! Failed to wake Spotify natively: {e}")
        # ----------------------------

        # If it STILL fails after the wake-up attempt
        if not devices.get('devices'):
            return "Sir, the Spotify app is completely unresponsive. Please open it manually."

        # Target the currently playing device, or default to the first available one
        device_id = None
        for d in devices['devices']:
            if d['is_active']:
                device_id = d['id']
                break
        
        if not device_id and len(devices['devices']) > 0:
            device_id = devices['devices'][0]['id']

        # 3. Fire the playback command directly to the device
        sp.start_playback(device_id=device_id, uris=[track_uri])
        return f"Playing {track_name} by {artist_name} on Spotify."

    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 403:
            return "Sir, Spotify rejected the command. Please ensure you have Premium."
        else:
            return f"Spotify API error: {e}"
    except Exception as e:
        return f"Failed to play on Spotify: {e}"