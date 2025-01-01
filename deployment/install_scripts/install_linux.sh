#!/bin/bash

# Installation script for Linux
APP_NAME="TradeLocker"
INSTALL_DIR="/opt/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"

# Check for dependencies
check_dependencies() {
    deps=("python3" "python3-pip" "python3-qt6")
    for dep in "${deps[@]}"; do
        if ! dpkg -l | grep -q "^ii  $dep"; then
            echo "Missing dependency: $dep"
            exit 1
        fi
    done
}

# Create installation directory
create_dirs() {
    sudo mkdir -p "$INSTALL_DIR"
    sudo mkdir -p "$INSTALL_DIR/data"
    sudo mkdir -p "$INSTALL_DIR/logs"
}

# Install application
install_app() {
    sudo cp -r ./* "$INSTALL_DIR/"
    sudo chmod +x "$INSTALL_DIR/trade_locker"
    
    # Create desktop entry
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Trade Locker
Exec=$INSTALL_DIR/trade_locker
Icon=$INSTALL_DIR/icons/app_icon.png
Type=Application
Categories=Finance;
EOF
}

# Main installation process
main() {
    echo "Installing $APP_NAME..."
    check_dependencies
    create_dirs
    install_app
    echo "Installation complete!"
}

main 