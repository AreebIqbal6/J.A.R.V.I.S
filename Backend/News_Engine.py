import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
import urllib.parse
import warnings

# Silence the BeautifulSoup XML warning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

class GlobalNewsEngine:
    def __init__(self):
        print(">> [NEWS ENGINE]: Global web scraper online.")

    def fetch_news(self, topic, count=3):
        """Scrapes Google News for the latest headlines on a specific topic."""
        try:
            print(f">> [NEWS ENGINE]: Scraping web for '{topic}'...")
            
            # Encode the topic for a URL (e.g., "apple stock" -> "apple%20stock")
            encoded_topic = urllib.parse.quote(topic)
            
            # We add 'when:1d' to the query to ensure we only get news from the last 24 hours
            url = f"https://news.google.com/rss/search?q={encoded_topic} when:1d&hl=en-US&gl=US&ceid=US:en"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, "html.parser")
            items = soup.find_all("item")
            
            # Fallback: If no news in the last 24 hours, do a general search
            if not items:
                url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=en-US&gl=US&ceid=US:en"
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.content, "html.parser")
                items = soup.find_all("item")

            if not items:
                return f"Sir, I could not find any recent articles regarding {topic}."
                
            report = f"Recent headlines regarding {topic}:\n"
            
            for i, item in enumerate(items[:count], 1):
                # Google News titles beautifully format as "Headline - Source"
                title = item.title.text
                report += f"{i}. {title}\n"
                
            return report.strip()
            
        except Exception as e:
            return f"Sir, the scraper encountered a network error: {e}"

    def process_query(self, query):
        """Aggressive NLP to strip punctuation and isolate the news topic."""
        query = query.lower().replace("jarvis", "").strip()
        
        # Strip all annoying punctuation
        for char in [",", "?", ".", "!", "-", "'"]:
            query = query.replace(char, "")
            
        # Remove trigger words
        triggers = [
            "what is the latest news on", "what is the latest news about",
            "give me the news about", "news about", "news on", "headlines for", 
            "latest news about", "search news for", "what is the latest"
        ]
        
        topic = query
        for t in triggers:
            if t in topic:
                topic = topic.replace(t, "").strip()
                break
                
        # If you just ask "what is the news", it defaults to global tech
        if not topic or topic in ["news", "the news", "headlines"]:
            topic = "global technology and finance"
            
        # Capitalize for neatness
        return self.fetch_news(topic.title())

# --- Quick Test Block ---
if __name__ == "__main__":
    engine = GlobalNewsEngine()
    print("\n--- SCRAPER TEST ---")
    print(engine.process_query("Jarvis, what is the latest news on Nvidia?"))