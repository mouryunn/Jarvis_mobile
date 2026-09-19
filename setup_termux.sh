#!/data/data/com.termux/files/usr/bin/bash

# ==============================================================================
# JARVIS MOBILE (Mark-LIV) - Automated Setup Script for Android Termux
# ==============================================================================

set -e

echo -e "\033[1;36m"
echo "===================================================================="
echo "    JARVIS MOBILE (MARK-LIV) - TERMUX INSTALLATION & SETUP          "
echo "===================================================================="
echo -e "\033[0m"

# 1. Update Termux Repositories
echo -e "\033[1;33m[*] Updating Termux package repositories...\033[0m"
pkg update -y && pkg upgrade -y

# 2. Install Required Native Packages
echo -e "\033[1;33m[*] Installing system dependencies (Python, Git, Termux-API, ADB, Clang)...\033[0m"
pkg install -y python git termux-api android-tools clang libjpeg-turbo libffi openssl

# 3. Upgrade Pip
echo -e "\033[1;33m[*] Upgrading pip and wheel...\033[0m"
python -m pip install --upgrade pip wheel setuptools

# 4. Install Python Requirements using Pre-built Termux Wheels
echo -e "\033[1;33m[*] Installing Python dependencies (using pre-built Termux wheels)...\033[0m"
pip install --extra-index-url https://termux-user-repository.github.io/pypi/ --extra-index-url https://eutalix.github.io/android-pydantic-core/ -r requirements.txt

# 5. Setup Environment Configuration
if [ ! -f .env ]; then
    echo -e "\033[1;33m[*] Creating .env configuration from template...\033[0m"
    cp .env.example .env
    echo -e "\033[1;32m[+] Created .env file. Please edit .env and set your GEMINI_API_KEY.\033[0m"
fi

# 6. Verify Termux:API Permissions
echo -e "\033[1;33m[*] Verifying Termux:API status...\033[0m"
if command -v termux-battery-status &> /dev/null; then
    echo -e "\033[1;32m[✓] Termux:API commands found.\033[0m"
else
    echo -e "\033[1;31m[!] Termux:API commands not found. Please ensure Termux:API is installed from F-Droid.\033[0m"
fi

# 7. Create launcher executable
chmod +x main.py setup_termux.sh

echo -e "\033[1;36m"
echo "===================================================================="
echo "    INSTALLATION COMPLETE!                                          "
echo "===================================================================="
echo -e "\033[0m"
echo -e "To start the Mobile Web HUD (viewable in your phone's browser):"
echo -e "    \033[1;32mpython main.py\033[0m -> then open \033[1;34mhttp://localhost:8000\033[0m"
echo ""
echo -e "To run directly inside the Termux terminal:"
echo -e "    \033[1;32mpython main.py --cli\033[0m"
echo ""
echo -e "Remember to add your \033[1;33mGEMINI_API_KEY\033[0m in the .env file!"
