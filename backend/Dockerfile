FROM python:3.10

WORKDIR /app

RUN APT_INSTALL="apt-get install -y --no-install-recommends --allow-unauthenticated" \
    && apt update \
    && DEBIAN_FRONTEND=noninteractive $APT_INSTALL \
    build-essential \
    libboost-all-dev \
    python3-dev \
    python3-tk \
    python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD exec gunicorn main:app --bind :8080 --workers 1 --timeout 180 --worker-class uvicorn.workers.UvicornWorker --threads 8