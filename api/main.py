# from fastapi import FastAPI, File, UploadFile
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# import pdfplumber
# from io import BytesIO
# import collections
# import re
# import os

# app = FastAPI()

# # السماح بالتواصل مع الواجهة (مثلاً React)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # استخراج النص من PDF
# def extract_text_from_pdf(pdf_file):
#     text = ""
#     with pdfplumber.open(BytesIO(pdf_file)) as pdf:
#         for page in pdf.pages:
#             page_text = page.extract_text()
#             if page_text:
#                 text += page_text + " "
#     return text

# # استخراج كلمات مفتاحية يدوياً (أكثر الكلمات تكراراً بعد تنظيف النص)
# def extract_keywords(text):
#     words = re.findall(r'\b\w{4,}\b', text.lower())  # كلمات بطول 4 أحرف أو أكثر
#     common_words = ["with", "from", "this", "that", "have", "your", "which", "will", "about", "other"]
#     filtered = [word for word in words if word not in common_words]
#     counter = collections.Counter(filtered)
#     most_common = counter.most_common(5)
#     return [word for word, _ in most_common]

# @app.post("/upload-cv/")
# async def upload_cv(file: UploadFile = File(...)):
#     try:
#         pdf_file = await file.read()
#         text = extract_text_from_pdf(pdf_file)
#         if text:
#             keywords = extract_keywords(text)
#             return JSONResponse(content={"keywords": keywords})
#         else:
#             return JSONResponse(content={"error": "No text found in the file."}, status_code=400)
#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)

# # لتشغيل السيرفر على Render أو محليًا
# # port = int(os.getenv("PORT", 8000))
# # if __name__ == "__main__":
# #     import uvicorn
# #     uvicorn.run(app, host="0.0.0.0", port=port)

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sklearn.metrics.pairwise import cosine_similarity
import pdfplumber
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
import os
import numpy as np
import re

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# 1. تحميل ملف الـ PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(BytesIO(pdf_file)) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# 2. تحديد الكلمات المفتاحية حسب المجال
def get_predefined_keywords(job_type):
    keywords_dict = {
        "web": ["web", "front end", "backend", "developer", "html", "css", "javascript", "react", "angular", "vue", "next", "node", "php", "laravel"],
        "data": ["data analyst", "machine learning", "python", "AI", "big data",],
        "graphic designer": ["graphic designer", "photoshop", "illustrator", "design", "branding", "visual"],
        "accountant": ["accountant", "finance", "tax", "audit", "bookkeeping", "balance sheet"],
        "doctor": ["doctor", "medicine", "healthcare", "medical", "clinic", "patient", "treatment"],
        "police": ["police", "law enforcement", "investigation", "criminal", "security", "law"],
        "lawyer": ["lawyer", "legal", "court", "litigation", "defense", "criminal", "contracts"],
        "pharmacist": ["pharmacist", "pharmacy", "medication", "prescription", "drugs", "healthcare"],
        "medical": ["healthcare", "medical", "patient", "doctor", "nurse", "treatment", "hospital"],
        "network": ["network", "IT", "cybersecurity", "cloud", "server", "networking", "infrastructure"]
    }
    return keywords_dict.get(job_type.lower(), [])

# 3. استخراج الكلمات المفتاحية من النص بناءً على الكلمات المحددة مسبقًا
def extract_keywords(text, job_type):
    predefined_keywords = get_predefined_keywords(job_type)
    found_keywords = []
    
    for keyword in predefined_keywords:
        if keyword.lower() in text.lower():
            found_keywords.append(keyword)
    
    return found_keywords[:2]  # إرجاع كلمتين مفتاحيتين فقط

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # السماح بطلبات React
    allow_credentials=True,
    allow_methods=["*"],  # السماح بجميع أنواع الطلبات (GET, POST, DELETE...)
    allow_headers=["*"],  # السماح بجميع الرؤوس
)

@app.post("/upload-cv/")
async def upload_cv(file: UploadFile = File(...), job_type: str = "web"):
    try:
        pdf_file = await file.read()
        text = extract_text_from_pdf(pdf_file)
        if text:
            keywords = extract_keywords(text, job_type)
            if keywords:
                return JSONResponse(content={"keywords": keywords})
            else:
                return JSONResponse(content={"error": "No relevant keywords found."}, status_code=400)
        else:
            return JSONResponse(content={"error": "No text found in the file."}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# # تشغيل السيرفر
# port = int(os.getenv("PORT", 8000))
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=port)
