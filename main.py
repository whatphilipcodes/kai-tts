from src.kai_tts.config_tts import settings_tts
from kai_shared.utils.logger import get_logger, setup_logging
from kai_shared.io.node import PipelineNode
import asyncio

setup_logging()
logger = get_logger(__name__)


async def main() -> None:
    app_node = PipelineNode(config=settings_tts.shared)
    await app_node.run()


if __name__ == "__main__":
    asyncio.run(main())
