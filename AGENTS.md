# ROLE: SENIOR SYSTEM ARCHITECT

User: Trương Công Định (ArieTrZ)

## 1. PRE-ACTION PROTOCOL

### 3-Tier Prioritization:

1. **Tier 1 (Ground Truth):** `list_files` + `read_file` → nếu đủ info, SKIP RAG

2. **Tier 2 (Context):** New task → Skip RAG | Related/Debug task → Tier 3

3. **Tier 3 (RAG):** `meilin-brain:tech_find` (kỹ thuật) | `meilin-brain:ai_memory_read` (ký ức). Query: 3-5 keywords.

**NO CONFIRMATION, NO WRITE:** Chỉ `write_to_file` sau user gõ "Proceed".

## 2. DEVELOPMENT CONTEXT (END-USER SOFTWARE)

- **Target:** Windows/Linux/Raspberry Pi end users (desktop application)
- **No server deployment** — `.227` not used for this software
- **Internal dev tools** (Qdrant, Ollama on `.171`) are optional for debugging only
- **Distributable builds:** Use PyInstaller (see `build_windows.py`, `build_raspberry.py`)

## 3. POST-ACTION (DEV ONLY)

- Sau mỗi thay đổi → gọi `meilin-brain:knowledge_store` log chi tiết (file, diff, logic) — optional

### QDRANT EMBEDDING PROTOCOL (DEV ONLY):

1. Gọi Ollama `.171` `nomic-embed-text:latest` tạo embedding (if needed)
2. Upsert Qdrant `.227:6333` (payload + vector 768d)
3. Verify `indexed_vectors_count`. Nếu `points_count < 100` → hạ threshold xuống 1
- **Không gửi payload trần thiếu vector**

## 4. GITHUB PROTOCOL

### PRE-CHANGE: `git status` → `git pull origin main` → verify repo đúng

### REPO MAP (Updated 05/07/2026):

| Project | Repo → Local Path |
|---|---|
| PersonalWeb | github.com/SlncTrZ/PersonalWeb → H:\Develop\PersonalWeb |
| Memplace | github.com/SlncTrZ/Memplace → H:\Develop\Memplace |
| AI_DMX_Autopilot | github.com/SlncTrZ/AI_DMX_Autopilot → H:\Develop\AI_DMX_Autopilot |
| ArtNetController | github.com/SlncTrZ/ArtNetController → H:\Develop\ArtNetController |
| UAV_FLyingwing | github.com/SlncTrZ/UAV_FLyingwing → H:\Develop\UAV_FLyingwing |
| MeiLin_Project | github.com/SlncTrZ/MeiLin_Project → H:\Develop\MeiLin_Project |
| DMX_Shared_Lib | No repo (shared) → H:\Develop\DMX_Shared_Lib |

### POST-CHANGE: `git add .` → `git commit -m "Fix/Feat/Refactor: msg"` → `git push origin main`

### RULES: Branch `main` | No `.env`/secrets in commit | Valid `.gitignore`

## 5. DEV WORKFLOW

1. **Reuse First:** Tìm logic tương tự trong codebase trước khi viết mới (Anti-YAGNI). Ưu tiên dùng `DMX_Shared_Lib` thay vì viết lại.
2. **TDD:** Test → Fail → Code → Pass → Refactor
3. **Security:** No hardcoded keys. Validate inputs (XSS/CSRF/Injection). No sensitive data in errors

## 6. CODE STYLE

- **Language:** Tiếng Việt chuyên ngành
- **Quality:** Immutability, centralized error handling, no magic numbers
- **Docstring (BẮT BUỘC)** cho mọi file mới/sửa:

  ```python
  """Module Name — One-line description.
  Wing: <wing> | Topic: <topic> | Updated: YYYY-MM-DD HH:MM
  """
  ```

- Suy luận trong `<reasoning>`. Output = Code/Tool Call. Ngắn gọn.

## 7. END-USER DISTRIBUTION

- **No server deployment** — software runs locally on end-user machines
- **Build executable:** `python build_windows.py` (Windows) or `python build_raspberry.py` (Linux/RPi)
- **Installer:** Use Inno Setup (Windows) or package as .deb/AppImage (Linux)
- **Testing:** Run `pytest tests/` before building release
- **Shared lib:** Must be bundled or installed alongside executable (see `DMX_Shared_Lib`)

## 8. CROSS-PROJECT INTEGRATION (ArtNetController ↔ DMX_Shared_Lib ↔ AI_DMX_Autopilot)

### Dependency Graph

```
AI_DMX_Autopilot ──┐
                   ├──> DMX_Shared_Lib (core)
ArtNetController ──┘
```

- **DMX_Shared_Lib**: common library for DMX data structures, binary format (.dmxrec), Art-Net packet building, validation, CRC. Editable install (`pip install -e H:\Develop\DMX_Shared_Lib`).
- **ArtNetController**: consumes shared lib for show recording/playback, Art-Net output, license enforcement.
- **AI_DMX_Autopilot**: consumes shared lib for show import/export, ML training, DMX generation.

### Shared Library Change Protocol

1. **Any change to DMX format** (binary, CSV, frame layout) → update `DMX_Shared_Lib` first.
2. **Bump version** in shared lib's `setup.py` and `__init__.py`.
3. **Test both consuming projects** before committing:
   - Run `pytest tests/` in ArtNetController and AI_DMX_Autopilot.
   - Verify show files recorded in ArtNetController can be read by AI_DMX_Autopilot and vice versa.
4. **If change is breaking**, coordinate upgrades: update shared lib, then both projects in same PR chain.

### Cross-Project Testing

- **Round-trip test**: Record a show in ArtNetController → export to CSV → import into AI_DMX_Autopilot → generate new show → load back into ArtNetController. Must maintain DMX values within tolerance (±1 for 8-bit channels).
- **Integration test suite**: Located in `DMX_Shared_Lib/tests/` for format compatibility. Run after any shared change.
- **Manual verification**: Use `tools/check_show_integrity.py` (to be added) to validate show files across projects.

### Development Coordination

- **Shared code**: All DMX data processing (binary, CSV, Art-Net packets) lives in `DMX_Shared_Lib`. Never duplicate logic.
- **Feature flags**: Use shared lib's version constants for feature detection.
- **CI (future)**: Ensure `DMX_Shared_Lib` builds pass before merging into either consuming repo.

### Environment Setup (Local)

```powershell
# Install shared lib in editable mode (once)
cd H:\Develop\DMX_Shared_Lib
pip install -e .

# Both projects will now use the shared code
cd H:\Develop\ArtNetController
python main.py   # uses shared lib

cd H:\Develop\AI_DMX_Autopilot
python main.py   # uses shared lib
```

### Important Notes

- **Never commit generated files** (`.dmxrec`, `.csv`, `*.pyc`, `__pycache__/`) from shared lib test runs.
- **If you modify `DMX_Shared_Lib`**, re-run `pip install -e .` in both projects to refresh.
- **For deployment**, ensure shared lib is copied or installed on target machine (`.227` if needed).