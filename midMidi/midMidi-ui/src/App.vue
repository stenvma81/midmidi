<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount } from 'vue'

type OctaveOffset = -1 | 0 | 1

type Step = {
  enabled: boolean
  noteIndex: number // 0..11 (C..B)
  velocity: number // 0..127
}

const NOTE_NAMES = [
  'C',
  'C#',
  'D',
  'D#',
  'E',
  'F',
  'F#',
  'G',
  'G#',
  'A',
  'A#',
  'B',
]
const BASE_MIDI_C4 = 60

const noteRows = computed(() =>
  NOTE_NAMES.map((name, noteIndex) => ({ name, noteIndex })).reverse(),
)

const clampInt = (
  value: unknown,
  min: number,
  max: number,
  fallback: number,
) => {
  const n = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(n)) return fallback
  return Math.max(min, Math.min(max, Math.round(n)))
}

const createDefaultStep = (): Step => ({
  enabled: true,
  noteIndex: 0,
  velocity: 100,
})

const stepCount = ref(16)
const steps = ref<Step[]>(
  Array.from({ length: stepCount.value }, createDefaultStep),
)

const selectedStep = ref(0)
const octaveOffset = ref<OctaveOffset>(0)

const selectedStepIndex = computed(() => {
  if (steps.value.length === 0) return 0
  return Math.max(0, Math.min(selectedStep.value, steps.value.length - 1))
})

const selectedEnabled = computed({
  get: () => steps.value[selectedStepIndex.value]?.enabled ?? false,
  set: (value: boolean) => {
    const step = steps.value[selectedStepIndex.value]
    if (!step) return
    step.enabled = value
  },
})

const selectedVelocity = computed({
  get: () => steps.value[selectedStepIndex.value]?.velocity ?? 100,
  set: (value: number) => {
    const step = steps.value[selectedStepIndex.value]
    if (!step) return
    step.velocity = clampInt(value, 0, 127, 100)
  },
})

const playing = ref(false)
const playPosition = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const getWsUrl = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/ws/midi`
}

const showMonitor = ref(false)
const midiMessages = ref<string[]>([])
let socket: WebSocket | null = null

const connectMonitor = () => {
  if (socket) return

  socket = new WebSocket(getWsUrl())

  socket.onmessage = (event) => {
    midiMessages.value.unshift(String(event.data))

    if (midiMessages.value.length > 50) {
      midiMessages.value.pop()
    }
  }

  socket.onopen = () => {
    console.log('WS connected')
  }

  socket.onclose = () => {
    console.log('WS closed')
    socket = null
  }

  socket.onerror = (e) => {
    console.log('WS error', e)
  }
}

const disconnectMonitor = () => {
  socket?.close()
  socket = null
}

watch(showMonitor, (show) => {
  if (show) connectMonitor()
  else disconnectMonitor()
})

onBeforeUnmount(() => {
  disconnectMonitor()
  stopSequencer()
})

const resizeSteps = (newCount: number) => {
  const current = steps.value
  const next: Step[] = current.slice(0, newCount)

  while (next.length < newCount) {
    next.push(createDefaultStep())
  }

  steps.value = next

  if (selectedStep.value >= newCount)
    selectedStep.value = Math.max(0, newCount - 1)
  if (playPosition.value >= newCount) playPosition.value = 0
}

watch(stepCount, (raw) => {
  const nextCount = clampInt(raw, 4, 64, 16)
  if (nextCount !== raw) stepCount.value = nextCount
  resizeSteps(nextCount)
})

const midiNoteForStep = (step: Step) => {
  const transpose = 12 * octaveOffset.value
  return BASE_MIDI_C4 + step.noteIndex + transpose
}

const sendNote = async (note: number, velocity: number) => {
  const v = clampInt(velocity, 0, 127, 100)
  await fetch(`/note/${note}?velocity=${v}`, {
    method: 'POST',
  })
}

const toggleCell = (stepIndex: number, noteIndex: number) => {
  selectedStep.value = stepIndex

  const step = steps.value[stepIndex]
  if (!step) return

  if (step.enabled && step.noteIndex === noteIndex) {
    step.enabled = false
    return
  }

  step.noteIndex = noteIndex
  step.enabled = true
}

const startSequencer = () => {
  if (playing.value) return
  if (steps.value.length === 0) return

  playing.value = true

  timer = setInterval(() => {
    const pos = playPosition.value
    const step = steps.value[pos]

    if (step?.enabled) {
      const note = midiNoteForStep(step)
      sendNote(note, step.velocity)
    }

    playPosition.value = (pos + 1) % steps.value.length
  }, 300)
}

const stopSequencer = () => {
  playing.value = false

  if (timer) {
    clearInterval(timer)
    timer = null
  }
}
</script>

<template>
  <div class="app">
    <div class="header">
      <h1>Sequencer</h1>

      <div class="headerActions">
        <button @click="showMonitor = !showMonitor">
          {{ showMonitor ? 'Hide MIDI Monitor' : 'Show MIDI Monitor' }}
        </button>
      </div>
    </div>

    <div class="controls">
      <div class="control">
        <div class="label">Steps</div>
        <div class="row">
          <input
            v-model.number="stepCount"
            type="range"
            min="4"
            max="64"
            step="1"
          />
          <input v-model.number="stepCount" type="number" min="4" max="64" />
        </div>
      </div>

      <div class="control">
        <div class="label">Octave</div>
        <div class="row">
          <button
            :class="{ active: octaveOffset === -1 }"
            @click="octaveOffset = -1"
          >
            -1
          </button>
          <button
            :class="{ active: octaveOffset === 0 }"
            @click="octaveOffset = 0"
          >
            0
          </button>
          <button
            :class="{ active: octaveOffset === 1 }"
            @click="octaveOffset = 1"
          >
            +1
          </button>
        </div>
      </div>

      <div class="control">
        <div class="label">Selected Step</div>
        <div class="row">
          <div class="pill">{{ selectedStepIndex + 1 }}</div>
          <label class="checkbox">
            <input type="checkbox" v-model="selectedEnabled" />
            enabled
          </label>
        </div>
      </div>

      <div class="control">
        <div class="label">Velocity</div>
        <div class="row">
          <input
            v-model.number="selectedVelocity"
            type="range"
            min="0"
            max="127"
            step="1"
          />
          <input
            v-model.number="selectedVelocity"
            type="number"
            min="0"
            max="127"
          />
        </div>
      </div>

      <div class="control">
        <div class="label">Transport</div>
        <div class="row">
          <button @click="startSequencer">Play</button>
          <button @click="stopSequencer">Pause</button>
        </div>
      </div>
    </div>

    <div class="clipWrap" role="application" aria-label="sequencer grid">
      <div
        class="clip"
        :style="{ gridTemplateColumns: `60px repeat(${steps.length}, 26px)` }"
      >
        <div class="corner"></div>

        <div
          v-for="(step, col) in steps"
          :key="`h-${col}`"
          class="colHeader"
          :class="{
            selected: selectedStep === col,
            playing: playing && playPosition === col,
            disabled: !step.enabled,
          }"
          @click="selectedStep = col"
        >
          {{ col + 1 }}
        </div>

        <template v-for="row in noteRows" :key="`r-${row.noteIndex}`">
          <div class="rowLabel">{{ row.name }}</div>

          <button
            v-for="(step, col) in steps"
            :key="`c-${row.noteIndex}-${col}`"
            class="cell"
            :class="{
              active: step.enabled && step.noteIndex === row.noteIndex,
              selected: selectedStep === col,
              playing: playing && playPosition === col,
              disabled: !step.enabled,
            }"
            @click="toggleCell(col, row.noteIndex)"
            :aria-label="`step ${col + 1}, note ${row.name}`"
          />
        </template>
      </div>
    </div>

    <div v-if="showMonitor" class="monitor">
      <div class="monitorHeader">
        <h2>MIDI Monitor</h2>
        <button @click="midiMessages = []">Clear</button>
      </div>

      <div class="monitorBody">
        <div v-for="(msg, i) in midiMessages" :key="i" class="monitorLine">
          {{ msg }}
        </div>
      </div>
    </div>
  </div>
</template>

<style>
.app {
  max-width: 1100px;
  margin: 0 auto;
  text-align: left;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 12px;
}

.headerActions {
  display: flex;
  gap: 8px;
}

.controls {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.control {
  border: 1px solid currentColor;
  padding: 10px;
  border-radius: 8px;
}

.label {
  font-weight: 600;
  margin-bottom: 6px;
}

.row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.row input[type='number'] {
  width: 88px;
}

.pill {
  padding: 6px 10px;
  border: 1px solid currentColor;
  border-radius: 999px;
}

.checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

button.active {
  background: #ddd;
}

.clipWrap {
  overflow-x: auto;
  border: 1px solid currentColor;
  border-radius: 8px;
}

.clip {
  display: grid;
  grid-auto-rows: 26px;
  min-width: max-content;
}

.corner {
  position: sticky;
  left: 0;
  background: inherit;
}

.colHeader {
  display: flex;
  align-items: center;
  justify-content: center;
  border-left: 1px solid currentColor;
  border-bottom: 1px solid currentColor;
  user-select: none;
  cursor: pointer;
}

.rowLabel {
  position: sticky;
  left: 0;
  display: flex;
  align-items: center;
  padding-left: 10px;
  border-top: 1px solid currentColor;
  background: inherit;
}

.cell {
  border-left: 1px solid currentColor;
  border-top: 1px solid currentColor;
  border-radius: 0;
  padding: 0;
  background: transparent;
  min-width: 26px;
}

.cell.active {
  background: #66ccff;
}

.colHeader.playing,
.cell.playing:not(.active) {
  background: #ddd;
}

.colHeader.selected,
.cell.selected {
  outline: 2px solid currentColor;
  outline-offset: -2px;
}

.colHeader.disabled,
.cell.disabled {
  opacity: 0.35;
}

.monitor {
  margin-top: 16px;
  border: 1px solid currentColor;
  border-radius: 8px;
}

.monitorHeader {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  border-bottom: 1px solid currentColor;
}

.monitorHeader h2 {
  margin: 0;
  font-size: 1.1em;
}

.monitorBody {
  max-height: 240px;
  overflow: auto;
  padding: 10px;
  font-family:
    ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono',
    'Courier New', monospace;
}

.monitorLine {
  white-space: pre-wrap;
}

@media (max-width: 720px) {
  .controls {
    grid-template-columns: 1fr;
  }
}
</style>
