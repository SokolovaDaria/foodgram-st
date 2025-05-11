
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libjpeg-dev \
    zlib1g-dev \

    && apt-get clean && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh


COPY . .

EXPOSE 8000


ENTRYPOINT ["/entrypoint.sh"]