from pathlib import Path
from dateutil import tz


DATA_FILE = Path.home() / ".lccal_data.json"
CST_TZ = tz.gettz("America/Chicago")


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
