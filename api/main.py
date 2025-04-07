from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pdfplumber
from keybert import KeyBERT
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


# 1. تحميل ملف الـ PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    with pdfplumber.open(BytesIO(pdf_file)) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

# 2. استخراج الكلمات المفتاحية باستخدام KeyBERT
def extract_keywords(text):
    kw_model = KeyBERT()
    keywords = kw_model.extract_keywords(text, top_n=5)  # استخراج أعلى 5 كلمات مفتاحية
    return keywords

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # السماح بطلبات React
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
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="https://qassim8.github.io/upload-cv/")