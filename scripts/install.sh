#!/bin/bash
# =============================================================================
# install.sh — Installation Script for Smart Glove Sign Language Translator
# =============================================================================
#
# This script sets up all dependencies and configuration needed to run the
# Smart Glove Sign Language Translator on a Raspberry Pi.
#
# Usage:
#   sudo bash install.sh
#
# What this script does:
#   1. Updates system packages
#   2. Installs system dependencies (Bluetooth, I2C, Python)
#   3. Enables the I2C interface
#   4. Installs Python dependencies from requirements.txt
#   5. Creates project directories
#   6. Tests I2C connection for OLED display
#   7. Prints a setup summary
#
# Prerequisites:
#   - Raspberry Pi running Raspberry Pi OS (Bullseye or later)
#   - Internet connection
#   - Run as root (sudo)
#
# =============================================================================

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REQUIREMENTS_FILE="$PROJECT_DIR/requirements.txt"
OLED_I2C_ADDRESS="0x3c"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# Counters
WARNINGS=0
ERRORS=0

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[ OK ]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ERRORS=$((ERRORS + 1))
}

log_step() {
    echo ""
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}  Step $1: $2${NC}"
    echo -e "${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (sudo)."
        echo "Usage: sudo bash $0"
        exit 1
    fi
}

check_raspberry_pi() {
    if [[ ! -f /proc/device-tree/model ]]; then
        log_warn "Cannot verify Raspberry Pi hardware. Continuing anyway..."
        return
    fi

    local model
    model=$(cat /proc/device-tree/model 2>/dev/null || echo "Unknown")
    log_info "Detected hardware: $model"
}

# -----------------------------------------------------------------------------
# Installation Steps
# -----------------------------------------------------------------------------

step_update_system() {
    log_step "1/6" "Updating System Packages"

    log_info "Updating package lists..."
    apt-get update -qq

    log_info "Upgrading installed packages..."
    apt-get upgrade -y -qq

    log_success "System packages updated."
}

step_install_system_deps() {
    log_step "2/6" "Installing System Dependencies"

    local packages=(
        # Bluetooth
        bluetooth
        bluez
        bluez-tools
        libbluetooth-dev

        # Python
        python3
        python3-pip
        python3-venv
        python3-dev

        # I2C
        i2c-tools
        python3-smbus

        # Serial
        python3-serial

        # Build tools (for compiling Python packages)
        build-essential
        libatlas-base-dev
        libopenblas-dev

        # General utilities
        git
        screen
    )

    log_info "Installing: ${packages[*]}"
    apt-get install -y -qq "${packages[@]}"

    log_success "System dependencies installed."
}

step_enable_i2c() {
    log_step "3/6" "Enabling I2C Interface"

    # Enable I2C in config.txt
    local config_file="/boot/config.txt"
    if [[ -f "/boot/firmware/config.txt" ]]; then
        config_file="/boot/firmware/config.txt"
    fi

    if grep -q "^dtparam=i2c_arm=on" "$config_file" 2>/dev/null; then
        log_success "I2C is already enabled in $config_file."
    else
        log_info "Enabling I2C in $config_file..."
        if grep -q "^#dtparam=i2c_arm" "$config_file" 2>/dev/null; then
            sed -i 's/^#dtparam=i2c_arm.*/dtparam=i2c_arm=on/' "$config_file"
        else
            echo "dtparam=i2c_arm=on" >> "$config_file"
        fi
        log_success "I2C enabled in $config_file."
    fi

    # Ensure I2C kernel modules are loaded
    if ! grep -q "i2c-dev" /etc/modules 2>/dev/null; then
        echo "i2c-dev" >> /etc/modules
        log_info "Added i2c-dev to /etc/modules."
    fi

    # Load module now
    modprobe i2c-dev 2>/dev/null || true

    # Add pi user to i2c group
    if id "pi" &>/dev/null; then
        usermod -aG i2c pi 2>/dev/null || true
        log_success "User 'pi' added to i2c group."
    fi

    log_success "I2C interface configured."
}

step_install_python_deps() {
    log_step "4/6" "Installing Python Dependencies"

    if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
        log_warn "requirements.txt not found at $REQUIREMENTS_FILE"
        log_info "Creating default requirements.txt..."

        cat > "$REQUIREMENTS_FILE" << 'EOF'
# Smart Glove Sign Language Translator — Python Dependencies
# Install with: pip3 install -r requirements.txt

# Machine Learning
scikit-learn>=1.2.0
joblib>=1.2.0

# Data Processing
numpy>=1.24.0
pandas>=1.5.0

# Serial Communication
pyserial>=3.5

# OLED Display
adafruit-circuitpython-ssd1306>=2.12.0
Pillow>=9.0.0

# Hardware (I2C/SPI)
RPi.GPIO>=0.7.0
adafruit-blinka>=8.0.0
board>=1.0

# Utilities
tqdm>=4.64.0
EOF
        log_success "Created requirements.txt."
    fi

    log_info "Installing Python packages..."
    pip3 install --break-system-packages -r "$REQUIREMENTS_FILE" 2>/dev/null \
        || pip3 install -r "$REQUIREMENTS_FILE"

    log_success "Python dependencies installed."

    # Verify critical imports
    log_info "Verifying critical Python packages..."

    local failed_imports=0
    for pkg in sklearn numpy pandas serial; do
        if python3 -c "import $pkg" 2>/dev/null; then
            log_success "  $pkg — importable"
        else
            log_warn "  $pkg — failed to import"
            failed_imports=$((failed_imports + 1))
        fi
    done

    if [[ $failed_imports -gt 0 ]]; then
        log_warn "$failed_imports package(s) could not be imported. Check installation."
    fi
}

step_create_directories() {
    log_step "5/6" "Creating Project Directories"

    local dirs=(
        "$PROJECT_DIR/models"
        "$PROJECT_DIR/dataset/raw"
        "$PROJECT_DIR/dataset/cleaned"
        "$PROJECT_DIR/logs"
    )

    for dir in "${dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_success "Created: $dir"
        else
            log_info "Already exists: $dir"
        fi
    done

    # Set ownership to pi user
    if id "pi" &>/dev/null; then
        chown -R pi:pi "$PROJECT_DIR"
        log_success "Set ownership to pi:pi."
    fi
}

step_test_i2c() {
    log_step "6/6" "Testing I2C Connection (OLED Display)"

    if ! command -v i2cdetect &>/dev/null; then
        log_warn "i2cdetect not found. Skipping I2C test."
        return
    fi

    log_info "Scanning I2C bus 1..."
    echo ""

    local i2c_output
    i2c_output=$(i2cdetect -y 1 2>/dev/null || echo "FAILED")

    if [[ "$i2c_output" == "FAILED" ]]; then
        log_warn "Could not scan I2C bus. Is I2C enabled?"
        echo "Try rebooting and running this script again."
        return
    fi

    echo "$i2c_output"
    echo ""

    # Check for OLED at expected address (0x3c)
    if echo "$i2c_output" | grep -q "3c"; then
        log_success "OLED display detected at address $OLED_I2C_ADDRESS."
    else
        log_warn "OLED display NOT detected at $OLED_I2C_ADDRESS."
        echo "  Possible causes:"
        echo "    1. OLED is not connected."
        echo "    2. Wiring issue (check SDA/SCL connections)."
        echo "    3. OLED uses a different address (check with i2cdetect -y 1)."
        echo "    4. I2C requires a reboot to take effect."
    fi
}

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

print_summary() {
    echo ""
    echo "============================================"
    echo " Installation Summary"
    echo "============================================"
    echo ""

    # Python version
    local py_version
    py_version=$(python3 --version 2>&1)
    echo "  Python:      $py_version"

    # pip version
    local pip_version
    pip_version=$(pip3 --version 2>&1 | awk '{print $2}')
    echo "  pip:         $pip_version"

    # scikit-learn version
    local sklearn_version
    sklearn_version=$(python3 -c "import sklearn; print(sklearn.__version__)" 2>/dev/null || echo "not installed")
    echo "  scikit-learn: $sklearn_version"

    # Bluetooth status
    local bt_status
    bt_status=$(systemctl is-active bluetooth 2>/dev/null || echo "unknown")
    echo "  Bluetooth:   $bt_status"

    # I2C
    local i2c_status="disabled"
    if [[ -e /dev/i2c-1 ]]; then
        i2c_status="enabled"
    fi
    echo "  I2C:         $i2c_status"

    echo ""
    echo "  Project:     $PROJECT_DIR"
    echo "  Warnings:    $WARNINGS"
    echo "  Errors:      $ERRORS"
    echo ""

    if [[ $ERRORS -gt 0 ]]; then
        echo -e "  ${RED}Status: Installation completed with errors.${NC}"
        echo "  Review the warnings/errors above."
    elif [[ $WARNINGS -gt 0 ]]; then
        echo -e "  ${YELLOW}Status: Installation completed with warnings.${NC}"
        echo "  The system should work but review the warnings above."
    else
        echo -e "  ${GREEN}Status: Installation completed successfully!${NC}"
    fi

    echo ""
    echo "  Next steps:"
    echo "    1. Reboot if I2C was just enabled:"
    echo "       sudo reboot"
    echo "    2. Set up Bluetooth:"
    echo "       sudo bash $SCRIPT_DIR/bluetooth_setup.sh"
    echo "    3. Run inference:"
    echo "       cd $PROJECT_DIR/raspberry_pi"
    echo "       python3 inference.py"
    echo ""
    echo "============================================"
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    echo ""
    echo "============================================"
    echo " Smart Glove — Installation Script"
    echo "============================================"
    echo ""
    echo " Project: Sign Language Translator"
    echo " Target:  Raspberry Pi 4"
    echo ""

    check_root
    check_raspberry_pi

    step_update_system
    step_install_system_deps
    step_enable_i2c
    step_install_python_deps
    step_create_directories
    step_test_i2c

    print_summary
}

main "$@"
