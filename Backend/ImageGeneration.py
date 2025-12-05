import asyncio
import httpx
from PIL import Image
from io import BytesIO
import os
from dotenv import dotenv_values
from time import sleep
import base64

# Load API key
env = dotenv_values(".env")
HF_KEY = env.get("HuggingFaceAPIKey")

# Correct Hugging Face Router endpoint
API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_KEY}"}

DATA_PATH = r"..\Data"
FRONTEND_DATA_PATH = r"..\Frontend\Files\ImageGeneration.data"


def open_images(prompt):
    prompt_clean = prompt.replace(" ", "_")
    for i in range(1, 5):
        for ext in ["jpg", "jpeg", "png"]:
            img_path = os.path.join(DATA_PATH, f"{prompt_clean}{i}.{ext}")
            if os.path.exists(img_path):
                try:
                    print(f"Opening Image → {img_path}")
                    Image.open(img_path).show()
                    sleep(1)
                except Exception as e:
                    print(f"Error opening {img_path}: {e}")


async def query(prompt_text):
    payload = {
        "inputs": prompt_text,
        "options": {"use_cache": False}  # Required by HuggingFace router
    }

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(API_URL, headers=headers, json=payload)

    # HuggingFace returns image bytes directly
    if "image" in response.headers.get("content-type", ""):
        return response.content

    # Or Base64 JSON
    try:
        data = response.json()
        if isinstance(data, list) and "generated_image" in data[0]:
            return base64.b64decode(data[0]["generated_image"])
        if "error" in data:
            print("HF Error:", data["error"])
    except:
        pass

    print("Unexpected response. No image received.")
    return None


async def generate_image(prompt):
    prompt_text = f"{prompt}, ultra detailed, 4K, sharp, professional"
    tasks = [asyncio.create_task(query(prompt_text)) for _ in range(4)]
    results = await asyncio.gather(*tasks)

    prompt_clean = prompt.replace(" ", "_")
    for i, img_bytes in enumerate(results):
        if not img_bytes:
            print(f"❌ Image {i+1} failed.")
            continue
        try:
            img = Image.open(BytesIO(img_bytes))
            ext = img.format.lower()
            out_path = os.path.join(DATA_PATH, f"{prompt_clean}{i+1}.{ext}")
            img.save(out_path)
            print(f"✔ Saved {out_path}")
        except Exception as e:
            print(f"❌ Invalid image {i+1}: {e}")


def ImageGeneration(prompt):
    asyncio.run(generate_image(prompt))
    open_images(prompt)


while True:
    try:
        with open(FRONTEND_DATA_PATH, "r") as f:
            txt = f.read().strip()

        if not txt or "," not in txt:
            sleep(1)
            continue

        prompt, status = txt.split(",")

        if status == "True":
            print("🎨 Generating images...")
            ImageGeneration(prompt)

            with open(FRONTEND_DATA_PATH, "w") as f:
                f.write(f"{prompt},False")

            break

    except Exception as e:
        print(f"Runtime error: {e}")
        sleep(1)
