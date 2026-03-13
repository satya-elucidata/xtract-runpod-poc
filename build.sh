#!/bin/bash
set -e

IMAGE_NAME="${1:-surya-ocr:latest}"
REGISTRY="${2:-docker.io}"

echo "Building Docker image: $IMAGE_NAME"
echo "Registry: $REGISTRY"

FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}"

echo "Building for linux/amd64 platform..."
docker build --platform linux/amd64 -t "$FULL_IMAGE" .

echo ""
echo "Image built successfully: $FULL_IMAGE"
echo ""
echo "To push to Docker Hub:"
echo "  docker push $FULL_IMAGE"
echo ""
echo "Then deploy to RunPod:"
echo "  python deploy.py --docker-image $FULL_IMAGE"
