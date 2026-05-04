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
from dotenv import load_dotenv



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
        pitch="+3Hz",
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
import datetime
import re
from collections import defaultdict

MEMORY_FILE = "smart_memory.json"

def load_memory():
    """Load memory from file with error handling."""
    try:
        with open(MEMORY_FILE, "r", encoding='utf-8') as f:
            data = json.load(f)
            # Ensure proper structure
            if not isinstance(data, dict):
                return {"personal": {}, "preferences": {}, "conversations": []}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize with default structure
        return {"personal": {}, "preferences": {}, "conversations": []}

def save_memory(memory):
    """Save memory to file with error handling."""
    try:
        with open(MEMORY_FILE, "w", encoding='utf-8') as f:
            json.dump(memory, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving memory: {e}")

def extract_memory(text):
    """Extract and store memory from user input using pattern matching."""
    text = text.lower().strip()
    memory = load_memory()

    # Initialize categories if they don't exist
    memory.setdefault("personal", {})
    memory.setdefault("preferences", {})
    memory.setdefault("conversations", [])

    current_time = datetime.datetime.now().isoformat()

    # Extract personal information (process in specific order to avoid conflicts)

    # Name first (most specific patterns)
    name_patterns = [
        r"my name is (\w+)",
        r"call me (\w+)"
    ]

    for pattern in name_patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            if not value.isdigit():  # Avoid matching numbers
                # Normalize name
                normalized = value.title()
                memory["personal"]["name"] = {
                    "value": normalized,
                    "timestamp": current_time,
                    "confidence": 0.95
                }
            break

    # Age (numeric patterns)
    age_patterns = [
        r"i am (\d+) years old",
        r"i'm (\d+) years old",
        r"my age is (\d+)"
    ]

    for pattern in age_patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            # store as integer string
            memory["personal"]["age"] = {
                "value": str(int(value)),
                "timestamp": current_time,
                "confidence": 0.95
            }
            break

    # Location
    location_patterns = [
        r"i live in ([^.!?]+)",
        r"i'm from ([^.!?]+)",
        r"my location is ([^.!?]+)"
    ]

    for pattern in location_patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            memory["personal"]["location"] = {
                "value": value.title(),
                "timestamp": current_time,
                "confidence": 0.9
            }
            break

    # Occupation
    occupation_patterns = [
        r"i work as (?:a |an )?([^.!?]+)",
        r"i'm a ([^.!?]+)",
        r"my job is ([^.!?]+)"
    ]

    for pattern in occupation_patterns:
        match = re.search(pattern, text)
        if match:
            value = match.group(1).strip()
            memory["personal"]["occupation"] = {
                "value": value.title(),
                "timestamp": current_time,
                "confidence": 0.9
            }
            break

    # Preferences and likes
    preference_patterns = {
        "likes": [
            r"i like ([^.!?]+)",
            r"i love ([^.!?]+)",
            r"my favorite ([^.!?]+) is ([^.!?]+)",
            r"i enjoy ([^.!?]+)"
        ],
        "dislikes": [
            r"i don't like ([^.!?]+)",
            r"i hate ([^.!?]+)",
            r"i dislike ([^.!?]+)"
        ],
        "hobbies": [
            r"i play ([^.!?]+)",
            r"i do ([^.!?]+) for fun",
            r"my hobby is ([^.!?]+)"
        ]
    }

    # Extract preferences
    for category, patterns in preference_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # Handle favorite pattern with two groups
                if "favorite" in pattern and len(match.groups()) > 1:
                    item = match.group(1).strip()
                    value = match.group(2).strip()
                    key = f"{item}_preference"
                else:
                    value = match.group(1).strip()
                    key = category

                # Normalize and possibly split compound mentions like 'pizza and pasta'
                parts = [p.strip() for p in re.split(r",| and | & |;", value) if p.strip()]

                for part in parts:
                    normalized = part.lower()
                    if key not in memory["preferences"]:
                        memory["preferences"][key] = []

                    # Avoid duplicates based on normalized value
                    existing = next((it for it in memory["preferences"][key] if it.get("value") == normalized), None)
                    if not existing:
                        memory["preferences"][key].append({
                            "value": normalized,
                            "timestamp": current_time,
                            "frequency": 1,
                            "last_mentioned": current_time
                        })
                    else:
                        existing["frequency"] = existing.get("frequency", 1) + 1
                        existing["last_mentioned"] = current_time
                break

    # Store conversation context (last 10 conversations)
    conversation_entry = {
        "text": text,
        "timestamp": current_time,
        "type": "user_input"
    }

    memory["conversations"].append(conversation_entry)
    # Keep only last 20 conversations
    if len(memory["conversations"]) > 20:
        memory["conversations"] = memory["conversations"][-20:]

    save_memory(memory)

def get_memory_context(query=None, max_items=5):
    """Build context string from memory, optionally filtered by query."""
    memory = load_memory()
    context_parts = []

    # Personal information
    if memory.get("personal"):
        personal_info = []
        for key, data in memory["personal"].items():
            if isinstance(data, dict) and "value" in data:
                personal_info.append(f"{key.title()}: {data['value']}")
        if personal_info:
            context_parts.append("Personal Information:\n" + "\n".join(f"• {info}" for info in personal_info))

    # Preferences
    if memory.get("preferences"):
        for category, items in memory["preferences"].items():
            if items:
                # Sort by frequency and recency
                sorted_items = sorted(items,
                                    key=lambda x: (x.get("frequency", 1), x.get("last_mentioned", x.get("timestamp", ""))),
                                    reverse=True)
                top_items = sorted_items[:max_items]
                values = [item["value"] for item in top_items]
                context_parts.append(f"{category.title()}: {', '.join(values)}")

    # Recent conversations context
    if memory.get("conversations"):
        recent_conversations = memory["conversations"][-3:]  # Last 3 conversations
        if recent_conversations:
            context_parts.append("Recent Conversation Topics:\n" +
                               "\n".join(f"• {conv['text'][:50]}..." for conv in recent_conversations))

    # Filter by query if provided
    if query:
        query_lower = query.lower()
        filtered_parts = []
        for part in context_parts:
            if any(keyword in part.lower() for keyword in query_lower.split()):
                filtered_parts.append(part)
        context_parts = filtered_parts

    return "\n\n".join(context_parts) if context_parts else ""


def summarize_memory_for_speech(memory=None, max_items=5):
    """Generate a concise natural-language summary from memory for speech output."""
    if memory is None:
        memory = load_memory()

    parts = []

    personal = memory.get("personal", {})
    if personal:
        # Name
        name = personal.get("name", {}).get("value") if isinstance(personal.get("name"), dict) else personal.get("name")
        if name:
            parts.append(f"Your name is {name}.")

        # Age
        age = personal.get("age", {}).get("value") if isinstance(personal.get("age"), dict) else personal.get("age")
        if age:
            parts.append(f"You are {age} years old.")

        # Location
        loc = personal.get("location", {}).get("value") if isinstance(personal.get("location"), dict) else personal.get("location")
        if loc:
            parts.append(f"You live in {loc}.")

        # Occupation
        occ = personal.get("occupation", {}).get("value") if isinstance(personal.get("occupation"), dict) else personal.get("occupation")
        if occ:
            parts.append(f"You work as {occ}.")

    # Preferences: pick top items per category
    prefs = memory.get("preferences", {})
    for category, items in prefs.items():
        if not items:
            continue
        # sort by frequency then last_mentioned
        sorted_items = sorted(items, key=lambda x: (x.get("frequency", 1), x.get("last_mentioned", x.get("timestamp", ""))), reverse=True)
        top = [it.get("value") for it in sorted_items[:max_items]]
        if top:
            # humanize category
            display = category.replace("_", " ")
            parts.append(f"Your {display} include: {', '.join(top)}.")

    # Recent conversation topics (summarize)
    conversations = memory.get("conversations", [])
    if conversations:
        recent = conversations[-3:]
        topics = [conv.get("text", "") for conv in recent]
        if topics:
            parts.append(f"Recent things you said: { '; '.join(t[:60] for t in topics)}.")

    # Join into a short paragraph (limit length)
    summary = " ".join(parts)
    if len(summary) > 800:
        summary = summary[:800].rsplit('.', 1)[0] + '.'

    return summary.strip()

def search_memory(keyword):
    """Search memory for specific information."""
    memory = load_memory()
    results = defaultdict(list)

    keyword_lower = keyword.lower()

    # Search personal info
    for key, data in memory.get("personal", {}).items():
        if isinstance(data, dict) and keyword_lower in data.get("value", "").lower():
            results["personal"].append({key: data["value"]})

    # Search preferences
    for category, items in memory.get("preferences", {}).items():
        for item in items:
            if keyword_lower in item.get("value", "").lower():
                results["preferences"].append({category: item["value"]})

    # Search conversations
    for conv in memory.get("conversations", []):
        if keyword_lower in conv.get("text", "").lower():
            results["conversations"].append(conv["text"])

    return dict(results)

def set_personal_field(field: str, value: str):
    """Set a personal memory field (name, age, location, occupation)."""
    memory = load_memory()
    memory.setdefault("personal", {})
    current_time = datetime.datetime.now().isoformat()
    memory["personal"][field] = {
        "value": value,
        "timestamp": current_time,
        "confidence": 0.95
    }
    save_memory(memory)
    return True


def delete_personal_field(field: str):
    """Delete a personal memory field if present."""
    memory = load_memory()
    if "personal" in memory and field in memory["personal"]:
        memory["personal"].pop(field, None)
        save_memory(memory)
        return True
    return False

def cleanup_memory(days_old=30):
    """Remove old memory entries."""
    memory = load_memory()
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days_old)

    # Clean conversations
    memory["conversations"] = [
        conv for conv in memory.get("conversations", [])
        if datetime.datetime.fromisoformat(conv["timestamp"]) > cutoff_date
    ]

    # Clean preferences (remove items with low frequency and old timestamps)
    for category, items in memory.get("preferences", {}).items():
        filtered_items = []
        for item in items:
            item_date = datetime.datetime.fromisoformat(item.get("last_mentioned", item.get("timestamp", "")))
            if item_date > cutoff_date and item.get("frequency", 1) > 0:
                filtered_items.append(item)
        memory["preferences"][category] = filtered_items

    save_memory(memory)

def build_context():
    """Legacy function for backward compatibility."""
    return get_memory_context()

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
    load_dotenv()
    key = os.getenv('WEATHER_API_KEY')

    if not key:
        return "Weather API key is missing."

    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": key,
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

    # -- Dynamic update / delete commands for personal info --
    # Examples: "change my name to Alice", "update my city to London", "forget my age"
    m = re.search(r"(?:change|update) my ([a-z ]+) to (.+)", command)
    if m:
        field = m.group(1).strip()
        value = m.group(2).strip()
        # map common field names to internal keys
        mapping = {
            "name": "name",
            "my name": "name",
            "age": "age",
            "my age": "age",
            "city": "location",
            "location": "location",
            "live in": "location",
            "occupation": "occupation",
            "job": "occupation",
        }
        key = mapping.get(field, field.replace(" ", "_"))
        # normalize some values
        if key in ("name", "occupation", "location"):
            value = value.title()
        if key == "age":
            try:
                value = str(int(re.search(r"(\d+)", value).group(1)))
            except Exception:
                pass
        set_personal_field(key, value)
        speak(f"Updated {field} to {value}.")
        return

    m2 = re.search(r"(?:forget|remove|delete) my ([a-z ]+)", command)
    if m2:
        field = m2.group(1).strip()
        mapping = {
            "name": "name",
            "age": "age",
            "city": "location",
            "location": "location",
            "occupation": "occupation",
            "job": "occupation",
        }
        key = mapping.get(field, field.replace(" ", "_"))
        ok = delete_personal_field(key)
        if ok:
            speak(f"I've removed your {field} from memory.")
        else:
            speak(f"I don't have {field} stored.")
        return

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
    

    # 🧠 Memory commands
    elif "what do you remember" in command or "tell me about myself" in command:
        memory = load_memory()
        summary = summarize_memory_for_speech(memory)
        if summary:
            speak("Here's what I remember about you:")
            # Break long summary into shorter sentences for TTS
            for sentence in [s.strip() for s in summary.split('.') if s.strip()]:
                speak(sentence + '.')
        else:
            speak("I don't have much information about you yet. Try telling me about yourself!")

    elif "remember this" in command or "remember that" in command:
        speak("What would you like me to remember?")
        with sr.Microphone() as source:
            print("Listening for memory...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        try:
            memory_text = recognizer.recognize_google(audio)
            extract_memory(memory_text)
            speak("Got it! I'll remember that.")
        except:
            speak("Sorry, I didn't catch that.")

    elif "search memory" in command or "find in memory" in command:
        speak("What would you like me to search for?")
        with sr.Microphone() as source:
            print("Listening for search term...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        try:
            search_term = recognizer.recognize_google(audio)
            results = search_memory(search_term)
            if results:
                speak(f"I found some information about {search_term}:")
                for category, items in results.items():
                    speak(f"{category}: {', '.join(str(item) for item in items[:3])}")
            else:
                speak(f"I couldn't find anything about {search_term} in my memory.")
        except:
            speak("Sorry, I didn't catch that.")

    elif "clear memory" in command or "forget everything" in command:
        speak("Are you sure you want me to clear all memory? Say 'yes' to confirm.")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=2)
        try:
            confirmation = recognizer.recognize_google(audio).lower()
            if "yes" in confirmation:
                # Reset memory file
                save_memory({"personal": {}, "preferences": {}, "conversations": []})
                speak("Memory cleared. Starting fresh!")
            else:
                speak("Memory not cleared.")
        except:
            speak("Memory not cleared.")

    elif "chat" in command:
        speak("Sure, ask me anything.")
        with sr.Microphone() as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        try:
            command_text = recognizer.recognize_google(audio)
            print("You:", command_text)

            # Extract memory from user input
            extract_memory(command_text)

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
    elif "exit" in command or "stop" in command or "goodbye" in command or "bye-bye" in command:
        speak("Goodbye sir!")
        exit()
 
    # ── Fallback ──────────────────────────
    else:
        speak("I didn't understand that command.")



   


# MAIN LOOP
if __name__ == "__main__":
    speak("Hello pankaj,  I am matrix, your personal assistant. How can I help you today?")

    interaction_count = 0

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

                    # Process command
                    processcommand(command)

                    # Periodic memory cleanup (every 50 interactions)
                    interaction_count += 1
                    if interaction_count % 50 == 0:
                        cleanup_memory(days_old=30)
                        print("Memory cleanup completed.")

        except Exception as e:
            print("Error:", e)