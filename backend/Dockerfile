FROM python:3.12-slim

WORKDIR /app

# System deps for numpy/scipy/torch/pymupdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Data dir will be mounted as volume
RUN mkdir -p /app/data/taric

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
