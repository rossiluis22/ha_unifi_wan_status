# UniFi WAN Status

A Home Assistant custom component to monitor UniFi WAN status directly from your UniFi Gateway (UDM, UDR, UXG).

## Features

- **Multi-WAN Support**: Automatically detects and monitors all available WAN interfaces (WAN. WAN2, etc.).
- **Real-time Status**: Shows if the WAN connection is Online or Offline.
- **Detailed Attributes**:
  - IP Address, Gateway, DNS, Netmask
  - ISP Name and Organization
  - Connection Type (DHCP, PPPoE, etc.)
  - Link Speed and Duplex status
  - Data usage (RX/TX bytes formatted)
  - Uptime and Latency monitoring

## Installation

### HACS (Recommended)

1. Ensure [HACS](https://hacs.xyz/) is installed.
2. Add this repository as a custom repository in HACS:
   - Go to HACS -> Integrations -> 3 dots (top right) -> Custom repositories.
   - URL: `https://github.com/rossiluis22/unifi-wan-status` (or your repo URL)
   - Category: Integration
3. Click "Add" and then install "UniFi WAN Status".
4. Restart Home Assistant.

### Manual Installation

1. Download the `unifi_wan_status` directory from the `custom_components` folder in this repository.
2. Copy the directory to your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## Configuration

1. Go to **Settings** -> **Devices & Services**.
2. Click **Add Integration**.
3. Search for "UniFi WAN Status".
4. Enter your UniFi Controller details:
   - **Host**: IP address or hostname of your UniFi Gateway/Controller.
   - **Username**: Local credentials (recommended) or Ubiquiti account.
   - **Password**: Password for the user.
   - **Port**: 443 (default).
   - **Verify SSL**: Uncheck if using self-signed certificates (default).

## Sensors

The integration will create one sensor per WAN interface (e.g., `sensor.wan`, `sensor.wan2`).

**State**: `Online` / `Offline`

**Attributes**:
- ISP Name
- IP Address
- Gateway
- Uptime
- Current Throughput (RX/TX)
- ...and more.

## Compatibility

Tested with:
- USG3
