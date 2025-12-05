from groq import Groq # type: ignore
from json import dump, dumps, load
import datetime
from dotenv import dotenv_values
import os
from dotenv import load_dotenv

# Load .env from the Backend folder
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)  # populates os.environ


Username = os.getenv("Username")
AssistantName = os.getenv("Assistantname")  # fix spelling
GroqAPIKey = os.getenv("GroqAPIKey")


if not GroqAPIKey:
    raise ValueError("GroqAPIKey not found in environment. Check your .env file")

# Initialize Groq client
from groq import Groq  # type: ignore
client = Groq(api_key=GroqAPIKey)
messages=[]

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {AssistantName} which also has real-time up-to-date information from the internet.
*** Do not tell time until I ask, do not talk too much, just answer the question.***
*** Reply in only English, even if the question is in Hindi, reply in English.***
*** Do not provide notes in the output, just answer the question and never mention your training data. ***
"""

SystemChatBot=[
    {"role": "system", "content": System},
]

try:
    with open(r"../Data/Chatlog.json", "r") as f:
       messages=load(f)
except:
    with open(r"../Data/Chatlog.json", "w") as f:
        dump([],f)

def RealtimeInformation():
    current_date_time= datetime.datetime.now()
    day=current_date_time.strftime("%A")
    date=current_date_time.strftime("%d")
    month=current_date_time.strftime("%B")
    year=current_date_time.strftime("%Y")
    hour=current_date_time.strftime("%H")
    minute=current_date_time.strftime("%M")
    second=current_date_time.strftime("%S")

    data=f"Please use this realtime information in your response: Day is {day}, Date is {date}, Month is {month}, Year is {year}, Time is {hour}:{minute}:{second}."
    return data

def AnswerModifier(Answer):
    lines=Answer.split("\n")
    non_empty_lines=[line for line in lines if line.strip()]
    modified_answer="\n".join(non_empty_lines)
    return modified_answer

def Chatbot(Query):
    """Function to interact with the Groq chatbot model."""
    try:
        with open(r"../Data/Chatlog.json", "r") as f:
            messages=load(f)
        
        messages.append({"role": "user", "content": Query})
        completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=SystemChatBot + [{"role":"system","content":RealtimeInformation()}] + messages,
        max_tokens=1000,
        temperature=0.7,
        top_p=0.9,
        stop=None,
    )

        Answer = completion.choices[0].message.content.strip()
        Answer = Answer.replace("</s>", "")

        messages.append({"role": "assistant", "content": Answer})

        with open(r"../Data/Chatlog.json", "w") as f:
            dump(messages, f, indent=4)

        return AnswerModifier(Answer=Answer)

    except Exception as e:
        return f"An error occurred: {str(e)}"
    
if __name__ == "__main__":
    while True:
        user_input = input("Enter Your Question : ")
        response = Chatbot(user_input)
        print(response)
            




