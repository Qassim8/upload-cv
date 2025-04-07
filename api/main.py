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

# 2. استخراج الكلمات المفتاحية باستخدام SentenceTransformer
def extract_keywords(text, top_n=5):
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    
    # تقسيم النص إلى كلمات أو جمل قصيرة
    words = list(set(re.findall(r'\b\w{4,}\b', text.lower())))  # كلمات أطول من 3 حروف

    if not words:
        return []

    # الحصول على التمثيل الشعاعي للجمل والكلمات
    text_embedding = model.encode([text])
    word_embeddings = model.encode(words)

    # حساب التشابه بين النص والكلمات
    similarities = cosine_similarity(text_embedding, word_embeddings)[0]

    # ترتيب الكلمات حسب التشابه
    top_indices = similarities.argsort()[-top_n:][::-1]
    keywords = [words[i] for i in top_indices]

    return keywords

# CORS middleware (السماح للـ React بالاتصال)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # السماح بطلبات React
    allow_credentials=True,
    allow_methods=["*"],  # السماح بجميع أنواع الطلبات (GET, POST, DELETE...)
    allow_headers=["*"],  # السماح بجميع الرؤوس
)

@app.post("/upload-cv/")
async def upload_cv(file: UploadFile = File(...)):
    try:
        pdf_file = await file.read()
        text = extract_text_from_pdf(pdf_file)
        if text:
            keywords = extract_keywords(text)
            return JSONResponse(content={"keywords": keywords})
        else:
            return JSONResponse(content={"error": "No text found in the file."}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# تشغيل السيرفر
port = int(os.getenv("PORT", 8000))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
