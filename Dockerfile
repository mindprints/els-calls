FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY index.html .
COPY settings.json .
COPY audio ./audio

CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
