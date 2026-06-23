from typing import Iterator
from pathlib import Path
from voxcpm import VoxCPM

from src.kai_tts.config import settings
from src.kai_tts.utils.logger import get_logger

logger = get_logger(__name__)

class TTSEngine:
    def __init__(self):
        logger.info(f"Initializing VoxCPM engine with model {settings.tts.model_name}")
        try:
            self.model = VoxCPM.from_pretrained(
                settings.tts.model_name,
                load_denoiser=True,
            )
        except Exception as e:
            logger.fatal(f"Failed to load VoxCPM model: {e}")
            raise
        
        # Resolve reference path against project root
        project_root = Path(__file__).resolve().parent.parent.parent
        ref_path = project_root / settings.tts.reference_wav_path
        
        if not ref_path.exists():
            logger.warning(f"Reference WAV file not found at {ref_path}")
            
        self.reference_wav_path = str(ref_path)
        self.reference_text = settings.tts.reference_text
        self.sample_rate = self.model.tts_model.sample_rate
        logger.info(f"VoxCPM engine initialized. Sample rate: {self.sample_rate}")

    def generate_audio(self, text: str) -> Iterator[bytes]:
        """
        Generates audio for a given text and yields chunks of raw bytes.
        """
        logger.debug(f"Generating audio for text: {text[:50]}...")
        try:
            for chunk in self.model.generate_streaming(
                text=text,
                prompt_wav_path=self.reference_wav_path,
                prompt_text=self.reference_text,
                reference_wav_path=self.reference_wav_path,
            ):
                yield chunk.tobytes()
        except Exception as e:
            logger.error(f"Error during TTS generation: {e}")
