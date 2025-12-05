import os
import datetime
from json import dump, load
from dotenv import load_dotenv
from googlesearch import search  # type: ignore
from groq import Groq  # type: ignore


env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

Username = os.getenv("Username")
AssistantName = os.getenv("Assistantname")
GroqAPIKey = os.getenv("GroqAPIKey")

if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in environment. Check your .env file")

client = Groq(api_key=GroqAPIKey)

# ---------------- Data paths ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "../Data")
os.makedirs(DATA_DIR, exist_ok=True)

CHATLOG_PATH = os.path.join(DATA_DIR, "ChatLog.json")

# Create empty ChatLog.json if missing
if not os.path.exists(CHATLOG_PATH):
    with open(CHATLOG_PATH, "w", encoding="utf-8") as f:
        dump([], f)

# ---------------- System message ----------------
System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {AssistantName} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

# ---------------- Google Search ----------------
def GoogleSearch(Query):
    results = list(search(Query, num_results=5))
    if not results:
        return None

    Answer = f"The search results for {Query} are :[start]\n"
    for r in results:
        Answer += f"Result: {str(r)}\n"
    Answer += "[end]"
    return Answer

# ---------------- Answer modifier ----------------
def AnswerModifier(Answer):
    lines = Answer.split("\n")
    non_empty_lines = [line for line in lines if line.strip()]
    return "\n".join(non_empty_lines)

# ---------------- System chat history ----------------
SystemChabot = [
    {"role": "system", "content": System},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I assist you today?"}
]

def Information():
    now = datetime.datetime.now()
    return (f"Please use this realtime information in your response: Day is "
            f"{now.strftime('%A')}, Date is {now.strftime('%d')}, "
            f"Month is {now.strftime('%B')}, Year is {now.strftime('%Y')}, "
            f"Time is {now.strftime('%H')}:{now.strftime('%M')}:{now.strftime('%S')}.")

# ---------------- RealTimeSearchEngine ----------------
def RealTimeSearchEngine(prompt):
    global SystemChabot

    # Read messages
    with open(CHATLOG_PATH, "r", encoding="utf-8") as f:
        messages = load(f)

    messages.append({"role": "user", "content": prompt})
    search_data = GoogleSearch(prompt)

    # Append search data if available
    if search_data:
        SystemChabot.append({"role": "system", "content": search_data})

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=SystemChabot + [{"role": "system", "content": Information()}] + messages,
        max_tokens=1000,
        temperature=0.7,
        top_p=0.9,
        stop=None,
    )

    Answer = completion.choices[0].message.content.strip()
    Answer = Answer.replace("</s>", "")
    messages.append({"role": "assistant", "content": Answer})

    # Save messages
    with open(CHATLOG_PATH, "w", encoding="utf-8") as f:
        dump(messages, f, indent=4)

    # Remove search data from system chat
    if search_data:
        SystemChabot.pop()

    return AnswerModifier(Answer)

# ---------------- Run standalone ----------------
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question : ")
        result = RealTimeSearchEngine(user_input)
        print(result)
