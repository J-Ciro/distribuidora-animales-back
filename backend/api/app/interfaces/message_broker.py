"""
Message Broker Protocol - Interface for message queue abstraction
Allows switching between RabbitMQ, Kafka, SQS without changing business logic
"""
from typing import Dict, Any, Protocol


class MessageBroker(Protocol):
    """Protocol (interface) for message broker implementations"""
    
    def connect(self) -> None:
        """Establish connection to message broker"""
        ...
    
    def publish(self, queue_name: str, message: Dict[str, Any], durable: bool = True) -> None:
        """
        Publish message to queue
        
        Args:
            queue_name: Name of the queue
            message: Message payload (will be JSON serialized)
            durable: Whether the message should persist on disk
        """
        ...
    
    def close(self) -> None:
        """Close connection to message broker"""
        ...
