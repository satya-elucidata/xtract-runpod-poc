# Surya OCR on RunPod Serverless

Deploy [Surya OCR](https://github.com/datalab-to/surya) to RunPod Serverless.

## Features

- OCR in 90+ languages
- Layout analysis (detection, tables, reading order)
- PDF support (automatic image extraction)
- GPU-accelerated (L4, A10G, A100)
- Serverless auto-scaling

## Prerequisites

- [RunPod Account](https://runpod.io)
- Docker installed
- Python 3.10+

## Quick Start

### 1. Build Docker Image

```bash
# Build the image
./build.sh yourusername/surya-ocr:latest docker.io

# Or manually:
docker build --platform linux/amd64 -t yourusername/surya-ocr:latest .
```

### 2. Push to Registry

```bash
# Push to Docker Hub
docker push yourusername/surya-ocr:latest

# Or use GHCR (GitHub Container Registry)
docker build --platform linux/amd64 -t ghcr.io/yourusername/surya-ocr:latest .
docker push ghcr.io/yourusername/surya-ocr:latest
```

### 3. Deploy to RunPod

```bash
# Install dependencies
pip install requests

# Deploy (using your Docker image)
python deploy.py --docker-image docker.io/yourusername/surya-ocr:latest
```

That's it! The script will:
- Create a serverless template with L4 GPU
- Create an endpoint with 0-1 workers

## Configuration Options

| Flag | Description | Default |
|------|-------------|---------|
| `--docker-image` | Docker image URL (required) | - |
| `--template-name` | Template name | `surya-ocr-template` |
| `--endpoint-name` | Endpoint name | `surya-ocr-endpoint` |
| `--gpu-id` | GPU type | `L4` |
| `--workers-min` | Minimum workers | `0` |
| `--workers-max` | Maximum workers | `1` |
| `--location` | Data center | `US-OR-1` |

### GPU Options

- `L4` - 24GB VRAM, good balance (recommended)
- `A10G` - 24GB VRAM
- `A100` - 40GB VRAM
- `RTX4090` - 24GB VRAM

### Locations

- `US-OR-1` - Oregon
- `US-NJ-1` - New Jersey  
- `EU-RO-1` - Romania
- `CA-MTL-1` - Montreal

## API Usage

### OCR (Default)

```bash
curl -X POST https://your-endpoint.runpod.app/run \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "file_url": "https://example.com/document.pdf",
      "languages": ["en"],
      "task": "ocr"
    }
  }'
```

### Layout Analysis

```json
{
  "input": {
    "file_url": "https://example.com/document.pdf",
    "task": "layout"
  }
}
```

### Table Recognition

```json
{
  "input": {
    "file_url": "https://example.com/table.png",
    "task": "table"
  }
}
```

### Full Analysis (OCR + Layout + Tables)

```json
{
  "input": {
    "file_url": "https://example.com/document.pdf",
    "task": "full"
  }
}
```

### Base64 Image

```json
{
  "input": {
    "image_base64": "iVBORw0KGgo...",
    "languages": ["en"],
    "task": "ocr"
  }
}
```

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Test locally
python handler.py

# Or run API server locally
python handler.py --rp_serve_api
```

## Scaling Up

```bash
# Deploy with more workers
python deploy.py --docker-image your-image --workers-max 5
```

## Files

| File | Description |
|------|-------------|
| `handler.py` | RunPod serverless handler |
| `deploy.py` | Deploy to RunPod |
| `build.sh` | Build Docker image |
| `Dockerfile` | Container definition |
| `requirements.txt` | Python dependencies |
| `test_input.json` | Test request |
