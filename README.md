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

## How to Run
1. Build the Docker image:
   ```bash
   docker build -t customer-service .
