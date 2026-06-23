import time
from src.kai_tts.utils.logger import get_logger, setup_logging
from src.kai_tts.io.sender import Sender
from src.kai_tts.io.receiver import Receiver
from src.kai_tts.schemata.ipc import DataReceive, DataSend

setup_logging()
logger = get_logger(__name__)

def handle_incoming_data(data: DataReceive):
    """Callback function triggered when valid data arrives."""
    logger.info(f"Received valid token: '{data.text_token}' at TS: {data.timestamp}")

def main():
    logger.critical("Launching src.kai_tts module...")
    
    # Initialize networking nodes
    sender = Sender()
    receiver = Receiver()
    
    receiver.register_callback(handle_incoming_data)
    receiver.start()

    try:
        while True:
            # Simulate processing and pipeline sequencing
            payload = DataSend(
                timestamp=time.time(),
                audio_buffer=b'\x00\x01\x02' # Simulated audio byte chunk
            )
            sender.send_payload(payload)
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received.")
    finally:
        receiver.stop()
        sender.close()

if __name__ == "__main__":
    main()