import requests
import json
import time
import logging
from datetime import datetime
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Constants
OLLAMA_URL = "http://localhost:11434"
REQUIRED_MODELS = ["qwen2.5-coder", "starcoder2"]
SAMPLE_PROMPTS = {
    "qwen2.5-coder": "Write a Python function to calculate the factorial of a number.",
    "starcoder2": "Explain the concept of recursion in programming."
}
RETRY_LIMIT = 3
RETRY_DELAY = 5  # seconds
# Function to check Ollama service availability
def check_service_availability():
    try:
        response = requests.get(OLLAMA_URL)
        if response.status_code == 200:
            logging.info("Ollama service is available.")
            return True
        else:
            logging.error(f"Failed to connect to Ollama service. Status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        logging.error(f"Request exception occurred while checking service availability: {e}")
        return False
# Function to validate required models
def validate_models():
    try:
        response = requests.get(f"{OLLAMA_URL}/models")
        if response.status_code == 200:
            installed_models = [model['name'] for model in response.json()]
            missing_models = set(REQUIRED_MODELS) - set(installed_models)
            if not missing_models:
                logging.info("All required models are installed.")
                return True
            else:
                logging.error(f"Missing models: {missing_models}")
                return False
        else:
            logging.error(f"Failed to fetch models. Status code: {response.status_code}")
            return False
    except requests.RequestException as e:
        logging.error(f"Request exception occurred while validating models: {e}")
        return False
# Function to test model inference with sample prompts
def test_model_inference():
    results = {}
    for model, prompt in SAMPLE_PROMPTS.items():
        start_time = time.time()
        try:
            response = requests.post(
                f"{OLLAMA_URL}/inference",
                json={"model": model, "prompt": prompt}
            )
            if response.status_code == 200:
                inference_result = response.json()
                success_rate = 1.0  # Assuming successful inference
                logging.info(f"Model {model} inference successful.")
            else:
                inference_result = None
                success_rate = 0.0
                logging.error(f"Failed to perform inference for model {model}. Status code: {response.status_code}")
        except requests.RequestException as e:
            inference_result = None
            success_rate = 0.0
            logging.error(f"Request exception occurred while performing inference for model {model}: {e}")
        end_time = time.time()
        response_time = end_time - start_time
        results[model] = {
            "response_time": response_time,
            "success_rate": success_rate,
            "inference_result": inference_result
        }
    return results
# Function to report health metrics
def report_health_metrics(results):
    overall_success_rate = sum(result['success_rate'] for result in results.values()) / len(results)
    logging.info(f"Overall Success Rate: {overall_success_rate:.2f}")
    health_report = {
        "timestamp": datetime.now().isoformat(),
        "service_available": check_service_availability(),
        "models_validated": validate_models(),
        "inference_results": results,
        "overall_success_rate": overall_success_rate
    }
    return health_report
# Function to exit with appropriate error codes for CI pipeline
def exit_with_error_code(health_report):
    if not health_report["service_available"]:
        logging.error("Exiting with error code 1: Ollama service is not available.")
        exit(1)
    elif not health_report["models_validated"]:
        logging.error("Exiting with error code 2: Required models are not installed.")
        exit(2)
    elif health_report["overall_success_rate"] < 0.5:
        logging.error("Exiting with error code 3: Inference success rate is below threshold.")
        exit(3)
    else:
        logging.info("All checks passed. Exiting with success code 0.")
        exit(0)
# Main function
def main():
    if not check_service_availability():
        exit_with_error_code({"service_available": False})
    if not validate_models():
        exit_with_error_code({"models_validated": False})
    retry_count = 0
    while retry_count < RETRY_LIMIT:
        results = test_model_inference()
        health_report = report_health_metrics(results)
        # Check for transient failures and retry if necessary
        if all(result['success_rate'] == 1.0 for result in results.values()):
            break
        logging.warning(f"Transient failure detected. Retrying ({retry_count + 1}/{RETRY_LIMIT})...")
        time.sleep(RETRY_DELAY)
        retry_count += 1
    # Output JSON for CI integration
    print(json.dumps(health_report, indent=4))
    exit_with_error_code(health_report)
if __name__ == "__main__":
    main()