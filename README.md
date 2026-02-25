# Ableton Collaborative MIDI Controller (Prototype)

This project is an experimental **Ableton Live controller interface** built with:

* **Python + FastAPI** – MIDI bridge and backend
* **Vue + Vite** – Browser-based control interface
* **WebSockets** – Real-time MIDI monitoring
* **python-rtmidi** – MIDI communication

The goal is to develop a **networked collaborative controller** where multiple users can interact with a shared Ableton project.

Current prototype features:

* Send MIDI notes from a web interface
* Simple 8-step sequencer
* Real-time MIDI monitor from Ableton
* FastAPI MIDI bridge
* Browser-based UI

---

# Project Structure

```
midMidi/

server/
    server.py

ui/
    src/
        App.vue
    package.json

.gitignore
README.md
```

---

# Requirements

## Software

Required:

* Python 3.10+
* Node.js 18+
* Ableton Live

macOS users also need:

* IAC MIDI Driver enabled (see below)

---

# Setup

## 1. Clone Repository

```
git clone <repo-url>
cd ableton-controller
```

---

# Python Server Setup

## 1. Create Virtual Environment

```
cd server

python3 -m venv venv
source venv/bin/activate
```

You should now see:

```
(venv)
```

---

## 2. Install Dependencies

```
pip install -r requirements.txt
```

Minimal dependencies:

```
fastapi
uvicorn
python-rtmidi
websockets
```

---

# Vue UI Setup

Open a new terminal:

```
cd ui
```

Install dependencies:

```
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

# Running the System

You need **two terminals**.

---

## Terminal 1 — Start Server

```
cd backend
source venv/bin/activate

uvicorn server:app --reload
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

## Terminal 2 — Start UI

```
cd mimidi-ui

npm run dev
```

Expected output:

```
Local: http://localhost:5173
```

Open in browser:

```
http://localhost:5173
```

---

# Using the Interface

## MIDI Notes

Clicking note buttons sends MIDI notes to Ableton.

---

## Step Sequencer

1. Select a step
2. Click a note
3. Press **Play**

The sequencer will send MIDI notes to Ableton.

---

## MIDI Monitor

The MIDI Monitor shows incoming MIDI messages from Ableton in real time.

Example:

```
MIDI [144, 60, 100]
MIDI [128, 60, 0]
```

---

# Stopping the System

Stop the server:

```
CTRL+C
```

Stop the UI:

```
CTRL+C
```

Deactivate venv:

```
deactivate
```

---

# Troubleshooting

## No MIDI Ports Found

Restart the server after enabling the IAC driver:

```
uvicorn server:app --reload
```

---

## No MIDI Messages in Monitor

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

## WebSocket Not Connecting

Ensure server is running:

```
uvicorn server:app --reload
```

Then refresh the browser.