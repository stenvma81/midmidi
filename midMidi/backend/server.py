from fastapi import FastAPI, Query, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import rtmidi
import asyncio
import os
import platform

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


IS_WINDOWS = platform.system().lower() == "windows"


def _env_int(name: str) -> int | None:
    value = os.getenv(name)
    if value is None or value == "":
        return None
    try:
        return int(value)
    except ValueError:
        print(f"Invalid {name}={value!r}; expected integer")
        return None


def _env_str(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _open_port_by_name(midi: rtmidi.MidiBase, name: str) -> bool:
    ports = midi.get_ports()
    name_lower = name.lower()
    for i, port_name in enumerate(ports):
        if name_lower in port_name.lower():
            midi.open_port(i)
            return True
    return False


def _open_port_auto(
    midi: rtmidi.MidiBase,
    *,
    direction: str,
    virtual_port_name: str,
) -> bool:
    ports = midi.get_ports()

    env_index = _env_int(f"MIDMIDI_MIDI_{direction}_PORT")
    env_name = _env_str(f"MIDMIDI_MIDI_{direction}_PORT_NAME")

    if env_name is not None:
        if _open_port_by_name(midi, env_name):
            return True
        print(
            f"MIDI {direction}: no port matched "
            f"MIDMIDI_MIDI_{direction}_PORT_NAME={env_name!r}"
        )

    if env_index is not None:
        try:
            midi.open_port(env_index)
            return True
        except Exception as exc:
            print(f"MIDI {direction}: failed to open port index {env_index}: {exc}")

    if IS_WINDOWS:
        # Prefer rtpMIDI session ports if present.
        for preferred in ("rtpmidi", "midmidi"):
            if _open_port_by_name(midi, preferred):
                return True

    if len(ports) > 0:
        midi.open_port(0)
        return True

    # On macOS/Linux, we can create a virtual port for local routing.
    if not IS_WINDOWS:
        try:
            midi.open_virtual_port(virtual_port_name)
            return True
        except NotImplementedError:
            pass

    if IS_WINDOWS:
        print(
            f"MIDI {direction}: no local ports available. "
            f"On Windows, create/activate an rtpMIDI session "
            f"(Tobias Erichsen rtpMIDI) and then set "
            f"MIDMIDI_MIDI_{direction}_PORT_NAME to its Local Name."
        )
    else:
        print(f"MIDI {direction}: no ports available")

    return False


####################
# MIDI OUTPUT
####################

midi_out = rtmidi.MidiOut()
midi_out_ready = False

print("MIDI OUT PORTS:")
for i, p in enumerate(midi_out.get_ports()):
    print(i, p)
midi_out_ready = _open_port_auto(
    midi_out,
    direction="OUT",
    virtual_port_name="midmidi-out",
)


@app.post("/note/{note}")
async def send_note(
    note: int,
    velocity: int = Query(default=100, ge=0, le=127),
):

    if not midi_out_ready:
        raise HTTPException(status_code=503, detail="MIDI output not available")

    note_on = [0x90, note, velocity]
    note_off = [0x80, note, 0]

    midi_out.send_message(note_on)

    await broadcast(f"MIDI OUT {note_on}")

    await asyncio.sleep(0.1)

    midi_out.send_message(note_off)

    await broadcast(f"MIDI OUT {note_off}")

    return {"ok": True}


####################
# MIDI INPUT
####################

midi_in = rtmidi.MidiIn()
midi_in_ready = False

print("MIDI IN PORTS:")
for i, p in enumerate(midi_in.get_ports()):
    print(i, p)
midi_in_ready = _open_port_auto(
    midi_in,
    direction="IN",
    virtual_port_name="midmidi-in",
)


####################
# WebSocket Clients
####################

clients: set[WebSocket] = set()


async def broadcast(text: str) -> None:

    dead: list[WebSocket] = []

    for ws in clients:
        try:
            await ws.send_text(text)

        except Exception:
            dead.append(ws)

    for d in dead:
        clients.remove(d)


@app.websocket("/ws/midi")
async def websocket_endpoint(ws: WebSocket):

    await ws.accept()

    print("WebSocket connected")

    clients.add(ws)

    try:
        while True:
            await ws.receive_text()  # keeps connection alive

    except Exception:
        pass

    finally:
        print("WebSocket disconnected")

        clients.remove(ws)


####################
# MIDI Listener
####################


async def midi_listener():

    print("MIDI listener running")

    while True:
        if not midi_in_ready:
            await asyncio.sleep(1.0)
            continue

        msg = midi_in.get_message()

        if msg:
            message, delta = msg

            text = f"MIDI IN {message}"

            print(text)

            await broadcast(text)

        await asyncio.sleep(0.01)


@app.on_event("startup")
async def startup():

    asyncio.create_task(midi_listener())
