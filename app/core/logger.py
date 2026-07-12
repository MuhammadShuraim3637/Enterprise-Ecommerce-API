import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("production_app.log", encoding="utf-8")
    ]
)

logger = logging.getLogger("enterprise-ecommerce")