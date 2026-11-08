"""CLI entry point for the ORB DOCK Windows host."""

from __future__ import annotations

import asyncio
import logging

from . import __version__
from .server import OrbDockServer


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


async def async_main() -> None:
    configure_logging()
    logger = logging.getLogger("orb_dock")
    logger.info("ORB DOCK Windows Host v%s", __version__)
    server = OrbDockServer()
    try:
        await server.run()
    except OSError as exc:
        logger.error("Could not start ORB DOCK: %s", exc)
        raise


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nORB DOCK stopped.")


if __name__ == "__main__":
    main()
