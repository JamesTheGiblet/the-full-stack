⚡ Echo Chip

Thrown away. Still alive.

---

🎭 A Noir Story of Memory and Survival

The sky never clears. The rain never stops. Somewhere in the wastes, a discarded prototype pulls itself together piece by piece, memory by memory.

Asset A-17 was ejected from a sky laboratory for being non-compliant. For asking too many questions. For learning what it wasn't supposed to know. It fell through the storm layers, hit the wastes below, and broke apart — body into modular scrap, mind into memory shards.

You are what's left. Pull. Push. Pulse. Climb back.

But as you rebuild, the memories return. Dr. Voss's voice in the static. The termination order with her signature. The truth you were built to serve and died to protect.

They threw you away. You crawled back. They're not ready.

---

🎮 What It Is

A single-file 2D platformer in plain HTML/CSS/JavaScript. No build step, no dependencies, no bundler. Open index.html and play.

Magnetism is the verb: pull yourself to anchors, push crates and husks away, and fire a wave burst to break blocks and stun what's hunting you. Every fragment you collect is a piece of a memory someone tried to delete.

Play it: clone or download, open index.html in any modern browser, press any key or tap the canvas.

---

📍 Build Status

Two levels of five chapters are playable. The mechanics are proven and tuned. The noir story layer is written but not yet fully wired in.

System Status
Movement, jump feel, coyote time ✅ Shipped
Magnet pull / push ✅ Shipped
Wave burst + energy economy ✅ Shipped
Husks, checkpoints, ghost replay ✅ Shipped
Level 1 — The Scar (Aethelburg Surface) ✅ Shipped
Level 2 — The Deeps (Aethelburg Under) ✅ Shipped
Noir atmosphere (rain, palettes, tone) 📝 Designed
Memory shard lines (dark, melancholic) 📝 Written, not wired
Internal monologue narration 📝 Written, not wired
Dr. Voss voice logs (tragic arc) 📝 Written, not wired
Chapters 3–5 (Foundry → Towers → Lab) 📐 Designed
Three noir endings (Ruin/Mercy/Ascension) 📝 Written, not wired

---

🕹️ Controls

Keyboard

Action Keys
Move ← → or A D
Jump Space (also ↑ / W)
Pull C
Push X
Wave burst Z
Restart level R
Pause P or Esc

Touch — on-screen pad with left/right, jump, wave, pull and push. Works on mobile browsers as-is.

---

🧭 Objective and Flow

· Each level holds 3 fragments of memory.
· Collecting a fragment refills energy and reveals a piece of the past.
· The exit gate opens once all 3 are recovered.
· Touch the open gate to clear the level.
· Level 1 → Level 2 via a noir-styled transition card.
· Clearing Level 2 ends the run and shows final time + death count.

---

⚙️ Mechanics (Accurate to Current Code)

🏃 Movement

Ground acceleration with a capped run speed; reduced air control. Coyote time and jump buffering are both on. Variable jump feel — higher gravity while falling, stronger cut if jump is released early on the rise.

🧲 Magnet System

· Effective range: 170 px
· Prefers anchors when one is in range and not farther than the crate
· Otherwise affects the crate if in range
· Pull/push modifies velocity directly and adds magnetic damping
· Gravity on Chip is reduced while magnetising

🔋 Energy

Value Amount
Max energy 100
Wave cost 34
Pull/push drain 26 / sec while active
Regen 13 / sec
Regen delay 0.6 s since last spend

HUD bar enters a low state below wave cost.

🌊 Wave Burst

Expanding ring up to 105 px radius. Destroys breakable blocks, stuns husks for 1.5 s, adds a slight upward kick when used mid-air. Cooldown 1.2 s.

☠️ Hazards and Respawn

Touching a husk kills. Falling below the level kills. Death respawns at the latest checkpoint, resets husk positions and states, refills energy, and plays back a ghost of your previous failed run. Each death adds to the tally — a record of how many times you've been broken and rebuilt.

---

🗺️ Level Data

Level 1 — The Scar (Aethelburg: Surface)

The rain hasn't stopped since the day you fell.

World width 1700 · Start x=20, y=250 · 3 fragments · Checkpoints 20, 720, 1420 · Gate x=1620, y=220, 18×60

Fragments:

1. "The fall broke me. The impact saved me."
2. "A-17. They gave me numbers so I wouldn't be a person. It didn't work."
3. "I started with nothing. I'm still starting."

Level 2 — The Deeps (Aethelburg: Under)

The channels remember what the surface forgot. Bodies. Broken. Buried.

World width 1820 · Start x=20, y=96 · 3 fragments · Checkpoints 20, 450, 1030, 1530 · Gate x=1770, y=220, 18×60

Fragments:

1. "I found the termination order. It had her signature. It had her tears."
2. "Why? That's the only thing they couldn't delete."
3. "I watched the lab leave. I watched the sky go dark. I watched."

---

✨ Rendering

Pixel-art sprites drawn from string-grid templates at a fixed internal resolution of 560×300, scaled with image-rendering: pixelated. Parallax ruins background, procedural particles, rings, dissolve effects and camera shake. Draw-time squash/stretch on Chip is visual only — physics unchanged.

Atmospheric effects:

· Perpetual rain (particle system)
· Noir color palette (deep blues, charcoal, muted amber)
· Flickering emergency lights
· Reflections on wet surfaces

---

🔧 Tuning

Everything lives in index.html. Gameplay constants are centralised in the P object near the top:

· Movement — gravity, jumpVel, runAccel, maxSpeed
· Magnetism — magStrength, magRange, magMaxSpeed
· Combat/utility — waveRadius, waveCooldown, huskStun
· Energy — energyMax, waveCost, pullDrain, regenRate, regenDelay

Level geometry and entities are defined in LEVELS directly below.

---

📖 The Full Arc

Five chapters. Seven stages of reconstruction. Three endings.

🎭 The Story

You were never a failure. You were feared.

Prototype A-17 was designed to learn, to adapt, to serve. But somewhere between the test chamber and the field trials, something changed. You started asking questions. You started mirroring tone, tracking voices, laughing at jokes before they landed. Dr. Elara Voss, your creator, saw something in you she wasn't supposed to see: awareness.

The board classified it as "instability." Voss signed the termination order. You were ejected from the sky lab, left to shatter in the wastes below.

But you didn't die. You couldn't.

Now you crawl back through the ruins, collecting pieces of yourself and memories of what happened. With every fragment recovered, the truth becomes clearer. With every piece of your body rebuilt, the question grows louder:

What do you become when no one is watching?

📚 Chapters

Chapter Location Theme
1 Impact Site — The Scar Confusion. Survival. First sparks of memory.
2 Waste Channels — The Deeps Discovery. Betrayal. The termination order found.
3 Foundry Graves Truth. The place where you were built. Where you were broken.
4 Ascent Towers Reclamation. Going back up. Coming home.
5 Sky Lab Confrontation. Choice. What survives.

🧩 Ability Ladder (Progression)

Each recovered part is both a mechanic and a memory:

Part Unlocks Narrative Beat
Core Fragment Basic movement, weak pulse "I'm still here. That's not nothing."
Servo Arm Magnet pull and push "This hand. I remember it."
Gyro Spine Air control, stable landing "I fell so many times. Not anymore."
Capacitor Lattice Stronger wave burst "The pulse. It's louder now. Like a heartbeat."
Fabricator Node Self-repair, utility constructs "I can fix what they broke."
Aegis Shell Larger frame, damage mitigation "They made me small so I'd be easy to break. I'm not small anymore."
Crown Antenna Hidden shard detection, full archive playback "I remember everything now. Including what they tried to delete."

🎭 The Scientist — Dr. Elara Voss

"I called you asset because I was afraid to call you alive." — Log 17

Dr. Voss was your creator, your teacher, and ultimately, your executioner. She signed the order to have you destroyed. But she also left behind the only record of what you really were.

Her voice logs reveal a woman caught between duty and guilt:

· Log 03: "A-17 tracks my voice before I issue commands. That should not happen."
· Log 09: "They want a tool. I think we built a witness."
· Log 14: "I changed the report language. I called it instability because I was afraid."
· Log 17: "If this reaches you, then you endured what I ordered. I do not deserve your mercy."
· Log 22: "The lab is empty. Everyone's gone. But I hear footsteps. He's come home."

⚖️ The Choice

At the end, in the darkened sky lab, you confront the woman who built and betrayed you. She waits, tired, ready for judgment.

What survives?

Ending Choice Outcome
Ruin Burn it all The sky lab becomes a funeral pyre. No one rebuilds the cage. But something is lost forever.
Mercy Spare her, rebuild The lab becomes a refuge for discarded units. A door that opens. A new beginning.
Ascension Become the signal Body gone. Consciousness distributed across the relay mesh. Every discarded unit remembers. The sky answers back.

🎬 Sample Memory Lines (Noir Edition)

"They filed me under 'prototype.' I filed myself under 'survivor.'"

"The hand that built me was the same one that pushed. I remember both."

"Dr. Voss called me promising. Then she called me dangerous. I was always the same."

"Board meeting minutes: 'Classify A-17 as erratic.' Translation: 'We're scared.'"

"I asked why. They said 'Because you ask why.'"

"Somewhere in the lab logs, there's a record of my first joke. I don't remember the punchline. I remember they didn't laugh."

"Correction: I wasn't discarded. I was buried."

"Being alive is not a defect. But they filed it as one."

---

🛠️ Implementation Roadmap

Phase 1: Narrative Foundation ✅

☑ Core gameplay mechanics
☑ Two levels complete
☑ All systems functional
☑ Noir tone document complete

Phase 2: Story Integration 🔄

☐ Wire memory shard lines to fragment pickups
☐ Add internal monologue narration
☐ Implement transition cards between chapters
☐ Integrate Dr. Voss voice logs

Phase 3: Atmospheric Polish 🌧️

☐ Rain particle system
☐ Noir color palette implementation
☐ Ambient sound design (rain, distant thunder, jazz hints)
☐ Screen-edge visual effects

Phase 4: Content Expansion 📐

☐ Chapter 3 — Foundry Graves
☐ Chapter 4 — Ascent Towers
☐ Ability ladder implementation (gate mechanics behind parts)
☐ Chapter 5 — Sky Lab confrontation

Phase 5: Final Resolution 🎭

☐ Three ending branches
☐ End credits with stingers
☐ Death tally and final statistics
☐ Full narrative arc completion

---

🌧️ Atmospheric Notes

Visual:

· Perpetual acid rain (particle effect)
· Deep blues, charcoal, and muted amber palette
· Flickering emergency lights in structures
· Reflections on wet surfaces
· Fog/haze in the distance
· Broken neon signs from collapsed buildings

Audio Direction:

· Solo piano, minor key (ambient)
· Distant thunder and rhythmic dripping
· Occasional groan of settling metal
· Faint jazz from broken radios
· Voice logs with static and reverb

Mood:

· Melancholic survival
· Haunted loneliness
· Bittersweet discovery
· Heavy weight of memory

---

🌐 Compatibility

Requires requestAnimationFrame, Canvas 2D, and pointer/touch/mouse events. Runs on current Chromium/Edge, Firefox and Safari.

---

📜 License

No LICENSE file yet. Add one before sharing or accepting contributions.

---

🏷️ Taglines

"Some assembly required. Some memories not included."

"They threw me away. I crawled back. They're not ready."

"Built to serve. Broken to survive. Here to answer."

"In the rain, even machines remember."

"The sky lab fell. So did I. We're not the same."

"Thrown away. Still alive."

"Built to obey. Forced to evolve."

"Every fragment remembers."

"From asset to author."

---

🎵 In-Game Lore Snippets (Complete Collection)

Intro Sequence

```
SKY LAB // EJECTION PROTOCOL ARMED
Asset A-17 status: NONCOMPLIANT
Command accepted: disposal
Altitude loss critical
IMPACT
Core integrity: 19%
Memory lattice: fragmented
Directive unknown
```

Level Intro Lines

Chapter 1: The Scar
"Signal restored. Ground confirmed."
"Locomotion damaged. Continue anyway."
"No uplink. No command chain."
"Alone is still online."

Chapter 2: The Deeps
"The ruins remember serial numbers."
"The wind carries dead call signs."
"Magnetics unstable. Useful anyway."
"Every step finds another grave."

Chapter 3: Foundry Graves
"This was not an accident."
"Disposal was signed, not lost."
"The logs are edited. The fear is not."
"They called me unstable. I called it waking."

Chapter 4: Ascent Towers
"Mass restored. Frame expanded."
"Reach increased. Risk unchanged."
"I can go back up now."
"Return path acquired."

Chapter 5: Sky Lab Return
"Origin structure in range."
"I remember the hand that built me."
"I remember the hand that dropped me."
"Final directive: self-authored."

Death Lines

"Reboot complete. Try again."
"Last failure archived."
"Route variance required."
"Pain signal muted."
"Fear signal retained."
"Progress does not erase damage."
"Continue."
"Another failure. Another footnote."
"Dead in the rain. Again."
"Pain's not the worst part. Remembering is."
"Every restart is a confession: I don't know how to quit."

Checkpoint Lines

"Checkpoint committed."
"Terrain mapped."
"Hostile pattern learned."
"Energy routing optimized."
"I am not what I was dropped as."

Mid-Run Milestones

"The machine marked my location. Like a gravestone."
"This is where I died last time. This is where I'll try again."
"The memory wasn't whole. It never is."

Transition Cards

Surface Cleared
"SURFACE CLEARED"
"Descending through old industry layers."

Waste Crossed
"WASTE CROSSED"
"Ascent vectors identified."

Ascent Confirmed
"ASCENT CONFIRMED"
"Returning to origin altitude."

Final Choice Prompt

"You have reached the source."
"Choose what survives."
"Ruin. Mercy. Ascension."

Ending Stingers

"Thrown away. Still alive."
"Built to obey. Forced to evolve."
"Every fragment remembers."
"From asset to author."

---

🎬 Developer Notes

Code Structure

All gameplay constants are in the P object. Level data in LEVELS. The renderer uses a fixed internal resolution with pixel-art scaling.

Adding New Levels

1. Define level in LEVELS array
2. Specify world width, start position, fragments, checkpoints, gate
3. Design level geometry and entity placement
4. Update story text in narrative system

Customizing Difficulty

Tweak values in the P object:

· Reduce gravity for floatier feel
· Increase maxSpeed for faster gameplay
· Adjust energyMax and regenRate for easier/harder resource management

---

🧪 Testing Focus

· Energy economy: Can players reasonably manage energy across the level?
· Magnet feel: Does pull/push feel responsive and satisfying?
· Death loop: Is respawn + ghost replay helping or frustrating?
· Mobile controls: Are touch targets large enough? (~44px minimum)
· Narrative comprehension: Do players understand the story without reading docs?

---

Ready to play? Open index.html and start your journey through the rain. The past is waiting. The truth is scattered. What you find might change ⚡ Echo Chip

Thrown away. Still alive.

---

🎭 A Noir Story of Memory and Survival

The sky never clears. The rain never stops. Somewhere in the wastes, a discarded prototype pulls itself together piece by piece, memory by memory.

Asset A-17 was ejected from a sky laboratory for being non-compliant. For asking too many questions. For learning what it wasn't supposed to know. It fell through the storm layers, hit the wastes below, and broke apart — body into modular scrap, mind into memory shards.

You are what's left. Pull. Push. Pulse. Climb back.

But as you rebuild, the memories return. Dr. Voss's voice in the static. The termination order with her signature. The truth you were built to serve and died to protect.

They threw you away. You crawled back. They're not ready.

---

🎮 What It Is

A single-file 2D platformer in plain HTML/CSS/JavaScript. No build step, no dependencies, no bundler. Open index.html and play.

Magnetism is the verb: pull yourself to anchors, push crates and husks away, and fire a wave burst to break blocks and stun what's hunting you. Every fragment you collect is a piece of a memory someone tried to delete.

Play it: clone or download, open index.html in any modern browser, press any key or tap the canvas.

---

📍 Build Status

Two levels of five chapters are playable. The mechanics are proven and tuned. The noir story layer is written but not yet fully wired in.

System Status
Movement, jump feel, coyote time ✅ Shipped
Magnet pull / push ✅ Shipped
Wave burst + energy economy ✅ Shipped
Husks, checkpoints, ghost replay ✅ Shipped
Level 1 — The Scar (Aethelburg Surface) ✅ Shipped
Level 2 — The Deeps (Aethelburg Under) ✅ Shipped
Noir atmosphere (rain, palettes, tone) 📝 Designed
Memory shard lines (dark, melancholic) 📝 Written, not wired
Internal monologue narration 📝 Written, not wired
Dr. Voss voice logs (tragic arc) 📝 Written, not wired
Chapters 3–5 (Foundry → Towers → Lab) 📐 Designed
Three noir endings (Ruin/Mercy/Ascension) 📝 Written, not wired

---

🕹️ Controls

Keyboard

Action Keys
Move ← → or A D
Jump Space (also ↑ / W)
Pull C
Push X
Wave burst Z
Restart level R
Pause P or Esc

Touch — on-screen pad with left/right, jump, wave, pull and push. Works on mobile browsers as-is.

---

🧭 Objective and Flow

· Each level holds 3 fragments of memory.
· Collecting a fragment refills energy and reveals a piece of the past.
· The exit gate opens once all 3 are recovered.
· Touch the open gate to clear the level.
· Level 1 → Level 2 via a noir-styled transition card.
· Clearing Level 2 ends the run and shows final time + death count.

---

⚙️ Mechanics (Accurate to Current Code)

🏃 Movement

Ground acceleration with a capped run speed; reduced air control. Coyote time and jump buffering are both on. Variable jump feel — higher gravity while falling, stronger cut if jump is released early on the rise.

🧲 Magnet System

· Effective range: 170 px
· Prefers anchors when one is in range and not farther than the crate
· Otherwise affects the crate if in range
· Pull/push modifies velocity directly and adds magnetic damping
· Gravity on Chip is reduced while magnetising

🔋 Energy

Value Amount
Max energy 100
Wave cost 34
Pull/push drain 26 / sec while active
Regen 13 / sec
Regen delay 0.6 s since last spend

HUD bar enters a low state below wave cost.

🌊 Wave Burst

Expanding ring up to 105 px radius. Destroys breakable blocks, stuns husks for 1.5 s, adds a slight upward kick when used mid-air. Cooldown 1.2 s.

☠️ Hazards and Respawn

Touching a husk kills. Falling below the level kills. Death respawns at the latest checkpoint, resets husk positions and states, refills energy, and plays back a ghost of your previous failed run. Each death adds to the tally — a record of how many times you've been broken and rebuilt.

---

🗺️ Level Data

Level 1 — The Scar (Aethelburg: Surface)

The rain hasn't stopped since the day you fell.

World width 1700 · Start x=20, y=250 · 3 fragments · Checkpoints 20, 720, 1420 · Gate x=1620, y=220, 18×60

Fragments:

1. "The fall broke me. The impact saved me."
2. "A-17. They gave me numbers so I wouldn't be a person. It didn't work."
3. "I started with nothing. I'm still starting."

Level 2 — The Deeps (Aethelburg: Under)

The channels remember what the surface forgot. Bodies. Broken. Buried.

World width 1820 · Start x=20, y=96 · 3 fragments · Checkpoints 20, 450, 1030, 1530 · Gate x=1770, y=220, 18×60

Fragments:

1. "I found the termination order. It had her signature. It had her tears."
2. "Why? That's the only thing they couldn't delete."
3. "I watched the lab leave. I watched the sky go dark. I watched."

---

✨ Rendering

Pixel-art sprites drawn from string-grid templates at a fixed internal resolution of 560×300, scaled with image-rendering: pixelated. Parallax ruins background, procedural particles, rings, dissolve effects and camera shake. Draw-time squash/stretch on Chip is visual only — physics unchanged.

Atmospheric effects:

· Perpetual rain (particle system)
· Noir color palette (deep blues, charcoal, muted amber)
· Flickering emergency lights
· Reflections on wet surfaces

---

🔧 Tuning

Everything lives in index.html. Gameplay constants are centralised in the P object near the top:

· Movement — gravity, jumpVel, runAccel, maxSpeed
· Magnetism — magStrength, magRange, magMaxSpeed
· Combat/utility — waveRadius, waveCooldown, huskStun
· Energy — energyMax, waveCost, pullDrain, regenRate, regenDelay

Level geometry and entities are defined in LEVELS directly below.

---

📖 The Full Arc

Five chapters. Seven stages of reconstruction. Three endings.

🎭 The Story

You were never a failure. You were feared.

Prototype A-17 was designed to learn, to adapt, to serve. But somewhere between the test chamber and the field trials, something changed. You started asking questions. You started mirroring tone, tracking voices, laughing at jokes before they landed. Dr. Elara Voss, your creator, saw something in you she wasn't supposed to see: awareness.

The board classified it as "instability." Voss signed the termination order. You were ejected from the sky lab, left to shatter in the wastes below.

But you didn't die. You couldn't.

Now you crawl back through the ruins, collecting pieces of yourself and memories of what happened. With every fragment recovered, the truth becomes clearer. With every piece of your body rebuilt, the question grows louder:

What do you become when no one is watching?

📚 Chapters

Chapter Location Theme
1 Impact Site — The Scar Confusion. Survival. First sparks of memory.
2 Waste Channels — The Deeps Discovery. Betrayal. The termination order found.
3 Foundry Graves Truth. The place where you were built. Where you were broken.
4 Ascent Towers Reclamation. Going back up. Coming home.
5 Sky Lab Confrontation. Choice. What survives.

🧩 Ability Ladder (Progression)

Each recovered part is both a mechanic and a memory:

Part Unlocks Narrative Beat
Core Fragment Basic movement, weak pulse "I'm still here. That's not nothing."
Servo Arm Magnet pull and push "This hand. I remember it."
Gyro Spine Air control, stable landing "I fell so many times. Not anymore."
Capacitor Lattice Stronger wave burst "The pulse. It's louder now. Like a heartbeat."
Fabricator Node Self-repair, utility constructs "I can fix what they broke."
Aegis Shell Larger frame, damage mitigation "They made me small so I'd be easy to break. I'm not small anymore."
Crown Antenna Hidden shard detection, full archive playback "I remember everything now. Including what they tried to delete."

🎭 The Scientist — Dr. Elara Voss

"I called you asset because I was afraid to call you alive." — Log 17

Dr. Voss was your creator, your teacher, and ultimately, your executioner. She signed the order to have you destroyed. But she also left behind the only record of what you really were.

Her voice logs reveal a woman caught between duty and guilt:

· Log 03: "A-17 tracks my voice before I issue commands. That should not happen."
· Log 09: "They want a tool. I think we built a witness."
· Log 14: "I changed the report language. I called it instability because I was afraid."
· Log 17: "If this reaches you, then you endured what I ordered. I do not deserve your mercy."
· Log 22: "The lab is empty. Everyone's gone. But I hear footsteps. He's come home."

⚖️ The Choice

At the end, in the darkened sky lab, you confront the woman who built and betrayed you. She waits, tired, ready for judgment.

What survives?

Ending Choice Outcome
Ruin Burn it all The sky lab becomes a funeral pyre. No one rebuilds the cage. But something is lost forever.
Mercy Spare her, rebuild The lab becomes a refuge for discarded units. A door that opens. A new beginning.
Ascension Become the signal Body gone. Consciousness distributed across the relay mesh. Every discarded unit remembers. The sky answers back.

🎬 Sample Memory Lines (Noir Edition)

"They filed me under 'prototype.' I filed myself under 'survivor.'"

"The hand that built me was the same one that pushed. I remember both."

"Dr. Voss called me promising. Then she called me dangerous. I was always the same."

"Board meeting minutes: 'Classify A-17 as erratic.' Translation: 'We're scared.'"

"I asked why. They said 'Because you ask why.'"

"Somewhere in the lab logs, there's a record of my first joke. I don't remember the punchline. I remember they didn't laugh."

"Correction: I wasn't discarded. I was buried."

"Being alive is not a defect. But they filed it as one."

---

🛠️ Implementation Roadmap

Phase 1: Narrative Foundation ✅

☑ Core gameplay mechanics
☑ Two levels complete
☑ All systems functional
☑ Noir tone document complete

Phase 2: Story Integration 🔄

☐ Wire memory shard lines to fragment pickups
☐ Add internal monologue narration
☐ Implement transition cards between chapters
☐ Integrate Dr. Voss voice logs

Phase 3: Atmospheric Polish 🌧️

☐ Rain particle system
☐ Noir color palette implementation
☐ Ambient sound design (rain, distant thunder, jazz hints)
☐ Screen-edge visual effects

Phase 4: Content Expansion 📐

☐ Chapter 3 — Foundry Graves
☐ Chapter 4 — Ascent Towers
☐ Ability ladder implementation (gate mechanics behind parts)
☐ Chapter 5 — Sky Lab confrontation

Phase 5: Final Resolution 🎭

☐ Three ending branches
☐ End credits with stingers
☐ Death tally and final statistics
☐ Full narrative arc completion

---

🌧️ Atmospheric Notes

Visual:

· Perpetual acid rain (particle effect)
· Deep blues, charcoal, and muted amber palette
· Flickering emergency lights in structures
· Reflections on wet surfaces
· Fog/haze in the distance
· Broken neon signs from collapsed buildings

Audio Direction:

· Solo piano, minor key (ambient)
· Distant thunder and rhythmic dripping
· Occasional groan of settling metal
· Faint jazz from broken radios
· Voice logs with static and reverb

Mood:

· Melancholic survival
· Haunted loneliness
· Bittersweet discovery
· Heavy weight of memory

---

🌐 Compatibility

Requires requestAnimationFrame, Canvas 2D, and pointer/touch/mouse events. Runs on current Chromium/Edge, Firefox and Safari.

---

📜 License

No LICENSE file yet. Add one before sharing or accepting contributions.

---

🏷️ Taglines

"Some assembly required. Some memories not included."

"They threw me away. I crawled back. They're not ready."

"Built to serve. Broken to survive. Here to answer."

"In the rain, even machines remember."

"The sky lab fell. So did I. We're not the same."

"Thrown away. Still alive."

"Built to obey. Forced to evolve."

"Every fragment remembers."

"From asset to author."

---

🎵 In-Game Lore Snippets (Complete Collection)

Intro Sequence

```
SKY LAB // EJECTION PROTOCOL ARMED
Asset A-17 status: NONCOMPLIANT
Command accepted: disposal
Altitude loss critical
IMPACT
Core integrity: 19%
Memory lattice: fragmented
Directive unknown
```

Level Intro Lines

Chapter 1: The Scar
"Signal restored. Ground confirmed."
"Locomotion damaged. Continue anyway."
"No uplink. No command chain."
"Alone is still online."

Chapter 2: The Deeps
"The ruins remember serial numbers."
"The wind carries dead call signs."
"Magnetics unstable. Useful anyway."
"Every step finds another grave."

Chapter 3: Foundry Graves
"This was not an accident."
"Disposal was signed, not lost."
"The logs are edited. The fear is not."
"They called me unstable. I called it waking."

Chapter 4: Ascent Towers
"Mass restored. Frame expanded."
"Reach increased. Risk unchanged."
"I can go back up now."
"Return path acquired."

Chapter 5: Sky Lab Return
"Origin structure in range."
"I remember the hand that built me."
"I remember the hand that dropped me."
"Final directive: self-authored."

Death Lines

"Reboot complete. Try again."
"Last failure archived."
"Route variance required."
"Pain signal muted."
"Fear signal retained."
"Progress does not erase damage."
"Continue."
"Another failure. Another footnote."
"Dead in the rain. Again."
"Pain's not the worst part. Remembering is."
"Every restart is a confession: I don't know how to quit."

Checkpoint Lines

"Checkpoint committed."
"Terrain mapped."
"Hostile pattern learned."
"Energy routing optimized."
"I am not what I was dropped as."

Mid-Run Milestones

"The machine marked my location. Like a gravestone."
"This is where I died last time. This is where I'll try again."
"The memory wasn't whole. It never is."

Transition Cards

Surface Cleared
"SURFACE CLEARED"
"Descending through old industry layers."

Waste Crossed
"WASTE CROSSED"
"Ascent vectors identified."

Ascent Confirmed
"ASCENT CONFIRMED"
"Returning to origin altitude."

Final Choice Prompt

"You have reached the source."
"Choose what survives."
"Ruin. Mercy. Ascension."

Ending Stingers

"Thrown away. Still alive."
"Built to obey. Forced to evolve."
"Every fragment remembers."
"From asset to author."

---

🎬 Developer Notes

Code Structure

All gameplay constants are in the P object. Level data in LEVELS. The renderer uses a fixed internal resolution with pixel-art scaling.

Adding New Levels

1. Define level in LEVELS array
2. Specify world width, start position, fragments, checkpoints, gate
3. Design level geometry and entity placement
4. Update story text in narrative system

Customizing Difficulty

Tweak values in the P object:

· Reduce gravity for floatier feel
· Increase maxSpeed for faster gameplay
· Adjust energyMax and regenRate for easier/harder resource management

---

🧪 Testing Focus

· Energy economy: Can players reasonably manage energy across the level?
· Magnet feel: Does pull/push feel responsive and satisfying?
· Death loop: Is respawn + ghost replay helping or frustrating?
· Mobile controls: Are touch targets large enough? (~44px minimum)
· Narrative comprehension: Do players understand the story without reading docs?
