# Atlan Lily LLD

# 1. Introduction

Atlan Lily is a metadata management platform designed to handle metadata ingestion, processing, and notification in real-time. The platform is cloud-agnostic, scalable, and extensible, supporting efficient storage, querying, and distribution of metadata. It ensures multi-tenancy, security, and observability.

# 2. System Architecture

## 2.1 High-Level Architecture

The system architecture is divided into several interconnected layers, each serving a distinct purpose in the metadata management lifecycle:

- **Event Ingestion Layer:** Responsible for receiving metadata from various sources and ensuring it is processed in near real-time. Utilizes FastAPI for handling HTTP , Webhooks and WebSocket requests and Apache Kafka for messaging.
- **Metadata Processing and Transformation Layer:** Handles the processing and transformation of ingested metadata. Uses Apache Flink with PyFlink for stream processing and Redis for temporary data storage during transformations.
- **Metadata Store:** Stores processed metadata entities and their relationships. MongoDB is used for storing metadata entities, while Neo4j is used for managing relationships between these entities since it is a graph DB.
- **Event Streaming and Notification Layer:** Manages near real-time notification of metadata updates. This layer uses Kafka for event streaming, FastAPI WebSockets for real-time notifications, and Celery for managing asynchronous tasks such as identifying updates and selecting proper websockets and topics.
- **Security Layer:** Ensures secure access to the system using OAuth2 for authentication and Role-Based Access Control (RBAC) for authorization. It also supports multi-tenancy to ensure data segregation.
- **Observability Layer:** Provides monitoring, logging, and tracing capabilities to maintain system reliability and performance. This layer leverages Prometheus and Grafana for monitoring, ELK Stack (Elasticsearch, Logstash, Kibana) for logging, and OpenTelemetry for tracing.
- **Integration and API Layer:** Supports external integrations and provides APIs for extending the platform’s capabilities. FastAPI is used for RESTful APIs, GraphQL for flexible querying, and Webhooks for event-driven interactions such as Slack, etc.

## 2.2 Components

- **FastAPI:** A fast web framework for building APIs with Python. It handles HTTP requests for metadata ingestion, handles Webhooks and provides WebSocket connections for real-time data updates.
- **Apache Kafka:** A distributed streaming platform used to publish and subscribe to streams of records, store them, and process them. Kafka is used for reliable, high-throughput messaging.
- **Apache Flink & PyFlink:** Flink is a stream processing framework that can handle both batch and real-time data. PyFlink allows the use of Python to write Flink jobs, which are responsible for transforming metadata streams.
- **Redis:** An in-memory data store used as a temporary cache to store intermediate metadata states, which result in lesser latency when fetching cached data.
- **MongoDB:** A NoSQL database used for storing metadata entities. It supports flexible schema designs, making it suitable for storing diverse types of metadata.
- **Neo4j:** A graph database used to store and manage relationships between metadata entities. It provides optimized queries for understanding complex dependencies among data assets.
- **Celery:** An asynchronous task queue that is based on distributed message passing. It is used for handling background async tasks such as sending notifications or performing additional data processing.
- **Prometheus & Grafana:** Prometheus is an open-source monitoring system with visualizations through Grafana. Grafana is used to create dashboards and visualize metrics collected by Prometheus.
- **ELK Stack (Elasticsearch, Logstash, Kibana):** A set of tools used for searching, analyzing, and visualizing log data. Elasticsearch is used for storing logs, Logstash for processing logs, and Kibana for visualizing log data.
- **OAuth2 & RBAC:** OAuth2 is an open standard for access delegation, used for token-based authentication and authorization. RBAC is a method of regulating access based on the roles of individual users within an organization.

## 2.3 Technologies Used

- **Programming Languages:** Python (for FastAPI, PyFlink, Celery)
- **Frameworks:** FastAPI (for API development), Apache Flink and PyFlink (for stream processing)
- **Databases:** MongoDB (for metadata storage), Neo4j (for managing metadata relationships), Redis (for caching)
- **Messaging Systems:** Apache Kafka (for event streaming and messaging)
- **Monitoring and Logging Tools:** Prometheus and Grafana (for monitoring and visualization), ELK Stack (for centralized logging)
- **Security Protocols:** OAuth2, JWT (for authentication and authorization)
- **Containerization and Orchestration:** Docker (for containerization), Kubernetes (for orchestration)

# 3. Detailed Design

## 3.1 Data Model

### MongoDB Schema

- **Entities Collection:** This collection stores metadata entities such as databases, schemas, tables, columns, dashboards, etc. Each document in the collection has the following structure:
    - `entity_id`: Unique identifier for the metadata entity.
    - `entity_type`: Type of the metadata entity (e.g., table, column, dashboard).
    - `attributes`: A JSON object containing various attributes of the entity (e.g., name, type, description).
    - `tenant_id`: Identifier for the tenant to support multi-tenancy.
    - `created_at`: Timestamp indicating when the entity was created.
    - `updated_at`: Timestamp indicating the last update to the entity.
- **Relationships:** Relationships between entities are managed externally in Neo4j.

### Neo4j Schema

- **Nodes:** Represents metadata entities. Each node contains properties such as:
    - `node_id`: Unique identifier for the node.
    - `node_type`: Type of metadata entity (e.g., table, column, dashboard).
    - `properties`: JSON object containing various properties of the entity.
    - `tenant_id`: Identifier for the tenant.
- **Edges:** Represents relationships between nodes. Edges have properties like:
    - `relationship_type`: Type of relationship (e.g., “uses”, “depends on”).
    - `source_node_id`: The `node_id` of the source entity.
    - `target_node_id`: The `node_id` of the target entity.
    - `created_at`: Timestamp indicating when the relationship was established.

This kind of Neo4j schema, will help us identify any services, dashboards or data stores downstream that depend on an upstream metadata source, thereby allowing us to assess the impact of metadata change in near real-time without complex queries or configurations.

## 3.2 API Design

### RESTful API Endpoints (FastAPI)

1. **POST /ingest-metadata**
    - **Description:** Ingests metadata from external sources into the system.
    - **Request Body:**
        
        ```json
        {  "entity_type": "string",  // Type of metadata entity (e.g., table, column)  "attributes": {           // Detailed attributes of the metadata entity    "name": "string",       // Name of the entity    "description": "string",// Description of the entity    "created_by": "string", // Identifier of the user or system that created the entity    "tags": ["string"]      // List of tags associated with the entity  },  "tenant_id": "string"     // Identifier for multi-tenancy}
        ```
        
    - **Response:**
        
        ```json
        {  "status": "success",  "metadata_id": "string"   // Unique identifier of the newly created metadata entity}
        ```
        
    - **Error Responses:**
        - `400 Bad Request`: Invalid input data or missing required fields.
        - `401 Unauthorized`: Authentication failed or token missing.
        - `500 Internal Server Error`: An unexpected error occurred on the server.
2. **GET /metadata/{id}**
    - **Description:** Retrieves metadata details by the specified ID.
    - **Path Parameter:**
        - `id`: Unique identifier of the metadata entity to retrieve.
    - **Response:**
        
        ```json
        {  "metadata_id": "string",  "entity_type": "string",  "attributes": {    "name": "string",    "description": "string",    "created_by": "string",    "tags": ["string"]  },  "tenant_id": "string",  "created_at": "datetime", // Timestamp of when the entity was created  "updated_at": "datetime"  // Timestamp of when the entity was last updated}
        ```
        
    - **Error Responses:**
        - `404 Not Found`: Metadata entity not found.
        - `401 Unauthorized`: Authentication failed or token missing.
        - `500 Internal Server Error`: An unexpected error occurred on the server.
3. **PUT /metadata/{id}**
    - **Description:** Updates an existing metadata entity by the specified ID.
    - **Path Parameter:**
        - `id`: Unique identifier of the metadata entity to update.
    - **Request Body:**
        
        ```json
        {  "attributes": {           // Updated attributes for the metadata entity    "name": "string",    "description": "string",    "tags": ["string"]  }}
        ```
        
    - **Response:**
        
        ```json
        {  "status": "success",  "metadata_id": "string"}
        ```
        
    - **Error Responses:**
        - `400 Bad Request`: Invalid input data or missing required fields.
        - `404 Not Found`: Metadata entity not found.
        - `401 Unauthorized`: Authentication failed or token missing.
        - `500 Internal Server Error`: An unexpected error occurred on the server.
4. **DELETE /metadata/{id}**
    - **Description:** Deletes a metadata entity by the specified ID.
    - **Path Parameter:**
        - `id`: Unique identifier of the metadata entity to delete.
    - **Response:**
        
        ```json
        {  "status": "success",  "metadata_id": "string"}
        ```
        
    - **Error Responses:**
        - `404 Not Found`: Metadata entity not found.
        - `401 Unauthorized`: Authentication failed or token missing.
        - `500 Internal Server Error`: An unexpected error occurred on the server.
5. **POST /webhook/monte-carlo**
    - **Description:** Endpoint to receive webhook notifications from Monte Carlo.
    - **Headers:**
        - `x-mcd-signature`: Signature generated by Monte Carlo for verifying the authenticity of the request.
    - **Request Body:** JSON payload sent by Monte Carlo. Example for a rule breach:
        
        ```json
        {  "account": {    "id": "9a59c6f1-203a-4c72-8cd7-132db7f21b92"  },  "action": "incident",  "payload": {    "event_list": [      {        "data": {          "hits": [            {              "field": null,              "measurement_timestamp": "Jan 15, 06:10PM",              "timestamp": "",              "value": "50.0",              "value_rounded": "50"            }          ],          "metric_display_name": "custom_metric_1234",          "rule_comparisons": [            {              "metric": "custom_metric_1234",              "operator": ">",              "threshold": "49.0"            }          ]        },        "rule": {          "comparisons": [            {              "field": null,              "full_table_id": null,              "metric": "custom_metric_1234",              "operator": "GT",              "threshold": 49.0,              "warehouse_uuid": "custom_metric_1234"            }          ],          "creator_id": null,          "description": "test rule",          "execution_time": null,          "prev_execution_time": null,          "rule_type": "custom_sql",          "start_time": null,          "timezone": null,          "uuid": "0c8e06aa-a44b-4f2d-8a37-5ed3f394431d"        },        "table_name": null      }    ],    "group_id": null,    "incident_id": "f83867b6-8f25-428b-807c-08518f63384c",    "url": "https://getmontecarlo.com/incidents/f83867b6-8f25-428b-807c-08518f63384c"  },  "type": "open_custom_rule_anomaly_incident",  "version": "v0.1"}
        ```
        
    - **Response:**
        - `200 OK`: Webhook received and processed successfully.
        - `403 Forbidden`: Signature verification failed.
        - `500 Internal Server Error`: An unexpected error occurred on the server.

### GraphQL API

- **Query:**
    - **Description:** Provides a flexible interface for querying metadata attributes and relationships.
    - **Supported Operations:** Allows filtering, sorting, and pagination to refine query results.
    - **Example Query:**
        
        ```graphql
        query {
          metadata(entity_type: "table", filter: {tag: "finance"}, sort: "created_at", order: "desc") {
            metadata_id
            entity_type
            attributes {
              name
              description
            }
            created_at
          }
        }
        ```
        
- **Mutation:**
    - **Description:** Allows creating, updating, and deleting metadata entities via GraphQL mutations.
    - **Supported Operations:** Supports creating new entities, updating existing ones, and deleting entities.
    - **Example Mutation:**
        
        ```graphql
        mutation {
          createMetadata(entity_type: "table", attributes: {name: "New Table", description: "Description of new table"}) {
            metadata_id
            status
          }
        }
        ```
        

### WebSocket Endpoints (FastAPI)

- **/ws/notifications:**
    - **Description:** Provides a real-time notification mechanism for clients to receive updates on metadata changes.
    - **Usage:** Clients can subscribe to this endpoint to receive live updates whenever metadata changes occur.
    - **Message Format:**
        
        ```json
        {  "type": "update",  "metadata_id": "string",  "entity_type": "string",  "change": "created/updated/deleted",  "timestamp": "datetime"}
        ```
        

### 

## 3.3 User Interface Design

- **Notification Panel:**
    - **Description:** Displays real-time updates and alerts based on metadata changes.
    - **Features:**
        - Shows a stream of recent changes to metadata.
        - Provides alerts for critical updates or issues.
        - Allows users to acknowledge and manage notifications.

# 4. Implementation Details

## 4.1 Core Algorithms

- **Metadata Ingestion Algorithm:**
    - **Description:** Handles the ingestion of metadata from external sources.
    - **Steps:**
        1. Receive HTTP requests or Webhook or WebSocket messages containing metadata.
        2. Validate the authenticity and integrity of the metadata.
        3. Push metadata events to Kafka for further processing.
- **Metadata Processing Algorithm:**
    - **Description:** Processes and transforms ingested metadata in real-time.
    - **Steps:**
        1. Flink jobs consume metadata events from Kafka topics.
        2. Apply necessary transformations and aggregations to the metadata.
        3. Store intermediate results in Redis for fast access.
        4. Once processing is complete, move enriched metadata from Redis to MongoDB for storage via a Celery task.
- **Change Propagation Algorithm:**
    - **Description:** Manages the propagation of metadata changes to downstream systems.
    - **Steps:**
        1. Detect changes in metadata stored in MongoDB or Neo4j.
        2. Celery tasks query Neo4j to identify affected entities and their relationships.
        3. Generate Kafka events to notify downstream systems of changes.
        4. Use WebSocket connections to send real-time notifications to subscribed clients.

## 4.2 Integration Points

- **External Data Sources:**
    - **Description:** Ingests metadata from various external systems and data sources.
    - **Integration Methods:** HTTP endpoints, webhooks, direct database connections.
    - **Supported Formats:** JSON, XML, CSV, XLSX.
- **Downstream Systems:**
    - **Description:** Sends real-time updates and notifications to connected systems and services.
    - **Integration Methods:** Kafka Streams, WebSocket connections, RESTful APIs.
    - **Use Cases:** Notifying subsequent services, data stores and user facing applications

# 5. Performance Considerations

Since all our major components, such as API Server, Messaging Service, Stream processor and Data Stores are separated, each one can be scaled independently as per requirements.

- **Caching:**
    - **Description:** Uses Redis for temporary storage of intermediate metadata states to reduce load on MongoDB and improve response times.
    - **Implementation:** Redis is configured to cache intermediate processing results.
- **Horizontal Scaling:**
    - **Description:** Scales FastAPI, Kafka, and Flink components horizontally to handle increased metadata volume and traffic.
    - **Implementation:** A cloud native solution can be used to handle auto scaling depending on load, else Kubernetes can be configured to handle this.
- **Load Balancing:**
    - **Description:** Distributes incoming traffic evenly across multiple FastAPI instances to ensure high availability and reliability.
    - **Implementation:** A load balancer is set up, to distribute HTTP Requests, Webhooks and Web sockets across multiple FastAPI instances to further reduce load.

# 6. Security Measures

- **Authentication:**
    - **Description:** Manages user authentication using OAuth2 and OpenID Connect protocols, issuing JWT tokens for secure session management.
    - **Implementation:** FastAPI has built in support for OAuth2 and JWT, helping implementation be seamless with our servers.
- **Authorization:**
    - **Description:** Role based access control via OAuth2 helps us prevent unauthorized data access
    - **Implementation:** Implemented via OAuth2’s authorization system alongwith a store of Role based policies that are implemented via FastAPI server validating tokens and ensuring roles.
- **Data Encryption:**
    - **Description:** Ensure sensitive data is encrypted to help privacy and security.
    - **Implementation:** MongoDB and Neo4j are configured to encrypt data at rest. Further data can be encrypted when entering the pipeline and decrypted on exit.

# 7. Testing Strategy

- **Unit Testing:**
    - **Description:** Tests individual components and modules to ensure each works as expected in isolation.
    - **Tools Used:** pytest
    - **Coverage:** Core algorithms, API endpoints, data processing logic.
- **Integration Testing:**
    - **Description:** Verifies interactions between different components and services to ensure they work together seamlessly.
    - **Tools Used:** pytest, Postman, Docker Compose.
    - **Coverage:** API integration with databases, Kafka integration with processing layers.
- **End-to-End Testing:**
    - **Description:** Tests the complete workflow from metadata ingestion to change propagation to ensure the entire system functions as intended.
    - **Tools Used:** pytest, Docker Compose.
    - **Coverage:** User interface workflows, real-time notifications, data ingestion and processing.
- **Performance Testing:**
    - **Description:** Assesses system performance under load to ensure it meets performance requirements and scales appropriately.
    - **Tools Used:** Apache JMeter
    - **Metrics Monitored:** Response times, throughput, error rates, resource utilization.
- **Security Testing:**
    - **Description:** Identifies and mitigates security vulnerabilities through comprehensive testing.
    - **Tools Used:** OWASP ZAP
    - **Tests Conducted:** Pen-testing, vulnerability scanning.

# 8. Deployment Plan

- **Environment Setup:**
    - **Description:** Sets up the necessary environment for deploying Atlan Lily, including all required services and dependencies such as Kafka brokers, Mongo DB, etc.
    - **Implementation:** Use Kubernetes for deploying the system on clusters for scalability and high availability.
    - **Steps:**
        1. Set up Kubernetes clusters.
        2. Use cloud services to handle Flink, Kafka, Redis, Mongo and Neo4j
        3. Deploy FastAPI applications and configure load balancers.
        4. Configure monitoring tools.
- **CI/CD Pipeline:**
    - **Description:** Automates the deployment process to ensure continuous integration and delivery.
    - **Implementation:** Uses GitHub Actions to automate the build, test, and deployment process.
    - **Steps:**
        1. Code changes are pushed to the GitHub repository.
        2. Pull Requests to main trigger test suite.
        3. Merge to main triggers Action.
        4. GitHub Actions triggers the CI/CD pipeline.
        5. The pipeline builds and tests the application.
        6. If tests pass, the application is deployed to the Kubernetes cluster.
- **Configuration Management:**
    - **Description:** Manage configurations and secrets across different environments.
    - **Implementation:** Uses tools like Helm to automate configuration management.
    - **Steps:**
        1. Define configurations in Helm charts.
        2. Deploy configurations to Kubernetes clusters.

# 9. Maintenance and Support

- **Monitoring:**
    - **Description:** Continuous monitoring to help with proactive alerts and high usage alerts.
    - **Implementation:** Prometheus is used to collect metrics, and Grafana is used to visualize these metrics in dashboards at near real-time.
- **Logging:**
    - **Description:** Centralized logging to help debug and troubleshoot.
    - **Implementation:** Logs are collected using Logstash and stored in Elasticsearch. Kibana is used for searching and visualizing log data.
- **Support Procedures:**
    - **Description:** Extensive monitoring and alerting as described raises alerts on any issues
    - **Implementation:**
        - Alerts are raised via Grafana dashboard, or via the ELK stack.
        - Logs are used to identify and debug the problem.