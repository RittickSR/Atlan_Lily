from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from kafka import KafkaProducer, KafkaAdminClient
from pymongo import MongoClient
from neo4j import GraphDatabase
import redis
import json
import asyncio

# Initialize FastAPI app
app = FastAPI()

# Initialize Kafka producer and admin client
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',  # Kafka server address
    value_serializer=lambda v: json.dumps(v).encode('utf-8')  # Serialize Python dicts to JSON before sending to Kafka
)
kafka_admin = KafkaAdminClient(bootstrap_servers='kafka:9092')  # Kafka admin client for connection testing

# MongoDB client
mongo_client = MongoClient('mongodb://mongodb:27017/')  # Connect to MongoDB server
mongo_db = mongo_client["metadata_db"]  # Access database 'metadata_db'
metadata_collection = mongo_db["entities"]  # Access collection 'entities' in the 'metadata_db' database

# Neo4j driver
neo4j_driver = GraphDatabase.driver("bolt://neo4j:7687", auth=("neo4j", "test"))  # Connect to Neo4j server

# Redis client
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)  # Connect to Redis server

# Hardcoded downstream nodes
DOWNSTREAM_NODES = [
    {"id": "kafka_node", "type": "kafka", "topic": "downstream_topic"},
    {"id": "websocket_node", "type": "websocket", "url": "ws://localhost:8000/ws/notifications"}
]

# Store active WebSocket connections
active_websockets = {}

class MetadataEntity(BaseModel):
    entity_type: str
    attributes: dict
    tenant_id: str

# WebSocket endpoint to simulate WebSocket notifications
@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_id = id(websocket)  # Unique ID for the WebSocket client
    active_websockets[client_id] = websocket  # Add WebSocket to active connections
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received WebSocket message from client {client_id}: {data}")
    except WebSocketDisconnect:
        print(f"WebSocket client {client_id} disconnected")
        active_websockets.pop(client_id, None)  # Remove WebSocket from active connections

@app.get("/", response_class=HTMLResponse)
async def get():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>WebSocket Viewer</title>
    </head>
    <body>
        <h1>WebSocket Viewer</h1>
        <div id="messages"></div>
        <script>
            const ws = new WebSocket('ws://localhost:8000/ws/notifications');

            ws.onopen = () => {
                console.log('Connected to WebSocket');
            };

            ws.onmessage = (event) => {
                const messagesDiv = document.getElementById('messages');
                const message = document.createElement('p');
                message.textContent = `Received: ${event.data}`;
                messagesDiv.appendChild(message);
            };

            ws.onclose = () => {
                console.log('WebSocket connection closed');
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/ingest-metadata")
def ingest_metadata(metadata: MetadataEntity):
    try:
        # Check if metadata already exists
        existing_metadata = metadata_collection.find_one({"attributes.name": metadata.attributes["name"]})

        if existing_metadata:
            # Update existing metadata
            metadata_collection.update_one({"_id": existing_metadata["_id"]}, {"$set": metadata.dict()})
            metadata_id = str(existing_metadata["_id"])
            is_new_entry = False
        else:
            # Insert new metadata
            metadata_id = str(metadata_collection.insert_one(metadata.dict()).inserted_id)
            is_new_entry = True

        # Update Neo4j relationships only if it's a new metadata entry
        if is_new_entry:
            with neo4j_driver.session() as session:
                session.write_transaction(create_metadata_and_connect_downstream, metadata_id, metadata.dict(), DOWNSTREAM_NODES)

        # Cache metadata in Redis
        redis_client.set(metadata_id, json.dumps(metadata.dict()))

        # Identify downstream actions for propagation
        downstream_actions = []
        with neo4j_driver.session() as session:
            downstream_actions = session.read_transaction(find_downstream_actions, metadata_id)
        print(f"Downstream actions: {downstream_actions}")

        # Propagate changes based on downstream actions
        for action in downstream_actions:
            if action["type"] == "kafka":
                # Produce Kafka message
                producer.send(action["topic"], {'metadata_id': metadata_id, 'impact': 'update', **metadata.dict()})
            elif action["type"] == "websocket":
                # Send WebSocket notification
                asyncio.run(send_websocket_notification(action["url"], {'metadata_id': metadata_id, 'impact': 'update', **metadata.dict()}))

        return {"status": "success", "metadata_id": metadata_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def create_metadata_and_connect_downstream(tx, metadata_id, metadata, downstream_nodes):
    # Create or update the metadata node
    query = """
    MERGE (m:Metadata {id: $id})
    SET m.entity_type = $entity_type, m.attributes = $attributes, m.tenant_id = $tenant_id
    """
    tx.run(query, id=metadata_id, entity_type=metadata['entity_type'], attributes=json.dumps(metadata['attributes']), tenant_id=metadata['tenant_id'])

    # Connect downstream nodes
    for downstream in downstream_nodes:
        if downstream["type"] == "kafka":
            downstream_query = """
            MERGE (d:KafkaNode {id: $downstream_id, topic: $topic})
            MERGE (m:Metadata {id: $id})-[:IMPACTS]->(d)
            """
            tx.run(downstream_query, downstream_id=downstream["id"], topic=downstream["topic"], id=metadata_id)
        elif downstream["type"] == "websocket":
            downstream_query = """
            MERGE (d:WebSocketNode {id: $downstream_id, url: $url})
            MERGE (m:Metadata {id: $id})-[:IMPACTS]->(d)
            """
            tx.run(downstream_query, downstream_id=downstream["id"], url=downstream["url"], id=metadata_id)

def find_downstream_actions(tx, metadata_id):
    query = """
    MATCH (m:Metadata {id: $id})-[:IMPACTS]->(d)
    RETURN d.id as id, labels(d)[0] as type, d.topic as topic, d.url as url
    """
    result = tx.run(query, id=metadata_id)
    actions = []
    for record in result:
        if record["type"] == "KafkaNode":
            actions.append({"type": "kafka", "topic": record["topic"]})
        elif record["type"] == "WebSocketNode":
            actions.append({"type": "websocket", "url": record["url"]})
    return actions

async def send_websocket_notification(url, message):
    # If the WebSocket URL matches our local testing endpoint, send message to all connected clients
    if url == "ws://localhost:8000/ws/notifications":
        for client_id, websocket in active_websockets.items():
            await websocket.send_text(json.dumps(message))
    else:
        # Handle other WebSocket URLs if needed
        pass

# Connection check endpoints

@app.get("/check-mongodb")
def check_mongodb():
    try:
        # List MongoDB databases to check connection
        mongo_client.admin.command('ping')
        return {"status": "success", "message": "Connected to MongoDB"}
    except Exception as e:
        return {"status": "failure", "message": str(e)}

@app.get("/check-neo4j")
def check_neo4j():
    try:
        # Run a simple query to test Neo4j connection
        with neo4j_driver.session() as session:
            result = session.run("RETURN 1")
            result.single()
        return {"status": "success", "message": "Connected to Neo4j"}
    except Exception as e:
        return {"status": "failure", "message": str(e)}

@app.get("/check-kafka")
def check_kafka():
    try:
        # Check Kafka by listing topics (requires KafkaAdminClient)
        kafka_admin.list_topics()
        return {"status": "success", "message": "Connected to Kafka"}
    except Exception as e:
        return {"status": "failure", "message": str(e)}

@app.get("/check-redis")
def check_redis():
    try:
        # Ping Redis to check connection
        redis_client.ping()
        return {"status": "success", "message": "Connected to Redis"}
    except Exception as e:
        return {"status": "failure", "message": str(e)}
