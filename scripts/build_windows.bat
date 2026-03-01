@echo off
echo Building Windows Executable...
cd ..
rem Using --onefile to generate a single .exe
rem --noconsole to hide terminal window (for GUI)
rem --hidden-import to ensure CustomTkinter and pandas deps are found
pyinstaller --name JanusTrace --icon=janustrace_icon.ico --onefile --windowed --add-data "config;config" --hidden-import="colorsys" --hidden-import="PIL" --hidden-import="pandas" --hidden-import="openpyxl" main_gui.py
echo Build Complete. Check dist/JanusTrace.exe
