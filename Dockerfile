FROM python:3.11-slim

WORKDIR /

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir torch==2.1.0 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir surya-ocr pdftext runpod

COPY handler.py /

ENV TORCH_DEVICE=cuda
ENV RECOGNITION_BATCH_SIZE=64
ENV DETECTOR_BATCH_SIZE=16

EXPOSE 8000

CMD ["python", "-u", "handler.py"]
