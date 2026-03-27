FROM python:3.11-slim

WORKDIR /app

# Install system deps for lxml and psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
EXPOSE 8000

# Use python main.py so PORT is read from env by pydantic-settings (no shell expansion needed)
CMD ["python", "main.py"]
