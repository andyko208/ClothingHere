# To run: 
# uvicorn main:app --reload
# fastapi dev main.py
"""
Deploying for Free
FastAPI can be deployed for free on platforms like Render, Railway, Deta Space, or Fly.io.
Just make sure your main.py and static/ folder are in your repo.
Most platforms will run your app with a command like uvicorn main:app --host 0.0.0.0 --port 10000.
"""
import io
import os
import json
import random

from PIL import Image
import pillow_avif
from pillow_heif import register_heif_opener

from setup import setup_LLM, set_config, set_modelLog
from google import genai

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware



load_dotenv()   # Load environment variables from .env
app = FastAPI() # Create FastAPI app
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WELCOME_SPEECH = "welcome_speech.mp3"
DESCRIBE_SPEECH = "describe_speech.mp3"
client, model = setup_LLM()
# tts = setup_TTS()
config = set_config(
    instruction="You are a fashion designer. Your job is to detect as many fabrics as precisely as possible with confidence scores "
            "and provide a detailed description of the clothing's design, shape, color, and texture in 1-2 sentences. "
            "Strictly follow this output format - {\"description\": \"description of image\", \"fabrics\": {\"fabric_name\": confidence_score}} "
            "Let the subject of description be the clothing. If image does not contain clothing, state as is in description and detect no fabric.",
    temperature=0.7,
    top_p=0.95,
    top_k=20
    # response_mime_type='application/json',
    # response_schema= list[Output]
)
prompt = "Analyze the clothing that appear in the image."

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("static/index.html")

@app.post("/choose_LLM")
async def choose_LLM(text: str = Form(...)):
    global client
    global model
    client, model = setup_LLM(int(text))

@app.post("/check_image")
async def check_image(file: UploadFile = File(...)):
    register_heif_opener()
    await file.read()
    try:
        im = Image.open(file.file)
        # img = im.resize((384, 384))
        # print(img.size)
        # img.save("uploaded_image.png")
        return JSONResponse({"status": model})
    except:
        
        return JSONResponse({"status": None})

@app.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...)):
    print(f'model: {model}')
    await file.read()
    im = Image.open(file.file)
    img = im.resize((384, 384))
    # img.save("uploaded_image.png")
    contents = {'img': img, 'audio': None, 'video': None, 'text': prompt}

    response = client.models.generate_content(
        model=model,
        config=config,
        contents=[contents['img'], contents['text']],
    )
    # set_modelLog(model, config, contents, response)
    
    if response.text:
        r = response.text
        return JSONResponse(content=json.loads(r[r.find('{'):r.rfind('}')+1]))
    return JSONResponse(content={"description": f'Request timeout.', "fabrics": {}})

from TTS.api import TTS
coqui_tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False, gpu=False)
@app.get("/welcome_speech")
async def welcome_speech():
    os.makedirs("tmp_audio", exist_ok=True)
    path = "tmp_audio/welcome.mp3"
    if not os.path.exists(path):
        coqui_tts.tts_to_file(text="Clothing here. Press enter for an example.", file_path=path)
    return FileResponse(path, media_type="audio/mpeg")


@app.post("/describe_speech")
async def describe_speech(text: str = Form(...)):
    os.makedirs("tmp_audio", exist_ok=True)
    path = f"tmp_audio/{hash(text)}.mp3"
    if not os.path.exists(path):
        try:
            coqui_tts.tts_to_file(text=text, file_path=path)
        except Exception as e:
            print("TTS conversion error:", e)
            return JSONResponse(status_code=500, content={"error": str(e)})
    return FileResponse(path, media_type="audio/mpeg")
