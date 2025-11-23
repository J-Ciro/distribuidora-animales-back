FROM python:3.11-slim

WORKDIR /app

# Install build deps
RUN apt-get update && apt-get install -y gcc g++ gnupg2 unixodbc-dev && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
