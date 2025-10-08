FROM mcr.microsoft.com/playwright/python:v1.50.0-noble

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
CMD ["sh", "-c", "python -m playwright install --with-deps chromium && uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
