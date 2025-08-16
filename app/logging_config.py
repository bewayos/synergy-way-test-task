import logging

from pythonjsonlogger import json


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure JSON logging to stdout.

    This keeps logs cloud-ready and easy to parse.
    """
    logger = logging.getLogger()
    logger.setLevel(level)
    handler = logging.StreamHandler()
    formatter = json.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    handler.setFormatter(formatter)
    logger.handlers = [handler]
