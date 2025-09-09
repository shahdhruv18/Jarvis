import speech_recognition as sr
import webbrowser
import pyttsx3
import time
import requests
from gtts import gTTS
import os
import google.generativeai as genai
import pygame
from rich.console import Console
from rich.text import Text
from dotenv import load_dotenv
import itertools
import threading

load_dotenv()
newsapi = os.getenv("api1")  # News API key from .env
genai.configure(api_key=os.getenv("api2"))  # Gemini API key from .env
console = Console()

engine = pyttsx3.init()
idle_running = True 

# ---------------- SPEECH ---------------- #
def speak(text, slow=False, lang="en-in"):
    tts = gTTS(text=text, lang=lang, slow=slow)
    tts.save("audio.mp3")

    pygame.mixer.init()
    pygame.mixer.music.load("audio.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

    pygame.mixer.music.unload()
    os.remove("audio.mp3")

# ---------------- EFFECTS ---------------- #

def show_intro():
    console.print(Text(">>> J.A.R.V.I.S ONLINE <<<", style="bold green"))
    console.print(Text("Awaiting your command...", style="cyan"))

def show_waveform(duration=2.5):
    frames = ["[=     ]", "[==    ]", "[===   ]", "[====  ]", "[===== ]", "[======]"]
    start = time.time()
    for frame in itertools.cycle(frames):
        print(f"\rActivating {frame}", end="")
        time.sleep(0.2)
        if time.time() - start > duration:
            break
    print("\r", end="")

def idle_animation():
    frames = ["⠁", "⠂", "⠄", "⡀", "⢀", "⠠", "⠐", "⠈"]
    for frame in itertools.cycle(frames):
        if not idle_running:
            break
        print(f"\r[cyan]💠 Jarvis standing by {frame}[/cyan]", end="")
        time.sleep(0.2)

# ---------------- AI (Gemini) ---------------- #
def ask_gemini(query: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(query)
        return response.text if response and response.text else "Sorry, I didn't get a response from Gemini."
    except Exception as e:
        return f"Gemini error: {str(e)}"

# ---------------- COMMANDS ---------------- #
def processCommand(c):
    if "open google" in c.lower():
        webbrowser.open("https://www.google.com/")
        speak("Opening Google")
    elif "open youtube" in c.lower():
        webbrowser.open("https://www.youtube.com/")
        speak("Opening YouTube")
    elif "open linkedin" in c.lower():
        webbrowser.open("https://www.linkedin.com/")
        speak("Opening LinkedIn")
    elif "open github" in c.lower():
        webbrowser.open("https://www.github.com/")
        speak("Opening GitHub")
    elif "play" in c.lower():
        parts = c.lower().split(" ", 1)
        if len(parts) < 2:
            speak("Please specify a song to play.")
            return
        song = parts[1].strip()
        url = f"spotify:search:{song.replace(' ', '%20')}"
        webbrowser.open(url)
        speak(f"Searching Spotify for {song}")
    elif "news" in c.lower():
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}")
            if r.status_code == 200:
                data = r.json()
                articles = data.get("articles", [])
                for article in articles:
                    speak(article['title'])
            else:
                speak("Sorry, I could not fetch the news right now.")
        except requests.exceptions.RequestException:
            speak("Sorry, my connection to the news service failed.")
    else:
        answer = ask_gemini(c)
        speak(answer)

# ---------------- MAIN ---------------- #
if __name__ == "__main__":
    show_intro()
    speak("Initializing Jarvis system")

    # start idle animation in background thread
    threading.Thread(target=idle_animation, daemon=True).start()

    while True:
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                audio = r.listen(source, timeout=7, phrase_time_limit=7)   
            word = r.recognize_google(audio)

            if word.lower() == "jarvis":
                # pause idle animation
                idle_running = False
                print("\r", end="")  # clear idle line
                
                show_waveform()
                speak("Hey! How can i help you ?")

                console.print("[yellow]Jarvis activated[/yellow]")

                with sr.Microphone() as source:
                    r.adjust_for_ambient_noise(source)
                    console.print("[cyan]Listening for command...[/cyan]")
                    audio = r.listen(source, timeout=7, phrase_time_limit=7)

                try:
                    command = r.recognize_google(audio)
                    processCommand(command)
                except sr.UnknownValueError:
                    speak("Sorry, I did not understand that.")
                except sr.RequestError:
                    speak("Sorry, my speech service is down.")

                # restart idle animation
                idle_running = True
                threading.Thread(target=idle_animation, daemon=True).start()

        except sr.UnknownValueError:
            pass
        except sr.RequestError:
            speak("Sorry, my speech service is down.")
