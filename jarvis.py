import google.generativeai as genai
import pyttsx3
import speech_recognition as sr
import webbrowser
import requests
import datetime
import time
import threading
from api_keys import GEMINI_API_KEY, OPENWEATHERMAP_API_KEY, NEWSAPI_API_KEY

# Configure the Google Generative AI
genai.configure(api_key=GEMINI_API_KEY)

def Reply(question):
    model = genai.GenerativeModel("gemini-pro")
    chat = model.start_chat(history=[])
    response = chat.send_message(question)
    return response.text

# Initialize the text-to-speech engine
engine = pyttsx3.init("sapi5")
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)

def speak(text):
    engine.say(text)
    engine.runAndWait()

def takeCommand():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening....")
        r.pause_threshold = 1
        audio = r.listen(source)
    try:
        print("Recognizing.....")
        query = r.recognize_google(audio, language="en-in")
        print(f"User Said: {query}\n")
    except sr.UnknownValueError:
        print("Could not understand the audio. Say that again, please.")
        return "None"
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
        return "None"
    return query

def get_weather(city):
    api_key = OPENWEATHERMAP_API_KEY
    base_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    try:
        response = requests.get(base_url)
        data = response.json()
        if response.status_code == 200:
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})
            temperature = main.get("temp", "N/A")
            humidity = main.get("humidity", "N/A")
            description = weather.get("description", "N/A")
            wind_speed = wind.get("speed", "N/A")
            pressure = main.get("pressure", "N/A")
            return (
                f"The weather in {city} is {description}. "
                f"Temperature is {temperature}°C, humidity is {humidity}%, "
                f"wind speed is {wind_speed} m/s, and pressure is {pressure} hPa."
            )
        else:
            return f"Unable to fetch weather data. Status code: {response.status_code}. Message: {data.get('message', 'Unknown error')}"
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return "Sorry, I couldn't fetch the weather information at the moment."

reminders = []

def set_reminder(reminder_text, reminder_time):
    now = datetime.datetime.now()
    if reminder_time <= now:
        speak("The reminder time must be in the future.")
        return
    
    reminders.append((reminder_text, reminder_time))
    speak(f"Reminder set for {reminder_time.strftime('%H:%M')}")

def check_reminders():
    now = datetime.datetime.now()
    reminders_to_speak = [reminder for reminder in reminders if now >= reminder[1]]
    reminders[:] = [reminder for reminder in reminders if now < reminder[1]]

    for reminder in reminders_to_speak:
        speak(f"Reminder: {reminder[0]}")

def get_news():
    api_key = NEWSAPI_API_KEY
    url = f"http://newsapi.org/v2/top-headlines?country=in&apiKey={api_key}"

    try:
        response = requests.get(url)
        news_data = response.json()
        articles = news_data.get("articles", [])
        headlines = [article["title"] for article in articles[:5]]
        return "Here are the top news headlines:\n" + "\n".join(headlines)
    except Exception as e:
        return "Sorry, I couldn't fetch the news at the moment."

def format_time(input_time):
    if len(input_time) == 4 and input_time.isdigit():
        return input_time[:2] + ":" + input_time[2:]
    return input_time

def reminder_checker():
    while True:
        check_reminders()
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=reminder_checker, daemon=True).start()
    
    while True:
        query = takeCommand().lower()

        if "hello" in query:
            speak("Which city's weather would you like to know?")
            city = takeCommand().lower()
            weather_info = get_weather(city)
            print(weather_info)
            speak(weather_info)
        elif "open youtube" in query:
            webbrowser.open("www.youtube.com")
        elif "open google" in query:
            webbrowser.open("www.google.com")
        elif "set reminder" in query:
            speak("What is the reminder?")
            reminder_text = takeCommand().lower()
            speak("At what time? Please say the time in HH:MM format.")
            reminder_time_str = takeCommand().lower()
            
            reminder_time_str = format_time(reminder_time_str)
            
            try:
                reminder_time = datetime.datetime.strptime(reminder_time_str, "%H:%M").replace(
                    year=datetime.datetime.now().year,
                    month=datetime.datetime.now().month,
                    day=datetime.datetime.now().day,
                )
                set_reminder(reminder_text, reminder_time)
            except ValueError:
                speak("Sorry, I couldn't understand the time format. Please try again.")
        elif "news" in query:
            news_info = get_news()
            print(news_info)
            speak(news_info)
        elif "goodbye" in query or "good bye" in query:
            speak("Goodbye!")
            break
        else:
            ans = Reply(query)
            print(ans)
            speak(ans)

        time.sleep(1)
