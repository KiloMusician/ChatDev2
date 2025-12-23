import socket
import logging
logger = logging.getLogger(__name__)
def send_data(data, timeout=30):
    try:
        network.send_data(data, timeout)
    except (socket.timeout, ConnectionError) as e:
        logger.error(f"Network error: {e}")