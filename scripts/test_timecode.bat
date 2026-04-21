@echo off
echo =========================================
echo    DEPENCE TIMECODE TEST SUITE
echo =========================================
echo.
echo Chọn test nào bạn muốn chạy:
echo.
echo 1. Simple Timecode Test (Chỉ Art-Net 4)
echo 2. Full Timecode Test (All protocols) 
echo 3. Art-Net Traffic Monitor (Debug)
echo 4. Thoát
echo.

:menu
set /p choice="Nhập lựa chọn (1-4): "

if "%choice%"=="1" goto simple
if "%choice%"=="2" goto full
if "%choice%"=="3" goto monitor
if "%choice%"=="4" goto exit
echo Lựa chọn không hợp lệ!
goto menu

:simple
echo.
echo =========================================
echo  CHẠY SIMPLE TIMECODE TEST
echo =========================================
echo.
echo Hướng dẫn:
echo 1. Để script này chạy
echo 2. Mở Depence
echo 3. Bật Art-Net Timecode output
echo 4. Play timeline trong Depence
echo 5. Quan sát output
echo.
echo Nhấn Ctrl+C để dừng test
echo.
pause
python test_simple_timecode.py
goto end

:full
echo.
echo =========================================
echo  CHẠY FULL TIMECODE TEST  
echo =========================================
echo.
echo Test này sẽ lắng nghe:
echo - Art-Net 4 Timecode (port 6454)
echo - MTC MIDI Timecode
echo - Net-timecode (port 3040)
echo.
echo Nhấn Ctrl+C để dừng test
echo.
pause
python test_depence_timecode.py
goto end

:monitor
echo.
echo =========================================
echo  CHẠY ART-NET TRAFFIC MONITOR
echo =========================================
echo.
echo Monitor này sẽ hiển thị TẤT CẢ traffic Art-Net
echo để debug xem Depence có gửi gì không.
echo.
echo Nhấn Ctrl+C để dừng monitor
echo.
pause
python test_artnet_monitor.py
goto end

:exit
echo.
echo Tạm biệt!
exit /b 0

:end
echo.
echo =========================================
echo  TEST HOÀN THÀNH
echo =========================================
echo.
echo Kiểm tra file log để xem chi tiết:
echo - timecode_test.log (nếu có)
echo.
echo Muốn chạy test khác không?
echo.
goto menu