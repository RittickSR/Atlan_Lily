# Atlan Lily HLD

## 1. Introduction

Atlan Lily is a metadata management platform intended for the handling of metadata ingests, processes, and propagates metadata in real-time. It should be capable of processing metadata from multiple sources, identifying and tracking the dependency of one data asset on another and propagating changes to the dependent systems in real time. The objective of this HLD is to outline a cloud-agnostic, scalable, and extensible architecture that supports:

- Fast receipt and processing of metadata in near real-time.
- Efficient storage and querying of metadata.
- Real-time distribution of the modifications to metadata.
- Multi-tenancy, security, and observability.

## 2. System Overview

The system architecture consists of several interconnected layers, each serving a distinct purpose in the metadata management lifecycle:

1. **Event Ingestion Layer**: Enables near real time metadata consumption from different sources with the help of FastAPI, Apache Kafka, and Kafka Connect.
2. **Metadata Processing and Transformation Layer**: Processes and transforms ingested metadata using Apache Flink, PyFlink, and Redis.
3. **Metadata Store**: Stores metadata entities in MongoDB while using Neo4j to handle relationships and dependencies between these entities.
4. **Event Streaming and Notification Layer**: Handles real-time broadcasting of metadata updates through Kafka Streams, FastAPI WebSockets, and Celery.
5. **Security Layer**: Ensures the access is secure and multi-tenancy through the implementation of OAuth2 and Role Based Access Control systems
6. **Observability Layer**: Uses Prometheus, Grafana, ELK Stack, and OpenTelemetry for monitoring, logging, and tracing operations
7. **Integration and API Layer**: Supports external integrations and provides APIs using FastAPI, GraphQL, and Webhooks.

## 3. Functional Requirements

The system must meet the following key functional requirements:

1. **Real-Time Metadata Ingestion**: Ingest metadata from various external and internal sources in near real-time.
2. **Metadata Processing and Transformation**: Process and transform ingested metadata for storage and downstream use.
3. **Efficient Metadata Storage**: Store metadata entities and manage relationships using suitable databases.
4. **Change Propagation**: Ensure that all downstream systems and processes are notified about any change in metadata.
5. **Secure Access Control**: Ensure secure access to metadata and enforce multi-tenancy.

## 4. Non-Functional Requirements

The system must adhere to the following non-functional requirements:

1. **Scalability**: Support horizontal scaling to handle high volumes of metadata ingestion and processing.
2. **Performance**: Ensure low-latency processing and real-time notification of metadata changes.
3. **Security**: Implement robust authentication and authorization system to protect metadata and ensure data privacy.
4. **Availability**: Maintain high availability, leveraging replicas and fail safe mechanisms.
5. **Extensibility**: Support easy integration with new data sources and downstream systems through modular components such as connectors and API endpoints.
6. **Observability**: Provide detailed monitoring, logging, and tracing to ensure platform reliability and help in debugging.

## 5. Design Constraints

The design must consider the following constraints:

1. **Technology Limitations**: The architecture must be cloud-agnostic.
2. **Regulatory Requirements**: Ensure compliance with data governance policies.
3. **Integration with Existing Systems**: The solution must integrate seamlessly with existing data tools and platforms used by customers (e.g., Monte Carlo).

## 6. System Architecture

The system architecture is composed of the following layers:

### **6.1. Event Ingestion Layer**

- **Components**: FastAPI (for HTTP and WebSockets), Apache Kafka, Kafka Connect, Load Balancer
- **Purpose**: This layer is responsible for receiving and handling metadata from various sources almost instantly, ensuring data flows smoothly into the system.
- **How It Works**:
    - **Webhook Ingestion**: The system receives notifications from external sources, like Monte Carlo, through webhooks. FastAPI checks the webhook's signature against a pre-shared secret to confirm that the request is authentic and trustworthy.
    - **HTTP Ingestion**: The system can also handle single, straightforward events sent via HTTP. FastAPI is designed to process these quickly, allowing the system to update its metadata as soon as new information arrives.
    - **WebSockets**: For scenarios requiring constant, low-latency communication, FastAPI uses WebSockets. This keeps a connection open, enabling continuous updates and ensuring real-time data ingestion and immediate notifications for connected clients.
    - **Kafka**: Once events are processed by FastAPI, they are published to Kafka topics. Kafka acts as a messaging system, organizing and preparing the data for further streaming and processing.
    - **Load Balancer**: Implement load balancing for FastAPI and scale horizontally.

### **6.2. Metadata Processing and Transformation Layer**

- **Components**: Apache Flink, PyFlink, Redis
- **Purpose**: This layer stream processes and transforms the ingested metadata, preparing it for storage and future use.
- **How It Works**:
    - **Flink**: Flink consumes metadata events from Kafka and performs necessary transformations and aggregations, in stream. It uses distributed data processing capabilities to handle large volumes of data efficiently and prepares this data for the next steps in the workflow.
    - **PyFlink**: PyFlink allows the use of Python within Flink jobs, providing more flexibility to perform complex transformations that might be required by specific use cases.
    - **Redis**: Enriched metadata is stored temporarily in Redis while flink job is running. This allows for fast access and caching, improving the efficiency of data retrieval during real-time processing and reducing response times.

### **6.3. Metadata Store**

- **Components**: MongoDB, Neo4j
- **Purpose**: This layer stores processed metadata in an organized manner, managing both individual data entities and their relationships.
- **How It Works**:
    - **MongoDB**: MongoDB is used to store metadata entities, such as databases, schemas, tables, columns, and dashboards. It provides a flexible NoSQL format that can accommodate various types of metadata.
    - **Neo4j**: Neo4j is utilized to store metadata entities as nodes and their relationships as edges. This graph database format is optimized for querying complex dependencies, which is useful for identifying upstream and downstream impact of change in any node.

### **6.4. Event Streaming and Notification Layer**

- **Components**: Python Kafka Client (Confluent Kafka), FastAPI WebSockets, Celery, Neo4j Python Driver
- **Purpose**: This layer ensures that changes in metadata are promptly communicated to downstream systems and components, enabling them to react in real time.
- **How It Works**:
    - **Python Kafka Client**: This client consumes metadata change events from Kafka topics. It identifies the type of change and initiates further processing based on this information.
    - **Neo4j Python Driver**: The system uses this driver to query the Neo4j database and understand the relationships and dependencies of affected metadata entities to help identify downstream processes and services.Based on the results from Neo4j, the system determines the necessary actions, such as notifying downstream systems, updating related metadata, or triggering workflows.
    - **FastAPI WebSockets**: Real-time notifications are sent to connected clients and systems about metadata changes through WebSocket messages and Kafka messages. This ensures that all monitoring tools and dashboards are updated immediately when changes occur.
    - **Celery**: Celery manages asynchronous tasks sending notifications or triggering additional data processing workflows in the background.

### **6.5. Security Layer**

- **Components**: FastAPI, OAuth2, OpenID Connect, JWT, Role-Based Access Control (RBAC)
- **Purpose**: This layer ensures secure access and enforces multi-tenancy within the system, managing user authentication and authorization.
- **How It Works**:
    - **FastAPI**: FastAPI handles user authentication and authorization directly. It supports OAuth2, OpenID Connect, and JWT (JSON Web Tokens) to manage secure user sessions and API access. FastAPI provides built-in dependencies to easily implement these security protocols, issuing tokens for authentication and managing user sessions.
    - **OAuth2 and OpenID Connect**: These protocols manage user authentication and authorization securely. They issue access tokens for API access, ensuring sensitive metadata is only accessible to authorized users.
    - **JWT (JSON Web Tokens)**: JWTs are used to encode user information and permissions securely, allowing the system to validate user identity and roles efficiently with each request.
    - **RBAC**: Role-Based Access Control is implemented within FastAPI to restrict access based on user roles and permissions, enforcing fine-grained access control policies. This limits user actions to only those necessary for their role within the system.

### **6.6. Observability Layer**

- **Components**: Prometheus, Grafana, ELK Stack (Elasticsearch, Logstash, Kibana)
- **Purpose**: This layer provides monitoring, logging, and tracing capabilities to maintain system reliability and performance.
- **How It Works**:
    - **Prometheus**: Prometheus collects and stores performance metrics from various system components. This data enables monitoring and alerts based on predefined thresholds, ensuring the system operates smoothly.
    - **Grafana**: Grafana visualizes metrics from Prometheus and other sources in real-time dashboards. It provides insights into system health and performance, making it easier to identify and address issues.
    - **ELK Stack**:
        - **Elasticsearch**: Indexes and stores log data from system components.
        - **Logstash**: Ingests, processes, and forwards log data to Elasticsearch for centralized logging.
        - **Kibana**: Offers a user interface for searching, analyzing, and visualizing log data stored in Elasticsearch, helping with troubleshooting and analysis.

### **6.7. Integration and API Layer**

- **Components**: FastAPI, GraphQL, Webhooks
- **Purpose**: This layer facilitates integration with external systems and provides APIs for extending the platform's capabilities.
- **How It Works**:
    - **FastAPI**: Exposes RESTful APIs for creating, reading, updating, and deleting metadata entities. These APIs allow external systems and users to interact with the platform.
    - **GraphQL**: GraphQL offers flexible querying capabilities for metadata analysis and generating useful insights.
    - **Webhooks**: The system uses webhooks for both receiving external notifications (such as from Monte Carlo) and sending HTTP callbacks to external systems when specific events occur. This supports seamless integration with third-party tools and services.

### **Architecture Diagram**

![architecture_diagram.png](Atlan%20Lily%20HLD%20diagrams/Architecture.png)

## 7. Data Flow

1. **Ingestion**: Metadata is ingested through FastAPI Webhooks or Websockets or HTTP calls and published to Kafka topics.
2. **Processing**: Flink jobs consume Kafka topics, transform data, and store it temporarily in Redis.
3. **Storage**: Once Flink jobs are complete, Celery jobs move the enriched metadata from Redis to MongoDB, and relationships are managed in Neo4j.
4. **Change Propagation**: Metadata changes trigger celery jobs, which publishes messages to Kafka. Neo4j queries used to determine, affected nodes and services which trigger appropriate Kafka events, notifying downstream systems via Kafka Streams and WebSockets.
5. **Security and Observability**: Security and observability layers interact with all other layers to ensure security and uptime of system.

### **Data Flow Diagram**

![Data flow diagram.png](Atlan%20Lily%20HLD%20diagrams/Dataflow.png)

## 8. Interface Design

**1. FastAPI Endpoints**

- **Type**: RESTful APIs
- **Purpose**: Provide endpoints for metadata ingestion, management, and processing. Enable external systems to perform CRUD operations on metadata.
- **Key Use Cases**: Ingest metadata from external tools, query metadata information, and update existing records.
1. **GraphQL Interface**
    - **Type**: GraphQL API
    - **Purpose**: Offer flexible querying capabilities for retrieving specific metadata views tailored to client needs.
    - **Key Use Cases**: Fetch specific metadata attributes and construct dynamic queries for customized data extraction.
2. **WebSocket Connections**
    - **Type**: WebSockets
    - **Purpose**: Enable real-time notifications and updates to downstream systems whenever metadata changes occur.
    - **Key Use Cases**: Provide immediate updates to connected clients and trigger real-time workflows based on metadata changes.

## 9. Database Design.

The database schema includes:

1. **MongoDB**:
    - **Collections**: Entities representing various metadata types such as tables, columns, dashboards, and reports. Each document contains a tenant_id to support multitenancy
    - **Relationships**: Managed externally via Neo4j or through embedded references where needed.
2. **Neo4j**:
    - **Nodes**: Represent metadata entities such as tables, columns, dashboards, etc. Each node contains a tenant_id.
    - **Edges**: Represent relationships like "uses", "transforms", or "depends on".
    - **Constraints**: Ensure data integrity and relationship consistency.

## 10. Security Considerations

The system implements the following security measures:

1. **Authentication**: Managed by Keycloak, supporting OAuth2 and OpenID Connect.
2. **Authorization**: Role-Based Access Control (RBAC) ensures fine-grained access control.
3. **Data Encryption**: All sensitive data is encrypted at rest and in transit.\
4. **Audit Logging**: All access and changes to metadata are logged for auditing purposes.

## 11. Testing Strategy

The testing strategy includes:

1. **Unit Testing**: For individual components and modules using tools like pytest.
2. **Integration Testing**: To verify interactions between components.
3. **End-to-End Testing**: To validate workflows from metadata ingestion to downstream propagation.
4. **Performance Testing**: To ensure the system meets performance requirements under load.
5. **Security Testing**: To identify and mitigate security vulnerabilities.

## 12. Deployment Strategy

The deployment strategy involves:

1. **Environment Setup**: Deploying the system on Kubernetes clusters for scalability and high availability.
2. **CI/CD Pipeline**: Automated deployment using Github Actions.
3. **Release Management**: Version-controlled releases with rollback capabilities.

## 13. Maintenance and Support

**Monitoring**: Continuous monitoring using Prometheus and Grafana to detect issues early.

**Logging**: Logging at various points and sources, accumulated in ELK to ensure ease in detection and debugging.

## 14. Use Cases

**Objective**: The Atlan platform must support near-real-time ingestion and consumption of metadata to meet the growing needs of customers who require rapid updates and immediate actionability for data observability, data security, and metadata management. The solution must be cloud-agnostic, scalable, secure, and capable of handling both inbound and outbound metadata flows.

### 14.1. Inbound Metadata Ingestion

**Use Case**:

1. **External Inbound**: A customer uses Monte Carlo for data observability to detect early issues with table health or data reliability. The customer wants Atlan to receive these alerts in near-real-time, attaching relevant metadata to the affected assets.
2. **Internal Inbound**: A prospect with a large metadata estate (spanning 1 billion assets) wants to ingest metadata into Atlan, prioritizing the most critical 10% of assets (databases, schemas, tables, and dashboards) with eventual consistency for the remaining 90% (columns and BI fields).

**Architecture Components**:

- **Event Ingestion Layer**: Utilizes FastAPI for HTTP and WebSocket-based ingestion of metadata from external sources such as Monte Carlo. This layer ensures the near-real-time ingestion of metadata alerts through Webhooks, facilitating immediate processing.
- **Metadata Processing and Transformation Layer**: Employs Apache Flink and PyFlink for stream processing, transforming ingested metadata events into a structured format suitable for storage. Redis is used for caching interim results to enhance processing efficiency.
- **Metadata Store**: MongoDB is used to store ingested metadata entities, while Neo4j manages the relationships and dependencies between these entities, crucial for understanding data lineage and impact.

**Workflow**:

1. **Inbound Event Reception**: FastAPI receives metadata ingestion events from Monte Carlo via Webhooks. These events are authenticated using pre-shared secrets to ensure the source’s integrity.
2. **Processing and Transformation**: Apache Flink consumes these events from Kafka topics, transforms them as needed, and stores them in Redis for quick access.
3. **Storage**: Transformed metadata is then moved to MongoDB for storage, and relationships are updated in Neo4j to maintain accurate metadata lineage.

**Scalability and Adaptability**:

- The architecture supports horizontal scaling by using load balancers and distributed processing with Apache Flink, allowing it to handle large volumes of metadata ingestion and processing.

### 14.2. Outbound Metadata Consumption

**Use Case**:

1. **Internal Outbound**: Internal enrichment automation requires that any change in the Atlan entity automatically triggers similar updates to entities downstream in the data lineage.
2. **External Outbound**: A customer requires immediate enforcement of data access security and compliance policies when an entity is marked as PII or GDPR-sensitive in Atlan. The downstream data tools should receive this information in real-time to enforce access control during SQL queries.

**Architecture Components**:

- **Event Streaming and Notification Layer**: Handles real-time broadcasting of metadata updates through Kafka Streams and FastAPI WebSockets. Celery is used for managing background tasks, such as sending notifications and triggering downstream updates.
- **Security Layer**: Implements OAuth2 and Role-Based Access Control (RBAC) to ensure secure access to metadata and enforce multi-tenancy, ensuring that sensitive data is only accessible to authorized users.

**Workflow**:

1. **Metadata Change Detection**: When a metadata change is detected in MongoDB or Neo4j (e.g., an entity marked as PII or GDPR), the Python Kafka client consumes this change event.
2. **Propagation and Notification**: The system uses Neo4j to identify all downstream entities affected by this change. Kafka Streams then broadcasts these updates to downstream systems, ensuring immediate enforcement of new data access policies.
3. **Security Enforcement**: Access control changes are applied in real-time using FastAPI WebSockets and RBAC, ensuring that only authorized users can access sensitive data.