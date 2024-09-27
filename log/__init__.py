import logging
import sys

from config import log_format

log_file_name = "log_collector_v2_pub.log"


def set_log_file_name(file_name):
    global log_file_name
    log_file_name = file_name


logging.basicConfig(stream=sys.stdout, filemode="a", format=log_format, level=logging.INFO)
logger = logging.getLogger()
