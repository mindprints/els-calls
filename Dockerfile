FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add cache-busting by including a timestamp
ARG CACHE_BUST=1
RUN echo "Cache bust: ${CACHE_BUST}"

# Copy application files
COPY app.py .
COPY index.html .
COPY index_wip.html .
COPY settings.json .
COPY audio ./audio

CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
