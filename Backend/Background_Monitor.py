import time
import threading
import yfinance as yf
from dotenv import dotenv_values

# Import JARVIS's mouth so he can speak independently
from Frontend.GUI import ShowTextToScreen
from Backend.TextToSpeech import TextToSpeech

class ProactiveSentry:
    def __init__(self):
        print(">> [SENTRY]: Proactive background monitoring online.")
        self.assistant_name = dotenv_values(".env").get("Assistantname", "Jarvis")
        
        # Keep track of alerts so he doesn't spam you with the same news every minute
        self.already_alerted_today = False 

    def check_market_volatility(self):
        """Silently checks a target stock and alerts if there's massive movement."""
        if self.already_alerted_today:
            return

        try:
            # We will use Tesla as the test case
            target_stock = "TSLA"
            
            stock = yf.Ticker(target_stock)
            hist = stock.history(period="5d")
            
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                previous_close = hist['Close'].iloc[-2]
                change = ((current_price - previous_close) / previous_close) * 100
                
                # TRIGGER: If the stock moves more than 2% up or down!
                if abs(change) >= 2.0:
                    direction = "surged" if change > 0 else "dropped"
                    
                    message = f"Pardon the interruption, sir. I am detecting high volatility in the market. Tesla has {direction} {abs(change):.2f}% today, currently trading at ${current_price:.2f}."
                    
                    # J.A.R.V.I.S. speaks without being prompted
                    ShowTextToScreen(f"{self.assistant_name} : {message}")
                    TextToSpeech(message)
                    
                    # Lock the alert so he doesn't repeat it 60 seconds later
                    self.already_alerted_today = True 
                    
        except Exception as e:
            # Sentry fails silently in the background so it doesn't crash your main loop
            pass

    def run(self):
        """The infinite loop that watches the environment."""
        # Wait 15 seconds after booting before starting the first check
        time.sleep(15) 
        
        while True:
            # 1. Check the stock market
            self.check_market_volatility()
            
            # 2. You can add more checks here later (e.g., F1 Race Start Times, Battery Low alerts)
            
            # Sleep for 60 seconds before checking again
            time.sleep(60) 

def StartSentryMode():
    sentry = ProactiveSentry()
    sentry.run()

# --- Quick Test Block ---
if __name__ == "__main__":
    StartSentryMode()