from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
from io import BytesIO
import collections
import re
import os

app = FastAPI()

# السماح بالتواصل مع الواجهة (مثلاً React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# استخراج النص من PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(BytesIO(pdf_file)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    return text

# استخراج كلمات مفتاحية يدوياً (أكثر الكلمات تكراراً بعد تنظيف النص)
def extract_keywords(text):
    words = re.findall(r'\b\w{4,}\b', text.lower())  # كلمات بطول 4 أحرف أو أكثر
    common_words = ["with", "from", "this", "that", "have", "your", "which", "will", "about", "other"]
    filtered = [word for word in words if word not in common_words]
    counter = collections.Counter(filtered)
    most_common = counter.most_common(5)
    return [word for word, _ in most_common]

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

# لتشغيل السيرفر على Render أو محليًا
port = int(os.getenv("PORT", 8000))
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
