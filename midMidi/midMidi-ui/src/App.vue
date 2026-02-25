<script setup lang="ts">

import { ref,onMounted } from 'vue'

const midiMessages = ref<string[]>([])

let socket:WebSocket

onMounted(()=>{

  socket = new WebSocket("ws://localhost:8000/ws/midi")

  socket.onmessage = (event)=>{

    midiMessages.value.unshift(event.data)

    if(midiMessages.value.length>20){
      midiMessages.value.pop()
    }

  }

  socket.onopen = ()=>{
  console.log("WS connected")
}

  socket.onclose = ()=>{
    console.log("WS closed")
  }

  socket.onerror = (e)=>{
    console.log("WS error",e)
  }

})

const notes = [
  { name: "C", note: 60 },
  { name: "D", note: 62 },
  { name: "E", note: 64 },
  { name: "F", note: 65 },
  { name: "G", note: 67 },
  { name: "A", note: 69 },
  { name: "B", note: 71 },
  { name: "C5", note: 72 }
]

// 8 sequencer steps
const steps = ref<number[]>([
  60,60,60,60,60,60,60,60
])

const selectedStep = ref(0)

const playing = ref(false)

let timer:any = null
let playPosition = ref(0)

const sendNote = async(note:number)=>{

  await fetch(`http://localhost:8000/note/${note}`,{
    method:"POST"
  })

}

const setNoteForStep = (note:number)=>{

  steps.value[selectedStep.value] = note

}

const startSequencer = ()=>{

  if(playing.value) return

  playing.value = true

  timer = setInterval(()=>{

    const note = steps.value[playPosition.value]

    sendNote(note)

    playPosition.value =
      (playPosition.value + 1) % 8

  },300)

}

const stopSequencer = ()=>{

  playing.value = false

  clearInterval(timer)

}

</script>


<template>

<div class="container">

<h1>8 Step Sequencer</h1>

<!-- Sequencer Steps -->

<div class="steps">

<div
v-for="(step,i) in steps"
:key="i"
class="step"
:class="{
selected: selectedStep===i,
playing: playPosition===i && playing
}"
@click="selectedStep=i"
>

{{ step }}

</div>

</div>


<!-- Note Selection -->

<h2>Notes</h2>

<div class="keyboard">

<button
v-for="n in notes"
:key="n.note"
@click="setNoteForStep(n.note)"
>

{{n.name}}

</button>

</div>


<!-- Controls -->

<div class="controls">

<button @click="startSequencer">

Play

</button>


<button @click="stopSequencer">

Pause

</button>

</div>

<h2>MIDI Monitor</h2>

<div class="monitor">

<div
v-for="(msg,i) in midiMessages"
:key="i"
>

{{msg}}

</div>

</div>

</div>

</template>


<style>

.container{
padding:40px;
font-family:sans-serif;
}

.steps{
display:flex;
gap:10px;
margin-bottom:20px;
}

.step{

width:60px;
height:60px;
border:2px solid black;
display:flex;
align-items:center;
justify-content:center;
cursor:pointer;
}

.selected{

background:#ddd;

}

.playing{

background:#66ccff;

}

.keyboard{

display:flex;
gap:10px;
margin-bottom:20px;
}

button{

padding:15px;
font-size:16px;
cursor:pointer;

}

.controls{

display:flex;
gap:10px;

}

.monitor{

margin-top:20px;
padding:10px;

border:1px solid black;

height:200px;
overflow:auto;

font-family:monospace;

}

</style>