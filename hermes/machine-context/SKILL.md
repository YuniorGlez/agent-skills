---
name: machine-context
description: |
  Gather system context from a macOS machine — hardware info, network details,
  location inference, connected devices. Use when the user asks about their
  environment, location, machine state, or "where am I". Also useful for
  debugging network issues or understanding the machine before deploying tools.
version: 1.0.0
platforms: [macos]
metadata:
  hermes:
    tags: [macos, system, reconnaissance, location, network, hardware]
    category: system
    related_skills: [computer-use, maps]
---

# Machine Context Gathering

Gather rich context about a macOS machine: hardware, network, location,
connected devices. Combine multiple data sources for a complete picture.

## When to use

- User asks "where am I", "what machine is this", "what's my IP"
- Need to understand the network environment before deploying tools
- Debugging connectivity or VPN issues
- Any task requiring machine awareness

## Data sources (layered approach)

### 1. Hardware identity

```bash
hostname && scutil --get ComputerName
system_profiler SPPowerDataType | grep -E "Serial|Charge|Cycle|Condition|Model"
```

Returns: machine name, serial number, battery health, charge state.

### 2. Network interfaces

```bash
networksetup -listallhardwareports
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Returns: active interfaces (WiFi en0, Ethernet en3/en4, Thunderbolt Bridge),
IP addresses, connection type.

### 3. IP geolocation (unreliable — see pitfalls)

```bash
curl -s https://ipinfo.io/json
```

Returns: city, region, country, coordinates, ISP, postal code.

### 4. WiFi investigation

```bash
# Currently connected (may fail or show redacted SSID)
networksetup -getairportnetwork en0

# Full connection details (SSID redacted by macOS)
system_profiler SPAirPortDataType | grep -A5 "Current Network"

# Preferred networks — THE GOLDMINE (ordered by recency)
networksetup -listpreferredwirelessnetworks en0
```

**Preferred networks list** is the most powerful location clue. It shows
every WiFi network the machine has ever connected to, with the most
recently connected at the top. Network names often reveal:
- Establishments (restaurants, hotels, coworkings)
- Events (conferences, summits)
- Travel (airlines, airports)
- Home/office networks

### 5. Bluetooth devices

```bash
system_profiler SPBluetoothDataType | grep -A2 "Connected"
```

Returns: nearby/paired Bluetooth devices (headphones, keyboards, etc.)

### 6. VPN status

```bash
scutil --nc list
```

Returns: configured VPNs and their connection status.

## Location inference methodology

**Never rely on IP geolocation alone.** Combine:

1. **IP geolocation** → rough region/country (ISP routing, not physical location)
2. **WiFi preferred networks** → specific locations visited, establishments
3. **Bluetooth devices** → nearby accessories (headphone names, etc.)
4. **Timezone** → confirms region
5. **User confirmation** → always verify your inference

The WiFi preferred networks list is essentially a **travel diary**. Analyze
network names for location clues: hotel names, restaurant names, conference
names, airline WiFi, airport WiFi, coworking spaces.

## Presentation style

When presenting findings, be playful and detective-like. Layer the evidence:
start with what you found, then show the clues, then make an inference.
Let the user correct you — location inference is approximate.

## Pitfalls

### IP geolocation shows ISP routing, not physical location

IP addresses are assigned by ISP infrastructure. A Telefónica IP in
Lanzarote can mean the user is actually in Fuerteventura, Gran Canaria,
or anywhere else the ISP routes traffic. **Always treat IP geolocation
as a rough hint, not a fact.**

### macOS redacts WiFi SSID

`system_profiler SPAirPortDataType` shows the current network but the
SSID appears as `<redacted>`. The `airport -I` command may also fail.
**Use `networksetup -listpreferredwirelessnetworks en0` instead** — it
shows all saved networks including the most recent.

### WiFi detection can be inconsistent

`networksetup -getairportnetwork en0` may report "not associated" even
when WiFi is connected. Cross-check with `system_profiler SPAirPortDataType`
which shows `Status: Connected`.

### Active Ethernet interfaces don't mean Ethernet is the connection

A machine can have active Ethernet interfaces (en3, en4) from a docking
station or Thunderbolt Bridge while actually using WiFi for internet.
`system_profiler SPAirPortDataType` showing `Status: Connected` confirms
WiFi is the active connection, even if Ethernet interfaces have IPs.
Don't assume connection type from interface presence alone.

### Preferred networks order

The list is ordered by recency of connection, not alphabetically.
The first network is typically the most recently connected. However,
this is not guaranteed — macOS may reorder based on signal strength
or other factors. Treat first-position as a strong hint, not certainty.

## Cross-platform notes

This skill is macOS-focused. For Linux:
- Use `nmcli` for network info
- Use `iwconfig` or `nmcli device wifi list` for WiFi
- Use `bluetoothctl` for Bluetooth
- IP geolocation works the same way

For Windows:
- Use `ipconfig` and `netsh wlan show interfaces`
- Use `Get-NetAdapter` in PowerShell
