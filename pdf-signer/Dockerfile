FROM python:3.12-slim

WORKDIR /app

# Install system packages required for OCR and PDF image conversion.
# tesseract-ocr is used by pytesseract.
# poppler-utils is used by pdf2image.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY sign_pdf.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]