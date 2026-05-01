"""
Network utilities for Art-Net Controller

Topic: utils
Last Updated: 2026-05-01
"""

import socket
import subprocess
import platform
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

def get_local_ip_addresses() -> List[str]:
    """
    Lấy danh sách các địa chỉ IP local của máy tính
    Returns list of IP addresses that can be used by external devices
    """
    ip_addresses = []
    
    try:
        # Method 1: Connect to external address to get preferred local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # Connect to Google DNS (doesn't actually send data)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            if primary_ip and primary_ip != "127.0.0.1":
                ip_addresses.append(primary_ip)
    except Exception as e:
        logger.warning(f"Could not get primary IP: {e}")
    
    try:
        # Method 2: Get all network interfaces
        hostname = socket.gethostname()
        all_ips = socket.gethostbyname_ex(hostname)[2]
        
        for ip in all_ips:
            # Filter out localhost and add unique IPs
            if ip != "127.0.0.1" and ip not in ip_addresses:
                # Check if it's a valid private IP range
                if (ip.startswith("192.168.") or 
                    ip.startswith("10.") or 
                    ip.startswith("172.")):
                    ip_addresses.append(ip)
    except Exception as e:
        logger.warning(f"Could not get network IPs: {e}")
    
    # Always add localhost as fallback
    if "127.0.0.1" not in ip_addresses:
        ip_addresses.append("127.0.0.1")
    
    return ip_addresses

def get_primary_ip() -> str:
    """
    Lấy địa chỉ IP chính để hiển thị cho user
    """
    ips = get_local_ip_addresses()
    
    # Prefer non-localhost IPs
    for ip in ips:
        if ip != "127.0.0.1":
            return ip
    
    # Fallback to localhost
    return "127.0.0.1"

def format_ip_info() -> str:
    """
    Format IP information for display
    """
    primary_ip = get_primary_ip()
    all_ips = get_local_ip_addresses()
    
    if len(all_ips) == 1:
        return f"IP: {primary_ip}"
    else:
        other_ips = [ip for ip in all_ips if ip != primary_ip]
        if other_ips:
            return f"Primary IP: {primary_ip}\nOther IPs: {', '.join(other_ips)}"
        else:
            return f"IP: {primary_ip}"

def get_artnet_connection_info() -> dict:
    """
    Lấy thông tin kết nối Art-Net để hiển thị cho user
    """
    primary_ip = get_primary_ip()
    all_ips = get_local_ip_addresses()
    
    return {
        "primary_ip": primary_ip,
        "all_ips": all_ips,
        "artnet_port": 6454,
        "webserver_port": 8080,
        "connection_string": f"{primary_ip}:6454",
        "instructions": [
            f"Nhập địa chỉ IP: {primary_ip}",
            "Port Art-Net: 6454 (tự động)",
            "Universe: 0-32767 (tùy chọn)",
            "Protocol: Art-Net v4"
        ]
    }