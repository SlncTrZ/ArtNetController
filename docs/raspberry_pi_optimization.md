# Performance và Memory Optimizations cho Raspberry Pi

## Tối ưu hóa hệ thống

### 1. GPU Memory Split
```bash
# Tăng GPU memory cho Qt performance
sudo raspi-config
# Advanced Options > Memory Split > 64MB
```

### 2. Overclock (nếu cần)
```bash
# Thêm vào /boot/config.txt
arm_freq=1400
gpu_freq=500
sdram_freq=500
```

### 3. Disable unused services
```bash
sudo systemctl disable bluetooth
sudo systemctl disable cups
sudo systemctl disable triggerhappy
```

## Tối ưu mạng cho Art-Net

### 1. Network buffer tuning
```bash
# Thêm vào /etc/sysctl.conf
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.netdev_max_backlog = 5000
```

### 2. Ethernet settings
```bash
# Disable power management
sudo ethtool -s eth0 wol d
echo 'ethtool -s eth0 wol d' | sudo tee -a /etc/rc.local
```

## Python optimizations

### 1. Bytecode compilation
```bash
# Compile all Python files
python -m compileall src/
```

### 2. Memory management
```python
# Trong code, sử dụng generators thay vì lists lớn
# Giới hạn buffer sizes
# Sử dụng threading cho I/O operations
```

## Monitoring performance

### 1. CPU và Memory usage
```bash
htop
```

### 2. Network performance
```bash
iftop
netstat -i
```

### 3. Real-time monitoring
```bash
# Tạo simple monitor script
#!/bin/bash
while true; do
    echo "$(date): CPU: $(vcgencmd measure_temp), RAM: $(free -m | awk 'NR==2{printf \"%.1f%%\", $3*100/$2}')"
    sleep 10
done
```