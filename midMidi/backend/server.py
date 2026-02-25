from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import rtmidi
import asyncio

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
for i,p in enumerate(midi_out.get_ports()):
    print(i,p)

midi_out.open_port(0)


@app.post("/note/{note}")
async def send_note(note:int):

    note_on = [0x90,note,100]
    note_off = [0x80,note,0]

    midi_out.send_message(note_on)

    await asyncio.sleep(0.1)

    midi_out.send_message(note_off)

    return {"ok":True}


####################
# MIDI INPUT
####################

midi_in = rtmidi.MidiIn()

print("MIDI IN PORTS:")
for i,p in enumerate(midi_in.get_ports()):
    print(i,p)

midi_in.open_port(0)


####################
# WebSocket Clients
####################

clients:set[WebSocket] = set()


@app.websocket("/ws/midi")
async def websocket_endpoint(ws:WebSocket):

    await ws.accept()

    print("WebSocket connected")

    clients.add(ws)

    try:
        while True:
            await ws.receive_text()  # keeps connection alive

    except:
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

            message,delta = msg

            text = f"MIDI {message}"

            print(text)

            dead=[]

            for ws in clients:

                try:
                    await ws.send_text(text)

                except:
                    dead.append(ws)

            for d in dead:
                clients.remove(d)

        await asyncio.sleep(0.01)


@app.on_event("startup")
async def startup():

    asyncio.create_task(midi_listener())