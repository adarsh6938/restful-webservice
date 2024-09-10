# Customer Service API

## Overview
This is a customer management REST API built using Python's FastAPI framework. The project implements CRUD operations, logging, telemetry, tracing, and authentication. 

## Features
- **Basic Authentication** using HTTP Basic Auth
- **Metrics** exposed for Prometheus at `/metrics`
- **Distributed Tracing** via OpenTelemetry and Jaeger
- **Structured Logging** using JSON format
- **Swagger** API documentation available at `/docs`
- **Redoc** API documentation available at `/redoc`

## Prerequisites:

- **Kubernetes**: Ensure that you have a running Kubernetes cluster.
- **Python**: Install Python 3.x on your local machine.
- **Docker**: Docker is required to build images and work with Kubernetes.
- **PostgreSQL**: The application uses PostgreSQL, which is deployed in Kubernetes.

# Private Docker Registry Setup, Customer API Deployment and postgres v17 database deployment in Kubernetes

This guide will help you deploy a private Docker registry on Kubernetes and build, tag, and push the Customer API app and PostgreSQL 17rc1 images to the registry. After that, you will deploy both to Kubernetes using the private registry.

## Step 1: Set Up the Private Docker Registry

To set up the private Docker registry, follow the steps provided in [this guide](https://www.paulsblog.dev/how-to-install-a-private-docker-container-registry-in-kubernetes/#install-docker-registry-using-helm). After completing the setup, continue with the following instructions.

### Kubernetes Files for Docker Registry Deployment

1. **Persistence Volume**: To create the persistence volume, use the `pv.yaml` file.

    ```bash
    kubectl apply -f k8s/pv.yaml
    ```

2. **Persistence Volume Claim**: To claim the persistence volume, use the `pvc.yaml` file.

    ```bash
    kubectl apply -f k8s/pvc.yaml
    ```

3. **Docker Registry Deployment**: To deploy the private Docker registry, use the `registry-deployment.yaml` file.

    ```bash
    kubectl apply -f k8s/registry-deployment.yaml
    ```

4. **Docker Registry Service**: To expose the private Docker registry, use the `registry-service.yaml` file.

    ```bash
    kubectl apply -f k8s/registry-service.yaml
    ```

After successfully deploying the private Docker registry, it will be available at `http://localhost:32000/` (as per the service configuration). The Docker registry is now exposed on port `32000`.

## Step 2: Build and Push Docker Images to the Private Registry

### 1. **Build and Push the Customer API App Docker Image**

Navigate to the project root, where the `Dockerfile` for the Customer API is located, and follow these steps:

1. **Build the Docker Image**:

    ```bash
    docker build -t customer-service-api:latest .
    ```

2. **Tag the Docker Image** for the private registry:

    ```bash
    docker tag customer-service-api:latest localhost:32000/customer-service-api:latest
    ```

3. **Push the Docker Image** to the private registry:

    ```bash
    docker push localhost:32000/customer-service-api:latest
    ```

### 2. **Push PostgreSQL 17rc1 Image to the Private Registry**

1. **Pull the PostgreSQL 17rc1 Image**:

    ```bash
    docker pull postgres:17rc1
    ```

2. **Tag the PostgreSQL Image** for the private registry:

    ```bash
    docker tag postgres:17rc1 localhost:32000/postgres:17rc1
    ```

3. **Push the PostgreSQL Image** to the private registry:

    ```bash
    docker push localhost:32000/postgres:17rc1
    ```

## Step 3: Deploy Customer API and PostgreSQL on Kubernetes

Once both images are pushed to the private Docker registry, you can deploy them in Kubernetes using your Kubernetes YAML files (e.g., `app-deployment.yaml`, `app-service.yaml`, and `postgres-deployment-service.yaml`). Ensure that the image references in the deployment YAML files point to `localhost:32000/customer-service-api:latest` and `localhost:32000/postgres:17rc1`.
    
   ```bash
    kubectl apply -f <deployment or service>.yaml -n <namespace>
  ```

# Setting Up Prometheus in Docker to Monitor Customer API Metrics

This guide explains how to download and run Prometheus using Docker, with the necessary configuration to monitor metrics from the Customer API, which is sending metrics at `http://localhost:32001/metrics`.

## Step 1: Download the Prometheus Docker Image

You can download the official Prometheus Docker image using the following command:

```bash
docker pull prom/prometheus
```

This command will pull the latest Prometheus image from Docker Hub.

## Step 2: Prometheus Configuration

To configure Prometheus to scrape metrics from the Customer API, you will use the provided `config/prometheus.yml` file. Ensure the file includes the necessary scrape configuration for the Customer API.

Here is an example `prometheus.yml` configuration:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'customer-api'
    static_configs:
      - targets: ['localhost:32001']
```

The `scrape_configs` section instructs Prometheus to scrape metrics from the Customer API at `http://localhost:32001/metrics`.

## Step 3: Running Prometheus in Docker

Run Prometheus in Docker using the following command, which will mount the `config/prometheus.yml` configuration file and expose the Prometheus UI on port 9090:

```bash
docker run --name prometheus -p 9090:9090 -v $(pwd)/config/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus
```

- **`--name prometheus`**: This names the container "prometheus".
- **`-p 9090:9090`**: This exposes port 9090, which allows you to access the Prometheus dashboard via `http://localhost:9090`.
- **`-v $(pwd)/config/prometheus.yml:/etc/prometheus/prometheus.yml`**: This mounts your local `prometheus.yml` configuration file to the container's Prometheus configuration directory.

## Step 4: Access the Prometheus Dashboard

Once Prometheus is running in Docker, you can access the Prometheus dashboard by navigating to:

```
http://localhost:9090
```

The dashboard will display metrics scraped from the Customer API, which is sending metrics at `http://localhost:32001/metrics`.

---

Follow these steps to successfully download, configure, and run Prometheus in Docker, and access the dashboard to monitor your Customer API metrics.


# Setting Up Jaeger in Docker to Scrape Traces

This guide explains how to download and run Jaeger using Docker, with the necessary configuration to scrape traces from the Customer API.

## Step 1: Download the Jaeger Docker Image

You can download the official Jaeger Docker image using the following command:

```bash
docker pull jaegertracing/all-in-one:latest
```

This command will pull the latest Jaeger image from Docker Hub.

## Step 2: Running Jaeger in Docker

To run Jaeger in Docker, use the following command, which will expose the Jaeger UI on port 16686, as well as the collector and query services:

```bash
docker run --name jaeger   -e COLLECTOR_ZIPKIN_HTTP_PORT=9411   -p 5775:5775/udp   -p 6831:6831/udp   -p 6832:6832/udp   -p 5778:5778   -p 16686:16686   -p 14268:14268   -p 14250:14250   -p 9411:9411   jaegertracing/all-in-one:latest
```

Explanation of the ports:
- **5775/udp**: For the `agent` service.
- **6831/udp, 6832/udp**: For receiving traces.
- **16686**: This exposes the Jaeger UI for accessing the traces.
- **14268, 14250**: For Jaeger's internal collectors and services.
- **9411**: For Jaeger to expose the Zipkin collector, useful for applications sending Zipkin traces.

## Step 3: Customer API Configuration to Send Traces to Jaeger

Ensure your Customer API is configured to send traces to Jaeger at the appropriate port (commonly 6831 for the UDP protocol). The traces will be sent from the Customer API to Jaeger running in Docker.

Example of configuring Jaeger in your application:

```yaml
JAEGER_SERVICE_NAME: customer-api
JAEGER_AGENT_HOST: localhost
JAEGER_AGENT_PORT: 6831
```

This setup will allow the Customer API to send traces to Jaeger running on `localhost`.

## Step 4: Access the Jaeger Dashboard

Once Jaeger is running in Docker, you can access the Jaeger dashboard by navigating to:

```
http://localhost:16686
```

From the dashboard, you can explore the traces collected from the Customer API.

---

Follow these steps to successfully download, configure, and run Jaeger in Docker, and access the dashboard to monitor your Customer API traces.



## Running Tests Locally

### Step 1: Ensure PostgreSQL in Kubernetes is Accessible

Before running the tests, you need to ensure that the PostgreSQL service running inside Kubernetes is accessible from your local machine. You can do this by port-forwarding the PostgreSQL service:

```bash
kubectl port-forward svc/postgres 5432:5432 -n docker-registry
```

In the above command, replace the `docker-registry` with the namespace where your PostgreSQL service is running. If you're unsure of the namespace or service name, run:

```bash
kubectl get svc -n <namespace>
```

### Step 2: Set Up the Python Environment

- Install all required dependencies by running:

  ```bash
  pip install -r requirements.txt
  ```

- Ensure you're in the root directory of the project (`restful-webservice`) when running the tests.

- If you encounter issues with the `app` module not being found, set the `PYTHONPATH` environment variable to the root of your project:

  **Linux/MacOS**:

  ```bash
  export PYTHONPATH=.
  ```

  **Windows**:

  ```bash
  set PYTHONPATH=.
  ```

### Step 3: Run the Tests

Once the environment is set up and PostgreSQL is accessible, you can run the tests using `pytest`.

To run all tests:

```bash
pytest
```

To run a specific test (for example, `test_read_customer_by_email` in the `test_customers.py` file):

```bash
pytest -v tests/test_customers.py::test_read_customer_by_email -p no:warnings
```

The `-v` flag enables verbose mode, and `-p no:warnings` suppresses warning messages in the test output.