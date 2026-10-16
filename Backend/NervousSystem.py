import time
import requests
import threading
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from pushbullet import Pushbullet, Listener
from dotenv import dotenv_values

# --- LIBRARY HANDLING: DuckDuckGo ---
try:
    from duckduckgo_search import DDGS
except ImportError:
    from ddgs import DDGS

env = dotenv_values(".env")

# ==========================================================================================
# 📡 PROACTIVE SENTRY (SPOTIFY & PHONE)
# ==========================================================================================
try:
    sp = Spotify(auth_manager=SpotifyOAuth(
        client_id=env.get("SPOTIFY_CLIENT_ID"),
        client_secret=env.get("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=env.get("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8080/"),
        scope="user-read-currently-playing,user-modify-playback-state"
    ))
except Exception as e:
    sp = None
    print(f"!! Spotify Init Error: {e}")

try:
    pb_key = env.get("PUSHBULLET_API_KEY")
    pb = Pushbullet(pb_key) if pb_key else None
except Exception as e:
    pb = None
    print(f"!! Pushbullet Init Error: {e}")

class SentryNerves:
    def __init__(self):
        self.last_track = ""
        self.unread_notifications = []
        self._start_pushbullet_listener()

    def _start_pushbullet_listener(self):
        """Creates a dedicated background thread to catch live WhatsApp/SMS pushes."""
        if not pb: return
        
        def on_push(data):
            try:
                # Catch Ephemeral (Live) Mirrored Notifications
                if data.get("type") == "push" and "push" in data:
                    push_data = data["push"]
                    if push_data.get("type") == "mirror":
                        app_name = push_data.get("application_name", "Phone")
                        title = push_data.get("title", "").strip()
                        body = push_data.get("body", "").strip()
                        
                        # Filter out empty ghost pings
                        if len(body) > 1:
                            msg = f"Sir, new message from {app_name}. {title} says: {body}"
                            self.unread_notifications.append(msg)
            except Exception:
                pass

        # Run the listener forever in the background
        self.pb_listener = Listener(account=pb, on_push=on_push)
        threading.Thread(target=self.pb_listener.run_forever, daemon=True).start()

    def check_spotify(self):
        """Checks what is playing and returns a string if it's a new vibe."""
        if not sp: return None
        try:
            current = sp.current_user_playing_track()
            if current and current.get('is_playing'):
                track_name = current['item']['name']
                artist_name = current['item']['artists'][0]['name']
                full_track = f"{track_name} by {artist_name}"
                
                if full_track != self.last_track:
                    self.last_track = full_track
                    return f"Now playing {full_track}, sir."
            return None
        except: return None

    def check_phone_notifications(self):
        """Pops the oldest unread notification from the live queue."""
        if self.unread_notifications:
            return self.unread_notifications.pop(0)
        return None

# ==========================================================================================
# 🧠 KNOWLEDGE & INTELLIGENCE
# ==========================================================================================
def GetNumberFact(number):
    try:
        url = f"http://numbersapi.com/{number}"
        return requests.get(url, timeout=5).text
    except:
        return "I couldn't find a fact for that number."

def GetBookInfo(query):
    try:
        url = f"https://openlibrary.org/search.json?q={query}"
        response = requests.get(url, timeout=5).json()
        if response.get('docs'):
            book = response['docs'][0]
            title = book.get('title', 'Unknown')
            author = book.get('author_name', ['Unknown'])[0]
            year = book.get('first_publish_year', 'Unknown')
            return f"Book Found: '{title}' by {author}, published in {year}."
        return "No books found."
    except:
        return "Library systems are down."

# ==========================================================================================
# 🗣️ LANGUAGE & TEXT
# ==========================================================================================
def GetUrbanDef(term):
    """Urban Dictionary: DuckDuckGo Bypass."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(f"urban dictionary definition {term}", max_results=1))
            if results:
                return f"Urban Definition: {results[0]['body']}"
    except Exception:
        pass
        
    return "Could not find a definition (Network blocked)."

# ==========================================================================================
# 📰 NEWS & STREAMS
# ==========================================================================================
def GetTechNews():
    try:
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=5).json()[:3]
        news = []
        for id in top_ids:
            story = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{id}.json", timeout=5).json()
            news.append(f"- {story.get('title')} ({story.get('url')})")
        return "Top Tech News:\n" + "\n".join(news)
    except:
        return "Hacker News is silent."

def GetSpaceNews():
    try:
        url = "https://api.spaceflightnewsapi.net/v4/articles/?limit=3"
        response = requests.get(url, timeout=5).json()
        news = [f"- {article['title']}" for article in response['results']]
        return "Latest Space News:\n" + "\n".join(news)
    except:
        return "Deep space comms are down."

# ==========================================================================================
# 🌍 LOCATION & MAPS
# ==========================================================================================
def GetCoordinates(city):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json"
        headers = {'User-Agent': 'JarvisAI/1.0'}
        response = requests.get(url, headers=headers, timeout=5).json()
        if response:
            data = response[0]
            return f"{city} is located at Lat: {data['lat']}, Lon: {data['lon']}."
        return "Location not found."
    except:
        return "GPS systems offline."

def GetISSLocation():
    try:
        url = "http://api.open-notify.org/iss-now.json"
        response = requests.get(url, timeout=5).json()
        pos = response['iss_position']
        return f"The ISS is currently at Lat: {pos['latitude']}, Lon: {pos['longitude']}."
    except:
        return "Tracking failed."

# ==========================================================================================
# 📈 FINANCE & ECONOMY
# ==========================================================================================
def GetCurrencyRate(currency="EUR"):
    try:
        url = f"https://api.frankfurter.app/latest?from=USD&to={currency.upper()}"
        response = requests.get(url, timeout=5).json()
        rate = response['rates'].get(currency.upper(), "Unknown")
        return f"1 USD is currently {rate} {currency.upper()}."
    except:
        return "Market data unavailable."

# ==========================================================================================
# 🎬 MEDIA & CULTURE
# ==========================================================================================
def GetMovieInfo(query):
    try:
        url = f"https://api.tvmaze.com/search/shows?q={query}"
        response = requests.get(url, timeout=5).json()
        if response:
            show = response[0]['show']
            name = show['name']
            summary = show['summary'].replace("<p>", "").replace("</p>", "").replace("<b>", "").replace("</b>", "")
            rating = show.get('rating', {}).get('average', 'N/A')
            return f"Show: {name}\nRating: {rating}/10\nSummary: {summary[:200]}..."
        return "Show not found."
    except:
        return "Media database unreachable."

def GetAnimeInfo(query):
    try:
        url = f"https://api.jikan.moe/v4/anime?q={query}&limit=1"
        response = requests.get(url, timeout=5).json()
        if response.get('data'):
            anime = response['data'][0]
            return f"Anime: {anime.get('title')}\nEpisodes: {anime.get('episodes')}\nScore: {anime.get('score')}"
        return "Anime not found."
    except:
        return "Otaku database error."

def GetGithubTrending(query="python"):
    try:
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc"
        response = requests.get(url, timeout=5).json()
        if response.get('items'):
            repo = response['items'][0]
            return f"Top Repo for '{query}': {repo['full_name']} ({repo['stargazers_count']} stars)\nDesc: {repo['description']}"
        return "No repos found."
    except:
        return "GitHub is offline."