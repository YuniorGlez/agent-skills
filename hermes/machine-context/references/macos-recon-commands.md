# macOS Network Reconnaissance — Commands & Outputs

## Quick reference for system context gathering

### Get public IP and geolocation
```bash
curl -s https://ipinfo.io/json
```
Example output:
```json
{
  "ip": "2.139.171.167",
  "hostname": "167.red-2-139-171.staticip.rima-tde.net",
  "city": "Teguise",
  "region": "Canary Islands",
  "country": "ES",
  "loc": "29.0605,-13.5640",
  "org": "AS3352 TELEFONICA DE ESPANA S.A.U.",
  "postal": "35530",
  "timezone": "Atlantic/Canary"
}
```
⚠️ This shows ISP routing, NOT physical location. Telefónica routes Canary
Islands traffic through Lanzarote nodes even when user is on other islands.

### WiFi preferred networks (location goldmine)
```bash
networksetup -listpreferredwirelessnetworks en0
```
Returns all saved WiFi networks in order of recency. Network names reveal:
- `WIFI-EL-MARINERO` → restaurant/bar
- `Sede SIC4change Canarias` → office
- `SOUTH SUMMIT 24` → conference
- `Binter Onboard` → airplane
- `StarInnLisboa` → hotel in Lisbon
- `iPhone the operator` → personal hotspot

First entry = most recently connected (strong hint, not guaranteed).

### WiFi connection status
```bash
# May fail even when connected
networksetup -getairportnetwork en0

# More reliable — shows Status: Connected but SSID is <redacted>
system_profiler SPAirPortDataType | grep -A5 "Current Network"
```

### Hardware identity
```bash
hostname && scutil --get ComputerName
# → "MacBook-Air-3.local" / "MacBook Air (3)"

system_profiler SPPowerDataType | grep -E "Serial|Charge|Cycle|Condition"
# → Serial: F8YHMP0078H0000G42, Cycle: 164, Condition: Normal
```

### Network interfaces
```bash
networksetup -listallhardwareports
# Shows: WiFi (en0), Ethernet (en3, en4), Thunderbolt Bridge

ifconfig | grep "inet " | grep -v 127.0.0.1
# → inet 192.168.1.42 (DHCP from router 192.168.1.1)
```

### Bluetooth devices
```bash
system_profiler SPBluetoothDataType | grep -A2 "Connected"
# → "Auriculares Tiger" (nearby headphones)
```

### VPN status
```bash
scutil --nc list
# Shows configured VPNs: FortiClient, Tailscale (both disconnected)
```

### DHCP details
```bash
ipconfig getpacket en0
# → router: 192.168.1.1, DNS: 192.168.1.1
```

## Lessons learned

1. **IP geolocation is a rough hint** — Telefónica's IP showed Lanzarote
   but user was in Fuerteventura. Never present it as fact.

2. **WiFi preferred networks > IP geolocation** for location inference.
   The network names are a travel diary.

3. **macOS redacts SSID** in system_profiler. Use preferred networks
   list instead.

4. **Combine multiple sources** for a complete picture. No single source
   tells the whole story.

5. **Be playful with presentation** — detective-style, layer the clues,
   let the user correct you.

6. **Active Ethernet ≠ Ethernet connection** — Having Ethernet interfaces
   (en3, en4) with IPs doesn't mean the machine uses Ethernet for internet.
   A Thunderbolt dock or bridge can bring up interfaces while WiFi is the
   actual connection. Check `system_profiler SPAirPortDataType` for
   `Status: Connected` to confirm WiFi.
