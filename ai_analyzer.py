import ollama
import json

import openai
from openai import OpenAI
from typing import List, Dict
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def analyze_image(image_path: str) -> dict:
    response = ollama.generate(
        model="llava",
        prompt=f"""
        Analyze this image from a person's daily life with high precision.
        Extract the following specific information:

        1. ACTIVITY: What is the person doing right now? Be specific and descriptive (e.g. "typing on laptop while drinking coffee" rather than just "working").
        2. OBJECTS: List exactly 3-7 most prominent objects visible in the image. Prioritize objects the person is interacting with.
        3. ENVIRONMENT: Describe the location specifically (e.g. "home office with natural lighting" instead of just "indoors").
        4. CONFIDENCE: For each element, assign a confidence score from 1-5 (where 1 is lowest confidence, 5 is highest).

        IMPORTANT INSTRUCTION: After assigning confidence scores, if ANY confidence score is LESS THAN 4, you MUST set "needs_clarification" to true in your response.

        Only include text visible if it's significant to understanding the scene.
        Maintain neutral, factual observations without assumptions about the person's feelings or intentions.

        Return ONLY a valid JSON object in exactly this format:
        {{
            "activity": "detailed description of activity",
            "objects": ["object1", "object2", "object3"],
            "environment": "detailed description of location",
            "confidence_scores": {{"activity": 5, "objects": 5, "environment": 5}},
            "needs_clarification": false
        }}

        FINAL CHECK: Before submitting your response, verify that "needs_clarification" is set to true if ANY confidence score is BELOW 4.
        """,
        images=[image_path]
    )

    try:
        text_response = response.get('response', '')
        json_text = text_response[text_response.find('{'): text_response.rfind('}') + 1]
        result = json.loads(json_text)

        # Add a safety check in case the model ignores instructions
        scores = result.get('confidence_scores', {})
        if any(scores.get(key, 5) < 4 for key in ['activity', 'objects', 'environment']):
            result['needs_clarification'] = True

        return result
    except Exception as e:
        print(f"JSON parse hatası: {e}")
        return {
            "activity": "unknown",
            "objects": [],
            "environment": "unknown",
            "confidence_scores": {
                "activity": 1,
                "objects": 1,
                "environment": 1
            },
            "needs_clarification": True
        }

def generate_daily_summary(analyses: List[Dict]) -> str:
    client = OpenAI()

    prompt = f"""
    Sen bir yaşam koçu ve veri analiz uzmanısın. Aşağıdaki kurallara göre bir kullanıcının günlük fotoğraf analizlerini özetleyeceksin:

### 🔍 **Analiz Formatı**
1. **Zaman Çizelgesi**  
   - Aktivite geçişlerini kronolojik sırayla listele.  
   - Örnek:  
     `09:00-11:30 → Masada çalışma (odak yüksek)`  
     `11:30-12:00 → Sosyal medya (telefon kullanımı)`

2. **Temel Metrikler**  
   - **Verimlilik:** Çalışma süresi & odak seviyesi (1-10 arası puan).  
   - **Sosyal Etkileşim:** İnsanlarla geçirilen süre.  
   - **Fiziksel Aktivite:** Hareketlilik oranı.  
   - **Dijital Detoks:** Telefon/PC dışı zaman.

3. **Eğilimler**  
   - **Olumlu:** Tekrarlanan iyi alışkanlıklar (örgün egzersiz).  
   - **Olumsuz:** Verim düşüren faktörler (sık multitasking).  

4. **Duygusal Durum**  
   - Yüz ifadeleri ve ortamdan çıkarım yap (mutlu/stresli/bitkin).  
   - Örnek:  
     `Öğleden sonra stres seviyesi artmış (yüz ifadesi + sık pozisyon değiştirme)`

5. **Öneriler**  
   - 3 somut iyileştirme tavsiyesi ver.  
   - Örnek:  
     `"Saat 15.00'teki verim düşüşü için 10 dakikalık şekerleme yapmayı dene."`

    Veri:
    {str(analyses)}

    Özet:
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    }
                ]
            }
        ],
        text={
            "format": {
                "type": "text"
            }
        },
        reasoning={},
        tools=[],
        temperature=1,
        max_output_tokens=2048,
        top_p=1,
        store=True
    )

    return response.output_text