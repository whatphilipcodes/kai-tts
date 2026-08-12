import uvloop
from kai_shared.io.node import PipelineNode
from kai_shared.utils.logger import setup_logging

from src.kai_tts.config_tts import settings_tts


async def main() -> None:
    setup_logging()
    node = PipelineNode(settings_tts.shared)
    await node.run()


if __name__ == "__main__":
    uvloop.run(main())
