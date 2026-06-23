import zmq
from pydantic import ValidationError

from src.kai_tts.config import settings
from src.kai_tts.schemata.ipc import DataSend
from src.kai_tts.utils.logger import get_logger

logger = get_logger(__name__)

class Sender:
    def __init__(self, host: str = "*", port: int | None = None):
        """
        Initializes the ZeroMQ PUB socket for broadcasting data.
        """
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.PUB)
        
        # Aggressively drop old frames to prevent buffer bloat
        self.socket.setsockopt(zmq.SNDHWM, 2)

        target_port = port or settings.network.port_out
        protocol = settings.network.protocol.value
        self.bind_addr = f"{protocol}{host}:{target_port}"

        try:
            self.socket.bind(self.bind_addr)
            logger.info(f"Sender bound and ready on {self.bind_addr}")
        except zmq.ZMQError as e:
            logger.fatal(f"Failed to bind Sender to {self.bind_addr}: {e}")
            raise

    def send_payload(self, data: DataSend) -> None:
        """
        Serializes a Pydantic model to JSON bytes and transmits it via ZMQ.
        """
        try:
            # Serialize the validated Pydantic model to raw bytes
            payload_bytes = data.model_dump_json().encode('utf-8')
            self.socket.send(payload_bytes)
            logger.debug(f"Transmitted payload: {len(payload_bytes)} bytes")
        except ValidationError as e:
            logger.error(f"Failed to validate outgoing payload: {e}")
        except zmq.ZMQError as e:
            logger.error(f"ZMQ transmission error: {e}")

    def close(self) -> None:
        """Safely terminates the socket."""
        self.socket.close()
        logger.info("Sender socket closed.")