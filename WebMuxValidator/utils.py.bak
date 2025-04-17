import os
import json
import time
import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# API Endpoints
PLATFORM_API_BASE = "https://platform-explorer.pshenmic.dev"

# Constants
SAVE_DIR = os.path.join(os.path.expanduser("~"), "tmp")
os.makedirs(SAVE_DIR, exist_ok=True)

EPOCH_INTERVALS_FILE = os.path.join(SAVE_DIR, "epoch_intervals.txt")

def load_cached_data(file_path, default=None):
    """Load data from cache file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read().strip()
                
            if content:
                if file_path.endswith('.json'):
                    return json.loads(content)
                elif isinstance(default, list):
                    return content.splitlines()
                elif isinstance(default, dict):
                    result = {}
                    for line in content.splitlines():
                        if ':' in line:
                            key, value = line.split(':', 1)
                            result[key.strip()] = value.strip()
                    return result
                else:
                    return content
    except Exception as e:
        logger.error(f"Error loading cache from {file_path}: {e}")
    
    return default if default is not None else None

def save_cached_data(file_path, data):
    """Save data to cache file"""
    try:
        with open(file_path, 'w') as f:
            if isinstance(data, (list, tuple)):
                f.write('\n'.join(str(item) for item in data))
            elif isinstance(data, dict):
                if file_path.endswith('.json'):
                    f.write(json.dumps(data, indent=2))
                else:
                    for key, value in data.items():
                        f.write(f"{key}: {value}\n")
            else:
                f.write(str(data))
    except Exception as e:
        logger.error(f"Error saving cache to {file_path}: {e}")

def update_epoch_intervals():
    """Update epoch intervals cache file"""
    try:
        if not os.path.exists(EPOCH_INTERVALS_FILE):
            # Fetch epoch data from API
            response = requests.get("https://dashsight.dashevo.org/insight-api-dash/sync")
            data = response.json()
            
            if 'blockChainHeight' in data:
                height = data['blockChainHeight']
                
                # Get timestamps for blocks around epoch transitions
                epochs = {}
                for block_height in range(100, height, 16320):  # Approximately 16320 blocks per epoch
                    try:
                        block_response = requests.get(f"https://dashsight.dashevo.org/insight-api-dash/block-index/{block_height}")
                        block_hash = block_response.json().get('blockHash')
                        
                        if block_hash:
                            block_data_response = requests.get(f"https://dashsight.dashevo.org/insight-api-dash/block/{block_hash}")
                            block_data = block_data_response.json()
                            
                            if 'time' in block_data:
                                epoch_num = block_height // 16320
                                epochs[epoch_num] = block_data['time']
                    except Exception as e:
                        logger.warning(f"Error fetching block data for height {block_height}: {e}")
                
                # Save epoch intervals to file
                save_cached_data(EPOCH_INTERVALS_FILE, epochs)
    except Exception as e:
        logger.error(f"Error updating epoch intervals: {e}")

def timestamp_to_epoch(timestamp):
    """Convert timestamp to epoch number"""
    # This function is now primarily for backwards compatibility
    # New code should use the direct epoch data from the API
    
    # Best approach: directly query current epoch from API
    try:
        response = requests.get("https://platform-explorer.pshenmic.dev/status")
        data = response.json()
        current_epoch = data.get('epoch', {}).get('number', 24) # Default to 24 if not available
        
        # For timestamps in the future, return current epoch
        current_time_ms = int(time.time() * 1000)
        if timestamp * 1000 > current_time_ms:  # Convert timestamp to milliseconds
            return current_epoch
        
        # For historical timestamps, use epoch data from API
        # Start from the earliest epoch (6) and check each one
        for epoch_num in range(6, current_epoch + 1):
            epoch_data = get_epoch_timestamps(epoch_num)
            if epoch_data:
                start_time, end_time = epoch_data
                # Convert timestamp to milliseconds for comparison
                if start_time <= timestamp * 1000 <= end_time:
                    return epoch_num
    except Exception as e:
        logger.error(f"Error in direct epoch determination: {e}")
        
    # If all else fails, return a reasonable default (current epoch)
    return 24

def fetch_validator_identity(validator_hash):
    """Fetch validator identity and IP from API"""
    try:
        url = f"https://platform-explorer.pshenmic.dev/validator/{validator_hash}"
        response = requests.get(url, timeout=10)  # Add timeout to prevent long wait
        data = response.json()
        
        # Extract identity from response
        identity = data.get('identity')
        if not identity:
            logger.warning(f"No identity found for validator {validator_hash}")
            return None
        
        # Also extract server IP if available (for display purposes)
        try:
            # Validator's IP address is in the proTxInfo.state.service field in format IP:PORT
            ip_port = data.get('proTxInfo', {}).get('state', {}).get('service', '')
            if ip_port and ':' in ip_port:
                server_ip = ip_port.split(':')[0]
                # Cache this IP address for this validator
                cache_file = os.path.join(SAVE_DIR, f"validator_ip_{validator_hash}.txt")
                with open(cache_file, 'w') as f:
                    f.write(server_ip)
        except Exception as e:
            logger.error(f"Error extracting server IP for validator {validator_hash}: {e}")
            
        return identity
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error fetching validator identity: {e}")
        # Return a placeholder indicating API connectivity issues rather than None
        # This allows us to show the error to the user 
        return f"API_CONNECTION_ERROR"
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching validator identity for {validator_hash}")
        return f"API_TIMEOUT_ERROR"
    except Exception as e:
        logger.error(f"Error fetching validator identity: {e}")
        return None

def fetch_withdrawal_data(validator_hash, epoch):
    """Fetch withdrawal data for a specific validator and epoch"""
    try:
        # First get identity for the validator
        identity = fetch_validator_identity(validator_hash)
        
        if identity == "API_CONNECTION_ERROR" or identity == "API_TIMEOUT_ERROR":
            # If we can't get identity due to connection issues, return the error
            return (validator_hash, epoch, identity)
            
        if not identity:
            logger.warning(f"No identity found for validator {validator_hash}, cannot fetch withdrawals")
            return None
            
        # Now get withdrawals data using the identity
        url = f"https://platform-explorer.pshenmic.dev/identity/{identity}/withdrawals?page=1&limit=100"
        response = requests.get(url, timeout=15)  # Increased timeout
        data = response.json()
        
        # Get epoch start and end timestamps
        epoch_data = get_epoch_timestamps(epoch)
        if not epoch_data:
            logger.warning(f"Could not get epoch timestamps for epoch {epoch}")
            return None
            
        epoch_start_time, epoch_end_time = epoch_data
        
        # Filter withdrawals for the specific epoch by timestamp
        epoch_withdrawals = [
            withdrawal for withdrawal in data.get('resultSet', [])
            if withdrawal.get('status') == 3  # Status 3 means completed withdrawals
            and is_timestamp_in_epoch(withdrawal.get('timestamp'), epoch_start_time, epoch_end_time)
        ]
        
        # Sum up all withdrawals for this validator in this epoch
        # Convert amount from smallest unit (satoshis) to DASH (1 DASH = 100,000,000 satoshis)
        total_amount = sum(withdrawal.get('amount', 0) / 100000000 for withdrawal in epoch_withdrawals)
        
        # Create result
        result = (validator_hash, epoch, total_amount if total_amount > 0 else 0)
        
        # Cache the result to reduce future API calls
        cache_file = os.path.join(SAVE_DIR, f"withdrawal_{validator_hash}_{epoch}.json")
        save_cached_data(cache_file, result)
        
        if total_amount > 0:
            return result
        else:
            return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error fetching withdrawal data: {e}")
        # Special error marker to detect network issues
        return (validator_hash, epoch, "API_CONNECTION_ERROR")
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching withdrawal data for {validator_hash}, epoch {epoch}")
        return (validator_hash, epoch, "API_TIMEOUT_ERROR")
    except Exception as e:
        logger.error(f"Error fetching withdrawal data for {validator_hash}, epoch {epoch}: {e}")
        return None
        
def get_epoch_timestamps(epoch_number):
    """Get start and end timestamps for a given epoch"""
    try:
        url = f"https://platform-explorer.pshenmic.dev/epoch/{epoch_number}"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        # Check if we have valid epoch data
        if not data or 'epoch' not in data:
            return None
            
        epoch_data = data['epoch']
        start_time = epoch_data.get('startTime')
        end_time = epoch_data.get('endTime')
        
        if not start_time or not end_time:
            return None
            
        return (start_time, end_time)
    except Exception as e:
        logger.error(f"Error fetching epoch timestamps for epoch {epoch_number}: {e}")
        return None
        
def is_timestamp_in_epoch(timestamp_str, epoch_start_time, epoch_end_time):
    """Check if a timestamp is within a given epoch's time range"""
    try:
        # Parse ISO timestamp to datetime with better error handling
        if not timestamp_str or not isinstance(timestamp_str, str):
            return False
            
        timestamp_dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        # Convert to milliseconds timestamp
        timestamp_ms = int(timestamp_dt.timestamp() * 1000)
        
        # Check if timestamp is within epoch boundaries
        return epoch_start_time <= timestamp_ms <= epoch_end_time
    except Exception as e:
        logger.error(f"Error comparing timestamp {timestamp_str} with epoch: {e}")
        return False

def get_current_epoch():
    """Get current epoch number from API"""
    try:
        response = requests.get(f"{PLATFORM_API_BASE}/status")
        data = response.json()
        current_epoch = data.get('epoch', {}).get('number')
        if current_epoch:
            return current_epoch
    except Exception as e:
        logger.error(f"Error fetching current epoch: {e}")
    
    # Fallback value if there's an error
    return 24

def calculate_totals(withdrawals_data, validators, current_epoch, start_epoch=6):
    """Calculate totals for all validators and epochs"""
    validator_totals = {}
    grand_total = 0
    epoch_range = list(range(start_epoch, current_epoch + 1))
    
    for validator in validators:
        if validator in withdrawals_data:
            validator_total = sum(withdrawals_data[validator].get(epoch, 0) for epoch in epoch_range)
            validator_totals[validator] = validator_total
            grand_total += validator_total
    
    return validator_totals, grand_total, epoch_range
