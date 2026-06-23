import threading
import queue
import time
import re
from typing import Optional

from src.kai_tts.io.receiver import Receiver
from src.kai_tts.io.sender import Sender
from src.kai_tts.engine import TTSEngine
from src.kai_tts.schemata.ipc import DataReceive, DataSend
from src.kai_tts.utils.logger import get_logger

logger = get_logger(__name__)

class StreamProcessor:
    def __init__(self, receiver: Receiver, sender: Sender, engine: TTSEngine):
        self.receiver = receiver
        self.sender = sender
        self.engine = engine
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        self.sentence_queue = queue.Queue()
        self.token_buffer = []
        
        self.receiver.register_callback(self.handle_incoming_data)
        
    def handle_incoming_data(self, data: DataReceive) -> None:
        token = data.text_token
        self.token_buffer.append(token)
        
        text_so_far = "".join(self.token_buffer)
        
        # Find all complete sentences
        while True:
            # Look for punctuation followed by space, newline, or end of string
            match = re.search(r'([.!?]+(?:\s+|\n|$))', text_so_far)
            if not match:
                break
                
            split_idx = match.end()
            sentence = text_so_far[:split_idx].strip()
            text_so_far = text_so_far[split_idx:]
            
            if sentence:
                logger.info(f"Detected sentence: '{sentence}'")
                self.sentence_queue.put(sentence)
                
        self.token_buffer = [text_so_far] if text_so_far else []

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        logger.info("StreamProcessor started.")
        
    def _process_loop(self):
        while self._running:
            try:
                sentence = self.sentence_queue.get(timeout=0.5)
            except queue.Empty:
                continue
                
            logger.info(f"Synthesizing sentence: '{sentence[:30]}...'")
            try:
                for chunk in self.engine.generate_audio(sentence):
                    if not self._running:
                        break
                    
                    payload = DataSend(
                        timestamp=time.time(),
                        audio_buffer=chunk
                    )
                    self.sender.send_payload(payload)
            except Exception as e:
                logger.error(f"Error during synthesis processing: {e}")
                
    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        logger.info("StreamProcessor stopped.")
