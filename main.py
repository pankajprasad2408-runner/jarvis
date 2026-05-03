import speech_recognition as sr
import webbrowser
import asyncio
import edge_tts
import pygame
import os
import uuid
import requests
import pywhatkit
import datetime
from client import get_result


recognizer = sr.Recognizer()

#🎙️ AI Voice
async def speak_async(text):
    filename = f"voice_{uuid.uuid4()}.mp3"
    pygame.mixer.pre_init(
        frequency=48000,
        size=-16,
        channels=2,
        buffer=512
    )
    communicate = edge_tts.Communicate(text,  voice="en-GB-RyanNeural",
        rate="+10%",
        pitch="+2Hz",
        volume="+20%",)
    await communicate.save(filename)
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    # Wait for music to finish playing
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    pygame.mixer.music.unload()
    os.remove(filename)

def speak(text):
    print("matrix:", text)
    asyncio.run(speak_async(text))
### 
import json

MEMORY_FILE = "smart_memory.json"

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)

def extract_memory(text):
    text = text.lower()

    memory = load_memory()

    # 👇 rules (you can expand later)
    if "my name is" in text:
        memory["name"] = text.split("my name is")[-1].strip()

    elif "i live in" in text:
        memory["city"] = text.split("i live in")[-1].strip()

    elif "i like" in text:
        memory["likes"] = text.split("i like")[-1].strip()

    elif "my favorite language is" in text:
        memory["fav_lang"] = text.split("my favorite language is")[-1].strip()

    save_memory(memory)

def build_context():
    memory = load_memory()
    return (
        f"User info:\n"
        f"Name: {memory.get('name', 'unknown')}\n"
        f"City: {memory.get('city', 'unknown')}\n"
        f"Likes: {memory.get('likes', 'unknown')}\n"
        f"Favorite Language: {memory.get('fav_lang', 'unknown')}\n"
    )
###
#  🎧 Listen Function
def listen(timeout=5, phrase_limit=8) -> str | None:
    """Listen from mic and return recognised text, or None on failure."""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        return recognizer.recognize_google(audio).strip()
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that.")
    except sr.RequestError:
        speak("Speech service seems to be down.")
    except Exception as e:
        print("Listen error:", e)
    return None

# 🌦️ Weather Function
def get_weather(city):
    api_key = os.getenv('WEATHER_API_KEY')

    if not api_key:
        return "Weather API key is missing."

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": api_key,
            "units": "metric"
        }

        response = requests.get(url, params=params, timeout=5)
        data = response.json()

        if response.status_code == 200:
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            humidity = data["main"]["humidity"]
            wind = data["wind"]["speed"]

            return (
                f"Currently in {city}, it's {temp}°C with {desc}. "
                f"Humidity is {humidity}% and wind speed is {wind} meters per second."
            )

        elif data.get("cod") == "404":
            return f"I couldn't find the city {city}."

        else:
            return "Weather service returned an unexpected response."

    except requests.exceptions.Timeout:
        return "Weather service is taking too long to respond."

    except requests.exceptions.RequestException:
        return "Network error while fetching weather."

    except Exception as e:
        print("Weather error:", e)
        return "Something went wrong while getting weather."

# 🎯 Command Handler
def processcommand(command):
    command = command.lower()

    # 🌐 Websites
    if "open google" in command:
        webbrowser.open("https://google.com")
        speak("Opening Google")

    elif "open youtube" in command:
        webbrowser.open("https://youtube.com")
        speak("Opening YouTube")

    # 🔍 Search
    elif "search" in command:
        query = command.replace("search", "")
        webbrowser.open(f"https://www.google.com/search?q={query}")
        speak(f"Searching {query}")

    # 🎵 Play Song (need upgrade)
    elif "play" in command:
        song = command.replace("play", "")
        speak(f"Playing {song}")
        pywhatkit.playonyt(song)

    # ⏰ Time
    elif "time" in command:
        time = datetime.datetime.now().strftime("%H:%M")
        speak(f"The time is {time}")

    # Message ( not propetly working, may be API problem)
    elif "send message" in command:
        speak("Tell me the number with country code")
        number = input("Enter number: ")
        speak("What message?")
        msg = input("Enter message: ")
        pywhatkit.sendwhatmsg_instantly(number, msg)
        speak("Message sent")

    # 🌦️ Weather
    elif "weather" in command:
        speak("Which city?")

        with sr.Microphone() as source:
            print("Listening for city...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

        city = recognizer.recognize_google(audio)
        city = city.lower().replace("india", "").replace("city", "").strip().title()
        print("City:", city)

        result = get_weather(city)
        speak(result)
    # open files
    elif "open code" in command:
        os.system("code")  

    elif "open chrome" in command:
        os.system("start chrome")
    


    elif "chat" in command:
        speak("Sure, ask me anything.")
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        try:
            command_text = recognizer.recognize_google(audio)
            print("You:", command_text) 
            
            # Build context from memory
            context = build_context()
            prompt = context + "\nUser: " + command_text + "\nAI:"
            
            # Get AI response from client.py
            answer = get_result(prompt)
            print("AI:", answer)
            speak(answer)
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
        except sr.RequestError:
            speak("Speech service seems to be down.")
        except Exception as e:
            print("AI error:", e)
            speak("Sorry, I couldn't reach the AI right now.")
 
    # ── Exit ──────────────────────────────
    elif "exit" in command or "stop" in command:
        speak("Goodbye sir!")
        exit()
 
    # ── Fallback ──────────────────────────
    else:
        speak("I didn't understand that command.")



   


# MAIN LOOP
if __name__ == "__main__":
    speak("Hello pankaj,  I am matrix, your personal assistant. How can I help you today?")
    
    

    while True:
        try:
            with sr.Microphone() as source:
                print("Listening...")
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)

            word = recognizer.recognize_google(audio).lower()
            print("You:", word)

            if "matrix" in word.lower():
                speak("Yes sir")
                while True:
                    with sr.Microphone() as source:
                        print("Command...")
                        recognizer.adjust_for_ambient_noise(source)
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)

                    command = recognizer.recognize_google(audio).lower()
                    print("Command:", command)

                    processcommand(command)

        except Exception as e:
            print("Error:", e)