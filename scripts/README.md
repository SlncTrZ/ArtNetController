# 🛠️ Build Scripts

Build and deployment scripts for DMX Master.

---

## 📋 Build Scripts

### `build.bat`
Main build script using PyInstaller with complete spec file.
```cmd
scripts\build.bat
```
- Uses `DMXMaster_Complete.spec`
- Creates single-file executable
- Output: `dist/DMXMaster.exe`

---

### `build_installer.bat`
Creates Windows installer using Inno Setup.
```cmd
scripts\build_installer.bat
```
- Requires: [Inno Setup 6.5.4+](https://jrsoftware.org/isdl.php)
- Output: `installer_output/DMXMaster_Setup_v1.0.0.exe`

---

### `build_simple.bat`
Simple build without spec file (for testing).
```cmd
scripts\build_simple.bat
```
- Quick build for development
- May miss dependencies

---

### `build_final.bat`
Build with all hidden imports via command line.
```cmd
scripts\build_final.bat
```
- Alternative to spec file approach
- All dependencies specified inline

---

## 🚀 Deployment Scripts

### `deploy.bat`
Creates deployment package with all necessary files.
```cmd
scripts\deploy.bat
```
- Creates ZIP package
- Includes executable, config, assets
- Output: `DMXMaster_v1.0.0.zip`

---

### `git_push.bat`
Push changes to GitHub repository.
```cmd
scripts\git_push.bat
```
- Adds all changes
- Commits with message
- Pushes to origin/main

---

## 🔧 Installation Scripts

### `install.bat`
Install Python dependencies.
```cmd
scripts\install.bat
```
- Installs from `requirements.txt`
- Upgrades pip

---

## 📝 Usage Notes

**For developers:**
1. Use `build.bat` for production builds
2. Use `build_simple.bat` for quick testing
3. Use `deploy.bat` to create distribution package

**For releases:**
1. Run `build.bat` to create executable
2. Run `build_installer.bat` to create installer
3. Test installer on clean Windows machine
4. Run `git_push.bat` to upload to GitHub

---

## 🔍 Troubleshooting

**Build fails?**
- Check Python version (3.8+)
- Ensure all dependencies installed
- Delete `build/` and `dist/` folders
- Run build again

**Installer fails?**
- Verify Inno Setup installed
- Check `DMXMaster_Installer.iss` path
- Ensure executable exists in `dist/`

**Missing modules in exe?**
- Update `DMXMaster_Complete.spec`
- Add module to `hiddenimports` list
- Rebuild with `build.bat`

---

**Last Updated:** January 2025
