# Digital lathe gearbox — system design

An electronic leadscrew (ELS) with an electronic half-nut ("NUT button") for a
9x20 / 10x22-class lathe (Grizzly G0602 / G4000, Jet BD-920, Optimum D240 and
clones). It replaces the change-gear train with a closed-loop stepper that is
slaved to an encoder on the spindle.

Inspired by Not An Engineer's videos ("Putting an end to the WORST kind of
gears", "How I gave my lathe a 'nut' button"). All code here is original.

## Block diagram

```
 spindle ──1:1 GT2 belt──► 600 PPR encoder ──► 74LVC14 ──► Teensy 4.1 (QuadEncoder, HW counter)
                                                                │ 100 kHz motion ISR
 keypad (9 keys) + EC11 knob + E-stop ─────────────────────────►│
 ILI9341 2.8" TFT ◄──────────── SPI ────────────────────────────┤
                                                                ▼
          CL57T closed-loop driver ◄── 74AHCT125 (3V3→5V) ◄── STEP / DIR / ENA
                 │  ALM ──────────────────────────────────────► Teensy (fault input)
                 ▼
          NEMA23 3 Nm closed-loop motor ──HTD-3M 20T:40T belt (2:1)──► leadscrew input
```

## Key numbers (defaults; all configurable in `firmware/include/lathe_config.h`)

| Item | Value |
|---|---|
| Spindle encoder | 600 PPR → 2400 counts/encoder rev (quadrature). Roher TBL-20/520 (= Axminster BV20M): driven from the change-gear stud (which turns 2 per 9 spindle turns) by a GT2 60T:20T belt → encoder at ⅔ spindle speed → 1600 counts/spindle rev (any ratio, fractional included, is exact) |
| Motor driver | 1600 microsteps / motor rev |
| Motor → leadscrew | HTD-3M 15 mm belt, 20T motor : 40T leadscrew (2:1) |
| Feed gearbox ratio | 1:1 (set to whatever the lathe's gearbox is left in) |
| Leadscrew | 3 mm (Roher TBL-20/520, confirmed; matches the counted 2:9 stud ratio and the manual's gear table, 2/9 × 3 = ⅔ mm) |
| Resolution | 3200 steps / leadscrew rev → 1066⅔ steps/mm (≈0.94 µm/step, kept as an exact fraction) |
| Motion ISR | 100 kHz; max step rate 45 kHz → ≈ 42 mm/s at 1066⅔ steps/mm |
| Default limits | 40 mm/s max, 600 mm/s² accel, 20 mm/s jog |

All pitch math is exact rational arithmetic, so e.g. an imperial thread on the
metric leadscrew, or an encoder at a fractional ratio, has zero cumulative error (no float drift over long threads).

## Teensy 4.1 pin map (source of truth: `firmware/include/pins.h`)

| Pin | Signal | Dir | Notes |
|---|---|---|---|
| 2 | SPINDLE_A | in | QuadEncoder ch1 via XBAR, through 74LVC14 |
| 3 | SPINDLE_B | in | " |
| 5 | STEP | out | via 74AHCT125 → CL57T PUL+ (PUL− to GND) |
| 6 | DIR | out | via 74AHCT125 → DIR+ |
| 7 | ENABLE | out | via 74AHCT125 → ENA+ (high = driver disabled on CL57T, see firmware `ENABLE_ACTIVE_LEVEL`) |
| 8 | DRIVER_ALARM | in | CL57T ALM opto output (open collector), pull-up, active low |
| 9 | TFT_DC | out | ILI9341 |
| 10 | TFT_CS | out | |
| 11 | TFT_MOSI | out | SPI0 |
| 12 | TFT_MISO | in | |
| 13 | TFT_SCK | out | |
| 41 | TFT_RST | out | |
| 14 | BTN_NUT | in | big 22 mm button; all buttons to GND, internal pull-up |
| 15 | BTN_MODE | in | feed ↔ thread |
| 16 | BTN_UNITS | in | metric ↔ imperial |
| 17 | BTN_DIR | in | toward headstock ↔ toward tailstock (LH thread) |
| 18 | BTN_STOP_L | in | press = set left stop here, hold 1 s = clear |
| 19 | BTN_STOP_R | in | press = set right stop here, hold 1 s = clear |
| 20 | BTN_JOG_L | in | hold to jog toward headstock |
| 21 | BTN_JOG_R | in | hold to jog toward tailstock |
| 22 | BTN_RETURN | in | rapid back to start of pass |
| 23 | ESTOP_SENSE | in | NC E-stop contact to GND; HIGH = tripped |
| 24 | LED_NUT | out | lit = engaged, blinking = armed (waiting for sync) |
| 25 | LED_FAULT | out | |
| 30 | MPG_A | in | EC11 knob (or 100 PPR MPG through 74LVC14) |
| 31 | MPG_B | in | |
| 32 | MPG_SW | in | knob push |

Coordinate convention: **+X = toward the tailstock (right)**. Spindle "forward"
= positive encoder counts. Normal RH threading/feeding moves the carriage −X.

## Behaviour

* **FEED mode** (mm/rev or thou/rev): NUT engages immediately; the carriage feeds
  until a stop, then the nut opens automatically.
* **THREAD mode** (pitch mm or TPI): the first NUT press of a thread anchors the
  spindle↔carriage phase. Every later NUT press **arms** the nut; it engages on
  the exact spindle angle that puts the tool back in the same groove, no matter
  where you jogged/returned to (the phase is kept modulo one spindle rev).
  Changing pitch, mode, units or direction starts a new thread (sync lost).
* **Stops**: soft limits for every kind of motion. Reaching a stop while engaged
  decelerates onto the stop and opens the nut — threading to a shoulder.
* **RETURN**: rapid to the start stop (the one opposite the feed direction), or to
  where the last pass started if no start stop is set.
* **Spindle reversal while engaged** is followed (metric-on-imperial technique).
* **Faults** (E-stop, driver alarm, spindle too fast for the pitch): motor stops,
  driver disabled on E-stop/alarm, thread sync invalidated if position may be
  lost. Any key clears once the cause is gone.
* Knob: turn = change pitch/feed; push = cycle knob between pitch / jog 0.01 /
  jog 0.1 / jog 1 mm per detent.

## Motion core

`firmware/lib/els_core` is plain freestanding C++ (no Arduino, no libc, no heap):
it is unit-tested on the PC (`pio test -e native`) and compiled to WebAssembly
for the browser simulator in `sim/`. The Teensy build wraps it with real IO.

Per 10 µs tick: read spindle count → compute exact target
`Z0 + floor((s − s0)·num/den)` → follower (feed-forward velocity + P term,
√(2a·d) braking onto stops, accel/velocity limits) → at most one step.
