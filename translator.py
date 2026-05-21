 
#import dotenv
import os
import requests
import base64
import json


with open("llm_prompt.json", 'r',encoding='utf-8') as f:
    llm_prompt_dict=json.load(f)


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



def translate_text(text, 
                    image_path=None,
                    llm_model_name="", 
                    extract_text_mode="ocr", 
                    language_mode="EN->TH",
                    story_name="",
                    api_key=""):
    """
    Translates the text using OpenRouter API, optionally with an image.
    """
    OPENROUTER_API_KEY=api_key
    MODEL= llm_model_name
    if not OPENROUTER_API_KEY:
        return "Error: OpenRouter API key not set."
        
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    print(text)

    base_prompt=llm_prompt_dict.get(language_mode)
    specific_prompt_dict = llm_prompt_dict.get("specific_story_prompt")
    specific_prompt=specific_prompt_dict.get(story_name, "")
    
    if specific_prompt:
        base_prompt+=specific_prompt

    content = [{"type": "text", "text": base_prompt}]
    if extract_text_mode=="llm":
        base64_image = encode_image(image_path)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/png;base64,{base64_image}"
            }
        })
    elif extract_text_mode=="ocr":
        content= [{"type": "text", "text": base_prompt+text}]
    else:
        raise ValueError("Invalid extract_text_mode")  
    data = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": content}
        ],
        "provider": {
            "sort": "latency",
            #"order": ["parasail/bf16","google-vertex/global"],
        }
    }
    #prompt_refine=f"ทำให้ภาษาที่แปลมาถูกต้อง และลื่นขึ้นเหมือนบทสนทนาในเกมจริงๆ ไม่ต้องมีคำอธิบายใดๆ\n\nDialogue:\n{text}"

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Translation error: {e}")
        return f"Translation error: {e}"


