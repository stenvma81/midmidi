# midmidi UI

Minimal Vue 3 + Vite frontend for the midmidi prototype.

What it does:

- 8-step sequencer UI (assign note numbers per step)
- Sends notes by calling `POST /note/{note}`
- Displays MIDI monitor messages received from WebSocket `/ws/midi`

## Prereqs

- Node.js 18+

## Run (dev)

```bash
npm install
npm run dev
```

Open: `http://localhost:5173`

## Backend connectivity

In development, Vite proxies requests to the backend:

- HTTP `/note/...` -> `http://localhost:8000`
- WS `/ws/...` -> `ws://localhost:8000`

So the backend is expected to be running at `http://localhost:8000`.

## Useful commands

```bash
npm run lint
npm run format
npm run build
```

## Where to modify UI

- Main UI is in `src/App.vue`
