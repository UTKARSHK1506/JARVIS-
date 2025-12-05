from selenium import webdriver  # type: ignore
from selenium.webdriver.chrome.service import Service  # type: ignore
from selenium.webdriver.common.by import By  # type: ignore
from selenium.webdriver.chrome.options import Options  # type: ignore
from webdriver_manager.chrome import ChromeDriverManager  # type: ignore
from dotenv import dotenv_values
import os
import mtranslate as mt  # pyright: ignore[reportMissingImports]

# Load InputLanguage from .env
env_vars = dotenv_values(".env")
InputLanguage = env_vars.get("InputLanguage", "en")

# HTML code for speech recognition
HtmlCode = '''<!DOCTYPE html>
<html lang="en">
<head>
    <title>Speech Recognition</title>
</head>
<body>
    <button id="start-btn" onclick="startRecognition()">Start Recognition</button>
    <button id="stop-btn" onclick="stopRecognition()">Stop Recognition</button>
    <p id="output"></p>
    <script>
        const output = document.getElementById('output');
        let recognition;

        function startRecognition() {
            recognition = new webkitSpeechRecognition() || new SpeechRecognition();
            recognition.lang = '';
            recognition.continuous = true;

            recognition.onresult = function(event) {
                const transcript = event.results[event.results.length - 1][0].transcript;
                output.textContent = transcript;
            };

            recognition.start();
        }

        function stopRecognition() {
            if (recognition) {
                recognition.stop();
            }
        }
    </script>
</body>
</html>'''

# Set the language
HtmlCode = HtmlCode.replace("recognition.lang = '';", f"recognition.lang = '{InputLanguage}';")

# ---------- FIXED PATH SYSTEM ----------
project_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
data_dir = os.path.join(project_root, "Data")
os.makedirs(data_dir, exist_ok=True)

html_path = os.path.join(data_dir, "Voice.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(HtmlCode)

Link = html_path.replace("\\", "/")
# --------------------------------------

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # <--- Hide Chrome
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--use-fake-device-for-media-stream")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-notifications")
chrome_options.add_argument("--allow-file-access-from-files")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-infobars")

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# TempDirPath for assistant status
TempDirPath = os.path.join(project_root, "Frontend", "Files")
os.makedirs(TempDirPath, exist_ok=True)

def SetAssistantStatus(Status):
    with open(os.path.join(TempDirPath, "AssistantStatus.txt"), 'w') as f:
        f.write(Status)

def QueryModifier(Query):
    new_query = Query.lower().strip()
    if not new_query.endswith(("?", ".", "!")):
        new_query += "?"
    return new_query.capitalize()

def Universaltranslate(text):
    english_translation = mt.translate(text, "en", "auto")
    return english_translation.capitalize()

def SpeechRecognition():
    driver.get(f"file:///{Link}")
    driver.find_element(By.ID, "start-btn").click()

    while True:
        try:
            text = driver.find_element(By.ID, "output").text
            if text:
                driver.find_element(By.ID, "stop-btn").click()
                SetAssistantStatus("Processing")

                if "en" in InputLanguage.lower():
                    return QueryModifier(text)
                else:
                    SetAssistantStatus("Translating")
                    return QueryModifier(Universaltranslate(text))

        except Exception:
            pass

if __name__ == "__main__":
    while True:
        text = SpeechRecognition()
        print("You said:", text)
