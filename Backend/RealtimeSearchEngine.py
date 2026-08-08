import re
import os
import sys
import datetime
import requests
import urllib.parse
import wikipedia
import yfinance as yf
from json import load, dump, JSONDecodeError
from dotenv import dotenv_values
from googlesearch import search
try:
    from duckduckgo_search import DDGS
except ImportError:
    from ddgs import DDGS

# --- ROBUST PATH FINDER ---
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.getcwd()

env_path = os.path.join(base_path, ".env")
chatlog_path = os.path.join(base_path, "Data", "ChatLog.json")

env_vars = dotenv_values(env_path)
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Jarvis")

System = f"""Hello, I am {Username}. You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Address me respectfully as 'sir'. ***
*** Provide Answers In a Professional Way. Use full stops, commas, and proper grammar.***
*** Just answer the question from the provided data in a professional way. Do not explain the search process. ***"""

# --- SAFE DIRECTORY SETUP ---
os.makedirs(os.path.dirname(chatlog_path), exist_ok=True)
if not os.path.exists(chatlog_path):
    with open(chatlog_path, "w", encoding='utf-8') as f:
        dump([], f)

# --- 1. Specialized Function for Stock Prices ---
def GetStockPrice(query):
    try:
        symbol = None
        query = query.lower()
        ticker_map = {
            "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "amazon": "AMZN",
            "tesla": "TSLA", "meta": "META", "nvidia": "NVDA", "netflix": "NFLX",
            "intel": "INTC", "amd": "AMD"
        }
        for company, ticker in ticker_map.items():
            if company in query:
                symbol = ticker
                break
        if symbol:
            stock = yf.Ticker(symbol)
            current_price = stock.info.get('currentPrice') or stock.history(period="1d")['Close'].iloc[-1]
            return f"The current stock price of {symbol.upper()} is ${current_price:.2f} USD."
        return "I couldn't identify the specific company ticker, sir."
    except: return "Stock market data is currently unavailable, sir."

# --- 2. Public API for Weather ---
def GetWeather(query="Karachi"):
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=24.86&longitude=67.00&current_weather=true"
        response = requests.get(url, timeout=5).json()
        temp = response['current_weather']['temperature']
        return f"The current temperature in Karachi is {temp}°C, sir."
    except: return "Weather data unavailable."

# --- 3. Public API for Crypto ---
def GetCryptoPrice(query):
    try:
        coin = "bitcoin"
        if "ethereum" in query.lower(): coin = "ethereum"
        elif "solana" in query.lower(): coin = "solana"
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        price = requests.get(url, timeout=5).json()[coin]['usd']
        return f"The price of {coin.capitalize()} is ${price} USD."
    except: return "Crypto rates are unreachable, sir."

# --- 4. Wikipedia Search ---
def WikipediaSearch(query):
    try:
        results = wikipedia.summary(query, sentences=3)
        return f"According to Wikipedia: {results}"
    except: return DuckDuckGoSearch(query)

# --- 5. DuckDuckGo Search ---
def DuckDuckGoSearch(query):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region='wt-wt', max_results=5))
        if not results: return GoogleSearch(query)
        Answer = f"Web results for '{query}':\n"
        for i in results:
            Answer += f"Title: {i.get('title')}\nDesc: {i.get('body')}\n\n"
        return Answer
    except: return GoogleSearch(query)

# --- 6. Google Search ---
def GoogleSearch(query):
    try:
        results = list(search(query, advanced=True, num_results=5))
        return "\n".join([f"Title: {i.title}\nDesc: {i.description}" for i in results])
    except: return "I am unable to access the web right now, sir."

def Information():
    now = datetime.datetime.now()
    return f"Time: {now.strftime('%I:%M:%S %p')}\nDate: {now.strftime('%d/%m/%Y')}\nLocation: Karachi, Pakistan\n"

def AnswerModifier(Answer):
    return '\n'.join([line for line in Answer.split('\n') if line.strip()])

# --- Main Engine ---
def RealtimeSearchEngine(prompt):
    from groq import Groq
    GroqAPIKey = env_vars.get("GroqAPIKey")
    client = Groq(api_key=GroqAPIKey)

    # 1. Load History
    try:
        with open(chatlog_path, "r", encoding='utf-8') as f:
            messages = load(f)
            if not isinstance(messages, list): messages = []
    except: messages = []

    # 2. THE CLEANING ALGORITHM
    original_prompt = prompt
    prompt_clean = prompt.lower().strip()
    remove_list = ["jarvis", "who is", "what is", "tell me", "search for", "please", "sir"]
    for word in remove_list:
        prompt_clean = prompt_clean.replace(word, "")
    prompt_clean = re.sub(r'[^\w\s]', '', prompt_clean).strip()
    if not prompt_clean: prompt_clean = original_prompt

    # 3. PRIORITY ROUTING
    lower_p = original_prompt.lower()
    if "weather" in lower_p:
        SearchResult = GetWeather(prompt_clean)
    elif "stock" in lower_p or ("price" in lower_p and "bitcoin" not in lower_p):
        SearchResult = GetStockPrice(prompt_clean)
    elif any(x in lower_p for x in ["bitcoin", "crypto", "ethereum"]):
        SearchResult = GetCryptoPrice(prompt_clean)
    elif any(x in lower_p for x in ["match", "vs", "versus", "score"]):
        # Force web search for sports results
        SearchResult = DuckDuckGoSearch(prompt_clean)
    else:
        words = prompt_clean.split()
        if 1 <= len(words) <= 3:
            SearchResult = WikipediaSearch(prompt_clean)
        else:
            SearchResult = DuckDuckGoSearch(prompt_clean)

    # 4. Context Assembly
    SystemChatBot = [
        {"role": "system", "content": System},
        {"role": "system", "content": f"Search Context: {SearchResult}"},
        {"role": "system", "content": Information()}
    ]
    
    # Append the CURRENT user prompt so the AI sees it in history
    messages.append({"role": "user", "content": original_prompt})
    api_messages = messages[-40:] if len(messages) > 40 else messages

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=SystemChatBot + api_messages,
            temperature=0.3,
            max_tokens=2048,
            stream=True
        )

        Answer = ""
        for chunk in completion:
            if chunk.choices[0].delta.content:
                Answer += chunk.choices[0].delta.content

        Answer = Answer.strip().replace("</s>", "")
        messages.append({"role": "assistant", "content": Answer})

        with open(chatlog_path, "w", encoding='utf-8') as f:
            dump(messages, f, indent=4, ensure_ascii=False)

        return AnswerModifier(Answer)
    except Exception as e:
        return f"AI Generation Error: {e}"

if __name__ == "__main__":
    while True:
        p = input("Enter your query: ")
        print(RealtimeSearchEngine(p))