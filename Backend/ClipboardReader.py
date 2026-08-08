import pyperclip
from dotenv import dotenv_values

def ReadClipboard(command):
    try:
        # 1. Lazy Load Client (Prevents startup hanging during imports)
        from groq import Groq
        env_vars = dotenv_values(".env")
        GroqAPIKey = env_vars.get("GroqAPIKey")
        
        if not GroqAPIKey:
            return "Error: Groq API Key is missing from the .env file."
            
        client = Groq(api_key=GroqAPIKey)

        # 2. Get text from clipboard
        clipboard_text = pyperclip.paste()
        
        if not clipboard_text or len(clipboard_text.strip()) < 1:
            return "Clipboard is empty or contains non-text data, sir."

        # 3. Truncate huge text (Safety Mechanism)
        # Limit to 15,000 characters to prevent API token limit errors
        if len(clipboard_text) > 15000:
            clipboard_text = clipboard_text[:15000] + "\n...(Text truncated due to length)..."

        # 4. Determine prompt based on command
        command = command.lower()
        if "summarize" in command or "short" in command:
            prompt = f"Summarize the following text in 3 concise bullet points:\n\n{clipboard_text}"
        elif "explain" in command:
            prompt = f"Explain the following text simply like I'm 5 years old:\n\n{clipboard_text}"
        elif "fix" in command or "code" in command or "debug" in command:
            prompt = f"Analyze the following code/text, fix any errors, and explain the fix:\n\n{clipboard_text}"
        elif "email" in command:
            prompt = f"Draft a professional reply to this email:\n\n{clipboard_text}"
        else:
            prompt = f"Analyze this text and tell me the key takeaways:\n\n{clipboard_text}"

        # 5. Ask AI
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are J.A.R.V.I.S., a helpful assistant. Analyze the user's clipboard text provided below. Address the user respectfully as 'sir'."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1024,
            temperature=0.6
        )
        
        answer = completion.choices[0].message.content.strip()
        return f"\n{answer}"
        
    except Exception as e:
        return f"Error analyzing clipboard: {e}"