# AMI Audio HAT — PCB brief (rev A)

**Status:** H1 brief · Accepted architecture  
**Date:** 2026-11-21  
**Product:** Artificial Modular Intelligence — **standalone home kiosk** (primary)  
**Form:** Raspberry Pi **I2S HAT-style** board (40-pin stacking header)  
**I/O locked:** **2× speaker out** + **1× mic in** (plug-in to board)  
**Not:** USB-primary audio PCB · not mobile-ami pocket BOM · not Stronghold-dependent  

**Owners**

| Layer | Owner |
|-------|--------|
| Electrical / PCB / fab notes | Hephaestus (craft) |
| 3D-print assembly sequence | Wil (known process) |
| Mechanical ICD (holes ↔ prints) | Joint — Wil supplies critical dims; craft freezes board outline |

**Companion:** `ASSEMBLY.md` · day-0 software `docs/SETUP.md` · backlog shipyard `2026-11-21-ami-standalone-day0-hardware`

---

## 1. Goal

One custom board that:

1. Stacks on **Pi 5** (Pi 4 OK for bring-up) via the **40-pin GPIO** as an **I2S audio HAT**.  
2. Accepts **two speakers** and **one microphone** on durable connectors (not soldered pigtails as the product path).  
3. Plays wake/TTS and captures speech for openWakeWord + local STT without a USB speakerphone.  
4. Coexists with **optional AI HAT+** (PCIe on Pi 5 — different connector; no 40-pin claim fight if we stay on standard I2S pins).  
5. Fits **Wil’s 3D-printed shell** (mount pattern + connector face + cable exits TBD from print SoR).

**Non-goals (rev A)**

- Hi-fi audiophile DAC / multi-room amp  
- Headset jack / Bluetooth audio  
- PoE HAT combo board  
- On-board MCU “smart amp” requiring custom firmware beyond Linux ASoC  
- Replacing HDMI glass or compute  

---

## 2. Architecture (locked shape)

```
                    ┌─────────────────────────────────────┐
  Pi 5 40-pin  ───► │  AMI Audio HAT (this PCB)            │
  I2S producer      │                                     │
  GPIO18 BCLK       │   I2S stereo DAC + Class-D amp  ──► SPK_L  (J1)
  GPIO19 LRCLK/WS   │         (2ch out)               ──► SPK_R  (J2)
  GPIO21 DOUT  ────►│                                     │
  GPIO20 DIN   ◄────│   I2S MEMS mic (or ADC)        ◄── MIC   (J3)
  5V / 3V3 / GND    │   level-safe · ESD · mute           │
  ID_SD/ID_SC       │   optional HAT EEPROM (ID)          │
                    └─────────────────────────────────────┘
```

**Pi role:** I2S **clock producer** (bit clock + word select from Pi).  
**Board role:** I2S **consumers** for DAC path; mic path is I2S **producer toward Pi DIN** (or codec that shares clocks — see §4).

**Why this split**

- Matches public Pi I2S practice (PCM/I2S on BCM GPIO 18–21).  
- Stereo out = left/right on one I2S data out line (time-multiplexed).  
- One mic is enough for kiosk wake+STT; keep BOM simple.  
- Class-D amp drives speakers directly from 5 V rail (typical kiosk levels).

---

## 3. Raspberry Pi electrical interface

### 3.1 Primary I2S lane (rev A — mandatory)

Physical header pin numbers (40-pin, standard HAT orientation):

| Function | BCM GPIO | Header pin | Direction (Pi view) | Board net |
|----------|----------|------------|---------------------|-----------|
| I2S bit clock (BCLK / SCLK) | **18** | **12** | Out (producer) | `I2S_BCLK` |
| I2S word select (LRCLK / WS) | **19** | **35** | Out | `I2S_LRCLK` |
| I2S data in (mic → Pi) | **20** | **38** | In | `I2S_DIN` |
| I2S data out (Pi → DAC) | **21** | **40** | Out | `I2S_DOUT` |
| 5 V | — | 2, 4 | Power | `+5V` |
| 3.3 V | — | 1, 17 | Power (logic only) | `+3V3` |
| GND | — | 6, 9, 14, 20, 25, 30, 34, 39 | GND | `GND` |
| ID_SD (HAT EEPROM, optional) | 0 | 27 | I2C | `ID_SD` |
| ID_SC (HAT EEPROM, optional) | 1 | 28 | I2C | `ID_SC` |

**Notes (Pi 5)**

- I2S is on **RP1**; Linux still exposes the familiar 18–21 mapping for the first bidirectional lane.  
- **MCLK is not provided** by Raspberry Pi SBCs — choose codecs/DACs that work **without MCLK**, or generate MCLK on-board from a local oscillator (prefer no-MCLK parts for rev A).  
- Do **not** 5 V-tolerate GPIO. All digital I/O to Pi = **3.3 V**.

### 3.2 Pins we deliberately free (rev A)

Leave free unless Wil’s shell needs a front-panel control later:

- GPIO 2/3 (I2C1) — reserved for future sensors / display bridge, not claimed by audio  
- UART 14/15 — debug  
- SPI0 — free  

Rev A **does not** require extra GPIOs for mute if the amp has hardware mute tied to a single GPIO — optional **GPIO16 or GPIO26** as `AMP_MUTE` (active low), documented if used.

### 3.3 Stacking / mechanical HAT rules

- **40-pin female** stacking header, standard 2×20, 2.54 mm.  
- Follow **Raspberry Pi HAT mechanical** envelope where practical:  
  - Board outline ≈ **65 mm × 56 mm** (full HAT) **or** smaller “Bonnet” if the print wants a partial plate — **Wil’s print decides outline**.  
  - Mounting holes: standard HAT four-hole pattern when using full HAT; if custom outline, **Wil provides hole coords** → freeze in §8 ICD.  
- Standoffs: M2.5 (HAT standard). Height: clear **active cooler** on Pi 5 — prefer low-profile parts on bottom of HAT; tall connectors face **away** from cooler / toward shell cable exits.  
- **AI HAT+** uses **PCIe FFC**, not the 40-pin audio pins — stack order: Pi → (optional PCIe AI HAT mechanically) vs 40-pin audio HAT. If both: confirm shell volume; electrical conflict is **not** on I2S pins. Prefer **audio on 40-pin, AI on PCIe** as separate modules.

---

## 4. Block design (electrical)

### 4.1 Playback path (2 speakers)

**Recommended rev A topology**

1. **I2S stereo DAC + integrated Class-D amp** (one IC or DAC+amp pair), **no MCLK required**.  
2. Outputs: **SPK_L**, **SPK_R** to connectors (differential Class-D pairs).  
3. Power: amp from **+5V** (Pi header 5 V and/or dedicated barrel if later — rev A = header 5 V only, budget current).  
4. Filter: manufacturer-recommended LC / ferrite per Class-D layout app note.  
5. **Pop suppression** / mute on boot (GPIO or amp auto-mute).  

**Example part classes (not locked SKUs — pick at H2/H3)**

| Role | Example class | Why |
|------|---------------|-----|
| Stereo I2S amp | MAX98357A ×2 (mono each) **or** stereo I2S Class-D (e.g. family like PAM/MAX stereo I2S amps) | Common Pi I2S pattern; no I2C required for basic play |
| Alt: DAC + external amp | PCM5102A-class (no MCLK variants) + stereo Class-D | More parts; only if amp choice needs line-level |

**Speaker load (rev A target)**

- **4 Ω or 8 Ω**, 2–5 W class each side (kiosk near-field, not PA).  
- Connector: **JST-PH 2-pin** or **screw terminal 2-pin** per speaker — **Wil picks for print/serviceability**. Default proposal: **JST-PH 2.0 2-pin** per channel + optional parallel pads.  

**Silkscreen:** `SPK_L`, `SPK_R`, polarity `+` / `−`.

### 4.2 Capture path (1 mic)

**Recommended rev A topology**

- **I2S digital MEMS microphone** (PDM→I2S bridge IC, or native I2S mic module footprint) clocked from Pi BCLK/LRCLK, data → `I2S_DIN` (GPIO20).  
- **or** small **I2S ADC** + electret with bias (more analog risk).  

Prefer **digital MEMS on I2S** for noise immunity inside a plastic shell next to Class-D.

**Mic connector:** **JST-PH 3- or 4-pin** (VDD, GND, DATA, optional SEL) if mic is off-board on a short harness to the shell snout; **or** on-board mic + only a shell acoustic port (no plug).  

**Product wording locked:** “mic plugs into” → **off-board mic on connector J3** is the default for rev A (matches Wil’s plug language). On-board footprint as DNP alternate OK.

**Bias / VDD:** 3.3 V from Pi, decoupled; never 5 V into mic digital pins.

### 4.3 Power tree

```
Pi 5V  ──► bulk cap ──► Class-D amp PVDD
Pi 3V3 ──► LDO/decap ──► DAC digital / mic / EEPROM
GND star / solid plane under amp; keep mic analog/digital away from amp switch node
```

**Budget (order-of-magnitude)**

| Rail | Rev A assumption |
|------|------------------|
| 5 V amp peaks | Design for **≤1.5 A** combined peaks (two small speakers); fuse or polyfuse on 5 V in |
| 3.3 V logic | **≤100 mA** |

If shell speakers are hungrier, rev B adds **barrel 5–12 V** for amp only (isolated carefully). Do not starve Pi 5 USB-C budget silently — document max continuous.

### 4.4 Protection / bring-up

- ESD on speaker and mic connectors (TVS where appropriate).  
- Test points: `TP_BCLK`, `TP_LRCLK`, `TP_DOUT`, `TP_DIN`, `TP_5V`, `TP_3V3`, `TP_GND`.  
- LED: power good (3.3 V).  
- Optional HAT ID EEPROM (24Cxx on ID_SD/ID_SC) programmed with vendor/product so `dtoverlay` can match — **nice-to-have rev A**, not blocker if overlay is manual.

---

## 5. Connectors (product face)

| Ref | Function | Proposal | Notes |
|-----|----------|----------|-------|
| J1 | Speaker left | 2-pin JST-PH | Marked SPK_L +/− |
| J2 | Speaker right | 2-pin JST-PH | Marked SPK_R +/− |
| J3 | Microphone | 3–4 pin JST-PH | VDD/GND/DATA/(SEL) |
| P1 | Pi 40-pin | Female stacking | Through-hole preferred for strength |
| J4 | (optional rev B) External 5–12 V amp | Barrel 2.1 mm | Not rev A |

**Cable exits:** defined by Wil’s print — board should put J1–J3 on **one edge** (cable face) so harnesses leave the shell without crossing the cooler.

---

## 6. Software contract (so PCB is not orphaned)

Day-0 software already runs with **USB interim**. When board lands:

| Item | Expectation |
|------|-------------|
| Device tree | `dtoverlay` for chosen amp/mic (e.g. `max98357a` ×2 or vendor overlay) |
| ALSA | Playback default → I2S amp; Capture default → I2S mic |
| AMI config | Document `audio.playback_device` / `audio.capture_device` (H5) once card names known |
| openWakeWord | Bind capture device explicitly |
| Test | `arecord` / `aplay` smoke before full `ami run` |

**Do not** require custom kernel forks.

---

## 7. Mechanical ICD (Wil + craft)

**Wil owns assembly process.** Craft needs these numbers before Gerbers freeze:

### 7.1 Provide (Wil)

1. Critical **board outline** max (L×W×H under cooler / above Pi).  
2. **Mount hole** positions relative to Pi camera/USB edge (or “use standard HAT four holes”).  
3. **Connector edge** preference (USB-side vs HDMI-side vs SD-side).  
4. Speaker sizes (mm) + magnet clearance.  
5. Mic port location on shell (snout distance from board → harness length).  
6. Whether board is **permanent stack** or **serviceable unplug** of speakers/mic only.

### 7.2 Craft freezes after inputs

- Outline DXF + hole table  
- 3D STEP of PCB+connectors (no fab house secrets)  
- Keep-out under cooler / over USB-C  
- Label map for print docs  

**Until Wil dims arrive:** assume **standard full HAT 65×56 mm**, connectors on **short edge opposite GPIO pin-1**, M2.5 HAT holes — **provisional**.

---

## 8. Fab / process (H3 preview)

| Item | Rev A intent |
|------|----------------|
| Layers | **2-layer** OK if Class-D layout careful; **4-layer** preferred for GND/power planes |
| Fab | JLCPCB / PCBWay class, 1.6 mm FR4, ENIG or HASL |
| Assembly | SMT both sides OK; hand-solder JST OK |
| Panel | Single board + mousebites if small run |
| Test jig | Pogo on TPs + 40-pin breakout Pi |

**Bring-up order**

1. Continuity / 5V–3V3 shorts  
2. Stack on unpowered Pi → visual  
3. Power Pi, check rails  
4. Load overlay, `aplay` tone left/right  
5. `arecord` mic → file  
6. `ami run` wake path  

---

## 9. BOM skeleton (fill part numbers at H3)

| Ref | Description | Qty | Status |
|-----|-------------|-----|--------|
| U1 | I2S → stereo Class-D (or 2× mono I2S amp) | 1–2 | class only |
| U2 | I2S MEMS mic **or** I2S mic codec | 1 | class only |
| U3 | HAT ID EEPROM 24C32 (optional) | 0–1 | optional |
| P1 | 2×20 female 2.54 header | 1 | |
| J1 J2 | Speaker connectors | 2 | |
| J3 | Mic connector | 1 | |
| C/L/F | Bulk + Class-D filter + decoupling | lot | per datasheet |
| D1 | Power LED | 1 | |
| F1 | Polyfuse 5 V | 1 | |
| — | Standoffs M2.5 | 4 | mechanical |

Speakers + mic capsules are **system BOM** (ASSEMBLY), not necessarily on PCB PO.

---

## 10. Risks

| Risk | Mitigation |
|------|------------|
| Class-D EMI into mic | Distance, GND plane, mic digital, ferrite on mic VDD |
| Pi 5 V current shared with USB | Budget speakers; document max; rev B external PVDD |
| Cooler / HAT height clash | Low profile top; measure Pi 5 active cooler |
| Overlay hell | Prefer well-supported I2S amp; document exact `config.txt` |
| DIN/DOUT confusion | Silkscreen + this brief: **Pi DOUT → amp DIN**, **mic DOUT → Pi DIN** |
| AI HAT volume | Shell design; separate PCIe path |

---

## 11. Open decisions (need Wil before Gerber)

1. **Board size:** standard HAT 65×56 vs custom outline from print.  
2. **Speaker connector type:** JST-PH vs screw terminal.  
3. **Mic on harness vs shell-only port** (connector still on PCB).  
4. **Amp chip lock** (pick one stereo or dual mono I2S amp).  
5. **Mute GPIO** yes/no.  
6. **HAT EEPROM** yes/no for rev A.  
7. Mount hole table (or “standard HAT”).  

---

## 12. Acceptance (PCB rev A “done”)

- [ ] Stacks on Pi 5 40-pin without forcing USB audio  
- [ ] Two speakers play independent L/R test tones  
- [ ] One mic records intelligible speech at kiosk distance  
- [ ] `ami run` wake → STT path works with documented ALSA devices  
- [ ] Fits Wil’s print with agreed holes/connector edge  
- [ ] No 5 V on GPIO; polyfuse on 5 V amp feed  
- [ ] Fab package: Gerber + BOM + CPL + test TP map  

---

## 13. Next craft steps (after this brief)

1. Wil returns §7 dims (or “standard HAT + connector edge X”).  
2. **H2** schematic: lock amp+mic part numbers.  
3. **H3** BOM + fab notes + JLCPCB cart.  
4. **H4** STEP + hole table in repo `docs/hardware/` or `cad/`.  
5. **H5** SETUP audio profile + dtoverlay snippet.  
6. Order rev A (small qty) while Pi day-0 smoke continues on USB interim.

---

## 14. References (public)

- Raspberry Pi I2S GPIO 18–21 (BCLK, FS/LRCLK, DIN, DOUT) — Pi 4 PCM / Pi 5 RP1 I2S0 first lane  
- Raspberry Pi docs: *Using the I2S peripherals on Raspberry Pi SBCs* (no MCLK on SBC)  
- HAT mechanical / ID EEPROM conventions (Raspberry Pi HAT design guide)  
- Common I2S amp bring-up patterns (e.g. MAX98357A-class mono I2S amp to Pi DOUT)

This brief does **not** copy proprietary CAD; part numbers stay **class-level** until H2 lock.
