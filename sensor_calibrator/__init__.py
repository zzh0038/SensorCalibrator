class Config:
    MAX_DATA_POINTS = 2000
    DISPLAY_DATA_POINTS = 200
    UPDATE_INTERVAL_MS = 50
    STATS_WINDOW_SIZE = 100
    SERIAL_TIMEOUT = 0.1
    SERIAL_WRITE_TIMEOUT = 1
    MAX_QUEUE_SIZE = 2000
    MAX_CONSECUTIVE_ERRORS = 5
    CALIBRATION_SAMPLES = 100
    EXPECTED_FREQUENCY = 100
    COMMAND_DELAY = 2.0
    RESPONSE_TIMEOUT = 5.0
    THREAD_JOIN_TIMEOUT = 2.0
    GRAVITY_CONSTANT = 9.8015
    
    SERIAL_CLEANUP_DELAY = 0.5
    SERIAL_STABILITY_DELAY = 0.5
    DATA_STREAM_STOP_DELAY = 1.0
    THREAD_ERROR_DELAY = 0.1
    PARSE_RETRY_DELAY = 0.05
    QUICK_SLEEP = 0.01
    BUFFER_CLEAR_DELAY = 0.5


def validate_ssid(ssid: str) -> tuple:
    if not ssid:
        return False, "SSID cannot be empty"
    if len(ssid) > 32:
        return False, "SSID too long (max 32 characters)"
    return True, ""


def validate_password(password: str) -> tuple:
    if len(password) > 64:
        return False, "Password too long (max 64 characters)"
    return True, ""


def validate_port(port: str) -> tuple:
    if not port:
        return False, "Port cannot be empty"
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            return False, "Port must be between 1 and 65535"
    except ValueError:
        return False, "Port must be a number"
    return True, ""


def validate_url(url: str) -> tuple:
    if not url:
        return True, ""
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "URL must start with http:// or https://"
    return True, ""
