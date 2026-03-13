FROM pytorch/pytorch:2.1.2-cuda12.1-cudnn8-runtime

WORKDIR /

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

RUN uv pip install --system "numpy<2.0.0"

RUN uv pip install --system pillow==10.0.0 transformers==4.36.2 huggingface_hub

RUN uv pip install --system pdftext

RUN uv pip install --system surya-ocr==0.4.0

RUN uv pip install --system runpod

COPY handler.py /

ENV TORCH_DEVICE=cuda
ENV RECOGNITION_BATCH_SIZE=64
ENV DETECTOR_BATCH_SIZE=16

EXPOSE 8000

CMD ["python", "-u", "handler.py"]
