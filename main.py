import os

os.environ["TORCH_COMPILE_DISABLE"] = "1"
os.environ["TORCHINDUCTOR_MAX_AUTOTUNE"] = "0"
os.environ["TORCHINDUCTOR_COMPILE_THREADS"] = "1"

import asyncio
import json
import queue
import threading
from pathlib import Path

import numpy as np
import torch
import torch._dynamo
import uvloop
from kai_shared.io.node import PipelineNode
from kai_shared.schemata.ipc import AudioStreamMetadata, TokenStreamMetadata
from kai_shared.utils.logger import get_logger, setup_logging
from pydantic import ValidationError
from voxcpm import VoxCPM

from src.kai_tts.config_tts import settings_tts

torch._dynamo.config.disable = True
torch.set_float32_matmul_precision("high")

logger = get_logger(__name__)


class TTSNode(PipelineNode):
    def __init__(self, config):
        super().__init__(config)
        self.model = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=True)
        self.ref_path = (
            Path(__file__).resolve().parent / "resources" / "source-ilja.wav"
        )
        self.ref_text = "Das Scheinwerferlicht bricht sich in der Stille des großen Hauses, während der Vorhang langsam beiseite gleitet. In diesem flüchtigen Moment zwischen Realität und Illusion verschmelzen die Worte des Dramas mit der Präsenz des Schauspielers, um das Publikum in eine Welt voll dramatischer Tiefe und ungeahnter Leidenschaft zu entführen."
        self.synthesis_lock = asyncio.Lock()

    async def handle_reliable(self, payload: bytes) -> None:
        meta_len = int.from_bytes(payload[:4], byteorder="big")
        meta_json_str = payload[4 : 4 + meta_len].decode("utf-8")

        try:
            meta_dict = json.loads(meta_json_str)
            if meta_dict.get("stream_type") != "token":
                return
            meta = TokenStreamMetadata(**meta_dict)
        except ValidationError, json.JSONDecodeError:
            return

        text_chunk = payload[4 + meta_len :].decode("utf-8")
        logger.info(f"Received text chunk for synthesis: '{text_chunk}'")
        asyncio.create_task(
            self._synthesize_and_stream(meta.request_id, text_chunk, meta.is_final)
        )

    async def _synthesize_and_stream(self, request_id: str, text: str, is_final: bool):
        async with self.synthesis_lock:
            if not text.strip():
                if is_final:
                    out_meta = AudioStreamMetadata(
                        request_id=request_id,
                        is_final=True,
                        sample_rate=24000,
                        dtype="float32",
                    )
                    out_meta_json = out_meta.model_dump_json().encode("utf-8")
                    out_meta_len = len(out_meta_json).to_bytes(4, byteorder="big")
                    await self.send_reliable(out_meta_len + out_meta_json + b"")
                return

            audio_queue = queue.Queue()

            def _run_synthesis():
                try:
                    for chunk in self.model.generate_streaming(
                        text=text,
                        prompt_wav_path=self.ref_path,
                        prompt_text=self.ref_text,
                        reference_wav_path=self.ref_path,
                    ):
                        if hasattr(chunk, "cpu"):
                            chunk = chunk.cpu().numpy()
                        chunk = np.array(chunk, dtype=np.float32)

                        audio_queue.put(
                            (
                                chunk.tobytes(),
                                "float32",
                                int(self.model.tts_model.sample_rate),
                            )
                        )
                except Exception as e:
                    logger.error(f"TTS Synthesis error: {e}")
                finally:
                    audio_queue.put(None)

            threading.Thread(target=_run_synthesis, daemon=True).start()

            last_sr = 24000
            last_dtype = "float32"

            while True:
                item = await asyncio.to_thread(audio_queue.get)

                if item is None:
                    if is_final:
                        logger.info(
                            "Final text chunk processed. Sending termination signal."
                        )
                        out_meta = AudioStreamMetadata(
                            request_id=request_id,
                            is_final=True,
                            sample_rate=last_sr,
                            dtype=last_dtype,
                        )
                        out_meta_json = out_meta.model_dump_json().encode("utf-8")
                        out_meta_len = len(out_meta_json).to_bytes(4, byteorder="big")
                        await self.send_reliable(out_meta_len + out_meta_json + b"")
                    break

                chunk_bytes, dtype, sr = item
                last_sr, last_dtype = sr, dtype
                logger.info(f"Sending audio chunk of size {len(chunk_bytes)} bytes")

                out_meta = AudioStreamMetadata(
                    request_id=request_id, is_final=False, sample_rate=sr, dtype=dtype
                )
                out_meta_json = out_meta.model_dump_json().encode("utf-8")
                out_meta_len = len(out_meta_json).to_bytes(4, byteorder="big")
                out_payload = out_meta_len + out_meta_json + chunk_bytes

                await self.send_reliable(out_payload)


async def main() -> None:
    setup_logging()
    node = TTSNode(settings_tts.shared)
    await node.run()


if __name__ == "__main__":
    uvloop.run(main())
