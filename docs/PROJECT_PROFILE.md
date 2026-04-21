# PROJECT PROFILE — DMX Master LTS

> **"Professional lighting control for everyone."**

---

## 1. Tầm nhìn (Vision)

DMX Master LTS được xây dựng dựa trên một niềm tin đơn giản nhưng mạnh mẽ:

> **Phần mềm điều khiển ánh sáng chuyên nghiệp không nên là đặc quyền của những người có ngân sách hàng chục nghìn đô.**

Trên thị trường hiện nay, các giải pháp đẳng cấp như GrandMA, ETC EOS, hay Resolume Arena đòi hỏi chi phí phần cứng và license khổng lồ, gây rào cản cho đại đa số event producer, lighting designer, và integrator — đặc biệt tại các thị trường mới nổi như Đông Nam Á.

DMX Master LTS lấp đầy khoảng trống đó: **phần mềm cấp độ chuyên nghiệp, giá thành tiếp cận được, chạy trên bất kỳ phần cứng nào từ Raspberry Pi đến máy tính Windows văn phòng.**

---

## 2. Vấn đề thực tế (Problem Statement)

### Thị trường lighting control hiện tại

| Giải pháp | Ưu điểm | Nhược điểm |
|---|---|---|
| GrandMA3 / ETC EOS | Chuẩn công nghiệp, đầy đủ tính năng | $5,000–$50,000+ phần cứng, curve học dốc |
| Resolume Arena | Mạnh về video | Không phải DMX controller chuyên dụng |
| Chamsys MagicQ | Miễn phí bản cơ bản | Phức tạp, UX lỗi thời |
| QLC+ | Open source | Thiếu show recording, binary playback, serial output |
| **DMX Master LTS** | **Cân bằng giữa đủ tính năng và dễ dùng** | Đang phát triển, ecosystem còn nhỏ |

### Pain points cụ thể mà DMX Master giải quyết

1. **Show recording & playback** — Đa số giải pháp miễn phí không có timeline recording + binary playback ổn định
2. **Raspberry Pi deployment** — Event production di động cần thiết bị nhỏ, chi phí thấp
3. **IOBoard integration** — Cầu nối giữa Art-Net (software) và DMX512 vật lý (hardware output) mà không cần converter đắt tiền
4. **Timecode sync** — Đồng bộ với Depence/GrandMA qua Net-Timecode và Art-Net 4 TC
5. **Chi phí** — Một license perpetual thay vì subscription hàng năm

---

## 3. Sản phẩm (Product)

**DMX Master LTS** là phần mềm điều khiển Art-Net chạy trên Windows, Linux và Raspberry Pi, cung cấp đầy đủ vòng lặp DMX:

```
[Phần mềm nguồn]          [DMX Master LTS]            [Phần cứng đầu ra]
Depence / GrandMA  ──►  ArtNet Receive ──► Record      ──► Art-Net UDP
Resolume Arena     ──►  Show Playback  ──► Timeline     ──► IOBoard Serial (DMX512)
Custom Script      ──►  Live Monitor   ──► Web Control  ──► Broadcast 255.255.255.255
```

### Tính năng cốt lõi (v1.3.0)

- **Multi-universe Art-Net** — 4 universes (FREE) đến 512 universes (LICENSED)
- **Binary DMX Recording** — Format `.dmxrec` độc quyền, nén 12× so với JSON, CRC16 validation
- **IOBoard Serial Integration** — DMX512 vật lý qua USB/Serial, auto-mapping, multi-board
- **Timecode Sync** — Art-Net 4 TC + Net-Timecode, tương thích Depence & Resolume
- **Show Management** — Playlist, metadata, binary/JSON auto-detect
- **Web Upload Server** — Upload audio từ bất kỳ thiết bị nào trong mạng LAN
- **License System** — RSA-2048 + hardware binding + AES-256 encryption
- **Raspberry Pi Native** — Build target riêng, tối ưu cho ARM

---

## 4. Đối tượng người dùng (Target Users)

### Segment 1: Event Producer / Live Lighting Operator
- Setup concert, festival, sân khấu quy mô vừa
- Cần: multi-universe, timecode sync, show playback ổn định
- Giải pháp thay thế họ đang dùng: MagicQ, phần mềm built-in của DMX node

### Segment 2: Lighting Integrator / Installer
- Lắp đặt hệ thống ánh sáng cố định: nhà hàng, khách sạn, kiến trúc
- Cần: Raspberry Pi deployment, auto-start, serial DMX output đến fixture
- Giải pháp thay thế: hardware controller $500+

### Segment 3: AV Technician / Show Programmer
- Sync ánh sáng với video (Depence, Resolume)
- Cần: timecode, low-latency Art-Net, nhiều universe
- Giải pháp thay thế: Depence built-in (chỉ trong ecosystem Depence)

### Segment 4: Educator / Student
- Học Art-Net protocol, thực hành DMX512
- Cần: FREE version đủ dùng, tài liệu rõ ràng
- Không có giải pháp thay thế thực sự ở mức giá này

---

## 5. Triết lý kỹ thuật (Technical Philosophy)

### Nguyên tắc thiết kế

**1. Correctness over cleverness**
Implement đúng spec Art-Net 4 trước, optimize sau. Mọi bug trong packet parsing đều dẫn đến ánh sáng nhấp nháy trên sân khấu — không thể chấp nhận.

**2. Offline-first**
License validation, show playback, DMX output — tất cả hoạt động không cần internet. Production environment không thể phụ thuộc vào cloud uptime.

**3. Hardware agnostic, khi có thể**
Cùng codebase chạy trên Windows x64 lẫn Raspberry Pi ARM. Không hardcode platform-specific assumptions.

**4. Binary format là lựa chọn đúng đắn**
JSON đẹp để đọc, nhưng 12× overhead khi ghi 40 FPS × 512 channels × nhiều universe là không thể chấp nhận. `.dmxrec` là binary format với CRC validation, không phải premature optimization.

**5. Security không phải tùy chọn**
Một license system yếu kém phá hủy business model. RSA-2048 + hardware binding + AES-256 là mức tối thiểu chấp nhận được cho phần mềm thương mại.

### Stack lựa chọn

| Layer | Technology | Lý do |
|---|---|---|
| GUI | PyQt6 | Native performance, cross-platform, mature |
| Core | Python 3.13+ | Rapid iteration, ecosystem phong phú |
| Protocol | UDP sockets | Art-Net yêu cầu raw UDP, không qua abstraction |
| Storage | Binary + JSON | Binary cho performance, JSON cho metadata |
| Security | cryptography (RSA/AES) | Thư viện battle-tested, không tự implement crypto |
| Web | Flask | Lightweight, đủ cho upload server |
| Build | PyInstaller | Single-file exe, không yêu cầu Python tại client |

---

## 6. Mô hình kinh doanh (Business Model)

### Freemium với giới hạn kỹ thuật rõ ràng

```
FREE (4 universes)          LICENSED (512 universes)
────────────────────        ────────────────────────
✓ Đủ cho home/studio        ✓ Professional production
✓ Học và thử nghiệm         ✓ Large venue / theater
✓ Evaluation không giới hạn ✓ Multi-IOBoard serial output
✗ > 4 universes             ✓ Full Art-Net spec range
```

**Tại sao Freemium thay vì Trial-then-paywall?**
- User có thể dùng FREE version mãi mãi → giảm friction khi giới thiệu
- Universe limit là giới hạn kỹ thuật thực sự, không phải tính năng bị khóa giả tạo
- Power user tự nhiên upgrade khi vượt 4 universes

**Tại sao Perpetual thay vì Subscription?**
- Người dùng production ghét subscription cho tooling — họ muốn chắc chắn phần mềm sẽ không tắt giữa show
- Perpetual license + free updates trong major version tạo trust
- Subscription phù hợp cho cloud services, không phải desktop software

### Kênh phân phối

1. **GitHub Releases** — Free download, primary channel
2. **Direct contact** — Sales qua email, phù hợp B2B
3. **Word-of-mouth** — Lighting community SEA, Vietnam events industry

---

## 7. Lợi thế cạnh tranh (Competitive Advantage)

### Khác biệt kỹ thuật

1. **`.dmxrec` binary format** — Không có giải pháp cùng phân khúc nào có efficient recording như vậy
2. **IOBoard integration** — Bridge Art-Net → DMX512 physical mà không cần hardware converter riêng
3. **Raspberry Pi native** — Embedded deployment không cần Windows machine
4. **Art-Net 4 TC** — Timecode sync chuẩn spec, không phải workaround

### Khác biệt thị trường

1. **Made in Vietnam, hiểu thị trường SEA** — Pricing, support, documentation tiếng Việt
2. **Solo developer = no overhead, cost advantage** — License price thấp hơn đáng kể so với competitor có đội sales
3. **Perpetual license** — Đây là điểm bán hàng mạnh trong thị trường ngành event

---

## 8. Lộ trình tầm nhìn (Roadmap Vision)

### v1.x LTS — Stability & Professional Features (Hiện tại)
- Hoàn thiện Art-Net 4 full spec compliance
- IOBoard multi-board scale-out
- Show format stability (backward compat guarantee)
- Comprehensive test coverage
- Documentation chuẩn hóa

### v2.x — Scale & Collaboration
- **Multi-adapter binding** — Nhận từ nhiều NIC đồng thời
- **Web dashboard** — Live DMX level monitoring qua WebSocket
- **Show export/import** — Package `.dmxshow` bao gồm audio + DMX + metadata
- **Remote management** — Control nhiều instance từ một master
- **Effect library** — Preset effects với visual editor

### v3.x — Intelligence & Ecosystem
- **AI-assisted effects** — Pattern generation từ music BPM
- **Cloud sync** — Show backup và collaboration
- **Plugin API** — Third-party effect developers
- **RDM support** — Art-Net RDM full implementation
- **Cross-platform mobile** — Remote control app iOS/Android

---

## 9. Về tác giả (About)

**Trương Công Định** là developer độc lập người Việt, xây dựng DMX Master LTS từ đầu với mục tiêu tạo ra công cụ chuyên nghiệp thực sự — không phải toy project, không phải clone của sản phẩm khác.

Dự án phản ánh triết lý: **code tốt không cần team lớn hay budget khủng, chỉ cần kiến trúc đúng và hiểu rõ domain.**

- GitHub: [truongcongdinh97](https://github.com/truongcongdinh97)
- Email: truongcongdinh97tcd@gmail.com
- Project: [DMX-Master](https://github.com/truongcongdinh97/DMX-Master)

---

## 10. Số liệu kỹ thuật tham khảo (Technical Reference)

| Chỉ số | Giá trị |
|---|---|
| Binary frame size | 524 bytes (8+2+512+2) |
| Recording compression | ~12× vs JSON |
| Max universes | 512 (LICENSED) |
| Art-Net port | UDP 6454 |
| IOBoard baud rate | 500,000 baud |
| IOBoard packet size | 517 bytes (5 header + 512 DMX) |
| Timecode sources | Art-Net 4 TC (0x9700), Net-Timecode UDP |
| License security | RSA-2048 + AES-256-GCM + SHA-256 hardware binding |
| Playback FPS (Raspberry Pi) | 60+ FPS stable |
| Network latency | <10ms Art-Net response |

---

*Document này thể hiện tầm nhìn và định hướng chiến lược của dự án DMX Master LTS.*  
*Cập nhật lần cuối: 2026-04-16 — v1.3.0*
