from flask import Flask, request
import requests
import concurrent.futures
import logging
import os

from kubernetes import client, config

expose_port=os.environ.get("EXPOSE_PORT", 8080)
app_selector=os.environ.get("APP_SELECTOR", "app=nginx-test")

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_destination_pods():
    config.load_incluster_config()

    api_client = client.ApiClient()

    namespace = open("/var/run/secrets/kubernetes.io/serviceaccount/namespace").read()

    label_selector = app_selector

    logger.debug("Looking for pods with label selector: %s", label_selector)

    v1 = client.CoreV1Api(api_client)

    pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)

    replica_urls = []
    for pod in pods.items:
        logger.debug("Current Pod IP: %s", pod.status.pod_ip)
        pod_ip = pod.status.pod_ip
        replica_urls.append(f"http://{pod_ip}:80")

    logger.debug("Replica URLs: %s", replica_urls)
    return replica_urls

def send_request(url, method, headers, data):
    try:
        response = requests.request(method, url, headers=headers, data=data, verify=False)
        logger.debug("Response: %s", response)
        return response.text, response.status_code, response.headers.items()
    except Exception as e:
        logger.error(f"Failed to send request to {url}: {str(e)}")
        return '', 500, []

def process_requests(urls, method, headers, data, path):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(send_request, f"{url}/{path}", method, headers, data)
            for url in urls
        ]
        for future in concurrent.futures.as_completed(futures):
            try:
                response = future.result()
                return response  # Return the first response received
            except Exception as e:
                logger.error(f"Error occurred while processing request: {str(e)}")

@app.route('/', methods=['GET', 'POST', 'PUT', 'DELETE'])
def root_gateway():
    path = '/'
    return gateway(path)

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def gateway(path):
    method = request.method
    headers = request.headers
    data = request.data

    logger.debug("Received request: %s %s", method, request.url)

    replica_urls = get_destination_pods()
    response = process_requests(replica_urls, method, headers, data, path)

    logger.debug("Response: %s", response)

    return response[0], response[1], dict(response[2])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=expose_port)