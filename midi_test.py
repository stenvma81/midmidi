import mido

print("Starting MIDI controller...")

port = mido.open_output('Python MIDI Controller', virtual=True)

print("MIDI port created")
print("Press SPACE + Enter to send note")
print("Press q + Enter to quit")

while True:

    key = input("> ")

    if key == " ":
        print("Sending MIDI note")

        port.send(mido.Message('note_on', note=60, velocity=100))
        port.send(mido.Message('note_off', note=60, velocity=0))

    elif key == "q":
        print("Exiting")
        break
