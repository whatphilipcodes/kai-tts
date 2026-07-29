from src.kai_tts.config_tts import settings_tts
from kai_shared.utils.logger import get_logger, setup_logging
from kai_shared.io.node import PipelineNode

setup_logging()
logger = get_logger(__name__)


def main() -> None:
    app_node = PipelineNode(config=settings_tts.shared)
    app_node.run()


if __name__ == "__main__":
    main()
