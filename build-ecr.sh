#!/bin/bash
set -e

AWS_REGION="${1:-ap-southeast-1}"
ECR_REPO="${2:-surya-ocr}"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

# Full ECR image URL
ECR_IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}:latest"

echo "Building Docker image for ECR..."
echo "Image: ${ECR_IMAGE}"

# Build for linux/amd64 (required for GPU)
docker build --platform linux/amd64 -t surya-ocr:latest .

# Tag for ECR
docker tag surya-ocr:latest ${ECR_IMAGE}

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Push to ECR
docker push ${ECR_IMAGE}

echo ""
echo "Image pushed to ECR: ${ECR_IMAGE}"
echo ""
echo "To deploy to RunPod:"
echo "  python deploy.py --docker-image ${ECR_IMAGE}"
