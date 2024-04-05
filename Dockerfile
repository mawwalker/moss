FROM python:3.11-bullseye

RUN apt-get update -y && apt-get install -y portaudio19-dev python3-pyaudio sox pulseaudio libsox-fmt-all ffmpeg wget libpcre3 libpcre3-dev libatlas-base-dev python3-dev build-essential libssl-dev ca-certificates libasound2 && \
    echo "==> Clean up..."  && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /moss
COPY requirements.txt /moss
RUN pip install --no-cache-dir -U pip && pip install --no-cache-dir -r /moss/requirements.txt
COPY . /moss
CMD ["python", "app.py"]