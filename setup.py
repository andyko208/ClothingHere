import os
import random

from datetime import datetime
from pydantic import BaseModel, PositiveInt

from google import genai
from google.genai import types, client
# from elevenlabs import ElevenLabs


# class Output(BaseModel):
#     description: str
#     fabrics: Dict[str, float]

class modelLog(BaseModel):
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    model: str
    total_tokens: int
    input_tokens: int
    prompt_len: int
    img_pixels: int
    audio_sec: float
    output_tokens: int
    temperature: float
    top_p: float
    top_k: float
    system_instruction: str
    prompt: str
    response: str

    def to_string(self):
        return f"{self.timestamp}\t{self.model}\t{self.total_tokens}\t{self.input_tokens}\t{self.prompt_len}\t{self.img_pixels}\t{self.audio_sec}\t{self.output_tokens}\t{self.temperature}\t{self.top_p}\t{self.top_k}\t{self.system_instruction}\t{self.prompt}\t{self.response}\n"


def setup_LLM(model_id=1) -> tuple[genai.Client, str]:
    """LLM for analyzing images"""
    gemini_client = genai.Client(api_key=os.getenv("GOOGLEGENAI_API_KEY"))
    gemini_models = {
        0: 'gemini-1.5-flash-8b',            # High volume and lower intelligence tasks
        1: 'gemini-1.5-flash',               # Fast and versatile performance across a diverse variety of tasks
        2: 'gemini-2.0-flash-lite',          # Cost efficiency and low latency
        3: 'gemini-2.0-flash',               # Next generation features, speed, thinking, and realtime streaming.
        4: 'gemini-2.5-flash-preview-05-20', # Adaptive thinking, cost efficiency
    }
    # gemini_model = gemini_models[random.randint(0, len(gemini_models)-1)] # 2.5 unavilable for now
    gemini_model = gemini_models[model_id]
    return gemini_client, gemini_model

# def setup_TTS() -> ElevenLabs:
#     elevenlabs = ElevenLabs(
#         api_key=os.getenv("ELEVENLABS_API_KEY"),
#     )
#     return elevenlabs

def set_modelLog(model: str, config: types.GenerateContentConfig, contents: dict, response: types.GenerateContentResponse) -> modelLog:
    """
    set modelInput from response and config
    """
    with open('logs/response_log.tsv', 'a') as f:
        if not response.text:
            return
        f.write(modelLog(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        model=model,
        total_tokens=response.usage_metadata.total_token_count,
        input_tokens=response.usage_metadata.prompt_token_count,
        prompt_len=len(contents['text']),
        img_pixels=contents['img'].size[0]*contents['img'].size[1],
        audio_sec=contents['audio'].duration if contents['audio'] else 0, # TODO: handle when there's audio/video
        output_tokens=response.usage_metadata.candidates_token_count,
        temperature=config.temperature,
        top_p=config.top_p,
        top_k=config.top_k,
        system_instruction=config.system_instruction,
        prompt=contents['text'],
        response=response.text.replace('\n', ' ').replace('\t', ' ')
    ).to_string())
    
def set_config(instruction: str, temperature=0.5, top_p=0.9, top_k=40, response_mime_type=None, response_schema=None):
    config = types.GenerateContentConfig(
        system_instruction=instruction,
        temperature=temperature,                  # Higher for creative lower for factual
        top_p=top_p,                              # Control diversity of outputs
        top_k=top_k,                              # Limit the number of highest probability tokens to consider
        max_output_tokens=512,                    # Limit the response length
    )
    if response_mime_type:
        config.response_mime_type = response_mime_type
    if response_schema:
        config.response_schema = response_schema
    return config