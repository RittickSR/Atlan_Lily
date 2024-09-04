
# Prototype FastAPI Application

This is a prototype FastAPI application designed to demonstrate integration with various services like Kafka, MongoDB, Neo4j, and Redis. **Note:** This prototype contains hard-coded configurations and is intended for testing and development purposes only.

## Features

- **FastAPI**: A modern, fast (high-performance), web framework for building APIs with Python.
- **WebSocket**: Simulates WebSocket notifications.
- **Kafka**: Produces messages to Kafka topics.
- **MongoDB**: Stores and retrieves metadata entities.
- **Neo4j**: Manages metadata relationships and downstream nodes.
- **Redis**: Caches metadata for quick retrieval.

## Hardcoded Configurations

This application has several hardcoded elements for the sake of simplicity and demonstration, including:

- **Kafka Configuration**: Assumes Kafka is running at `kafka:9092`.
- **MongoDB Configuration**: Assumes MongoDB is running at `mongodb:27017`.
- **Neo4j Configuration**: Assumes Neo4j is running at `neo4j:7687` with default authentication (`neo4j`, `test`).
- **Redis Configuration**: Assumes Redis is running at `redis:6379`.
- **Downstream Nodes**: A list of downstream nodes (`DOWNSTREAM_NODES`) is hardcoded into the application.

## Prerequisites

- **Docker**: Ensure Docker is installed and running on your system.
- **Docker Compose**: Ensure Docker Compose is installed to manage multi-container Docker applications.

## Running the Application

To run the application using Docker Compose, follow these steps:

1. **Clone the Repository**: Clone this repository to your local machine.
   
2. **Navigate to the Project Directory**: Open a terminal and navigate to the directory containing the `docker-compose.yml` file.

3. **Build and Run the Application**: Use Docker Compose to build and run the application.

    ```bash
   docker-compose up --build
    ```
   This command will build the Docker images as specified in the `docker-compose.yml` file and start the application.

4. **Access the Application**: Once the containers are up and running, you can access the FastAPI application at [http://localhost:8000](http://localhost:8000).

## Endpoints

- **WebSocket Endpoint**: `/` — Connect to a webpage displaying all downstream notifications.
- **Metadata Ingestion**: `/ingest-metadata` — Endpoint to ingest metadata into MongoDB and propagate changes.
- **Service Health Checks**:
  - `/check-mongodb` — Checks the MongoDB connection.
  - `/check-neo4j` — Checks the Neo4j connection.
  - `/check-kafka` — Checks the Kafka connection.
  - `/check-redis` — Checks the Redis connection.

## Notes

- **Prototype Use Only**: This code is intended for prototyping and development purposes. It contains hard-coded elements and is not suitable for production use without significant modifications.
- **Data Persistence**: Be aware that the MongoDB, Redis, and Neo4j containers are configured for development purposes. Data stored in these services will not persist if the containers are removed.
- **No Celery**: No Celery is used since this is a protoype, actual implementaion architecture will be different.
