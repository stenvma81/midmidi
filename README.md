# midmidi (Prototype)

Experimental **browser-based MIDI controller + monitor** intended to be routed into Ableton Live.

- Backend: **FastAPI** + **python-rtmidi** (MIDI I/O + WebSocket broadcast)
- UI: **Vue 3 + Vite** (clip-style sequencer grid + MIDI monitor)

**Current prototype features**

- Send MIDI notes from the browser
- Sequencer grid (4–64 steps, chromatic note rows)
- Per-step enable/disable and velocity
- Octave transpose (-1 / 0 / +1)
- MIDI monitor (shows recent inbound/outbound messages)
- WebSocket fan-out to all connected clients

---

# Project Structure

```
README.md
midMidi/
    backend/
        server.py
        requirements.txt
        requirements-dev.txt
        pyproject.toml
    midMidi-ui/
        package.json
        vite.config.ts
        src/
            App.vue
```

---

# Requirements

## Software

Required:

- Python 3.10+
- Node.js 18+
- Ableton Live (optional, but the intended target for MIDI routing)

macOS users also need:

- IAC MIDI Driver enabled (see below)

Windows users (if you want “virtual” / network MIDI ports) also need:

- Tobias Erichsen **rtpMIDI** (and Apple **Bonjour** if the installer requests it)

Why: `python-rtmidi` can create virtual ports on macOS/Linux, but on Windows the
default Windows MultiMedia MIDI API does **not** support virtual ports. rtpMIDI
solves this by creating network MIDI “Sessions” that show up as normal MIDI
ports to apps.

---

# Setup

## 1. Clone repository

```bash
git clone <repo-url>
cd midmidi
```

---

# Backend (FastAPI + MIDI)

## 1. Create a virtual environment

```bash
cd midMidi/backend
python -m venv venv
```

Activate it:

- macOS/Linux: `source venv/bin/activate`
- Windows (PowerShell): `venv\Scripts\Activate.ps1`

You should now see:

```
(venv)
```

---

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

Optional (dev tooling):

```bash
pip install -r requirements-dev.txt
```

Notes:

- MIDI port selection is automatic by default (first available port).
- You can override it via env vars:
  - By index: `MIDMIDI_MIDI_OUT_PORT` / `MIDMIDI_MIDI_IN_PORT`
  - By name (substring match): `MIDMIDI_MIDI_OUT_PORT_NAME` / `MIDMIDI_MIDI_IN_PORT_NAME`

---

# UI (Vue + Vite)

Open a new terminal:

```bash
cd midMidi/midMidi-ui
```

Install dependencies:

```bash
npm install
```

---

# macOS MIDI Setup

The prototype uses the **IAC Driver** for virtual MIDI routing.

## Enable IAC Driver

Open:

```
Audio MIDI Setup
```

Then:

```
Window → Show MIDI Studio
```

Double-click:

```
IAC Driver
```

Enable:

```
✓ Device is online
```

Default port:

```
IAC Driver Bus 1
```

---

# Windows MIDI Setup (rtpMIDI)

Install **rtpMIDI** (Tobias Erichsen). If the installer reports Bonjour is
missing, install Apple **Bonjour** first (rtpMIDI uses it for “Zero-Config” peer
discovery on LAN).

Then:

1. Open the rtpMIDI configuration app.
2. In **My Sessions**, click `+` to add a session.
3. Set the session **Local Name** to something recognizable (example: `midmidi`).
4. Check the session’s **Enabled** checkbox.

That Local Name is what most apps (and this backend) will see as the MIDI port.

To force the backend to use that port, set:

- `MIDMIDI_MIDI_OUT_PORT_NAME=midmidi`
- `MIDMIDI_MIDI_IN_PORT_NAME=midmidi`

PowerShell example:

```powershell
$env:MIDMIDI_MIDI_OUT_PORT_NAME = "midmidi"
$env:MIDMIDI_MIDI_IN_PORT_NAME = "midmidi"
```

If you want to connect to a DAW on a different machine, connect peers in rtpMIDI
via **Directory** → select a peer → **Connect** (rtpMIDI will re-connect on
boot).

---

# Ableton Live Setup

Open:

```
Preferences → Link / MIDI
```

Under **Output:**

Enable for the IAC driver:

```
Track ✓
Remote ✓
```

Example:

```
IAC Driver Bus 1
✓ Track
✓ Remote
```

Under **Input:**

Enable:

```
Track ✓
Remote ✓
```

---

# Running the system (dev)

You need **two terminals**.

---

## Terminal 1 — start backend

```bash
cd midMidi/backend
source venv/bin/activate

# default: http://localhost:8000
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

Expected output:

```
MIDI OUT PORTS:
0 IAC Driver Bus 1

MIDI IN PORTS:
0 IAC Driver Bus 1

MIDI listener running
```

---

## Terminal 2 — start UI

```bash
cd midMidi/midMidi-ui
npm run dev
```

Expected output:

```
Local: http://localhost:5173
```

Open in browser: `http://localhost:5173`

Dev proxy behavior:

- UI requests to `/note/...` are proxied to `http://localhost:8000`
- UI WebSockets under `/ws/...` are proxied to `ws://localhost:8000`

---

# Using the interface

## Sequencer grid

1. Set **Steps** to choose the sequence length (4–64)
2. Click a cell in the grid to set a note for that step (columns = steps, rows = notes)
3. Click the active cell again to disable that step
4. Adjust **Velocity** for the selected step
5. Set **Octave** (-1 / 0 / +1) to transpose playback
6. Press **Play** (sends one note every ~300ms)

## MIDI monitor

Toggle the monitor on/off from the UI header.

The monitor displays recent WebSocket messages, including:

- `MIDI IN [...]` (messages received from the selected MIDI input)
- `MIDI OUT [...]` (messages sent by the backend)

---

# Stopping

Stop the backend:

`CTRL+C`

Stop the UI:

`CTRL+C`

Deactivate venv: `deactivate`

---

# API reference (backend)

- `POST /note/{note}`: sends a MIDI note-on then note-off (`velocity` query param optional, default 100; duration currently ~100ms)
- `GET/WS /ws/midi`: WebSocket that receives broadcast text messages

Example:

```bash
curl -X POST http://localhost:8000/note/60
```

WebSocket URL (when connecting directly to backend): `ws://localhost:8000/ws/midi`

---

# Development commands

Backend (from `midMidi/backend`, with venv activated):

```bash
python -m ruff check .
python -m ruff format .
```

UI (from `midMidi/midMidi-ui`):

```bash
npm run lint
npm run format
npm run build
```

---

# Troubleshooting

## No MIDI ports found

If no system MIDI ports exist:

- macOS/Linux: the backend creates virtual ports named `midmidi-out` / `midmidi-in`.
- Windows: virtual ports are not supported by the default Windows MIDI API; use rtpMIDI
  to create an enabled Session and then set `MIDMIDI_MIDI_OUT_PORT_NAME` /
  `MIDMIDI_MIDI_IN_PORT_NAME` to its Local Name.

On macOS, also confirm the IAC Driver is enabled, then restart the backend.

---

## No MIDI messages in monitor

Check Ableton:

```
Preferences → Link/MIDI
```

Ensure IAC Driver has:

```
Track ✓
Remote ✓
```

---

## WebSocket not connecting

Ensure the backend is running on `http://localhost:8000` (the UI dev proxy assumes that), then refresh the browser.
