@echo off
echo Lexi Convert - Building Portable Version...
REM PyInstaller를 이용해 폴더 형태의 실행 파일 생성
REM --windowed: 콘솔 창 없이 GUI 모드로 실행
REM --icon: 실행 파일 아이콘 지정
REM --add-data: 추가 데이터 파일 포함 (이미지 등)

pyinstaller --noconfirm --windowed --icon="..\assets\images\Lexi_Convert.png" ^
--add-data "..\assets\images\Lexi_Convert.png;assets\images" ^
--name "Lexi_Convert_Portable" ^
..\main.py

echo Build completed. Check the 'dist\Lexi_Convert_Portable' folder for the portable version.
pause
