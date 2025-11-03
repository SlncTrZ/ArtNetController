#!/bin/bash
# Raspberry Pi optimization script for Art-Net Controller

echo "Optimizing Art-Net Controller for Raspberry Pi..."

# Update system
echo "Updating system packages..."
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-venv python3-dev
sudo apt install -y libqt6-dev qt6-base-dev
sudo apt install -y libasound2-dev portaudio19-dev

# Install GPIO library for Pi
echo "Installing Raspberry Pi GPIO library..."
pip install RPi.GPIO

# Create performance optimization config
echo "Creating performance optimization config..."
cat > rpi_config.json << EOF
{
  "performance": {
    "gui_refresh_rate": 15,
    "dmx_refresh_rate": 20,
    "max_memory_usage": 256,
    "enable_gpu_acceleration": false,
    "reduce_logging": true
  },
  "artnet": {
    "max_universes": 4,
    "buffer_size": 1024,
    "send_threaded": true
  },
  "webserver": {
    "max_file_size": 25,
    "thread_count": 2
  }
}
EOF

# Create systemd service for auto-start
echo "Creating systemd service..."
sudo tee /etc/systemd/system/artnet-controller.service > /dev/null << EOF
[Unit]
Description=Art-Net Controller
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ArtNetController
ExecStart=/home/pi/ArtNetController/venv/bin/python run.py --no-debug
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable GPU memory split for better performance
echo "Configuring GPU memory split..."
if ! grep -q "gpu_mem=64" /boot/config.txt; then
    echo "gpu_mem=64" | sudo tee -a /boot/config.txt
fi

# Optimize network settings for Art-Net
echo "Optimizing network settings..."
sudo tee -a /etc/sysctl.conf > /dev/null << EOF

# Art-Net Controller optimizations
net.core.rmem_max = 134217728
net.core.rmem_default = 65536
net.core.wmem_max = 134217728
net.core.wmem_default = 65536
net.core.netdev_max_backlog = 5000
EOF

# Create Pi-specific launch script
cat > run_pi.py << 'EOF'
#!/usr/bin/env python3
"""
Raspberry Pi optimized launcher for Art-Net Controller
"""

import os
import sys
import platform
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def is_raspberry_pi():
    """Check if running on Raspberry Pi"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        return 'BCM' in cpuinfo and 'ARM' in platform.machine().upper()
    except:
        return False

def optimize_for_pi():
    """Apply Pi-specific optimizations"""
    # Set environment variables for better Qt performance
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    os.environ['QT_QUICK_BACKEND'] = 'software'
    
    # Reduce GUI refresh rate
    os.environ['ARTNET_GUI_REFRESH'] = '15'
    
    # Enable reduced logging
    os.environ['ARTNET_REDUCED_LOGGING'] = '1'

def main():
    """Main entry point"""
    if is_raspberry_pi():
        print("Running on Raspberry Pi - applying optimizations...")
        optimize_for_pi()
    
    # Import main application
    from main import main as app_main
    
    # Run with Pi-optimized settings
    sys.argv.extend(['--debug'] if '--debug' in sys.argv else [])
    
    try:
        app_main()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

chmod +x run_pi.py

echo "Raspberry Pi optimization complete!"
echo ""
echo "To start the service automatically:"
echo "  sudo systemctl enable artnet-controller"
echo "  sudo systemctl start artnet-controller"
echo ""
echo "To run manually with Pi optimizations:"
echo "  python3 run_pi.py"
echo ""
echo "Note: Reboot recommended to apply all optimizations."