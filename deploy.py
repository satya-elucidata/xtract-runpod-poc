import requests
import os
import sys

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
REST_URL = "https://rest.runpod.io/v1"


def create_template(name, image_name, env_vars, ports="8000/http"):
    """Create a serverless template using REST API."""
    url = f"{REST_URL}/templates"

    env_dict = {k: v for k, v in env_vars.items()}

    payload = {
        "name": name,
        "imageName": image_name,
        "env": env_dict,
        "ports": [ports],
        "isServerless": True,
        "isPublic": False,
        "containerDiskInGb": 10,
    }

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200 and response.status_code != 201:
        raise Exception(f"API request failed: {response.text}")

    return response.json()


def create_endpoint(template_id, name):
    """Create a serverless endpoint using REST API."""
    url = f"{REST_URL}/endpoints"

    payload = {
        "name": name,
        "templateId": template_id,
    }

    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200 and response.status_code != 201:
        raise Exception(f"API request failed: {response.text}")

    return response.json()


def main():
    import argparse
    import time

    parser = argparse.ArgumentParser(
        description="Deploy Surya OCR to RunPod Serverless"
    )
    parser.add_argument("--docker-image", required=True, help="Docker image URL")
    parser.add_argument(
        "--template-name",
        default=f"surya-ocr-template-{int(time.time())}",
        help="Template name",
    )
    parser.add_argument(
        "--endpoint-name", default="surya-ocr-endpoint", help="Endpoint name"
    )

    args = parser.parse_args()

    env_vars = {
        "TORCH_DEVICE": "cuda",
        "RECOGNITION_BATCH_SIZE": "64",
        "DETECTOR_BATCH_SIZE": "16",
    }

    print(f"Creating template: {args.template_name}")
    print(f"Using Docker image: {args.docker_image}")

    template = create_template(
        name=args.template_name,
        image_name=args.docker_image,
        env_vars=env_vars,
    )

    print(f"Template created: {template.get('id')}")

    print(f"\nCreating endpoint: {args.endpoint_name}")
    endpoint = create_endpoint(
        template_id=template["id"],
        name=args.endpoint_name,
    )

    print(f"\nDeployment complete!")
    print(f"Endpoint ID: {endpoint.get('id')}")
    print(f"Endpoint URL: https://api.runpod.ai/v2/{endpoint.get('id')}/run")

    print("\nTest your endpoint:")
    print(
        f'curl -X POST https://api.runpod.ai/v2/{endpoint.get("id")}/run -H "Authorization: Bearer {RUNPOD_API_KEY}" -H "Content-Type: application/json" -d \'{{"input": {{"file_url": "https://example.com/document.pdf", "languages": ["en"], "task": "ocr"}}}}\''
    )


if __name__ == "__main__":
    main()
