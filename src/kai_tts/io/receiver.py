import threading
from typing import Callable, Optional
import zmq
from pydantic import ValidationError

from src.kai_tts.config import settings
from src.kai_tts.schemata.ipc import DataReceive
from src.kai_tts.utils.logger import get_logger

logger = get_logger(__name__)

class Receiver:
    def __init__(self, host: str = "localhost", port: int | None = None):
        """
        Initializes the ZeroMQ SUB socket and background listener.
        """
        self.context = zmq.Context.instance()
        self.socket = self.context.socket(zmq.SUB)
        
        self.socket.setsockopt(zmq.RCVHWM, 2)
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")

        target_port = port or settings.network.port_in
        protocol = settings.network.protocol.value
        self.connect_addr = f"{protocol}{host}:{target_port}"

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable[[DataReceive], None]] = None

        try:
            self.socket.connect(self.connect_addr)
            logger.info(f"Receiver connected to {self.connect_addr}")
        except zmq.ZMQError as e:
            logger.fatal(f"Failed to connect Receiver to {self.connect_addr}: {e}")
            raise

    def register_callback(self, callback: Callable[[DataReceive], None]) -> None:
        """Registers a function to handle incoming, validated payloads."""
        self._callback = callback

    def start(self) -> None:
        """Spawns the listening loop in a background daemon thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Receiver listening loop started.")

    def _listen_loop(self) -> None:
        """
        Polls the socket internally to allow for graceful thread termination 
        without blocking indefinitely on recv().
        """
        poller = zmq.Poller()
        poller.register(self.socket, zmq.POLLIN)

        while self._running:
            try:
                # Poll with a 500ms timeout
                socks = dict(poller.poll(500))
                
                if self.socket in socks and socks[self.socket] == zmq.POLLIN:
                    message_bytes = self.socket.recv()
                    self._process_message(message_bytes)
            except zmq.ContextTerminated:
                break
            except Exception as e:
                logger.error(f"Unexpected error in receiver loop: {e}")

    def _process_message(self, message_bytes: bytes) -> None:
        """Deserializes and validates bytes into a Pydantic model."""
        try:
            # Pydantic natively parses JSON bytes
            data = DataReceive.model_validate_json(message_bytes)
            if self._callback:
                self._callback(data)
        except ValidationError as e:
            logger.warning(f"Discarding malformed payload: validation failed.\n{e}")

    def stop(self) -> None:
        """Signals the loop to stop and cleans up resources."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        self.socket.close()
        logger.info("Receiver socket closed.")