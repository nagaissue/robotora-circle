# ADA031 Robotic Arm PC Control Project - Handover Document

## Project Overview
This project establishes direct PC-based control for the Adeept ADA031 5-DOF robotic arm via USB Serial communication, separate from the original teaching/playback firmware.

---

## Directory Structure
```
Z:\robotry\
├── arduino_pc_control\
│   ├── arduino_pc_control.ino       # Arduino firmware
│   ├── pc_controller.py             # Interactive keyboard controller with TUI
│   ├── pc_controller_example.py     # Simple test script
│   └── requirements.txt             # Python dependencies (pyserial, keyboard)
└── arduino\
    └── ada031_teaching\
        └── ada031_teaching.ino      # Original teaching firmware (reference)
```

---

## Pin Configuration (Arduino)
Defined in `arduino_pc_control.ino`:
- **Base (0)**: Pin D9
- **Shoulder (1)**: Pin D6
- **Elbow (2)**: Pin D5
- **Wrist (3)**: Pin D3
- **Gripper (4)**: Pin D11

---

## Serial Communication Protocol
- **Baud Rate**: 115200
- **Commands**:
  - `M:a1,a2,a3,a4,a5`: Move servos to specified angles (0-180 degrees). Example: `M:90,45,135,90,30`
  - `HOME`: Reset all servos to 90 degrees.
  - `STATUS`: Query current servo angles (returns `STATUS:ANGLES=v1,v2,v3,v4,v5`).

---

## Python Interactive Controller (`pc_controller.py`)
- Uses `COM5` by default at 115200 baud.
- Provides real-time terminal UI (TUI) with visual angle bars, limit warnings (`LIMIT ▼/▲`), and keyboard shortcut handling.

### Keyboard Controls
| Key | Axis / Function | Action |
|     |     |     |
| `A` / `D` | Base | Decrease / Increase angle |
| `W` / `S` | Shoulder | Increase / Decrease angle |
| `Q` / `E` | Elbow | Decrease / Increase angle |
| `R` / `F` | Wrist | Increase / Decrease angle |
| `Z` / `X` | Gripper | Decrease / Increase angle |
| `H` | All | Reset to Home (90°) |
| `+` / `-` | Step | Increase / Decrease step size (1° - 45°) |
| `ESC` | Exit | Quit controller |

---

## Setup & Running Instructions
1. Upload `arduino_pc_control.ino` to the Arduino board using the Arduino IDE (ensure pins and board type match).
2. Install Python dependencies:
   ```bash
   pip install -r Z:\robotry\arduino_pc_control\requirements.txt
   ```
3. Run the interactive controller:
   ```bash
   python Z:\robotry\arduino_pc_control\pc_controller.py
   ```
