from AppOpener import close,open as appopen # type: ignore
from webbrowser import open as webopen
from pywhatkit import search,playonyt # type: ignore
from dotenv import dotenv_values
from bs4 import BeautifulSoup
from rich import print
from groq import Groq # type: ignore
import webbrowser
import subprocess
import os
import requests
import shutil
import webbrowser
import asyncio
import keyboard # type: ignore

import os
from dotenv import load_dotenv

# Load .env from Backend folder
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)  

# Get API key from environment
GroqAPIKey = os.getenv("GroqAPIKey")
if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in environment. Check your .env file")

# Initialize client
from groq import Groq  # type: ignore
client = Groq(api_key=GroqAPIKey)


classes = [
    "zCubwf", "hgKEIc", "LTKOO sY7ric", "z0LCW", "gsrt vk_bk FzvWSb YwPhnf",
    "pclqee", "tw-Data-text tw-text-small tw-ta", "IZ6rdc", "O5uR6d LTKOO",
    "vIzY6d", "webanswers-webanswers_table__webanswers-table", "dOoNo ikb4Bb gsrt",
    "sXLAoe", "LWkfKe", "VQF4g", "qv3Wpe", "kno-rdesc", "SPZz6b"
]

useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"


professional_responses = [
    "Your satisfaction is my priority. How can I assist you further?",
    "I am here to help you with any questions or concerns you may have.",
]

messages=[]

SystemChatBot = [
    {"role": "system",
     "content": f"Hi, I am {os.environ.get('Username', 'User')}! You are a helpful assistant and a content writer. Write a letter based on the user's request."}
]

def GoogleSearch(topic):
    search(topic)
    return True


def Content(topic):
    def notepad(File):
        default_editor = 'notepad.exe'
        subprocess.Popen([default_editor, File])

    def Contentwriter(prompt):
        messages.append({"role": "user", "content": prompt})
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            top_p=0.9,
            stream=False,
            stop=None
        )

        Answer = completion.choices[0].message.content.strip()
        Answer = Answer.replace("</s>", "")

        messages.append({"role": "assistant", "content": Answer})
        return Answer

    topic = topic.replace("Content", "")
    Contentai = Contentwriter(topic)

    with open(f"../Data/{topic}.txt", "w") as f:
        f.write(Contentai)
        notepad(f"../Data/{topic}.txt")
    return True


def YTSearch(topic):
    URL = f"https://www.youtube.com/results?search_query={topic}"
    webbrowser.open(URL)
    return True



def PlayOnYT(topic):
    playonyt(topic)
    return True





def Openapp(app_name):

    app_path = shutil.which(app_name)

    if app_path:
        print(f"Opening {app_name}...")
        os.startfile(app_path)
    else:
        print(f"{app_name} not found. Searching online...")
        
        # Replace spaces for search query
        query = app_name.replace(" ", "+")
        url = f"https://www.google.com/search?q=download+{query}"
        webbrowser.open(url)



def closeapp(app):
    if "chrome" in app:
        pass
    else:
        try:
            close(app)
            return True
        except:
            return False
        

    

def System(command):
    def mute():
        keyboard.press_and_release("volume mute")
        return "System volume muted."
    
    def unmute():
        keyboard.press_and_release("volume unmute")
        return "System volume unmuted."
    
    def volumeup():
        keyboard.press_and_release("volume up")
        return "System volume increased."
    
    def volumedown():
        keyboard.press_and_release("volume down")
        return "System volume decreased."
    
    if command=="mute":
        mute()
    elif command=="unmute":
        unmute()
    elif command=="volumeup":
        volumeup()
    elif command=="volumedown":
        volumedown()
    return True


async def translateandexecute(commands:list[str]):
    funcs = []

    for command in commands:
        if command.startswith("open "):
            if "open it" in command:
                pass
            if "open file" in command:
                pass
            else:
                fun = asyncio.to_thread(Openapp, command.removeprefix("open "))
                funcs.append(fun)

        elif command.startswith("general "):
            pass

        elif command.startswith("realtime "):
            pass

        elif command.startswith("close "):
            fun = asyncio.to_thread(closeapp, command.removeprefix("close "))
            funcs.append(fun)

        elif command.startswith("content "):
            fun = asyncio.to_thread(Content, command.removeprefix("content "))
            funcs.append(fun)

        elif command.startswith("play "):
            fun = asyncio.to_thread(PlayOnYT, command.removeprefix("play "))
            funcs.append(fun)

        elif command.startswith("google search "):
            fun = asyncio.to_thread(GoogleSearch, command.removeprefix("google search "))
            funcs.append(fun)

        elif command.startswith("youtube search "):
            fun = asyncio.to_thread(YTSearch, command.removeprefix("youtube search "))
            funcs.append(fun)

        elif command.startswith("system "):
            fun = asyncio.to_thread(System, command.removeprefix("system "))
            funcs.append(fun)

        else:
            print(f"[red]Unknown command: {command}[/red]")

    results = await asyncio.gather(*funcs, return_exceptions=True)
    for r in results:
        yield r


async def Automation(commands:list[str]):
    async for _ in translateandexecute(commands):
        pass
    return True


    