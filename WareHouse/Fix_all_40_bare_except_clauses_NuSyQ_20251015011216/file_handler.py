import os
import logging
logger = logging.getLogger(__name__)
def read_file(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path,'r', encoding='utf-8') as file:
                return file.read()
        else:
            logger.error(f"File not found: {file_path}")
            return None
    except IOError as e:
        logger.error(f"IO error: {e}")
        return None