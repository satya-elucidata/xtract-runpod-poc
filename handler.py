import io
import os
import time
import base64
import tempfile
from pathlib import Path
from typing import Union, List, Dict, Any, Optional

import runpod
import torch
from PIL import Image
from surya.detection import DetectionPredictor
from surya.recognition import RecognitionPredictor
from surya.layout import LayoutPredictor
from surya.table_rec import TableRecPredictor
from surya.foundation import FoundationPredictor
from surya.settings import settings

MODEL_WARMED_UP = False
detector = None
recognizer = None
layout_predictor = None
table_predictor = None


def load_models():
    """Load Surya OCR models into GPU memory."""
    global detector, recognizer, layout_predictor, table_predictor, MODEL_WARMED_UP

    print("Loading Surya OCR models...")
    start = time.time()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    foundation_predictor = FoundationPredictor()

    detector = DetectionPredictor(foundation_predictor)
    recognizer = RecognitionPredictor(foundation_predictor)
    layout_predictor = LayoutPredictor(foundation_predictor)
    table_predictor = TableRecPredictor(foundation_predictor)

    print(f"Models loaded in {time.time() - start:.2f}s")
    MODEL_WARMED_UP = True


def download_file(url: str) -> Path:
    """Download file from URL to temporary location."""
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
    """Load PIL Image from base64 encoded string."""
    image_data = base64.b64decode(base64_str)
    return Image.open(io.BytesIO(image_data))


def process_ocr(
    images: List[Image.Image], languages: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Run OCR on images and return results."""
    if languages is None:
        languages = ["en"]

    ocr_results = recognizer(images)

    results = []
    for idx, result in enumerate(ocr_results):
        page_data = {"page": idx + 1, "text_lines": []}

        for line in result.text_lines:
            page_data["text_lines"].append(
                {
                    "text": line.text,
                    "confidence": line.confidence,
                    "bbox": line.bbox if hasattr(line, "bbox") else None,
                    "polygon": line.polygon if hasattr(line, "polygon") else None,
                }
            )

        results.append(page_data)

    return {"pages": results, "num_pages": len(results)}


def process_layout(images: List[Image.Image]) -> Dict[str, Any]:
    """Run layout analysis on images."""
    layout_results = layout_predictor(images)

    results = []
    for idx, result in enumerate(layout_results):
        page_data = {"page": idx + 1, "elements": []}

        for bbox_data in result.bboxes:
            page_data["elements"].append(
                {
                    "bbox": bbox_data.bbox,
                    "polygon": bbox_data.polygon,
                    "label": bbox_data.label,
                    "position": bbox_data.position,
                }
            )

        results.append(page_data)

    return {"pages": results, "num_pages": len(results)}


def process_table(images: List[Image.Image]) -> Dict[str, Any]:
    """Run table recognition on images."""
    table_results = table_predictor(images)

    results = []
    for idx, result in enumerate(table_results):
        page_data = {"page": idx + 1, "tables": []}

        for table_idx, table in enumerate(result.tables):
            table_data = {
                "table_idx": table_idx,
                "rows": table.rows,
                "cols": table.cols,
                "cells": table.cells,
            }
            page_data["tables"].append(table_data)

        results.append(page_data)

    return {"pages": results, "num_pages": len(results)}


def load_input_files(input_data: Dict[str, Any]) -> List[Image.Image]:
    """Load images from various input formats."""
    images = []

    file_url = input_data.get("file_url")
    base64_image = input_data.get("image_base64")
    pdf_path = input_data.get("pdf_path")

    if file_url:
        if file_url.lower().endswith(".pdf"):
            import pdftext

            filepath = download_file(file_url)
            pdf_images = pdftext.pdf_to_images(filepath, dpi=150)
            images.extend(pdf_images)
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

    elif pdf_path:
        import pdftext

        pdf_images = pdftext.pdf_to_images(pdf_path, dpi=150)
        images.extend(pdf_images)

    if not images:
        raise ValueError(
            "No valid input provided. Use file_url, image_base64, or pdf_path."
        )

    return images


def handler(event):
    """
    RunPod serverless handler for Surya OCR.

    Expected input format:
    {
        "input": {
            "file_url": "https://example.com/document.pdf",  // URL to image or PDF
            "languages": ["en", "hi"],  // Optional: languages to detect
            "task": "ocr"  // Optional: ocr, layout, table, or full
        }
    }

    Or for base64 image:
    {
        "input": {
            "image_base64": "<base64_encoded_image>",
            "languages": ["en"],
            "task": "ocr"
        }
    }
    """
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

    if task == "layout":
        result = process_layout(images)
    elif task == "table":
        result = process_table(images)
    elif task == "full":
        ocr_result = process_ocr(images, languages)
        layout_result = process_layout(images)
        table_result = process_table(images)
        result = {
            "ocr": ocr_result,
            "layout": layout_result,
            "tables": table_result,
        }
    else:
        result = process_ocr(images, languages)

    processing_time = time.time() - start_time
    print(f"Processing completed in {processing_time:.2f}s")

    result["processing_time_seconds"] = processing_time
    result["model_warmed_up"] = MODEL_WARMED_UP

    return result


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
