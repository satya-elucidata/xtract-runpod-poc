import io
import os
import time
import base64
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional

import runpod
import torch
from PIL import Image
from surya.ocr import run_ocr
from surya.model.detection.segformer import (
    load_model as load_det_model,
    load_processor as load_det_processor,
)
from surya.model.recognition.processor import load_processor as load_rec_processor
from surya.model.recognition.model import load_model as load_rec_model

MODEL_WARMED_UP = False
det_model = None
det_processor = None
rec_model = None
rec_processor = None


def load_models():
    global det_model, det_processor, rec_model, rec_processor, MODEL_WARMED_UP

    print("Loading Surya OCR models...")
    start = time.time()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    det_model = load_det_model()
    det_processor = load_det_processor()
    rec_model = load_rec_model()
    rec_processor = load_rec_processor()

    det_model = det_model.to(device)
    rec_model = rec_model.to(device)
    det_model.eval()
    rec_model.eval()

    print(f"Models loaded in {time.time() - start:.2f}s")
    MODEL_WARMED_UP = True


def download_file(url: str) -> Path:
    import urllib.request
    import urllib.error

    tmp_dir = Path(tempfile.mkdtemp())
    filename = url.split("/")[-1]
    filepath = tmp_dir / filename

    try:
        urllib.request.urlretrieve(url, filepath)
        return filepath
    except urllib.error.URLError as e:
        raise ValueError(f"Failed to download file from {url}: {str(e)}")


def load_image_from_base64(base64_str: str) -> Image.Image:
    image_data = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(image_data))


def load_input_files(input_data: Dict[str, Any]) -> List[Image.Image]:
    images = []

    file_url = input_data.get("file_url")
    base64_image = input_data.get("image_base64")

    if file_url:
        if file_url.lower().endswith(".pdf"):
            import pypdfium2

            filepath = download_file(file_url)
            pdf = pypdfium2.PdfDocument(filepath)
            for page_idx in range(len(pdf)):
                page = pdf[page_idx]
                pil_image = page.render(
                    scale=2.0,
                    rotation=0,
                ).to_pil()
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
                images.append(pil_image)
            pdf.close()
            filepath.unlink(missing_ok=True)
        else:
            filepath = download_file(file_url)
            img = Image.open(filepath)
            if img.mode != "RGB":
                img = img.convert("RGB")
            images.append(img)
            filepath.unlink(missing_ok=True)

    elif base64_image:
        img = load_image_from_base64(base64_image)
        if img.mode != "RGB":
            img = img.convert("RGB")
        images.append(img)

    if not images:
        raise ValueError("No valid input provided. Use file_url or image_base64.")

    return images


def process_ocr(images: List[Image.Image], languages: List[str]) -> Dict[str, Any]:
    if languages is None:
        languages = ["en"]

    langs = [languages] * len(images)

    ocr_results = run_ocr(
        images, langs, det_model, det_processor, rec_model, rec_processor
    )

    results = []
    for idx, result in enumerate(ocr_results):
        page_data = {"page": idx + 1, "text_lines": []}

        for line in result.text_lines:
            page_data["text_lines"].append(
                {
                    "text": line.text,
                    "confidence": line.confidence,
                }
            )

        results.append(page_data)

    return {"pages": results, "num_pages": len(results)}


def handler(event):
    global MODEL_WARMED_UP

    if not MODEL_WARMED_UP:
        load_models()

    input_data = event.get("input", {})

    languages = input_data.get("languages", ["en"])
    task = input_data.get("task", "ocr")

    print(f"Processing request: task={task}, languages={languages}")

    images = load_input_files(input_data)
    print(f"Loaded {len(images)} images/pages")

    start_time = time.time()

    result = process_ocr(images, languages)

    processing_time = time.time() - start_time
    print(f"Processing completed in {processing_time:.2f}s")

    result["processing_time_seconds"] = processing_time
    result["model_warmed_up"] = MODEL_WARMED_UP

    return result


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
