#!/data/data/com.termux/files/usr/bin/bash
# Convenient runner script for Termux
if [ "$1" == "--cli" ]; then
    python main.py --cli
else
    python main.py
fi
