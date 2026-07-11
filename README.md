# Groundstation

Groundstation is the receiver/display side of the Ogma system. It is not part of the flight stack itself; it receives telemetry from Ogma and gives the operator a local display. The longer-term plan is for Ogma Console to switch into groundstation mode when this board is connected to a laptop.

## Role In Ogma

- Receives telemetry from the flight stack radio path.
- Displays useful field data locally.
- Provides a future high-detail laptop telemetry view through Ogma Console.

## Current Firmware

Current firmware is CircuitPython code in `firmware/`:

- `code.py`: main display loop.
- `gps_data.py`: GPS data container/parser.
- `screens.py`: ST7789 display screens for GPS/radio status.
- `sx1272.py`: polling SX1272 receive driver.
- `telemetry_protocol.py`: CRC-checked Ogma radio protocol decoder.

The receiver decodes Teachtaire protocol v1, updates the local GPS display, and prints USB serial lines directly consumable by Ogma Console:

- GPS as JSONL.
- CAN as `123#AABBCC...`.
- receiver diagnostics as ignored `#OGMA` comments.

PCB pin map used by firmware: shared SPI, TFT CS/DC/reset `D5/D4/D10`, radio CS/reset `D9/D2`, radio RX/TX switches `A0/A1`.

## Hardware

The repo contains hardware for:

- mobile receiver board,
- SPI display adapter,
- UART adapter.

## Ogma Console Support

Ogma Console can capture mixed GPS/CAN telemetry from the board's CircuitPython USB serial port, decode canonical CAN frames, plot telemetry, and save local bundles. Hardware RF/USB validation remains in the HIL campaign.
