import psutil
import os
import logging
from config import LOGGING

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, LOGGING['level']),
        format=LOGGING['format'],
        handlers=[
            logging.FileHandler(LOGGING['file']),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('StatusChecker')

def is_monitor_running():
    """Check if the monitor process is running"""
    logger = setup_logging()
    
    # Get all Python processes
    python_processes = [p for p in psutil.process_iter(['pid', 'name', 'cmdline']) 
                       if 'python' in p.info['name'].lower()]
    
    # Look for our monitor process
    for process in python_processes:
        try:
            cmdline = process.info['cmdline']
            if cmdline and 'monitor.py' in cmdline:
                logger.info(f"Monitor is running with PID: {process.info['pid']}")
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    logger.warning("Monitor is not running")
    return False

def get_monitor_status():
    """Get detailed status of the monitor"""
    logger = setup_logging()
    
    if not is_monitor_running():
        return {
            'status': 'not_running',
            'message': 'Monitor is not running'
        }
    
    # Check if log file exists and get last update
    log_file = LOGGING['file']
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                last_lines = f.readlines()[-5:]  # Get last 5 lines
                last_update = last_lines[-1].strip()
        except Exception as e:
            logger.error(f"Error reading log file: {str(e)}")
            last_update = "Unable to read log file"
    else:
        last_update = "Log file not found"
    
    # Check if results file exists
    results_file = 'scan_results.csv'
    has_results = os.path.exists(results_file)
    
    return {
        'status': 'running',
        'last_update': last_update,
        'has_results': has_results,
        'message': 'Monitor is running and collecting data'
    }

if __name__ == "__main__":
    status = get_monitor_status()
    print("\nMonitor Status:")
    print(f"Status: {status['status']}")
    print(f"Message: {status['message']}")
    print(f"Last Update: {status['last_update']}")
    print(f"Has Results: {status['has_results']}") 