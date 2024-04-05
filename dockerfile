FROM python:3.10-bullseye

RUN apt-get update -y && apt-get install -y portaudio19-dev python3-pyaudio sox pulseaudio libsox-fmt-all ffmpeg wget libpcre3 libpcre3-dev libatlas-base-dev python3-dev && \
    echo "==> Clean up..."  && \
    apt-get clean  && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /moss
COPY requirements.txt /moss
RUN pip install --no-cache-dir -r /moss/requirements.txt
COPY . /moss
CMD ["python", "app.py"]