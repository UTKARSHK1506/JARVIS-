import os 
from dotenv import load_dotenv


env_path = os.path.join(os.path.dirname(__file__), "Backend", ".env")
load_dotenv(env_path) 


from Frontend.GUI import (
    GraphicalUserInterface,
    SetAssistantStatus,
    ShowTextToScreen,     
    TempdirPath as TempDirectoryPath,         
    SetMicrophoneStatus,
    Answermodifier as AnswerModifier,
    Querymodifier as QueryModifier,
    GetMicrophoneStatus,
    GetAssistantStatus
)

# read environment variables using os.getenv 
CohereAPIKey = os.getenv("CohereAPIKey")
Username = os.getenv("Username")
AssistantName = os.getenv("Assistantname")

# Now import Backend modules
from Backend.Model import FirstLayerDMM
from Backend.RealTimeSearchEngine import RealTimeSearchEngine # type: ignore
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition
from Backend.Chatbot import Chatbot as ChatBot
from Backend.TextToSpeech import TextToSpeech

from asyncio import run
from time import sleep
import subprocess
import threading
import json

import time
import traceback

DefaultMessage = f'''
{Username} : Hello {AssistantName}, How are you?
{AssistantName} : Welcome {Username}. I am doing well. How may i help you?
'''

Subprocesses = []

Functions = ["open", "close", "play", "system", "content", "google search", "youtube search"]




def ShowDefaultChatIfNoChats():
    """
    Create default temp files if ChatLog.json is empty or missing.
    Uses safe open/close and avoids leaving a file handle open.
    """
    try:
        path = r'Data\ChatLog.json'
        # ensure file and directory exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, "w", encoding='utf-8') as f:
                json.dump([], f)
      
            with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                file.write("")
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                file.write("")
            return

        # check length safely
        with open(path, "r", encoding='utf-8') as File:
            content = File.read()
        if len(content.strip()) < 2:
            with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
                file.write("")
            with open(TempDirectoryPath('Responses.data'), 'w', encoding='utf-8') as file:
                file.write("")
    except Exception as e:
        # Log error so we can debug if needed but do not crash
        print(f"[debug] ShowDefaultChatIfNoChats error: {e}")


def ReadChatLogJson():
    """
    Safe loader for ChatLog.json. Returns list always.
    If file is corrupt, tries to recover by truncating to an empty list.
    """
    path = r'Data\ChatLog.json'
    try:
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding='utf-8') as f:
                json.dump([], f)
            return []
        with open(path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                if isinstance(data, list):
                    # trim to last 50 entries to avoid sending huge context
                    return data[-50:]
                else:
                    return []
            except json.JSONDecodeError:
                # corrupted JSON: overwrite with empty list and return empty
                with open(path, "w", encoding='utf-8') as f:
                    json.dump([], f)
                return []
    except Exception as e:
        print(f"[debug] ReadChatLogJson error: {e}")
        return []


def ChatLogIntegration():
    """
    Build a small, trimmed formatted chatlog and write to Database.data.
    Trim to last 12 pairs (approx) to keep downstream model input small.
    """
    try:
        json_data = ReadChatLogJson()
        formatted_chatlog = ""

        # Keep only recent entries to avoid super long formatted strings
        recent = json_data[-24:]  # ~12 user/assistant pairs

        for entry in recent:
            if entry.get("role") == "user":
                formatted_chatlog += f"User: {entry.get('content','')}\n"
            elif entry.get("role") == "assistant":
                formatted_chatlog += f"Assistant: {entry.get('content','')}\n"

        formatted_chatlog = formatted_chatlog.replace("User", (Username or "User") + " ")
        formatted_chatlog = formatted_chatlog.replace("Assistant", (AssistantName or "Assistant") + " ")

        # Guard AnswerModifier — if it fails, fallback to raw formatted_chatlog
        try:
            out = AnswerModifier(formatted_chatlog)
        except Exception as e:
            print(f"[debug] AnswerModifier error: {e}")
            out = formatted_chatlog

        
        with open(TempDirectoryPath('Database.data'), 'w', encoding='utf-8') as file:
            file.write(out)
    except Exception as e:
        print(f"[debug] ChatLogIntegration error: {e}")


def ShowChatsOnGUI():
    File = open(TempDirectoryPath('Database.data'), "r", encoding='utf-8')
    Data = File.read()

    if len(str(Data)) > 0:
        lines = Data.split('\n')
        result = '\n'.join(lines)
        File.close()

        File = open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8')
        File.write(result)
        File.close()


def InitialExecution():
    SetMicrophoneStatus("False")
    ShowTextToScreen("")
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    ShowChatsOnGUI()


InitialExecution()


# -------------------------
# Instrumented MainExecution 
# -------------------------
_iteration_counter = 0

def MainExecution():
    """
    Instrumented MainExecution:
    - per-step timings and debug prints
    - try/except around each external call to ensure failures don't kill the loop
    - prints full tracebacks on exceptions so we can find root cause
    """
    global _iteration_counter
    _iteration_counter += 1
    iteration_id = _iteration_counter

    def _log(msg):
        print(f"[iter {iteration_id}] {msg}")

    TaskExecution = False
    ImageExecution = False
    ImageGenerationQuery = ""

    try:
        _log("start MainExecution")
        SetAssistantStatus("Listening...")

        t0 = time.time()
        try:
            Query = SpeechRecognition()
            _log(f"SpeechRecognition returned: {repr(Query)}")
        except Exception as e:
            Query = None
            _log("SpeechRecognition raised exception:")
            traceback.print_exc()

        t1 = time.time()
        _log(f"SpeechRecognition elapsed: {t1 - t0:.3f}s")

        if not Query:
            _log("No Query captured; exiting this iteration early.")
            return False

        ShowTextToScreen(f"{Username} : {Query}")
        SetAssistantStatus("Thinking...")

        # FirstLayerDMM
        t0 = time.time()
        try:
            Decision = FirstLayerDMM(Query)
            _log(f"FirstLayerDMM returned: {repr(Decision)}")
        except Exception as e:
            Decision = [f"general {Query}"]
            _log("FirstLayerDMM raised exception:")
            traceback.print_exc()
        t1 = time.time()
        _log(f"FirstLayerDMM elapsed: {t1 - t0:.3f}s")

        print("")
        print(f"Decision : {Decision}")
        print("")

        G = any([i for i in Decision if i.startswith("general")])
        R = any([i for i in Decision if i.startswith("realtime")])

        Mearged_query = " and ".join(
            [" ".join(i.split()[1:]) for i in Decision if i.startswith("general") or i.startswith("realtime")]
        )

        for queries in Decision:
            if "generate" in queries:
                ImageGenerationQuery = str(queries)
                ImageExecution = True

        # Task automations - catch exceptions
        for queries in Decision:
            if TaskExecution == False:
                if any(queries.startswith(func) for func in Functions):
                    try:
                        # run automations but guard exceptions
                        run(Automation(list(Decision)))
                        TaskExecution = True
                        _log("Automation executed synchronously")
                    except Exception:
                        _log("Automation raised exception; attempting background submit")
                        try:
                            # try to fire-and-forget in background to avoid blocking
                            threading.Thread(target=lambda: run(Automation(list(Decision))), daemon=True).start()
                            TaskExecution = True
                            _log("Automation scheduled in background thread")
                        except Exception:
                            _log("Failed to schedule Automation in background")
                            traceback.print_exc()

        if ImageExecution == True:
            # write flag quickly
            try:
                with open(r"Frontend\Files\ImageGeneratioon.data", "w") as file:
                    file.write(f"{ImageGenerationQuery},True")
            except Exception:
                _log("Failed to write ImageGeneratioon.data")
                traceback.print_exc()

            try:
                p1 = subprocess.Popen(
                    ['python', r'Backend\ImageGeneration.py'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    shell=False
                )
                Subprocesses.append(p1)
                _log("ImageGeneration subprocess started")
            except Exception as e:
                _log(f"Error starting ImageGeneration.py: {e}")
                traceback.print_exc()

        if G and R or R:
            SetAssistantStatus("Searching...")
            _log(f"Calling RealTimeSearchEngine with: {repr(Mearged_query)}")
            t0 = time.time()
            try:
                Answer = RealTimeSearchEngine(QueryModifier(Mearged_query))
                _log(f"RealTimeSearchEngine returned (len {len(str(Answer))}): {repr(Answer)[:200]}")
            except Exception as e:
                Answer = "Sorry, I couldn't fetch realtime information right now."
                _log("RealTimeSearchEngine raised exception:")
                traceback.print_exc()
            t1 = time.time()
            _log(f"RealTimeSearchEngine elapsed: {t1 - t0:.3f}s")

            try:
                ShowTextToScreen(f"{AssistantName} : {Answer}")
            except Exception:
                _log("ShowTextToScreen failed:")
                traceback.print_exc()

            SetAssistantStatus("Answering...")

            # TTS - try/catch and non-fatal on failure
            t0 = time.time()
            try:
                TextToSpeech(Answer)
                _log("TextToSpeech completed")
            except Exception:
                _log("TextToSpeech raised exception:")
                traceback.print_exc()
            t1 = time.time()
            _log(f"TextToSpeech elapsed: {t1 - t0:.3f}s")

            return True

        else:
            for Queries in Decision:

                if "general" in Queries:
                    SetAssistantStatus("Thinking...")
                    QueryFinal = Queries.replace("general ", "")
                    t0 = time.time()
                    try:
                        Answer = ChatBot(QueryModifier(QueryFinal))
                        _log(f"ChatBot returned: {repr(Answer)}")
                    except Exception:
                        Answer = "Sorry, I couldn't produce an answer right now."
                        _log("ChatBot raised exception:")
                        traceback.print_exc()
                    t1 = time.time()
                    _log(f"ChatBot elapsed: {t1 - t0:.3f}s")

                    try:
                        ShowTextToScreen(f"{AssistantName} : {Answer}")
                    except Exception:
                        _log("ShowTextToScreen failed in general path:")
                        traceback.print_exc()

                    SetAssistantStatus("Answering...")
                    try:
                        TextToSpeech(Answer)
                    except Exception:
                        _log("TTS failed in general path:")
                        traceback.print_exc()
                    return True

                elif "realtime" in Queries:
                    SetAssistantStatus("Searching...")

                elif "exit" in Queries:
                    QueryFinal = "Okay, Bye!"
                    try:
                        Answer = ChatBot(QueryModifier(QueryFinal))
                    except Exception:
                        Answer = "Okay, Bye!"
                        traceback.print_exc()

                    ShowTextToScreen(f"{AssistantName} : {Answer}")
                    SetAssistantStatus("Answering...")
                    try:
                        TextToSpeech(Answer)
                    except Exception:
                        _log("TTS failed during exit:")
                        traceback.print_exc()
                    SetAssistantStatus("Answering...")
                    os._exit(1)

    except Exception as e:
        # Catch any unexpected exceptions in MainExecution so the FirstThread keeps running
        print(f"[error] MainExecution unexpected exception: {e}")
        traceback.print_exc()
        # small pause to avoid tight loop on repeated errors
        sleep(0.5)
        return False


def FirstThread():
    """
    Polls microphone state and runs MainExecution when microphone is active.
    Wrapped in try/except so any exception in MainExecution won't kill the thread.
    """
    while True:
        try:
            CurrentStatus = GetMicrophoneStatus()

            if CurrentStatus == "True":
                try:
                    MainExecution()
                    # lightweight log to help debug hangs
                    print("[debug] MainExecution completed one iteration")
                except Exception as inner_e:
                    # Log but keep the loop alive so it can continue after failures
                    print(f"[error] MainExecution raised: {inner_e}")
                    traceback.print_exc()
                    # small sleep to avoid busy-looping on persistent error
                    sleep(0.5)
            else:
                AIStatus = GetAssistantStatus()

                if "Available..." in AIStatus:
                    sleep(0.1)
                else:
                    SetAssistantStatus("Available...")
                    sleep(0.1)
        except Exception as e:
            # Catch any unexpected exceptions in the polling loop so the thread doesn't stop
            print(f"[error] FirstThread outer exception: {e}")
            traceback.print_exc()
            sleep(0.5)


def SecondThread():
    GraphicalUserInterface()


if __name__ == "__main__":
    thread2 = threading.Thread(target=FirstThread, daemon=True)
    thread2.start()
    SecondThread()
