#!/bin/bash
echo "Building Linux Executable..."
cd ..
# Using --onefile for single binary
# --windowed might behave differently on Linux without X server, but for GUI it's standard.
# Ensure 'config' folder is bundled if you rely on it default, or user provides it external.
# We bundle it for convenience.
pyinstaller --name JanusTrace --onefile --windowed --add-data "config:config" --hidden-import="colorsys" --hidden-import="PIL" --hidden-import="pandas" --hidden-import="openpyxl" main_gui.py
echo "Build Complete. Check dist/JanusTrace"
