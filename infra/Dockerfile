FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./backend/requirements.txt .


RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


COPY ./backend/ /app/backend/

