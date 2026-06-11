#!/bin/bash
# =============================================================================
# bluetooth_setup.sh — Bluetooth Setup Script for Smart Glove
# =============================================================================
#
# This script automates the process of discovering, pairing, and binding the
# SmartGlove ESP32 device to a serial port on the Raspberry Pi.
#
# Usage:
#   sudo bash bluetooth_setup.sh              # Auto-detect SmartGlove
#   sudo bash bluetooth_setup.sh <MAC_ADDR>   # Use a specific MAC address
#   sudo bash bluetooth_setup.sh --scan       # Only scan for devices
#   sudo bash bluetooth_setup.sh --unbind      # Remove existing rfcomm binding
#
# Prerequisites:
#   - Raspberry Pi with Bluetooth support
#   - bluez, bluez-utils, and rfcomm packages installed
#   - Run as root (sudo)
#
# The script will:
#   1. Check for required tools and permissions
#   2. Scan for Bluetooth devices (or use provided MAC address)
#   3. Pair with the SmartGlove ESP32
#   4. Bind the device to /dev/rfcomm0
#   5. Test the serial connection
#
# =============================================================================

set -euo pipefail

# Configuration
DEVICE_NAME="ESP32_GLOVE"
RFCOMM_DEV="/dev/rfcomm0"
RFCOMM_CHANNEL=1
SCAN_TIMEOUT=10
BAUD_RATE=115200
TEST_READ_TIMEOUT=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (sudo)."
        echo "Usage: sudo bash $0 [MAC_ADDRESS]"
        exit 1
    fi
}

check_dependencies() {
    local missing=()

    for cmd in bluetoothctl rfcomm hcitool; do
        if ! command -v "$cmd" &>/dev/null; then
            missing+=("$cmd")
        fi
    done

    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "Missing required commands: ${missing[*]}"
        echo "Install them with:"
        echo "  sudo apt install bluez bluez-tools"
        exit 1
    fi

    log_success "All required tools are available."
}

check_bluetooth_service() {
    if ! systemctl is-active --quiet bluetooth; then
        log_warn "Bluetooth service is not running. Starting it..."
        systemctl start bluetooth
        sleep 2

        if ! systemctl is-active --quiet bluetooth; then
            log_error "Failed to start Bluetooth service."
            exit 1
        fi
    fi
    log_success "Bluetooth service is running."
}

check_bluetooth_adapter() {
    if ! hcitool dev | grep -q "hci0"; then
        log_error "No Bluetooth adapter found. Check your hardware."
        exit 1
    fi

    local adapter_info
    adapter_info=$(hcitool dev | grep "hci0" | awk '{print $2}')
    log_success "Bluetooth adapter found: $adapter_info"
}

# -----------------------------------------------------------------------------
# Core Functions
# -----------------------------------------------------------------------------

scan_devices() {
    log_info "Scanning for Bluetooth devices (${SCAN_TIMEOUT}s)..."
    log_info "Make sure the SmartGlove is powered on and in pairing mode."
    echo ""

    # Enable the adapter and start scanning
    bluetoothctl power on &>/dev/null
    bluetoothctl discoverable on &>/dev/null
    bluetoothctl agent on &>/dev/null

    # Scan and capture output
    local scan_output
    scan_output=$(timeout "$SCAN_TIMEOUT" bluetoothctl scan on 2>/dev/null || true)

    # List discovered devices
    echo "Discovered devices:"
    echo "--------------------------------------------"
    bluetoothctl devices 2>/dev/null | while read -r _ mac name; do
        printf "  %-20s %s\n" "$mac" "$name"
    done
    echo "--------------------------------------------"
    echo ""
}

find_smartglove() {
    local mac
    mac=$(bluetoothctl devices 2>/dev/null | grep -i "$DEVICE_NAME" | awk '{print $2}' | head -n 1)

    if [[ -z "$mac" ]]; then
        return 1
    fi

    echo "$mac"
}

pair_device() {
    local mac="$1"

    log_info "Pairing with device $mac..."

    # Check if already paired
    if bluetoothctl paired-devices 2>/dev/null | grep -q "$mac"; then
        log_success "Device $mac is already paired."
        return 0
    fi

    # Set up agent for automatic pairing
    bluetoothctl agent NoInputNoOutput &>/dev/null || true
    bluetoothctl default-agent &>/dev/null || true

    # Attempt to pair
    if bluetoothctl pair "$mac" 2>/dev/null; then
        log_success "Successfully paired with $mac."
    else
        log_error "Failed to pair with $mac."
        echo "Troubleshooting:"
        echo "  1. Make sure the SmartGlove is in pairing mode."
        echo "  2. Try removing the device first: bluetoothctl remove $mac"
        echo "  3. Power cycle the SmartGlove and try again."
        exit 1
    fi

    # Trust the device for automatic reconnection
    bluetoothctl trust "$mac" &>/dev/null
    log_success "Device $mac is now trusted."
}

unbind_rfcomm() {
    if [[ -e "$RFCOMM_DEV" ]]; then
        log_info "Releasing existing rfcomm binding..."
        rfcomm release 0 2>/dev/null || true
        sleep 1
    fi
}

bind_rfcomm() {
    local mac="$1"

    unbind_rfcomm

    log_info "Binding $mac to $RFCOMM_DEV (channel $RFCOMM_CHANNEL)..."

    if rfcomm bind 0 "$mac" "$RFCOMM_CHANNEL" 2>/dev/null; then
        sleep 1
        if [[ -e "$RFCOMM_DEV" ]]; then
            log_success "Device bound to $RFCOMM_DEV."
        else
            log_error "$RFCOMM_DEV was not created. The binding may have failed."
            exit 1
        fi
    else
        log_error "Failed to bind rfcomm device."
        echo "Try manually: sudo rfcomm bind 0 $mac $RFCOMM_CHANNEL"
        exit 1
    fi
}

test_connection() {
    log_info "Testing serial connection on $RFCOMM_DEV..."
    log_info "Reading data for ${TEST_READ_TIMEOUT} seconds..."
    echo ""

    local line_count=0
    local sample_line=""

    while IFS= read -r -t "$TEST_READ_TIMEOUT" line; do
        line_count=$((line_count + 1))

        if [[ $line_count -eq 1 ]]; then
            sample_line="$line"
        fi

        if [[ $line_count -ge 5 ]]; then
            break
        fi
    done < "$RFCOMM_DEV"

    if [[ $line_count -gt 0 ]]; then
        log_success "Received $line_count lines of data."
        echo ""
        echo "Sample data:"
        echo "  $sample_line"
        echo ""

        # Validate CSV format
        local field_count
        field_count=$(echo "$sample_line" | awk -F',' '{print NF}')
        if [[ "$field_count" -eq 11 ]]; then
            log_success "Data format is correct (11 comma-separated values)."
        else
            log_warn "Unexpected field count: $field_count (expected 11)."
            echo "Expected format: flex1,flex2,flex3,flex4,flex5,ax,ay,az,gx,gy,gz"
        fi
    else
        log_warn "No data received within ${TEST_READ_TIMEOUT} seconds."
        echo "Possible causes:"
        echo "  1. ESP32 is not running the SmartGlove firmware."
        echo "  2. The Bluetooth connection dropped."
        echo "  3. Wrong rfcomm channel (try channel 2 or 3)."
    fi
}

print_summary() {
    local mac="$1"

    echo ""
    echo "============================================"
    echo " Bluetooth Setup Complete"
    echo "============================================"
    echo ""
    echo "  Device:     $DEVICE_NAME"
    echo "  MAC:        $mac"
    echo "  Serial:     $RFCOMM_DEV"
    echo "  Baud Rate:  $BAUD_RATE"
    echo ""
    echo "  To use in Python:"
    echo "    import serial"
    echo "    ser = serial.Serial('$RFCOMM_DEV', $BAUD_RATE, timeout=2)"
    echo "    line = ser.readline().decode('utf-8').strip()"
    echo ""
    echo "  To reconnect after reboot:"
    echo "    sudo rfcomm bind 0 $mac $RFCOMM_CHANNEL"
    echo ""
    echo "  To unbind:"
    echo "    sudo rfcomm release 0"
    echo ""
    echo "============================================"
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    echo ""
    echo "============================================"
    echo " SmartGlove Bluetooth Setup"
    echo "============================================"
    echo ""

    check_root
    check_dependencies
    check_bluetooth_service
    check_bluetooth_adapter

    local mac=""

    # Handle command-line arguments
    case "${1:-}" in
        --scan)
            scan_devices
            echo "To connect, run:"
            echo "  sudo bash $0 <MAC_ADDRESS>"
            exit 0
            ;;
        --unbind)
            unbind_rfcomm
            log_success "rfcomm binding removed."
            exit 0
            ;;
        "")
            # Auto-detect mode
            log_info "Searching for $DEVICE_NAME..."
            scan_devices

            mac=$(find_smartglove || true)
            if [[ -z "$mac" ]]; then
                log_error "Could not find a device named '$DEVICE_NAME'."
                echo ""
                echo "Options:"
                echo "  1. Make sure the SmartGlove is powered on and discoverable."
                echo "  2. Specify the MAC address manually:"
                echo "     sudo bash $0 <MAC_ADDRESS>"
                echo "  3. Scan for all devices:"
                echo "     sudo bash $0 --scan"
                exit 1
            fi

            log_success "Found $DEVICE_NAME at $mac"
            ;;
        *)
            # MAC address provided as argument
            mac="$1"
            # Basic MAC address format validation
            if ! echo "$mac" | grep -qE '^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'; then
                log_error "Invalid MAC address format: $mac"
                echo "Expected format: XX:XX:XX:XX:XX:XX"
                exit 1
            fi
            log_info "Using provided MAC address: $mac"
            ;;
    esac

    # Pair, bind, and test
    pair_device "$mac"
    bind_rfcomm "$mac"
    test_connection
    print_summary "$mac"
}

main "$@"
