# Wiring

Everything electrical for the ELS: connection lists, circuits, grounding and bring-up.
[DESIGN.md](DESIGN.md) is the source of truth for the Teensy pin map (and `firmware/include/pins.h`
must match it). Parts are in [BOM.md](BOM.md). The system picture is [wiring.svg](wiring.svg).

> **This drives a machine tool and touches mains.** Section 3.1 is not optional reading. If you
> are not comfortable wiring mains, have a qualified person do sections 3.1 and 10 for you.

Contents: 1 Conventions, 2 Interface-board circuits, 3 Power, 4 CL57T driver, 5 Spindle encoder,
6 Teensy pin table, 7 Cable tables, 8 Panel (buttons, LEDs, knob, TFT), 9 E-stop, 10 Grounding,
shielding, routing, 11 Bring-up, 12 Review notes.

---

## 1. Conventions

### 1.1 Power domains

```
 MAINS 120/230 V AC  ──F1──switch──┬──────────────► LRS-350-48 ──► 48 V DC ──► CL57T ──► motor
                                   │                                │
                                   └─(opt.) IRM-20-5               ▼ (F3, 1 A)
                                                              5 V buck ──► 5 V logic rail
                                                                           ├─► Teensy VIN ─► 3V3 pin
                                                                           ├─► 74AHCT125 VCC
                                                                           ├─► spindle encoder + pull-ups
                                                                           ├─► K1 coil (via E-stop NC1)
                                                                           └─► LED drivers, TFT module
```

| Domain | Voltage | Source | Feeds |
|---|---|---|---|
| Mains | 120/230 V AC | wall | PSU (and the IRM-20-5 if used) |
| Motor | 48.0 V DC | LRS-350-48 | CL57T only (through F2 and K1) |
| Logic 5 V | 5.0 V | buck from 48 V (minimum) or IRM-20-5 (recommended) | Teensy VIN, AHCT125, encoder, K1 coil, LEDs |
| Logic 3.3 V | 3.3 V | Teensy 3V3 pin | 74LVC14 VCC, pull-ups to 3V3, TFT logic |

5 V rail budget, to size the supply (approx.): Teensy 100 mA, TFT 100 mA, K1 coil 106 mA,
encoder up to 80 mA, optocoupler drive 30 mA, LEDs 12 mA, so about **430 mA**. A 2 A buck or the 4 A IRM-20-5 is ample.

### 1.2 Wire colour code used in the tables

| Function | Colour | Gauge (AWG / mm²) |
|---|---|---|
| Mains L / N / PE | brown / blue / green-yellow (US: black / white / green) | 18 / 1.0 |
| 48 V DC + / 0 V | red / black | 16 / 1.5 |
| 5 V logic + / GND | orange / blue | 22 / 0.35 |
| 3.3 V | pink | 24-26 / 0.15-0.25 |
| STEP / DIR / ENA | white / yellow / green | 24 / 0.25 |
| ALM | violet | 24 |
| Switch and sense lines | grey, or any one colour per signal | 24-26 |
| E-stop loop | red/white (K1 coil), yellow (sense) | 22-24 |
| Motor phases (vendor) | A+ black, A- green, B+ red, B- blue (typical StepperOnline, **verify with a multimeter**) | 18-20 / 0.5-0.75 |
| Spindle encoder (vendor) | red +V, black 0 V, green A, white B (typical LPD3806, **verify**) | 24 |

"Shield" in the tables means a cable shield or foil drain wire. Rules are in section 10.

### 1.3 Connector names

Screw terminals on the interface board:

| ID | Purpose | Positions |
|---|---|---|
| J1 | 5 V in | 2 (+5 V, GND) |
| J2 | CL57T P1 control | 8 (PUL+, PUL-, DIR+, DIR-, ENA+, ENA-, ALM, COMO) |
| J3 | Spindle encoder | 5 (+5 V, GND, A, B, SHIELD) |
| J4 | Keypad | 10 (GND, 9 buttons) |
| J5 | Knob | 5 (GND, A, B, SW, spare) |
| J6 | TFT | 9 (see 8.4) |
| J7 | E-stop and K1 | 6 (+5 V, NC1 out, K1 coil-, NC2 sense, GND, spare) |
| J8 | LEDs | 4 (+5 V, NUT-, FAULT-, spare) |

---

## 2. Interface-board circuits

### 2.1 Block diagram

```
                         ┌───────────────────── INTERFACE BOARD ─────────────────────────┐
  spindle encoder        │                                                                │
  A,B (open collector) ──┤► [1k pull-up to 5V][100R+100pF] ─► 74LVC14 ─► Teensy 2, 3      │
                         │                                    (VCC=3V3)                   │
  EC11 knob A,B  ────────┤► [10k to 3V3][100nF] ────────────► 74LVC14 ─► Teensy 30, 31    │
  knob push, 9 buttons ──┤────────────────────────────────────────────► Teensy 32, 14-22  │
  E-stop NC2 ────────────┤────────────────────────────────────────────► Teensy 23         │
                         │                                                                │
  CL57T P1 ◄─────────────┤◄─ 74AHCT125 (VCC=5V) ◄── Teensy 5 (STEP), 6 (DIR), 7 (ENA)     │
  CL57T ALM ─────────────┤► [10k to 3V3] ───────────────────────────► Teensy 8            │
                         │                                                                │
  ILI9341 TFT ◄──────────┤◄── SPI 9, 10, 11, 12, 13, 41                                   │
  LEDs ◄─ 2N3904 ◄───────┤◄── Teensy 24 (NUT), 25 (FAULT)                                 │
                         └────────────────────────────────────────────────────────────────┘
```

### 2.2 Spindle encoder channel (74LVC14)

The LPD3806 outputs are **NPN open-collector**. Each output needs a pull-up and must never be
tied straight to V+ (it would burn the transistor). The pull-up goes to **5 V**; the
74LVC14 runs from **3.3 V**, and its inputs are 5 V tolerant, so the signal swings 0 to 5 V and
the output swings 0 to 3.3 V into the Teensy.

```
                          +5 V
                           │
                          [R1 1k]
                           │
 LPD3806 A (green) ────────┴──────[R3 100R]──────┬──────────► 74LVC14 pin 1 (1A)
 open collector                                   │
 (NPN pulls to GND)                             ──┴── C1 100 pF (C0G)
                                                ──┬──
                                                  │
 LPD3806 0 V (black) ───────────────────────────GND

                      74LVC14  1Y (pin 2) ─────────────────────► Teensy pin 2  (SPINDLE_A)
 
 Channel B is identical:  R2 1k / R4 100R / C2 100 pF ─► pin 3 (2A);  2Y (pin 4) ─► Teensy pin 3
```

Notes:

* **Inverting both A and B keeps the direction.** The 74LVC14 inverts. If A' = not A and B' = not B,
  the sequence A'B' runs through the same states in the same order (00, 10, 11, 01 becomes 11, 01, 00, 10,
  the same cycle), so QuadEncoder counts up for forward rotation exactly as before. Only the absolute
  phase of the counter changes, which is irrelevant here.
* The R3/C1 filter has tau = 100 ohm x 100 pF = 10 ns. It only kills RF spikes; the Schmitt
  trigger does the real cleaning. The 1 kΩ pull-up gives a rise time of about 0.2-0.4 us with the
  cable capacitance, much faster than the 25 kHz maximum channel frequency (2500 rpm x 600 / 60).
* Pull-up current is 5 mA per channel when the output is low. The encoder is rated for far more.
* Check polarity at the Teensy after wiring: INSTALL 6.2 (counts must increase on forward rotation).

74LVC14 (SOIC-14 on the adapter) pin use:

| Pin | Function | Connected to |
|---|---|---|
| 14 | VCC | **Teensy 3V3**, with C 100 nF to GND close to the pin |
| 7 | GND | GND |
| 1 (1A) | in | SPINDLE_A filtered |
| 2 (1Y) | out | **Teensy pin 2** |
| 3 (2A) | in | SPINDLE_B filtered |
| 4 (2Y) | out | **Teensy pin 3** |
| 5 (3A) | in | KNOB_A |
| 6 (3Y) | out | **Teensy pin 30** |
| 9 (4A) | in | KNOB_B |
| 8 (4Y) | out | **Teensy pin 31** |
| 11 (5A), 13 (6A) | **unused inputs** | **tie to GND** (never leave a CMOS input floating) |
| 10 (5Y), 12 (6Y) | unused outputs | leave open |

### 2.3 EC11 knob (and optional 100 PPR MPG)

The EC11 contacts are mechanical switches to a common. Debounce them with RC and let the Schmitt trigger clean the edge:

```
        3V3
         │
       [10k]
         │        100R
 EC11 A ─┴────────/\/\/────┬───────────► 74LVC14 pin 5 (3A)   ──► 3Y pin 6 ─► Teensy 30
                           │
                         ──┴── 100 nF
                         ──┬──
                           │
 EC11 C (common) ─────────GND

 EC11 B: identical network (10k to 3V3, 100R, 100 nF) ──► 74LVC14 pin 9 (4A) ──► 4Y pin 8 ─► Teensy 31
```

* A 10 kΩ pull-up to 3V3 and 100 nF gives about 1 ms; plenty for a hand-turned knob.
* The same inverting trick as 2.2 applies: both channels inverted, direction preserved.
* EC11 push switch: **direct** from Teensy pin 32 to GND (internal pull-up), no LVC.
* If you fit a 100 PPR open-collector MPG instead, wire it exactly like the spindle encoder (2.2): 1 kΩ to 5 V and 100 Ω / 100 pF.

### 2.4 STEP / DIR / ENA drive (74AHCT125 at 5 V)

The CL57T inputs are optocouplers. With the S3 switch in **5 V** they want a high level of 3.5-5 V
and 7-16 mA. A Teensy 3.3 V pin cannot do that, so a 74AHCT125 at **5 V** acts as a buffer:

* AHCT inputs are TTL-compatible: VIH(min) = 2.0 V. The Teensy 3.3 V output (VOH about 3.0 V or more) is well above that. A plain 74HC125 would need 3.5 V, which is too high.
* AHCT outputs swing 0 to 5 V and drive the opto LED directly.

```
                                  +5 V ──┬──── 74AHCT125 pin 14 (VCC)
                                         │
                                       100 nF
                                         │
                                        GND ── pin 7

   Teensy pin 5 ─┬─ pin 2 (1A)   1Y pin 3 ────────────► CL57T PUL+      PUL- ─► GND
 (STEP)         [10k] to GND  /OE pin 1 ─► GND
   Teensy pin 6 ─┬─ pin 5 (2A)   2Y pin 6 ────────────► CL57T DIR+      DIR- ─► GND
 (DIR)          [10k] to GND  /OE pin 4 ─► GND
   Teensy pin 7 ─┬─ pin 9 (3A)   3Y pin 8 ────────────► CL57T ENA+      ENA- ─► GND
 (ENABLE)       [10k] to 3V3  /OE pin 10 ─► GND
                 (PULL-UP: driver stays DISABLED while the Teensy boots)
   spare gate 4:  pin 12 (4A) ─► GND,   pin 13 (4/OE) ─► +5 V (Hi-Z),  pin 11 (4Y) open
```

Polarity (matches `lathe_config.h`: `ENABLE_ACTIVE_LEVEL = LOW`): Teensy pin 7 **LOW** gives AHCT output LOW, ENA
opto OFF, **motor enabled**. Pin HIGH gives opto ON, **motor disabled**. This is why the ENA input has a
10 kΩ pull-up to **3V3**: while the Teensy is unprogrammed or booting its pins float, and the pull-up asserts ENA so the motor stays off.

* STEP and DIR get 10 kΩ pull-downs so they sit LOW (no edges) while the Teensy boots.
* Pull-up to **3V3, not 5 V**: Teensy 4.1 pins are not 5 V tolerant, and a pull-up on a pin that is an output would back-feed through the ESD clamp.
* Timing the driver needs (V4.0 manual, section 7): pulse width >= 1.0 us (the firmware makes it 10 us), DIR set up >= 2 us before the pulse edge (firmware: one 10 us tick), **ENA ahead of DIR by >= 200 ms**.

### 2.5 CL57T ALM input

```
        3V3
         │
        [R 10k]
         │
 CL57T ALM ─┴────────────────────► Teensy pin 8 (DRIVER_ALARM)
 (opto collector)
 CL57T COMO ──────────────────────► GND  (opto emitter / common)
```

* The ALM output is an optocoupler transistor ("they take a sinking or sourcing 100 mA current at 5-24 V, max 30 V"), so it is galvanically isolated and safe to pull up to 3V3.
* **Check the polarity on your driver before you trust it** (section 12, note 2). The firmware's `ALARM_ACTIVE_LEVEL` is `LOW` (the output conducts on alarm). The older CL57T manual says the opposite default (low impedance in normal operation, high on fault). If yours does that, set `ALARM_ACTIVE_LEVEL` to `HIGH`.

### 2.6 LED drivers (NUT, FAULT)

A Teensy pin can only supply a few mA, so each LED is switched by a small NPN from the 5 V rail:

```
 +5 V ──[R 470]──►|──┐         (if your NUT LED ring already has a resistor
                    C│          inside, 5-6 V type, omit the 470 R)
 Teensy 24 ─[2.2k]─B   2N3904
 (or 25)           E│
                  GND
```

About 6 mA through the LED. Use the same circuit for LED_NUT (pin 24) and LED_FAULT (pin 25).

### 2.7 E-stop and K1 (summary; full story in sections 3.3 and 9)

```
 +5 V ──► E-STOP NC1 ──► K1 coil (A1) ... (A2) ──► GND         1N4007 across the coil
                                                      (cathode on the A1 / +5 V side)

 PSU V+ ──[F2 10 A]── K1 pole 1 (COM→NO) ── K1 pole 2 (COM→NO) ──► CL57T +VDC
 PSU V- ─────────────────────────────────────────────────────────► CL57T GND

 E-STOP NC2 ─────────────────────────────────────► Teensy pin 23 ,  other leg to GND
```

### 2.8 Decoupling and power at the Teensy

| Where | Part |
|---|---|
| AHCT125 pin 14 to GND | 100 nF X7R, at the pin |
| LVC14 pin 14 to GND | 100 nF X7R, at the pin |
| 5 V rail at J1 | 47 µF electrolytic plus 100 nF |
| Teensy 3V3 near the LVC14 | 10 µF plus 100 nF |
| Encoder supply at J3 | 10 µF plus 100 nF |

The 5 V rail goes to Teensy **VIN**. **Never connect USB and the 5 V rail at the same time** unless you cut
the thin link between VUSB and VIN on the bottom of the Teensy (PJRC: "power should not be applied to VIN while a USB cable is used", or current can flow back into the computer). Easiest: cut the VUSB-VIN link once, then both can stay connected.

---

## 3. Power

### 3.1 Mains and safety

You are connecting a mains PSU, a metal machine and an enclosure. Do this part carefully.

* **Earth everything.** The PE wire from the mains inlet goes to a **single PE stud on the enclosure**.
  From that stud: PSU FG terminal, the lathe bed (a separate green-yellow wire to a bolt on the bed, 16 AWG), the motor cable shield clamp at the driver, the metal enclosure. Use ring terminals and star washers on bare metal.
* **Fuse the live.** F1: 5x20 mm slow-blow (T): 3.15 A at 230 V, 6.3 A at 120 V. The LRS-350 has a large cold-start inrush, so do not choose a fast fuse. Check the Mean Well datasheet for your voltage.
* **Switch.** A rocker switch in the inlet (double pole if you can) so the whole unit can be isolated without pulling the plug.
* **Enclosure.** A closed, screwed-shut box. No bare mains terminals within reach: use a terminal block with a cover, ferrules on every wire, strain relief on the mains cable, a gland on every entry.
* **DC side is low voltage but high current.** 48 V at several amps can heat a wire red-hot in a short. The 10 A fuse F2 protects it.
* **First power-up** through an isolating transformer or an RCD / GFCI outlet. Section 11 gives the order.
* The lathe's own spindle motor circuit is not part of this. Leave it as it was. The ELS E-stop does **not** stop the spindle (section 9).

Table: mains and PE wiring.

| From | To | Colour | Gauge | Shield |
|---|---|---|---|---|
| Mains cable L | Inlet fuse / switch | brown (black) | 18 AWG | no |
| Switch out (fused L) | PSU `AC/L` | brown (black) | 18 AWG | no |
| Inlet N | PSU `AC/N` | blue (white) | 18 AWG | no |
| Inlet PE | PE stud on enclosure | green-yellow (green) | 18 AWG | no |
| PE stud | PSU `FG` | green-yellow | 18 AWG | no |
| PE stud | lathe bed bolt | green-yellow | 16 AWG | no |
| PSU `AC/L`, `AC/N` | IRM-20-5 `AC(L)`, `AC(N)` (recommended build) | brown, blue | 20 AWG | no |

### 3.2 48 V DC

Set the LRS-350-48 to **48.0 V** with its trim pot **with no load**, measured at the PSU terminals, before wiring the driver. The PSU's adjustment range goes above the CL57T's **50 V maximum**; do not wind it up. (The CL57T V4.0 manual: operating voltage 18-50 VDC, recommended 24-48 VDC.)

| From | To | Colour | Gauge | Shield |
|---|---|---|---|---|
| PSU `V+` | F2 (10 A DC fuse) in | red | 16 AWG | no |
| F2 out | K1 pole 1 `COM` | red | 16 AWG | no |
| K1 pole 1 `NO` | K1 pole 2 `COM` (link) | red | 16 AWG | no |
| K1 pole 2 `NO` | CL57T P4 `+VDC` | red | 16 AWG | no |
| PSU `V-` | CL57T P4 `GND` | black | 16 AWG | no |
| PSU `V+` (second terminal) | F3 (1 A) then buck `IN+` | red | 20 AWG | no |
| PSU `V-` | buck `IN-` | black | 20 AWG | no |

Twist the red and black power pair for the CL57T. Do not plug or unplug P3 or P4 with power on (manual).

### 3.3 Hardware E-stop: DC contactor K1

**Why not ENA?** On the CL57T an *energised* ENA opto **disables** the motor; ENA left unconnected = enabled. Putting an NC contact in the ENA circuit would therefore *enable* the motor when the button is pressed. So the hardware stop is a relay in the **48 V feed**, and ENA is only used by the firmware.

* E-stop **NC1** is in series with the K1 **coil** (5 V). Pressing the button (or a broken wire, or loss of the 5 V rail) drops K1 and removes the 48 V from the driver.
* E-stop **NC2** goes from Teensy pin 23 to GND. Firmware sees HIGH = tripped (it also fires on a broken wire), stops stepping and drives ENA to disable.
* K1 is a DPDT relay with **both poles in series** in the +48 V line. Two breaks double the arc gap; a DC arc does not go out at a zero crossing like an AC one.

Things you must check, because this is switching 48 V DC:

1. **Breaking capacity.** The G2R-2's contacts are 5 A, and DigiKey quotes up to 125 VDC switching voltage, but the *current it can break at 48 V DC* comes from the DC load-breaking curve in the Omron datasheet, and it is lower than 5 A. The CL57T supply current while the lathe is cutting is typically only 1-3 A. Measure yours (a DC clamp meter or the PSU current display while jogging at full speed) and compare with the datasheet curve. If your current is near the limit, use a **proper DC contactor** (rated >= 60 VDC, >= 20 A, with magnetic blow-out, coil that works from your 5 V rail or a small 12/24 V coil rail). I could not find one with a 5 V coil online; none is in the BOM.
2. **PSU output capacitors.** When K1 opens the PSU stays on and its output capacitors stay charged at 48 V. Only the driver side is dead. The driver's input capacitors keep their charge for a few seconds: wait and measure before touching P4. Treat the K1 input side as live.
3. **Back-EMF.** After K1 opens, a coasting motor acts as a generator into the driver's bridge diodes and its bus capacitors, with no supply to absorb it. At the speeds this lathe uses (<= 1500 rpm motor) the back-EMF stays below 48 V, so the bus should not rise, but this is my engineering judgement, not a manufacturer figure. The driver's over-voltage trip is well above (V4.0 manual: check supply "higher than 90 VDC"). The optional 54 V TVS at P4 clamps any excursion.
4. **Closing inrush.** When K1 closes the driver capacitors charge from a live 48 V supply through a few milliohms of wire. The PSU's current limit handles it, but the relay contacts see the pulse. The optional NTC (5 Ω cold, >= 8 A) in the +48 V line softens it.
5. **Re-arm sequence.** Release the E-stop, K1 pulls in, the driver powers up (and auto-tunes, see 4.7), and the Teensy shows "E-STOP" until you press any key (after the contact closes). ENA stays disabled until the fault is cleared.

### 3.4 5 V logic supply

* **Minimum build:** buck module from the 48 V PSU. Set it to 5.0-5.1 V **before** connecting the Teensy. Fit F3 (1 A) on its input and a 1 A polyfuse or fast fuse (F4) on its output. Because this converter is not isolated, logic GND is 48 V 0 V.
* **Recommended build:** Mean Well IRM-20-5 fed from the mains L/N. The logic ground is isolated, and the CL57T's optocoupled inputs and outputs preserve that isolation.

| From | To | Colour | Gauge | Shield |
|---|---|---|---|---|
| Buck / IRM `+5 V` | F4, then J1 `+5 V` | orange | 22 AWG | no |
| Buck / IRM `GND` | J1 `GND` | blue | 22 AWG | no |
| J1 `+5 V` | Teensy `VIN` | orange | 24 AWG | no |
| J1 `GND` | Teensy `GND` | blue | 24 AWG | no |

---

## 4. CL57T driver

Sources: StepperOnline *CL57T (V4.0) Closed Loop Stepper Drive user manual, rev. 4.0*,
[oyostepper.com copy](https://www.oyostepper.com/images/upload/File/CL57T_V4.0.pdf) (read in full), and the CL57T-V41 product listings. The V4.1 manual
PDFs on omc-stepperonline.com returned HTTP 403, so I could not read them. StepperOnline states the only V4.0 to V4.1 change is that V4.1 opens the RS232 debug port and ships a debug cable. **Compare the labels printed on your unit with the tables below before applying power.**

### 4.1 Connectors

| Connector | Pins | Function |
|---|---|---|
| P1 | PUL+, PUL-, DIR+, DIR-, ENA+, ENA-, ALM, BRK, COMO | control and outputs |
| P2 | EB+, EB-, EA+, EA-, VCC, EGND | motor encoder (VCC is +5 V **output** to the encoder) |
| P3 | A+, A-, B+, B- | motor phases |
| P4 | GND, +VDC | power in, 18-50 VDC |

The order of the pins on each connector is printed on the driver; the manual gives names, not
positions. Always go by the printed labels.

### 4.2 DIP switches S2 (V4.0 manual, section 5.2)

**1600 pulses/rev** (`MOTOR_STEPS_PER_REV 1600`, microstep 8): **SW1 = ON, SW2 = OFF, SW3 = ON, SW4 = ON.**

Micro-step table (V4.0 manual):

| Pulses/rev | SW1 | SW2 | SW3 | SW4 |
|---|---|---|---|---|
| 200 | on | on | on | on |
| 800 | off | on | on | on |
| **1600** | **on** | **off** | **on** | **on** |
| 3200 | off | off | on | on |
| 6400 | on | on | off | on |
| 12800 | off | on | off | on |
| 25600 | on | off | off | on |
| 51200 | off | off | off | on |
| 1000 | on | on | on | off |
| 2000 | off | on | on | off |
| 4000 | on | off | on | off |
| 5000 | off | off | on | off |
| 8000 | on | on | off | off |
| 10000 | off | on | off | off |
| 20000 | on | off | off | off |
| 40000 | off | off | off | off |

Mode switches:

| Switch | ON | OFF | Set to |
|---|---|---|---|
| SW5 | rotation CW | rotation CCW | **OFF**. Fix direction in firmware with `INVERT_DIR` (do not use both) |
| SW6 | **open loop** | **closed loop** | **OFF = closed loop** per the V4.0 manual (see the warning below) |
| SW7 | CW/CCW (double pulse) | PUL/DIR (single pulse) | **OFF** (STEP/DIR) |
| SW8 | pulse filter 10 ms | no filter (1.5 ms) | **OFF**. The filter delays the commanded motion (up to 10 ms). That delay becomes a thread phase shift proportional to spindle speed (about 0.4 mm at 40 mm/s), so threads would not re-register if you change rpm between passes. Even the 1.5 ms setting has this effect, so keep the same rpm for every pass of one thread |

> **SW6 warning.** The V4.0 manual (the one I read) says SW6 ON = *open loop* and its troubleshooting says
> "set SW6 to ON to make the motor run in open loop mode; if the alarm disappears, it means encoder wiring error". But a
> third-party page quoting a V4.1 troubleshooting step says "SW6 must be ON for closed loop". I could not read the V4.1 manual. Look at the label printed on **your** driver and the manual in the box. The failsafe test: with SW6 in your chosen closed-loop position, the red LED must stay **off** after power-up and the motor must hold against a hand turning the shaft. If it hunts or the red LED blinks 4 or 7 times, flip SW6.

### 4.3 Rotary switch S1 (current and gain)

| Code | Peak | RMS | Vel-loop Ki | Pos-loop Kp | Vel-loop Kp |
|---|---|---|---|---|---|
| 0 (factory) | 2.8 A | 2 A | 0 | 25 | 25 |
| 1 | 2.8 A | 2 A | 0 | 50 | 15 |
| 2 | 2.8 A | 2 A | 16 | 25 | 25 |
| 3 | 2.8 A | 2 A | 16 | 50 | 15 |
| **4** | **5.6 A** | **4 A** | 0 | 25 | 25 |
| 5 | 5.6 A | 4 A | 0 | 50 | 15 |
| 6 | 5.6 A | 4 A | 0 | 100 | 5 |
| 7 | 5.6 A | 4 A | 16 | 25 | 25 |
| 8 | 5.6 A | 4 A | 16 | 50 | 15 |
| 9 | 5.6 A | 4 A | 16 | 100 | 5 |
| A-F | 7.0 A | 5 A | same patterns as 4-9 | | |

The motor is rated 4.2 A/phase. Start at **S1 = 4** (5.6 A peak, 4 A RMS, soft gain). Raise to 5 or 6 only if you see following error
or soft stops. Higher gain gives more noise. The manual suggests keeping factory gain settings.

### 4.4 Input level selector S3 (5 V / 24 V)

* Factory setting is **24 V**. We drive with 5 V from the 74AHCT125, so **move S3 to 5 V before you connect P1** or the motor will not move.
* With S3 on 24 V and a 5 V signal the opto sees only the 5 V and "the motor won't work"; with S3 on 5 V and a **24 V** signal "the S3 selection of 5V will damage the input photo-coupling." Never feed 24 V into a driver set to 5 V.
* In 5 V mode no external resistor is needed. (Manual: 12 V signals in 5 V mode need a 1 kΩ in series; not our case.)
* Input signal current: 7-16 mA (typically 10 mA). High level 3.5-5 V, low 0-0.5 V.

### 4.5 Signal wiring (P1)

| Driver pin | Connects to | Wire | Notes |
|---|---|---|---|
| PUL+ | 74AHCT125 pin 3 (1Y) | white | STEP, Teensy pin 5 |
| PUL- | GND | black | |
| DIR+ | 74AHCT125 pin 6 (2Y) | yellow | DIR, Teensy pin 6 |
| DIR- | GND | black | |
| ENA+ | 74AHCT125 pin 8 (3Y) | green | ENABLE, Teensy pin 7; **high = motor disabled** |
| ENA- | GND | black | |
| ALM | Teensy pin 8 + 10 kΩ pull-up to 3V3 | violet | optocoupler collector |
| COMO | GND | black | common (emitter) of ALM / BRK |
| BRK | not connected | | brake output, unused |

Timing (V4.0): max pulse input 500 kHz (the V4.1 listing quotes 200 kHz; we use 50 kHz max), pulse >= 1.0 us, low >= 1.0 us, DIR before pulse >= 2.0 us, ENA before DIR >= 200 ms.

### 4.6 ALM (alarm output)

* V4.0 manual: "They takes a sinking or sourcing 100mA current at 5-24V. Max 30V." On a fault the red LED blinks and "the impedance state between ALM and COM- will change (from low to high or high to low depending on configuration)". An earlier CL57T manual (V3.0) says the default is *low impedance in normal operation and high on fault*.
* If that default holds on your unit, ALM reads **LOW when healthy** and **HIGH on fault**, which is the opposite of the firmware default. Measure pin 8 with the driver powered and healthy: if it reads LOW, set `ALARM_ACTIVE_LEVEL` to `HIGH` in `lathe_config.h`. As a bonus, this normally-closed kind is fail-safe: an unpowered driver or a broken wire reads as a fault.
* Blink codes: 1 = over-current, 2 = over-voltage, 3 = chip error, 4 = failed to lock motor shaft, 5 = EEPROM, 6 = auto-tune failed, 7 = position following error.

### 4.7 Power-up behaviour

On power-up the driver does a short auto-tune and locks the shaft. Keep the carriage free to move a few mm and keep clear of the moving parts for the first power-up.

### 4.8 Motor and encoder cables

Motor (P3), 4 conductors; pin numbers are from the StepperOnline motor page, wire colours are typical and **not confirmed** (check A+/A- resistance with a multimeter: about 0.8 ohm between two wires of one phase, open between phases).

| Motor connector pin | Signal | CL57T P3 | Typical colour | Gauge | Shield |
|---|---|---|---|---|---|
| 1 | A+ | A+ | black | 18-20 AWG | overall, **driver end only** |
| 2 | A- | A- | green | | |
| 3 | B+ | B+ | red | | |
| 4 | B- | B- | blue | | |

Encoder (P2), differential 1000 PPR (4000 CPR), 4.5-5 V:

| Motor encoder pin | Signal | CL57T P2 | Notes |
|---|---|---|---|
| 1 | EA+ | EA+ | twist A+/A- |
| 13 | EA- | EA- | |
| 11 | EB+ | EB+ | twist B+/B- |
| 12 | EB- | EB- | |
| 2 | VCC (+5 V from driver) | VCC | |
| 3 | GND | EGND | |

Use the 1.7 m extension that comes with the kit, and plug it straight into P2. A wrong A/B pairing gives alarm 7 (position following error) or a runaway motor. If you see following error, set SW6 to the open-loop position as a test: if the alarm vanishes, the encoder wiring is at fault.

---

## 5. Spindle encoder

### 5.1 Encoder cable (LPD3806-600BM-G5-24C)

Vendor wiring is **usually** red = +V (5-24 V), black = 0 V, green = A, white = B, bare = shield, but some sellers use other colours. Verify: connect +V and 0 V to 5 V, and watch each signal wire with a multimeter while turning the shaft by hand: it should swing between about 0 V and the pull-up voltage.

| From (encoder wire) | To | Colour in your extension | Gauge | Shield |
|---|---|---|---|---|
| red (+V) | J3 `+5 V` (via GX16 pin 1) | red | 24 AWG | 4-core shielded, **drain to J3 `SHIELD` only, board end** |
| black (0 V) | J3 `GND` (pin 2) | black | 24 AWG | |
| green (A, open collector) | J3 `A` (pin 3), to R1 / R3 | green | 24 AWG | |
| white (B, open collector) | J3 `B` (pin 4), to R2 / R4 | white | 24 AWG | |
| shield / drain | J3 `SHIELD` (pin 5), to the board GND star | bare | | encoder end: **cut back and insulated** |

Do **not** connect A or B directly to +5 V. Keep the cable under 3 m. The encoder body should be mounted on an insulating (printed) bracket so there is no ground loop through the lathe.

### 5.2 Mechanical coupling

See INSTALL 4. `ENCODER_CPR` = 600 x 4 = **2400** counts per encoder turn; the drive ratio goes in `ENCODER_TURNS` / `SPINDLE_TURNS` (Roher TBL-20/520: stud 2/9 x GT2 60T:20T belt = 2 / 3).

---

## 6. Teensy 4.1 pin table

Authoritative source: [DESIGN.md](DESIGN.md) / `firmware/include/pins.h`. This table adds only the wiring.

| Pin | Signal | Dir | Wiring |
|---|---|---|---|
| 2 | SPINDLE_A | in | 74LVC14 pin 2 (1Y) |
| 3 | SPINDLE_B | in | 74LVC14 pin 4 (2Y) |
| 5 | STEP | out | 74AHCT125 pin 2 (1A), 10 kΩ to GND |
| 6 | DIR | out | 74AHCT125 pin 5 (2A), 10 kΩ to GND |
| 7 | ENABLE | out | 74AHCT125 pin 9 (3A), **10 kΩ to 3V3** |
| 8 | DRIVER_ALARM | in | CL57T ALM, 10 kΩ to 3V3 |
| 9 | TFT_DC | out | TFT `DC/RS` |
| 10 | TFT_CS | out | TFT `CS` |
| 11 | TFT_MOSI | out | TFT `SDI(MOSI)` |
| 12 | TFT_MISO | in | TFT `SDO(MISO)` |
| 13 | TFT_SCK | out | TFT `SCK` |
| 41 | TFT_RST | out | TFT `RESET` |
| 14 | BTN_NUT | in | 22 mm NUT button to GND |
| 15 | BTN_MODE | in | button to GND |
| 16 | BTN_UNITS | in | button to GND |
| 17 | BTN_DIR | in | button to GND |
| 18 | BTN_STOP_L | in | button to GND |
| 19 | BTN_STOP_R | in | button to GND |
| 20 | BTN_JOG_L | in | button to GND |
| 21 | BTN_JOG_R | in | button to GND |
| 22 | BTN_RETURN | in | button to GND |
| 23 | ESTOP_SENSE | in | E-stop NC2 to GND (open = HIGH = tripped) |
| 24 | LED_NUT | out | 2.2 kΩ to base of NPN |
| 25 | LED_FAULT | out | 2.2 kΩ to base of NPN |
| 30 | MPG_A | in | 74LVC14 pin 6 (3Y) |
| 31 | MPG_B | in | 74LVC14 pin 8 (4Y) |
| 32 | MPG_SW | in | knob push to GND |
| VIN | | | +5 V rail |
| 3V3 | | | 74LVC14 VCC, pull-ups, TFT logic |
| GND | | | star point |

All switch inputs use `INPUT_PULLUP` in firmware (the 8 ms debounce is in firmware). Pin 23 is also `INPUT_PULLUP`, so **with the E-stop loop not fitted (or disconnected) pin 23 reads HIGH and the unit shows E-STOP.** For bench tests put a jumper to GND on pin 23.

---

## 7. Cable tables

All tables: From → To, wire colour, gauge, shield.

### 7.1 CL57T P1 (control), interface board J2

| Signal | From | To | Colour | AWG | Shield |
|---|---|---|---|---|---|
| PUL+ | 74AHCT125 pin 3 | J2-1 → P1 PUL+ | white | 24 | twisted with PUL- |
| PUL- | GND | J2-2 → P1 PUL- | black | 24 | |
| DIR+ | 74AHCT125 pin 6 | J2-3 → P1 DIR+ | yellow | 24 | twisted with DIR- |
| DIR- | GND | J2-4 → P1 DIR- | black | 24 | |
| ENA+ | 74AHCT125 pin 8 | J2-5 → P1 ENA+ | green | 24 | twisted with ENA- |
| ENA- | GND | J2-6 → P1 ENA- | black | 24 | |
| ALM | P1 ALM | J2-7 → Teensy 8 | violet | 24 | |
| COMO | P1 COMO | J2-8 → GND | black | 24 | |

Keep this cable short (<= 0.4 m) and inside the enclosure. If it is longer, use a shielded multi-core with the
shield tied to GND at the **board end only**.

### 7.2 CL57T P3 (motor power)

| From (driver) | To (motor) | Colour | AWG | Shield |
|---|---|---|---|---|
| P3 A+ | motor A+ | black | 18-20 | shielded 4-core, shield to the PE clamp **at the driver end**; motor end open |
| P3 A- | motor A- | green | | |
| P3 B+ | motor B+ | red | | |
| P3 B- | motor B- | blue | | |

Optional GX16-5 connector in the middle: pins 1-4 phases, pin 5 shield (through the connector shell to PE at the panel end).

### 7.3 CL57T P2 (motor encoder)

See 4.8. Kit cable, plug and play. Shield at the driver end only.

### 7.4 CL57T P4 (power), K1 and fuses

See 3.2.

### 7.5 Spindle encoder, J3

| From | To | Colour | AWG | Shield |
|---|---|---|---|---|
| encoder +V (red) | GX16-5 pin 1 → J3 `+5 V` | red | 24 | 4-core shielded cable, drain to J3 pin 5 |
| encoder 0 V (black) | pin 2 → J3 `GND` | black | 24 | |
| encoder A (green) | pin 3 → J3 `A` | green | 24 | |
| encoder B (white) | pin 4 → J3 `B` | white | 24 | |
| shield drain | pin 5 → J3 `SHIELD` | bare | | at the board end only |

### 7.6 Keypad, J4

| Pin | Signal | To Teensy | Colour | AWG | Shield |
|---|---|---|---|---|---|
| 1 | common | GND | blue | 24 | none (inside the enclosure or a short pendant cable) |
| 2 | NUT (22 mm) | 14 | grey | 24 | |
| 3 | MODE | 15 | grey | 24 | |
| 4 | UNITS | 16 | grey | 24 | |
| 5 | DIR | 17 | grey | 24 | |
| 6 | STOP_L | 18 | grey | 24 | |
| 7 | STOP_R | 19 | grey | 24 | |
| 8 | JOG_L | 20 | grey | 24 | |
| 9 | JOG_R | 21 | grey | 24 | |
| 10 | RETURN | 22 | grey | 24 | |

Daisy-chain the GND tags of all buttons on one blue wire (this is the "common"). Optional 100 nF from each input to GND on cable runs over 0.5 m.

### 7.7 Knob, J5

| Pin | Signal | To | Colour | AWG |
|---|---|---|---|---|
| 1 | EC11 C (common) and push-switch leg | GND | blue | 24 |
| 2 | EC11 A | RC network to 74LVC14 pin 5 | green | 24 |
| 3 | EC11 B | RC network to 74LVC14 pin 9 | white | 24 |
| 4 | push switch | Teensy 32 | grey | 24 |

### 7.8 E-stop and K1, J7

| Pin | From | To | Colour | AWG | Notes |
|---|---|---|---|---|---|
| 1 | J1 `+5 V` | E-stop NC1 terminal 11 | red/white | 22 | |
| 2 | E-stop NC1 terminal 12 | K1 coil A1 | red/white | 22 | |
| 3 | K1 coil A2 | GND | blue | 22 | 1N4007 across the coil |
| 4 | E-stop NC2 terminal 21 | Teensy 23 | yellow | 24 | twisted with pin 5 |
| 5 | E-stop NC2 terminal 22 | GND | blue | 24 | |

Terminal numbers on the E-stop blocks vary by make: use a multimeter to find the two NC pairs.

### 7.9 LEDs, J8

| Pin | From | To | Colour | AWG |
|---|---|---|---|---|
| 1 | J1 `+5 V` | LED anodes (via 470 Ω if no ring resistor) | orange | 24 |
| 2 | NUT LED cathode | NPN collector (Teensy 24) | grey | 24 |
| 3 | FAULT LED cathode | NPN collector (Teensy 25) | grey | 24 |

### 7.10 TFT, J6

See 8.4.

---

## 8. Panel

### 8.1 Buttons

All buttons connect one terminal to GND and the other to the Teensy pin. No external resistor: the
internal pull-up (about 22-47 kΩ) is enough, and firmware debounces. Normally open, momentary.

| Button | Size | Teensy pin | Function |
|---|---|---|---|
| NUT | 22 mm (with LED) | 14 | engage / arm / open the electronic half-nut |
| MODE | 16 mm | 15 | feed / thread (tap), **hold 1 s = new thread (resets sync)** |
| UNITS | 16 mm | 16 | metric / imperial |
| DIR | 16 mm | 17 | toward headstock / toward tailstock (LH thread) |
| STOP_L | 16 mm | 18 | tap = set left stop here, **hold 1 s = clear** |
| STOP_R | 16 mm | 19 | tap = set right stop here, **hold 1 s = clear** |
| JOG_L | 16 mm | 20 | hold to jog toward the headstock |
| JOG_R | 16 mm | 21 | hold to jog toward the tailstock |
| RETURN | 16 mm | 22 | rapid back to the start of the pass |

### 8.2 LEDs

See 2.6. NUT LED lit = engaged, blinking = armed. FAULT LED lit on E-stop, driver alarm or overspeed.

### 8.3 Knob

EC11 with RC debounce into the 74LVC14. Turn = change pitch/feed; push = cycle knob between pitch / jog 0.01 / jog 0.1 / jog 1 mm per detent. Firmware expects 4 counts per detent.

### 8.4 ILI9341 TFT (SPI, 3.3 V logic)

| TFT pin (typical label) | Connect to |
|---|---|
| VCC | 5 V rail **if the module has an on-board 3.3 V regulator and jumper J1 is open**; otherwise 3V3 with J1 closed. Check the module's schematic |
| GND | GND |
| CS | Teensy 10 |
| RESET | Teensy 41 |
| DC / RS | Teensy 9 |
| SDI (MOSI) | Teensy 11 |
| SCK | Teensy 13 |
| LED (backlight) | 3V3 (some modules want a resistor; follow the module) |
| SDO (MISO) | Teensy 12 |
| T_CLK, T_CS, T_DIN, T_DO, T_IRQ (touch) | not connected |

Measure the module's logic supply with a multimeter before attaching signals. All signals are 3.3 V; the ILI9341 chip is not 5 V tolerant.

---

## 9. E-stop

The E-stop is a 22 mm twist-release mushroom with **two NC contact blocks**.

* **NC1:** the 5 V coil circuit of K1 (hardware). Removes 48 V from the CL57T. Fail-safe: a cut wire or lost 5 V drops K1.
* **NC2:** Teensy pin 23 to GND (software). HIGH = tripped. The firmware stops stepping, drives ENA to disable, invalidates thread sync, shows E-STOP. After release, press any key to clear.

What this E-stop is **not**: it is a machine-protection stop for the leadscrew drive, built from commodity parts, not a certified safety function. It does **not** stop the lathe spindle. The spindle motor has its own switch; if you want the E-stop to cut it too, add a third NC block and wire it into the spindle motor's no-volt release circuit (or use a contactor), by someone who understands that circuit. Keep a hand on the spindle switch the first time.

---

## 10. Grounding, shielding, routing

### 10.1 Grounding / star points

```
                     PE STAR (stud on enclosure)
                    ╱        │          │         ╲
        mains PE ──┘         │          │          └── lathe bed bolt
                       PSU FG        driver motor-cable
                                      shield clamp

   48 V 0 V (PSU V-) ──► CL57T GND ────────────────┐
                                                   │ (buck only: IN- = OUT-)
   LOGIC GND STAR (at the Teensy GND pin) ─────────┘
       ├─ AHCT125 / LVC14 GND (short, wide)
       ├─ J3 shield drain, encoder GND
       ├─ all button commons
       └─ one 1 MΩ || 100 nF/2 kV to PE (optional, one place only)
```

* One logic-ground star at the Teensy. Run each return wire separately to it; no daisy-chaining through the TFT or encoder.
* The DC 0 V is **floating** with respect to PE (the LRS output is isolated). Do not bond it to PE at more than one place. If you want a bond, use the 1 MΩ || 100 nF at the logic star only.
* With the IRM-20-5 option the logic ground is also isolated from the 48 V 0 V; the opto inputs of the CL57T are the only coupling.

### 10.2 Shields (grounded at one end only)

| Cable | Shield goes to | Other end |
|---|---|---|
| Spindle encoder | J3 `SHIELD` → logic GND star (receiver end) | floating, insulated |
| Motor power | PE clamp at the **driver** end | floating at the motor |
| Motor encoder (kit cable) | EGND / PE at the **driver** end | floating at the motor |
| CL57T control (if >0.4 m) | logic GND at the board end | floating |

Grounding both ends of a shield on a lathe makes a loop with a lot of motor-current return and shows up as encoder noise and false counts.

### 10.3 Routing

* Motor cable (A+/A-/B+/B-) and 48 V DC wires on one side of the enclosure, signal wires on the other side. Keep >= 100 mm between them, and cross at 90 degrees if they must cross. This is straight from the CL57T manual: "don't tie control signal cables and power wires together".
* Twisted pairs for each signal/return, and for A+/A-, B+/B-.
* The spindle encoder cable runs away from the spindle motor wiring and the belt-drive area.
* Keep the 74LVC14 and the filters at the encoder input terminals on the board, with the pull-ups there too.
* The 48 V and motor cable gets a metal gland with 360-degree shield contact where it enters the box.

---

## 11. Bring-up order

1. **No mains, no motor.** Check with a continuity meter: logic GND to PE open (or the optional 1 MΩ), 48 V + to 0 V not shorted, +5 V to GND not shorted, PE to enclosure/PSU FG/lathe bed continuous.
2. **Mains on (isolating transformer), driver and Teensy not connected.** PSU: trim to **48.0 V**. Buck/IRM: **5.0 V**. Disconnected from the Teensy.
3. **Connect 5 V logic only** (Teensy programmed via a separate USB, with the VUSB-VIN link cut, or with VIN not connected). Check the 3V3 pin: 3.3 V. LVC14 pin 14 = 3.3 V, AHCT pin 14 = 5.0 V.
4. **E-stop circuit:** K1 pulls in with the button released; clicks off when pressed. With K1 open, measure 0 V across the driver P4 (meter).
5. **Switches:** set DIP switches (4.2), S1 = 4, **S3 = 5 V**.
6. **Driver, no motor.** Connect 48 V to P4 via K1. Green LED on, red LED blinks 4 (no motor): that is correct.
7. **Connect the motor and encoder.** Power up: the shaft locks, the red LED stays off. Test ENA: motor held when Teensy pin 7 is LOW; shaft free when HIGH.
8. **Check ALM:** measure Teensy pin 8 healthy and during an alarm (unplug the motor encoder to force one). Set `ALARM_ACTIVE_LEVEL` to match (4.6).
9. **Encoder:** check A and B with the multimeter or scope, then the INSTALL 6.2 direction test.
10. Continue with [INSTALL.md](INSTALL.md).

---

## 12. Review notes

Where I think DESIGN.md or the firmware config is electrically doubtful. I changed nothing in DESIGN.md.

1. **STEP/DIR/ENA drive current is at the AHCT125's edge.** The CL57T optocoupler input needs 7-16 mA (typical 10 mA, V4.0 manual and listing). The 74AHCT125 is rated for 8 mA (output current at 4.5 V, with VOH guaranteed about 3.8 V), absolute maximum 25 mA per pin. At 5 V the opto input draws roughly the typical 10 mA, so the buffer is slightly over its recommended output current, but with VOH still above the driver's 3.5 V threshold. This works in practice. For margin: (a) measure the drive voltage at PUL+ (should stay > 3.8 V); (b) for STEP, parallel the spare gate (4A to 1A, 4Y to 1Y, 4/OE to GND); or (c) use a pin-compatible 74ACT125, which has TTL-level inputs and a 24 mA output rating (check the datasheet of the part you buy; I did not verify it online). The pin map is unaffected.
2. **ALM polarity.** `ALARM_ACTIVE_LEVEL = LOW` assumes ALM conducts on alarm. The earlier CL57T manual says the default is the opposite (conducts when healthy). If so, the unit would raise a fault the moment the firmware starts. Measure and set `ALARM_ACTIVE_LEVEL` to `HIGH` if needed.
3. **ENA polarity is not stated explicitly in the manual.** `ENABLE_ACTIVE_LEVEL = LOW` is consistent with "ENA unconnected = drive enabled" and the troubleshooting line "the drive is disabled: ... keep ENA+, ENA- unconnected", and with the CL57T family. Verify at bring-up step 7.
4. **ENA to DIR lead time.** The V4.0 manual (figure 10, t1) wants ENA ahead of DIR by at least 200 ms. I did not see the firmware enforce that delay (it clears a fault on a key press and the ISR then re-enables the driver). In practice the next key press is later than 200 ms, but do not trigger a jog in the same instant as clearing a fault.
5. **Button count.** DESIGN.md has 9 button inputs including NUT, so 8 x 16 mm + 1 x 22 mm are needed. The BOM carries 9 x 16 mm as requested; one is a spare.
6. **74LVC14 is SMD-only** (no DIP). An SOIC/TSSOP-to-DIP adapter is in the BOM.
7. **SW6 meaning differs between the V4.0 manual and a V4.1 page** (4.2). Use the label on your driver.
8. **K1 breaks 48 V DC.** The G2R-2's DC breaking rating at 48 V must be checked against the actual supply current (3.3). If it is borderline, use a proper DC contactor.
9. **PSU trim range.** The LRS-350-48 can be turned up beyond the CL57T's 50 V limit. Set 48.0 V and consider sealing the pot with paint.
10. **Spindle encoder speed.** Some LPD3806 listings quote a 20 kHz response, i.e. about 2000 rpm at 600 PPR. Threading is done at a fraction of that; for turning at full speed check against your lathe's maximum rpm.
11. `lathe_config.h` comments quote "CL57T needs >= 2.5 us pulse" and "DIR setup >= 5 us". The V4.0 manual says 1.0 us and 2.0 us (earlier versions 2.5 us). The firmware's 10 us values satisfy both.
