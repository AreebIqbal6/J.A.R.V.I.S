import os
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import warnings
from Backend.News_Engine import GlobalNewsEngine # INJECT THE NEWS ENGINE

# Suppress warnings
warnings.filterwarnings("ignore")

# ==========================================
# --- SECURE CHART CACHE ---
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHART_DIR = os.path.join(BASE_DIR, "Data", "Charts")
os.makedirs(CHART_DIR, exist_ok=True)

class QuantBroker:
    def __init__(self):
        print(">> [QUANT BROKER]: Wall Street visual terminal & News Sentiment online.")
        self.news_scraper = GlobalNewsEngine() # Initialize the scraper
        
        self.known_tickers = {
            "apple": "AAPL",
            "microsoft": "MSFT",
            "google": "GOOGL",
            "alphabet": "GOOGL",
            "amazon": "AMZN",
            "nvidia": "NVDA",
            "tesla": "TSLA",
            "meta": "META",
            "facebook": "META",
            "netflix": "NFLX",
            "amd": "AMD",
            "intel": "INTC",
            "spotify": "SPOT",
            "disney": "DIS",
            "bitcoin": "BTC-USD",
            "ethereum": "ETH-USD"
        }

    def extract_ticker(self, query):
        query = query.lower()
        for company, ticker in self.known_tickers.items():
            if company in query:
                return ticker, company.title()
        return None, None

    def generate_chart(self, ticker, company_name, hist_data):
        try:
            print(f">> [QUANT BROKER]: Rendering visual telemetry for {ticker}...")
            file_path = os.path.join(CHART_DIR, f"{ticker}_market_analysis.png")
            
            mc = mpf.make_marketcolors(up='g', down='r', edge='inherit', wick='inherit', volume='in')
            s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=True)
            
            mpf.plot(hist_data, type='candle', style=s,
                     title=f"{company_name} ({ticker}) - 6 Month Quantitative Analysis",
                     ylabel='Price (USD)', 
                     volume=True, 
                     mav=(50),
                     savefig=file_path,
                     figsize=(10, 6))
            
            if os.path.exists(file_path):
                os.startfile(file_path)
                
        except Exception as e:
            print(f"!! [CHART ERROR]: Failed to generate visual for {ticker}: {e}")

    def analyze_stock(self, ticker, company_name):
        try:
            print(f">> [QUANT BROKER]: Ripping real-time market data for {ticker}...")
            stock = yf.Ticker(ticker)
            hist = stock.history(period="6mo")
            
            if hist.empty:
                return f"Sir, I could not retrieve market data for {company_name}."

            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2]
            daily_change = ((current_price - previous_close) / previous_close) * 100
            sma_50 = hist['Close'].tail(50).mean()
            
            fast_info = stock.fast_info
            year_high = fast_info.year_high

            trend = "bullish" if current_price > sma_50 else "bearish"
            
            # --- TRIGGER VISUALS ---
            self.generate_chart(ticker, company_name, hist)

            # --- FETCH NEWS SENTIMENT ---
            news_report = self.news_scraper.fetch_news(f"{company_name} stock", count=2)

            # --- BUILD FINAL REPORT ---
            report = (
                f"Market analysis for {company_name}. "
                f"The current price is ${current_price:.2f}, "
            )
            
            if daily_change > 0:
                report += f"up {daily_change:.2f}% today. "
            else:
                report += f"down {abs(daily_change):.2f}% today. "
                
            report += f"The stock is {trend}. "
            
            # Append the news context
            if "could not find" not in news_report:
                report += f"Here is the latest market context: {news_report}"

            return report

        except Exception as e:
            return f"Error analyzing {company_name} stock: {str(e)}"

    def process_query(self, query):
        ticker, company_name = self.extract_ticker(query)
        
        if ticker:
            return self.analyze_stock(ticker, company_name)
        else:
            return "Sir, I did not recognize the company name. Please specify a major tech stock or crypto."