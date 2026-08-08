import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
import os

load_dotenv()
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# --- THE SPAM FILTER ---
# Add any annoying sender keywords here. If the sender's email contains these, Jarvis ignores it.
JUNK_FILTERS = [
    "facebook", "linkedin", "indeed", "reddit", "gamma", "norton", 
    "no-reply", "noreply", "newsletter", "alerts", "marketing", "promotions",
    "nayapay", "faysal", "faysalbank", "codesandbox", "github", "gitlab", "bitbucket", "twitter", "instagram", "tiktok", "snapchat",
]

def CheckNewEmails():
    if not EMAIL_USER or not EMAIL_PASS:
        return None
        
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")
        
        status, messages = mail.search(None, "UNSEEN")
        if status != "OK" or not messages[0]:
            mail.logout()
            return None
            
        email_ids = messages[0].split()
        latest_id = email_ids[-1]
        
        res, msg_data = mail.fetch(latest_id, "(RFC822)")
        
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                # Check sender email address against our Junk Filter
                raw_sender = msg.get("From", "").lower()
                
                # Mark as read so we don't keep checking it
                mail.store(latest_id, '+FLAGS', '\\Seen')
                
                if any(junk in raw_sender for junk in JUNK_FILTERS):
                    # It's spam/social media. Ignore it silently.
                    mail.logout()
                    return None
                
                # If it passed the filter, decode and announce it!
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                    
                sender_name = raw_sender.split("<")[0].replace('"', '').strip().title()
                
                mail.logout()
                return f"Sir, you just received a new email from {sender_name}. The subject is: {subject}"
                
        mail.logout()
        return None
    except Exception as e:
        return None