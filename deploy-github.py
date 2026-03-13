import requests
import os
import sys

RUNPOD_API_KEY = os.environ.get("RUNPOD_API_KEY", "")
BASE_URL = "https://api.runpod.io/graphql"


def run_query(query, variables=None):
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(BASE_URL, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"API request failed: {response.text}")

    result = response.json()
    if "errors" in result:
        raise Exception(f"GraphQL errors: {result['errors']}")

    return result.get("data", {})


def create_template_from_github(
    name, github_repo, github_branch, dockerfile_path, env_vars
):
    """Create a serverless template that builds from GitHub."""
    query = """
    mutation createServerlessTemplate($input: CreateServerlessTemplateInput!) {
        createServerlessTemplate(input: $input) {
            id
            name
            imageName
        }
    }
    """

    env_list = [{"key": k, "value": v} for k, v in env_vars.items()]

    variables = {
        "input": {
            "name": name,
            "githubRepo": github_repo,
            "githubBranch": github_branch,
            "dockerfilePath": dockerfile_path,
            "env": env_list,
            "ports": "8000/http",
            "isServerless": True,
            "isPublic": False,
            "containerDiskInGb": 10,
            "volumeInGb": 0,
        }
    }

    data = run_query(query, variables)
    return data.get("createServerlessTemplate", {})


def create_endpoint(
    template_id, name, gpu_id, workers_min, workers_max, location, idle_timeout=300
):
    query = """
    mutation createEndpoint($input: CreateEndpointInput!) {
        createEndpoint(input: $input) {
            id
            name
            url
        }
    }
    """

    variables = {
        "input": {
            "templateId": template_id,
            "name": name,
            "gpuIds": gpu_id,
            "workersMin": workers_min,
            "workersMax": workers_max,
            "idleTimeout": idle_timeout,
            "locations": location,
        }
    }

    data = run_query(query, variables)
    return data.get("createEndpoint", {})


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Deploy Surya OCR to RunPod Serverless"
    )
    parser.add_argument(
        "--github-repo", required=True, help="GitHub repo (e.g., user/repo)"
    )
    parser.add_argument("--github-branch", default="main", help="GitHub branch")
    parser.add_argument(
        "--template-name", default="surya-ocr-template", help="Template name"
    )
    parser.add_argument(
        "--endpoint-name", default="surya-ocr-endpoint", help="Endpoint name"
    )
    parser.add_argument("--gpu-id", default="L4", help="GPU type")
    parser.add_argument("--workers-min", type=int, default=0, help="Min workers")
    parser.add_argument("--workers-max", type=int, default=1, help="Max workers")
    parser.add_argument("--location", default="US-OR-1", help="Data center")

    args = parser.parse_args()

    env_vars = {
        "TORCH_DEVICE": "cuda",
        "RECOGNITION_BATCH_SIZE": "64",
        "DETECTOR_BATCH_SIZE": "16",
        "COMPILE_ALL": "true",
    }

    print(f"Creating template from GitHub: {args.github_repo}")

    template = create_template_from_github(
        name=args.template_name,
        github_repo=args.github_repo,
        github_branch=args.github_branch,
        dockerfile_path="Dockerfile",
        env_vars=env_vars,
    )

    print(f"Template created: {template.get('id')}")
    print(
        "Note: Image build may take 10-15 minutes. Check RunPod console for build status."
    )

    print(f"\nCreating endpoint: {args.endpoint_name}")
    endpoint = create_endpoint(
        template_id=template["id"],
        name=args.endpoint_name,
        gpu_id=args.gpu_id,
        workers_min=args.workers_min,
        workers_max=args.workers_max,
        location=args.location,
    )

    print(f"\nDeployment complete!")
    print(f"Endpoint ID: {endpoint.get('id')}")
    print(f"Endpoint URL: {endpoint.get('url')}")


if __name__ == "__main__":
    main()
