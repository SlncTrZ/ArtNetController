"""
Network utilities - Get available network adapters

Topic: utils
Last Updated: 2026-05-01
"""

import socket
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def get_network_adapters() -> Dict[str, str]:
    """
    Get all available network adapters with their IP addresses
    
    Returns:
        Dict mapping adapter_name to IP address
        Example: {
            "Ethernet": "192.168.1.10",
            "WiFi": "192.168.1.20",
            "Loopback": "127.0.0.1"
        }
    """
    adapters = {}
    
    try:
        # Try using psutil for better adapter info (if available)
        try:
            import psutil
            net_if_addrs = psutil.net_if_addrs()
            
            for interface_name, sniff in net_if_addrs.items():
                for addr in sniff:
                    if addr.family == socket.AF_INET:  # IPv4 only
                        adapters[interface_name] = addr.address
                        break
            
            if adapters:
                logger.info(f"Found {len(adapters)} network adapters using psutil")
                return adapters
        except ImportError:
            logger.debug("psutil not available, using socket module")
    except Exception as e:
        logger.warning(f"Error with psutil: {e}")
    
    # Fallback: use socket module (less reliable but always available)
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        adapters["Primary Network"] = local_ip
        logger.info(f"Found primary network adapter: {local_ip}")
    except Exception as e:
        logger.warning(f"Could not get primary network adapter: {e}")
    
    # Always add localhost
    adapters["Loopback (127.0.0.1)"] = "127.0.0.1"
    
    # Always add broadcast option
    adapters["Broadcast (0.0.0.0)"] = "0.0.0.0"
    
    return adapters


def get_primary_ip() -> str:
    """
    Get primary (non-loopback) network adapter IP address
    
    Returns:
        IP address string or "127.0.0.1" if only loopback available
    """
    try:
        # Connect to Google DNS to determine primary interface (doesn't actually send)
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))
        primary_ip = temp_socket.getsockname()[0]
        temp_socket.close()
        
        if primary_ip and primary_ip != "127.0.0.1":
            return primary_ip
    except Exception as e:
        logger.warning(f"Could not get primary IP: {e}")
    
    return "127.0.0.1"


def validate_ip_address(ip: str) -> bool:
    """
    Validate if string is a valid IP address
    
    Args:
        ip: IP address string to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False
