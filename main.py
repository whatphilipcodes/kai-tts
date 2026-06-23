import time
from src.kai_tts.utils.logger import get_logger, setup_logging
from src.kai_tts.io.sender import Sender
from src.kai_tts.io.receiver import Receiver
from src.kai_tts.engine import TTSEngine
from src.kai_tts.processor import StreamProcessor

setup_logging()
logger = get_logger(__name__)

def main():
    logger.critical("Launching src.kai_tts module...")
    
    # Initialize networking nodes
    sender = Sender()
    receiver = Receiver()
    
    # Initialize engine and processor
    engine = TTSEngine()
    processor = StreamProcessor(receiver, sender, engine)
    
    # Start the components
    receiver.start()
    processor.start()

    try:
        logger.info("Ready. Press Ctrl+C to exit.")
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutdown signal received.")
    finally:
        processor.stop()
        receiver.stop()
        sender.close()

if __name__ == "__main__":
    main()