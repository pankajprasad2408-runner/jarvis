
import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary

recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()


def processcommand(command):
    command=command.lower()
    
    if "open google" in command:
        webbrowser.open("https://google.com")
        speak("Opening Google")
    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com/")
        speak("opening youtube")
    elif"open instagram" in command:
        webbrowser.open("https://www.instagram.com")
        speak("opening instagram")
    # elif command.startwith("play"):
    #     song= command.lower().split(" ")[1]
    #     musicLibrary.music[song]
    # elif command.startswith("play") :
    #     song= command.lower().replace("play","")
    #     if song in musicLibrary.music:
    #         link=musicLibrary.music[song]
    #         webbrowser.open(link)
    #     else:
    #         speak("song not found in library")
    #     link=musicLibrary.music[song]
    #     webbrowser.open(link)
    elif command.startswith("play"):
        song = command.lower().replace("play ", "")

    if song in musicLibrary.music:
        link = musicLibrary.music[song]
        speak(f"Playing {song}")
        webbrowser.open(link)
         
    elif "stop" in command or "quit" in command or "exit" in command:
        print("good bye")
        exit()
        
if __name__ == "__main__":
    speak("Initializing jarvis..")
    

    while True:
        try:
            with sr.Microphone() as source:
                print("Listening...")
                recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            word= recognizer.recognize_google(audio)
            print("you say", word)
            
            if "jarvis" in word.lower():    
                speak("yes sirrr....")

                with sr.Microphone() as source:
                    print("Listening command...")
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                command=recognizer.recognize_google(audio)
                print("command",command)
                processcommand(command)
              
           
                      
            

        except sr.WaitTimeoutError:
            print("No speech detected")

        except Exception as e:
            print("Error:", e)
    