from flask import Flask, request
from twitchio.ext import commands
import requests
import asyncio
import threading

app = Flask(__name__)

# Konfiguracja bota Twitch
BOT_NICK = "POLSL"  # Nazwa użytkownika bota
BOT_TOKEN = "oauth:xxxxxxxxxxxxxxxx"  # OAuth token bota
CHANNEL = "xxxxxxxxxxxxxxx"  # Nazwa kanału Twitch

# Konfiguracja Ollamy
OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Adres lokalnego API Ollamy
MODEL_NAME = "llama3"  # Nazwa modelu Ollamy, np. llama3

def query_ollama(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload)
        response.raise_for_status()
        return response.json().get("response", "Błąd: Brak odpowiedzi od modelu.")
    except requests.exceptions.RequestException as e:
        return f"Błąd: Nie udało się połączyć z Ollamą ({e})."

# Funkcja do dzielenia długich wiadomości
def split_message(message, max_length=400):  
    if len(message) <= max_length:
        return [message]
    
    messages = []
    while message:
        split_index = message[:max_length].rfind(" ")
        if split_index == -1 or split_index < max_length // 2:
            split_index = max_length - 3
        part = message[:split_index].strip()
        if part:
            messages.append(part + ("..." if len(message) > split_index else ""))
        message = message[split_index:].strip()
        if not message:
            break
    return messages

# Klasa bota Twitch
class TwitchBot(commands.Bot):
    def __init__(self, loop):
        super().__init__(token=BOT_TOKEN, prefix="!", initial_channels=[CHANNEL], loop=loop)

    async def event_ready(self):
        print(f"Zalogowano jako {self.nick} | Połączono z kanałem: {CHANNEL}")

    async def event_message(self, message):
        if message.echo:
            return
        await self.handle_commands(message)

    @commands.command(name="bot")
    async def bot_command(self, ctx):
        message_content = ctx.message.content.replace("!bot ", "").strip()
        if not message_content:
            await ctx.send("Użyj: !bot <pytanie>")
            return

        response = query_ollama(message_content)
        
        prefix = f"🤖 @{ctx.author.name}: "
        max_response_length = 500 - len(prefix)  
        
        response_parts = split_message(response, max_response_length)
        
        for part in response_parts:
            await ctx.send(f"{prefix}{part}")


def run_flask():
    app.run(debug=True, use_reloader=False)

def run_twitch_bot():
    loop = asyncio.new_event_loop()  
    asyncio.set_event_loop(loop)  
    bot = TwitchBot(loop=loop)
    try:
        loop.run_until_complete(bot.start())  
    finally:
        try:
            loop.run_until_complete(bot.close())  
        except AttributeError as e:
            print(f"Błąd przy zamykaniu bota: {e}")
        finally:
            loop.close() 

if __name__ == "__main__":
    twitch_thread = threading.Thread(target=run_twitch_bot)
    twitch_thread.start()

    run_flask()