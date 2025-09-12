from datetime import datetime, timedelta

def parse_datetime(dt_str):
    """
    Parses a datetime string into a datetime object.
    Supports various common datetime formats.
    Args:
        dt_str (str): The datetime string to parse.
    Returns:
        datetime: The parsed datetime object, or None if parsing fails.
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S", # ISO format
        "%Y-%m-%dT%H:%M",    # ISO format without seconds
        "%Y-%m-%d",          # Date only
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None

def format_datetime(dt_obj, fmt="%Y-%m-%d %H:%M:%S"):
    """
    Formats a datetime object into a string.
    Args:
        dt_obj (datetime): The datetime object to format.
        fmt (str): The desired string format.
    Returns:
        str: The formatted datetime string.
    """
    if isinstance(dt_obj, datetime):
        return dt_obj.strftime(fmt)
    return str(dt_obj) # Return as string if not a datetime object, or handle error
