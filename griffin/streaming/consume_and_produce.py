import json
import logging
from kafka import KafkaConsumer, KafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]
SOURCE_TOPIC = "source.public.source"
TARGET_TOPIC = "source"

def create_consumer():
    """Create a Kafka consumer."""
    return KafkaConsumer(
        SOURCE_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        group_id="python-consumer",
        value_deserializer=lambda x: json.loads(x.decode("utf-8"))
    )

def create_producer():
    """Create a Kafka producer."""
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda x: json.dumps(x).encode("utf-8"),
            api_version=(0, 10, 2)
        )
    except Exception as e:
        logger.error(f"Error creating Kafka producer: {e}")
        raise

def process_message(message):
    """Process a Debezium message and extract relevant data."""
    try:
        logger.debug(f"Received message: {message}")
        if not isinstance(message, dict):
            logger.error(f"Invalid message format (not a dict): {message}")
            return None
        
        # Check operation type directly at root level
        if message.get("op") in ["c", "u"]:  # Create or Update
            after = message.get("after")
            if not after:
                logger.error(f"No 'after' field in message: {message}")
                return None
            return {
                "id": after["id"],
                "user_id": after["user_id"],
                "user_verified": after["user_verified"],
                "username": after["username"],
                "url": after["url"],
                "published_on": after["published_on"],
                "text": after["text"],
                "image_count": after["image_count"],
                "video_count": after["video_count"],
                "has_audio": after["has_audio"]
            }
        logger.debug(f"Message skipped (operation {message.get('op')} not processed)")
        return None
    except KeyError as e:
        logger.error(f"KeyError processing message: {e}, message: {message}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing message: {e}, message: {message}")
        return None

def main():
    """Main function to consume Debezium messages and send to target topic."""
    try:
        # Initialize consumer and producer
        consumer = create_consumer()
        producer = create_producer()
        
        logger.info(f"Starting to listen to source topic: {SOURCE_TOPIC}")
        logger.info(f"Will send processed messages to target topic: {TARGET_TOPIC}")
        
        # Continuously poll for new messages
        for message in consumer:
            try:
                # Check if message value exists
                if message.value is None:
                    logger.warning("Received empty message")
                    continue
                    
                # Process the Debezium message
                processed_data = process_message(message.value)
                
                if processed_data:
                    # Log the processed message
                    logger.info(f"Processing message with id: {processed_data['id']}")
                    
                    # Send processed data to the target topic
                    producer.send(
                        TARGET_TOPIC,
                        value=processed_data
                    )
                    
                    # Flush to ensure message is sent
                    producer.flush()
                    
                    logger.info(f"Successfully sent message with id: {processed_data['id']} to {TARGET_TOPIC}")
                else:
                    logger.debug("Message skipped (delete operation or no relevant data)")
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}")
        raise
        
    finally:
        # Clean up resources
        if 'consumer' in locals():
            consumer.close()
        if 'producer' in locals():
            producer.close()

if __name__ == "__main__":
    main()
    

if __name__ == "__main__":
    main()
