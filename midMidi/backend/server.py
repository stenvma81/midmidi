from fastapi import FastAPI, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import rtmidi
import asyncio
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

####################
# MIDI OUTPUT
####################

midi_out = rtmidi.MidiOut()

print("MIDI OUT PORTS:")
for i, p in enumerate(midi_out.get_ports()):
    print(i, p)

out_ports = midi_out.get_ports()
out_port_env = os.getenv("MIDMIDI_MIDI_OUT_PORT")
if out_port_env is not None:
    midi_out.open_port(int(out_port_env))
elif len(out_ports) > 0:
    midi_out.open_port(0)
else:
    midi_out.open_virtual_port("midmidi-out")


@app.post("/note/{note}")
async def send_note(
    note: int,
    velocity: int = Query(default=100, ge=0, le=127),
):

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

print("MIDI IN PORTS:")
for i, p in enumerate(midi_in.get_ports()):
    print(i, p)

in_ports = midi_in.get_ports()
in_port_env = os.getenv("MIDMIDI_MIDI_IN_PORT")
if in_port_env is not None:
    midi_in.open_port(int(in_port_env))
elif len(in_ports) > 0:
    midi_in.open_port(0)
else:
    midi_in.open_virtual_port("midmidi-in")


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
