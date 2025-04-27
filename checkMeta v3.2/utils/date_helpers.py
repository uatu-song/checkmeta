"""
META Fantasy League Simulator - Date Helpers
Provides utilities for date handling and scheduling
"""

import datetime
from typing import Dict, List, Any, Optional, Tuple
from config import get_config

def get_formatted_date(date_format=None):
    """Get current date in specified format
    
    Args:
        date_format: Optional format (defaults to config setting)
        
    Returns:
        str: Formatted date
    """
    config = get_config()
    format_str = date_format or config.date["date_format"]
    return datetime.datetime.now().strftime(format_str)

def get_formatted_timestamp():
    """Get current timestamp in configured format
    
    Returns:
        str: Formatted timestamp
    """
    config = get_config()
    return datetime.datetime.now().strftime(config.date["timestamp_format"])

def get_matchday_date(day_number):
    """Get date for a specific match day
    
    Args:
        day_number: Day number in the season
        
    Returns:
        str: Formatted date for the match day
    """
    config = get_config()
    
    # Simulate weekly matches (match every 7 days)
    # Start with current date and calculate based on day number
    base_date = datetime.datetime.strptime(config.date["current_date"], config.date["date_format"])
    match_date = base_date + datetime.timedelta(days=(day_number - 1) * 7)
    
    return match_date.strftime(config.date["date_format"])

def create_dated_filename(prefix, suffix="", include_time=True):
    """Create a filename with date/time components
    
    Args:
        prefix: Filename prefix
        suffix: Filename suffix/extension
        include_time: Whether to include time in the filename
        
    Returns:
        str: Generated filename
    """
    config = get_config()
    
    if include_time:
        timestamp = get_formatted_timestamp()
        return f"{prefix}_{timestamp}{suffix}"
    else:
        date_str = datetime.datetime.now().strftime("%Y%m%d")
        return f"{prefix}_{date_str}{suffix}"

def parse_match_date(date_str, format_str=None):
    """Parse a date string into a datetime object
    
    Args:
        date_str: Date string to parse
        format_str: Optional format string
        
    Returns:
        datetime: Parsed datetime object
    """
    config = get_config()
    format_str = format_str or config.date["date_format"]
    
    try:
        return datetime.datetime.strptime(date_str, format_str)
    except ValueError:
        # Try alternate formats if the main one fails
        alternate_formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%d %B %Y"
        ]
        
        for fmt in alternate_formats:
            try:
                return datetime.datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If all parsing attempts failed, raise an error
        raise ValueError(f"Unable to parse date: {date_str}")

def generate_season_schedule(start_date, num_days=10, day_interval=7):
    """Generate a season schedule
    
    Args:
        start_date: Season start date (string or datetime)
        num_days: Number of match days
        day_interval: Days between matches
        
    Returns:
        dict: Season schedule
    """
    config = get_config()
    
    # Parse start date if string
    if isinstance(start_date, str):
        start_date = parse_match_date(start_date)
    
    # Generate schedule
    schedule = {}
    current_date = start_date
    
    for day in range(1, num_days + 1):
        date_str = current_date.strftime(config.date["date_format"])
        
        # Get matchups for this day
        matchups = config.get_matchups_for_day(day)
        
        # Store in schedule
        schedule[day] = {
            "date": date_str,
            "matchups": matchups
        }
        
        # Move to next match day
        current_date += datetime.timedelta(days=day_interval)
    
    return schedule