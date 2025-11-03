# Art-Net Connection Guide
## Kết nối từ External Software đến Art-Net Controller

### 📍 Thông tin kết nối hiện tại:
- **Địa chỉ IP chính:** `192.168.1.171`
- **Port Art-Net:** `6454` (standard)
- **Protocol:** Art-Net v4
- **Webserver:** http://192.168.1.171:8080

---

## 🎯 Hướng dẫn cấu hình cho từng phần mềm:

### 1. **Depence² (Syncronorm)**
```
Art-Net Output Settings:
- IP Address: 192.168.1.171
- Port: 6454
- Universe: 0 (hoặc universe bạn muốn)
- Protocol: Art-Net
```

**Các bước:**
1. Mở Depence² → **Setup** → **DMX Settings**
2. Chọn **Art-Net Output**
3. Nhập IP: `192.168.1.171`
4. Port: `6454` (auto)
5. Enable output và chọn universe

### 2. **Resolume (Avenue/Arena)**
```
Art-Net Settings:
- Target IP: 192.168.1.171
- Port: 6454
- Universe: 0-15 (tùy setup)
- Mode: Art-Net
```

**Các bước:**
1. **Composition** → **Advanced Output**
2. Chọn **Art-Net** 
3. **Target IP:** `192.168.1.171`
4. **Universe:** chọn universe muốn control
5. Enable output

### 3. **Madrix 5**
```
Device Manager Settings:
- Protocol: Art-Net
- IP Address: 192.168.1.171  
- Port: 6454
- Universe: 0+ (multi-universe support)
```

**Các bước:**
1. **Device Manager** → **Add Device**
2. Chọn **Art-Net**
3. **IP Address:** `192.168.1.171`
4. **Universe mapping** theo nhu cầu
5. Apply và Start Output

### 4. **GrandMA2/MA3**
```
Network Settings:
- Art-Net Node IP: 192.168.1.171
- Universe: định nghĩa trong patch
- Port: 6454 (default)
```

### 5. **Chamsys MagicQ**
```
Setup → View DMX I/O:
- Art-Net enabled
- Art-Net nodes: 192.168.1.171
- Universe assignment
```

---

## 🔧 Troubleshooting:

### Nếu không kết nối được:

1. **Kiểm tra mạng:**
   ```bash
   ping 192.168.1.171
   ```

2. **Kiểm tra firewall:**
   - Windows: Allow Python.exe through firewall
   - Hoặc tạm tắt firewall để test

3. **Kiểm tra port:**
   ```bash
   netstat -ano | findstr :6454
   ```

4. **Alternative IPs** (nếu có):
   - Localhost: `127.0.0.1` (chỉ local machine)
   - Check Settings tab → Network Info trong app

### Common Issues:

- **Port 6454 bị chiếm:** Tắt software khác dùng Art-Net
- **Firewall block:** Cho phép port 6454 UDP
- **Wrong subnet:** Đảm bảo cùng network 192.168.1.x
- **Multiple NICs:** Chọn đúng network adapter

---

## 📊 Testing & Monitoring:

### Trong Art-Net Controller:
1. **DMX View tab:** Xem data nhận được real-time
2. **Hardware Manager:** Monitor connected nodes  
3. **Status Bar:** Hiển thị IP và connection status
4. **Record tab:** Record incoming DMX để analyze

### Test Commands:
```bash
# Test ping connectivity
ping 192.168.1.171

# Check Art-Net port
telnet 192.168.1.171 6454
```

---

## 💡 Pro Tips:

1. **Static IP:** Đặt IP tĩnh cho stable connection
2. **Multiple Universes:** Mỗi universe = 512 channels DMX
3. **Backup IP:** Note down alternative IPs nếu network thay đổi
4. **Monitor tab:** Luôn check DMX View để verify data
5. **Recording:** Dùng Record tab để capture và replay shows

---

## 🌐 Network Requirements:

- **Same subnet:** External software phải cùng mạng LAN
- **UDP Protocol:** Art-Net dùng UDP port 6454
- **Broadcast support:** Network phải hỗ trợ broadcast
- **Low latency:** Gigabit Ethernet recommend cho performance

---

**✅ Current Status:** Art-Net Controller đang chạy và ready nhận data!

Địa chỉ này sẽ được update tự động trong app nếu network thay đổi.