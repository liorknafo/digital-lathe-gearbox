# Bill of materials

Electronic leadscrew (ELS) retrofit for a 9x20 / 10x22-class lathe. This list matches
[DESIGN.md](DESIGN.md) (pin map and key numbers) and [WIRING.md](WIRING.md) (circuit).

**How to read the prices.** USD, one unit, excluding shipping, tax and import duty, as seen
in web searches on 2026-10-30.

* `(V)` = a price I saw on a vendor or distributor page or search result this session.
  Stock and price move; re-check before you order.
* `(E)` = my estimate. I could not confirm it online. Treat it as +/- 50 %.

A URL appears only where I actually found it. Where there is no URL, the "example source"
column gives a vendor and a search term.

---

## 1. Electronics

| Qty | Part | Exact spec | Example source | Approx USD | Notes |
|---|---|---|---|---|---|
| 1 | Teensy 4.1, **with pins** | NXP i.MX RT1062, 8 MB flash. No-Ethernet variant is fine and cheaper. Header pins soldered | SparkFun DEV-16996 (with headers) [sparkfun.com/teensy-4-1.html](https://www.sparkfun.com/teensy-4-1.html), also DigiKey. PJRC itself now refers buyers to SparkFun | 35.95 (V) | DEV-16771 is the same board without pins, 31.50 (V), plus 2x 24-pin headers, about 2.25 (V). Pins 0-33 are on the standard rows. Pin 41 (TFT_RST) is on the extra pads, so solder a wire there |
| 1 | 74LVC14 hex Schmitt inverter | **SOIC-14 or TSSOP-14** (TI SN74LVC14A or Nexperia 74LVC14A). 1.65-3.6 V VCC, **inputs 5.5 V tolerant** | TI [ti.com/product/SN74LVC14A](https://www.ti.com/product/SN74LVC14A); Mouser or DigiKey, search `SN74LVC14ADR` | 0.60 (E) | **Not made in DIP** (TI lists SOIC/SSOP/TSSOP/TVSOP/VQFN only). Solder it onto an adapter |
| 1 | SOIC-14 (or TSSOP-14) to DIP-14 adapter board | 0.1 in pitch, matches the package you bought | Amazon / AliExpress, search `SOIC14 to DIP14 adapter` | 1 (E) | Alternative: draw a SOIC pad on a custom PCB |
| 1 | 74AHCT125 quad buffer, 3-state | **DIP-14**, TI SN74AHCT125N. VCC 5 V, VIH(min) = 2.0 V | [DigiKey SN74AHCT125N](https://www.digikey.com/en/products/detail/texas-instruments/SN74AHCT125N/375798), Mouser 595-SN74AHCT125N | 0.95 (V) | Do **not** substitute 74HC125 (VIH at 5 V is 3.5 V, too high for Teensy 3.3 V outputs) |
| 2 | DIP-14 IC socket | Turned-pin or standard | Any | 1 (E) | Use one for the AHCT125. Do not socket the adapter board unless the adapter has pins |
| 1 | ILI9341 2.8 in SPI TFT | 240x320, SPI, 3.3 V logic, on-board backlight. Touch/SD optional (unused) | [ShillehTek ILI9341 2.8 in](https://shillehtek.com/products/2-8-spi-tft-lcd-touch-screen-module-240x320-ili9341-for-arduino) (10.99 V); Adafruit #1770 is about 30-37 (V) if you want a known-good breakout | 10.99 (V) | Check the silkscreen for the **LED / VCC** pins and any 3.3 V / 5 V solder jumper |
| 1 | EC11 rotary encoder with push switch, plus knob | EC11, 15-20 mm shaft, 6 mm D or knurled. **4 quadrature counts per detent** (firmware `kKnobCountsPerDetent = 4`), 20 PPR / 20 detent is typical | AliExpress / Amazon, search `EC11 encoder with switch knob 20 detent` | 2.50 (E) | If your EC11 is 2 counts per detent, change that constant in firmware |
| 9 | 16 mm momentary panel push button | Metal, IP65, **NO**, screw or solder terminals, 1 NO, 3 A or better. LED version not needed | eBay / AliExpress / Amazon, search `16mm momentary push button metal waterproof`. Seen 1.59-5.49 each (V) | 18-27 (V range) | The pin map uses **8** of these (MODE, UNITS, DIR, STOP_L, STOP_R, JOG_L, JOG_R, RETURN), because NUT is the 22 mm one. The 9th is a spare, as requested |
| 1 | 22 mm momentary button, "NUT" | 22 mm, NO, **with LED ring** (5-6 V or 12 V ring, see wiring) | Same sources, search `22mm momentary push button LED` | 4-6 (E) | LED driven by a transistor, see WIRING 8.2. If you buy a 12 V ring, power it from the 5 V rail through a lower resistor or accept dimmer light; a 5-6 V ring is best |
| 1 | LED for FAULT | 5 mm or 8 mm panel LED, red, with holder | Any | 1 (E) | Driven by a transistor, see WIRING 8.2 |
| 1 | 22 mm twist-release E-stop, **2 NC** | 22 mm mount, red mushroom, twist release, **2 NC contacts**, 10 A / 250 V AC contacts | Eaton M22-PVT-K02 [imc-direct.com/products/m22-pvt-k02](https://www.imc-direct.com/products/m22-pvt-k02) 35.54 (V). Cheap generic 2NC, e.g. uxcell LAY37-02ZS, about 11 (V) on eBay | 11-36 (V) | **Needs 2 NC**: one for the contactor, one for Teensy pin 23. A 1NC button works only if you give up the hardware cut or the sense input. Cheap buttons are not safety rated; this is a machine-protection stop, see WIRING 9 |
| 1 | K1 power relay, DPDT, 5 V coil | Omron G2R-2-DC5 (DPDT, 5 VDC coil 106 mA, 5 A contacts, rated to 125 VDC switching voltage). PCB or socketed | [DigiKey G2R-2 DC5](https://www.digikey.com/en/products/detail/omron-electronics-inc-emc-div/G2R-2-DC5/368768), Newark 17C1352 | 7.24 (V) | **Series both poles** in the +48 V feed. DC-breaking capacity is limited, see WIRING 3.3 for the check you must do. A DC-rated contactor is a better part if you can find one that works with a 5 V coil |
| 1 | Socket for K1 | Matching G2R-2 socket (e.g. Omron P2RF-08 family) | DigiKey / Mouser, search `P2RF-08 socket` | 5 (E) | Optional, lets you replace the relay |
| 1 | Flyback diode for K1 coil | 1N4007 or 1N4148 | Any | 0.10 (E) | Across the coil, cathode to +5 V |
| 2 | NPN transistor, TO-92 | 2N3904 or BC337 (LED drivers for NUT and FAULT) | Any | 0.30 (E) | |
| 1 | 48 V PSU | **Mean Well LRS-350-48**: 48 V, 7.3 A, 350 W, universal AC input, trim-pot adjustable output. LRS-200-48 is enough electrically | [Mouser LRS-350-48](https://www.mouser.com/en/ProductDetail/MEAN-WELL/LRS-350-48?qs=ah3jBNVE1PSzhibo2xPJuA%3D%3D) 33.30 (V); DigiKey 1866-3350-ND (about 32 (V), a year old); TRC 36.11 (V) | 33.30 (V) | Set the output to **48.0 V** with the trim pot before connecting the driver. The CL57T maximum is 50 V |
| 1 | 5 V logic supply, **buck** | 48 V in (**60 V-rated input**, not a 40 V part), 5.0 V out, 2 A or better, set to 5.0-5.1 V before connecting | LM2596HV-type module (4.5-60 V). eBay / AliExpress, search `LM2596HV 60V buck module`. Seen 1.5-2.7 (V), shipping often more. Quality varies; several listings quote 48-55 V real maximum | 3 (V range) | Minimum build. See "5 V supply options" below |
| 1 | 5 V logic supply, **isolated AC-DC** (recommended) | Mean Well IRM-20-5: 85-305 VAC in, 5 V, 4 A | [DigiKey IRM-20-5](https://www.digikey.com/en/products/detail/mean-well-usa-inc/IRM-20-5/7704667), Mouser 709-IRM20-5 | 9.10 (V) | Fed from the mains side, galvanically isolated from the 48 V ground. Needs its own fuse. Buy this **instead of** the buck in the recommended build |
| 2 | 1 A fuse or polyfuse | F3 on the buck's 48 V input (minimum build) and F4 on the 5 V output. Fuse must be rated >= 60 VDC for F3 | Any | 1 (E) | |
| 1 | Mains inlet, fused, switched | IEC C14 inlet, with fuse drawer and rocker switch (DP preferred), panel mount | Amazon / DigiKey, search `IEC C14 inlet fuse switch` | 6 (E) | Recommended build: add a mains EMI filter version (10 (E)) |
| 1 | Mains fuse | 5x20 mm **slow-blow (T)**: 3.15 A T for 230 V, 6.3 A T for 120 V | Any | 1 (E) | LRS-350 has high inrush. Check the PSU datasheet before choosing a smaller value |
| 1 | DC fuse, 48 V line | 10 A, rated >= 60 VDC. Blade (ATO) with holder, or 5x20 mm DC-rated | Any | 3 (E) | Between PSU V+ and the K1 contacts |
| 1 | Resistor kit | 1/4 W 1 %: **4x 1 kΩ** (encoder pull-ups, 2 spindle plus 2 spare), **4x 100 Ω** (filter R), **~10x 10 kΩ**, 2x 2.2 kΩ, 2x 470 Ω, 1x 330 Ω | Any | 2 (E) | See WIRING section 2 for where each goes |
| 1 | Capacitor kit | **4x 100 pF** C0G/NP0 (filter C), **~8x 100 nF** X7R (decoupling, EC11 debounce), 2x 10 µF, 2x 47 µF/16 V electrolytic | Any | 2 (E) | |
| 1 | Perfboard | Double-sided 70x90 mm or larger, 2.54 mm. Or a small custom PCB | Any | 3 (E) | Recommended: a 2-layer PCB with a ground plane |
| 1 | Screw terminals / headers | 5.08 mm pluggable screw terminals (about 40 positions), 2.54 mm female headers for the Teensy and TFT | Any | 6 (E) | |
| 1 (opt) | TVS diode, 48 V rail | Unidirectional, standoff >= 51 V, e.g. SMCJ54A class, at the CL57T power terminals | Mouser / DigiKey, search `SMCJ54A` | 1 (E) | Optional: absorbs back-EMF energy when K1 opens at speed |
| 1 (opt) | NTC inrush limiter in the +48 V feed | About 5 Ω cold, rated >= 8 A continuous | Mouser / DigiKey, search `NTC inrush limiter 5 ohm 10A` | 2 (E) | Optional: softens the charge of the driver capacitors when K1 closes |

### 5 V supply options

* **Minimum build:** 48 V to 5 V buck module fed from the PSU output (before the K1 contacts). Cheap
  but not isolated, and the real input limit on cheap "HV" modules is often lower than the 60 V on
  the label. A 48 V PSU can show 50+ V on a quiet day. Check the module before trusting it.
* **Recommended build:** Mean Well IRM-20-5 from the mains side. Isolated, certified, 4 A,
  and keeps the logic ground separate from the motor supply ground (the CL57T inputs are
  optoisolated, so this isolation is worth keeping).

---

## 2. Motion

| Qty | Part | Exact spec | Example source | Approx USD | Notes |
|---|---|---|---|---|---|
| 1 | **Closed-loop NEMA 23 kit, ~3 Nm, 8 mm shaft** | StepperOnline **1-CL57T-S30A-V41**: CL57T-V41 driver (0-8 A, 24-48 VDC) plus **23HS45-4204D-E1000** motor (1.8 deg, 3.0 Nm, 4.2 A/phase, 0.82 Ω, 3.6 mH, 57x57 mm, 1000 PPR = 4000 CPR differential encoder). Kit includes the RS232 debug cable and a 1.7 m encoder extension cable | [StepperOnline kit page](https://www.omc-stepperonline.com/ts-series-3-0-nm-424-92oz-in-1-axis-closed-loop-stepper-cnc-kit-nema-23-motor-driver-1-cl57t-s30a-v41) 64.34 (V). Related: 1-CL57T-S30-V41 62.70 (V) | 64.34 (V) | Shaft: **8 mm, 21 mm long, 15 mm D-cut** (StepperOnline, Oyostepper). One Skysmotor page says 10 mm, probably a listing error. Body length is quoted 113, 135 and 138 mm by different pages; get the dimension drawing before you design the mount. The kit's motor lead is only 300 mm, so plan the mount near the driver or add an extension. **Not for the Roher TBL-20/520:** its gear door is only 65 mm deep, so the motor sticks out through a window in the door (`cad/designs/door_bezel_motor.sc`). The window has to stay on the door, which limits the motor to about **95 mm overall** (90 to be safe). This motor is too long; use the 1.2 Nm kit in the next row |
| 1 | **Roher: CHOSEN (2026-10-31, to order): Leadshine 57CME13 + CL57 closed-loop kit** | Leadshine **57CME13** motor (1.3 Nm, 4.0 A, 0.42 Ω, 1.6 mH, rotor 300 g·cm², 1000-line encoder, **8 mm x 21 mm shaft**, 47.14 mm bolt square, body **74-75 mm**: same electrical data as the CS-M22313, whose Leadshine curve gives ~1.2 Nm at 600 rpm and ~0.7 Nm at 1600 rpm on 48 V) plus the Leadshine **CL57** closed-loop driver. On the listing pick the variant **"57CME13 With CL57"** | [AliExpress item 1005011653745696](https://he.aliexpress.com/item/1005011653745696.html), seller Millin Shtrs Shop Store (reseller, store 4.9 / 5,000+ sold, this item 0 sold): **₪391.90** + shipping ₪153.34 to Israel (delivery 19-28 Nov when checked), VAT added at checkout, about **₪640** all in | ~175 (V) | **Before paying, ask the seller:** that the CL57 has ALM (alarm out) and ENA (enable in), accepts 48 V, and that the motor is a genuine 57CME13. **When it arrives:** set `motor_len` in `cad/params.json` to the measured length (75 expected, fits the door with room to spare), run `python3 cad/build.py` (designs, windows, bezels and fit checks follow), and redo the driver section of docs/WIRING.md for the CL57 (written for the CL57T). Lab-measure: torque is ample (needs ~0.6 Nm worst case while threading); set the driver's command filter / smoothing to its minimum for threading |
| 1 | **Roher fallback: closed-loop NEMA 23 kit, 1.2 Nm** | StepperOnline **1-CL57T-S12-V41**: the same CL57T-V41 driver plus the **23HS22-4004D-E1000** motor (1.2 Nm, 4.0 A, 8 mm D-cut shaft, 1000-line encoder). About **81 mm** long including the encoder according to one listing; check the datasheet before buying | [StepperOnline kit page](https://www.omc-stepperonline.com/ts-series-1-2-nm-170oz-in-1-axis-closed-loop-stepper-cnc-kit-nema-23-motor-driver-1-cl57t-s12-v41), 55.82 (V); [StepperOnline UK](https://www.stepperonline.co.uk/ts-series-1-2nm-169-93oz-in-1-axis-closed-loop-stepper-cnc-kit-nema-23-motor-driver-1-cl57t-s12-v41.html) 44.10 GBP (V) | 55.82 (V) | 1.2 Nm through the 2:1 belt on the 3 mm leadscrew pushes the carriage with well over 1 kN, several times what this lathe needs. With 81 mm it sticks 52 mm out of the 65 mm door through a 76 x 61 mm window. Set `motor_len` in `cad/params.json` to the datasheet length |
| (alt) | Motor only | 23HS45-4204D-E1000 | [StepperOnline motor page](https://www.omc-stepperonline.com/nema-23-closed-loop-stepper-motor-3-0nm-424oz-in-encoder-1000ppr-4000cpr-23hs45-4204d-e1000), UK store 28.46 GBP | 36.02 (V) | CL57T-V41 alone: price not confirmed, kit minus motor is about 28 |
| 1 | HTD-3M pulley, **20 T**, 8 mm bore (motor) | Aluminium, **15 mm belt**, flanged, 2 set screws (pitch dia 19.10 mm) | BEMONOC HTD3M 20T 8 mm [Amazon B016NKEV14](https://www.amazon.com/3M-HTD-Pulley-Belt-Timing/dp/B016NKEV14) (price not shown); Mädler PN 17032000 [maedlernorthamerica.com](https://maedlernorthamerica.com/partshop/timing-belt-pulley-htd-3m-material-aluminium-20-teeth-for-belt-width-15mm-pn-17032000/) 17.05 (V), 6 mm pilot bore (you bore to 8 mm) | 8-17 | Use the D-cut flat on the motor shaft; one set screw on the flat. Loctite 243 |
| 1 | HTD-3M pulley, **40 T**, bored to the leadscrew end | Aluminium, **15 mm belt**, pitch dia 38.20 mm, OD 37.44 mm | Xuulan 40-3M-15 BF [Amazon B09H5QGM3C](https://www.amazon.com/Teeth-Synchronous-Pulley-Timing-40Teeth/dp/B09H5QGM3C) (bore options 6-20 mm); eBay 3M40 step type 8.60 (V); Mädler PN 17034000 [maedlernorthamerica.com](https://maedlernorthamerica.com/partshop/timing-belt-pulley-htd-3m-material-aluminium-40-teeth-for-belt-width-15mm-pn-17034000/) 24.81 (V), 6 mm pilot, max bore 16.5 mm | 9-25 | **Roher TBL-20/520:** `cad/designs/pulley_htd3m_40T.sc` (STL `cad/stl/pulley_htd3m_40T.stl`) prints this 40T with the leadscrew's keyed bore, held by the original end screw and washer. Or buy one and bore and key it. **Measure the leadscrew end first** (INSTALL 2.1). If the shaft is larger than the pulley's max bore you need a machined hub. Buy a pulley with a pilot or small bore and bore it on the lathe |
| 1 | HTD-3M closed-loop belt, **15 mm wide** | Pitch 3 mm. **Roher layout in `cad/`: 3M-207 (69 T) at C = 57.71 mm.** 3M-204 (C 56.2) or 3M-210 (C 59.2) also fit within the base plate's slide. Other machines: 3M-189 (63 T) for C about 48.6 mm; 3M-201 (67 T) C about 54.7 mm; 3M-225 (75 T) C about 66.8 mm | Mädler, Gates or Misumi catalogues; search `3M-189-15 timing belt`. I did not find a listing with a price | 6-10 (E) | Buy two lengths if unsure. Centre distance formula in INSTALL 3.3 |
| 1 + 1 | GT2 pulleys, 6 mm belt: **20 T, 6 mm bore** (encoder) + **60 T** (change-gear stud) | **Roher layout:** the 20T goes on the encoder (LPD3806 shaft is 6 mm; the toothed part plus hub must be 12.3 mm long or less). The 60T goes on the change-gear stud: print it from `cad/designs/pulley_gt2_60T.sc` (STL: `cad/stl/pulley_gt2_60T.stl`) with the stud's keyed bore, or bore and key an aluminium one. Encoder at 2/9 x 60/20 = ⅔ chuck speed = 1600 counts/rev | Phidgets TRM4105_0 (8 mm, 60 T) [phidgets.com](https://www.phidgets.com/?prodid=754) 3.00 (V); Bulkman3D GT0002-60 (6 mm bore listed) [bulkman3d.com](https://bulkman3d.com/product/gt0002-60/) 1.40-1.92 (V); Studica 60 T 6 mm D-shaft [studica.co](https://www.studica.co/60-tooth-gt2-6mm-timing-belt-pulley) | 3-6 | 60T pitch diameter 38.20 mm, 20T 12.73 mm. A common 3D-printer kit (GT2 20T + 60T + 200 mm belt) has exactly this ratio and belt. Check the 20T bore (often 5 mm; you need 6 mm) |
| 1 | GT2 closed-loop belt, **6 mm wide** | **Roher layout: 200 mm (100 T) at C = 58.61 mm** (60T/20T) | Studica sells closed 6 mm belts in 240 and 330 mm (V, price not seen). Amazon / eBay, search `GT2 closed loop belt 6mm 240` | 5 (E) | The 20T/60T + 200 mm belt kits at 12-16 (V) on Amazon/eBay match this layout exactly |

---

## 3. Sensors

| Qty | Part | Exact spec | Example source | Approx USD | Notes |
|---|---|---|---|---|---|
| 1 | Spindle encoder **LPD3806-600BM-G5-24C** | 600 PPR, AB two-phase, **NPN open-collector** outputs, 5-24 V supply, 38 mm body, 6 mm shaft, 1.5 m cable, 5000 rpm max | Alibaba listing [alibaba.com/product-detail/New-and-original-Incremental-rotary-encoder_60781883725.html](https://www.alibaba.com/product-detail/New-and-original-Incremental-rotary-encoder_60781883725.html): wholesale about 9.50-11 (V), MOQ up to 50. eBay US stock about 44-60 (V). AliExpress: price not shown, search `LPD3806-600BM-G5-24C` | 15 (E) via AliExpress, 44.50 (V) via eBay US | Wire colours usually red = +V, black = 0 V, **green = A, white = B**, but some sellers differ; verify (WIRING 5.1). Some listings quote "20 kHz response", i.e. about 2000 rpm for 600 PPR. Fine for threading, check your max spindle rpm |
| 1 | Encoder bracket | Printed PETG/ASA, slotted for belt tension | Your printer | (filament) | Printed bracket also insulates the encoder body from the lathe, which avoids a ground loop |

---

## 4. Mechanical hardware

| Qty | Part | Exact spec | Example source | Approx USD | Notes |
|---|---|---|---|---|---|
| 1 | Base plate (replaces the change-gear banjo) | **Roher:** `cad/designs/base_plate.sc`, cut from **6-8 mm aluminium** using `cad/dxf/base_plate.dxf` (with 6 mm, set `base_t` to 6 in `cad/params.json`, rebuild, and see cad/README). Print it in PETG/ASA only as a fit check | Local metal supplier / your printer | 10-25 (E) | Clamped by the old banjo bolts in ±3 mm slots for belt tension. Do not run the motor on a printed plate long term: PETG creeps under bolt clamp |
| 1 | Encoder bracket | `cad/designs/encoder_bracket.sc` (STL: `cad/stl/encoder_bracket.stl`), printed PETG/ASA face-down, no supports | Your printer | 1 (E) | 2x M4 to the base plate (heat-set inserts) |
| 4 | M5 hex standoffs, steel, **35 mm** + M5 washers, 2.5 mm stack each (shim to 37.5 mm) | Carry the motor off the base plate. The exact length is in `cad/fit_checks.md` (`python3 cad/build.py`) | Hardware store / Amazon | 4 (E) | A 40 mm standoff with no shim also works and puts the motor 2.5 mm further out |
| 3 | Rubber grommets, 12 mm hole | One per lead through the end panel: motor power (A1), motor encoder (A2), spindle encoder (B), see cad/README step 7 | Hardware store | 1 (E) | The leads must not run outside the door: it would sweep them when opening |
| 2 | Door bezels + seal | `cad/designs/door_bezel_motor.sc` + `door_bezel_encoder.sc`, printed PETG/ASA, frame the windows cut in the gear door for the motor and the encoder (it pokes 8.8 mm past the 65 mm door). Self-adhesive **brush strip** (about 10-15 mm bristles) or soft foam round the opening | Your printer; brush strip: Amazon/AliExpress, search `self adhesive brush strip 15mm` | 6 (E) | Plus **14x M3 x 10 + nyloc nuts** through the door (4 on the motor bezel, 10 on the encoder bezel: only where there is sheet behind) |
| 2 | M5 countersunk screws, DIN 7991 | Replace the two banjo clamp bolts. The banjo (17.66 mm) sits on the panel and the plate (8 mm) takes its place, so length = old banjo bolt length - 9.66 mm, rounded down to the next stock length | Hardware store | 1 (E) | Heads sit flush under the 40T pulley |
| 4 | Motor screws | M5 socket head, **length = plate thickness + 5 mm, never beyond the motor tap depth** (check the datasheet) | Hardware store | 2 (E) | Spring or lock washers |
| 1 | Screw assortment | M3 / M4 / M5 / M6 / M8 socket head, button head and countersunk, with nuts and washers | Amazon, search `M3 M4 M5 M6 M8 screw assortment kit` | 20 (E) | M3 for boards/standoffs, M4 for printed brackets, M5 for motor and pulleys, M6/M8 for lathe-side mounts and slot bolts |
| 1 | Heat-set inserts | M3 x 5.7 mm and M4 x 8 mm brass (about 50 each), plus M5 if the enclosure uses them | Amazon, search `heat set inserts M3 M4 assortment` | 8 (E) | For the printed encoder bracket and panel parts |
| 8 | M3 standoffs | 10 mm nylon or brass, with screws | Any | 3 (E) | Board mounting |
| 1 | M4/M5 set screws, hex key set | M4 x 5, M5 x 6 cup-point | Any | 3 (E) | For the pulleys |
| 1 | Thread locker | Loctite 243 (blue) | Hardware store | 8 (E) | Pulley set screws and motor screws |
| 1 | PETG or ASA filament | 1 kg, 1.75 mm. ASA/PETG for any part near the lathe (oil, heat) | Any | 20-25 (E) | Brackets, panel, encoder mount, cable clips |
| 1 | Key stock / hub stock | As needed for the leadscrew end | Local | 5 (E) | Only if your leadscrew end has a keyway to reuse |

---

## 5. Wiring & connectors

| Qty | Part | Exact spec | Example source | Approx USD | Notes |
|---|---|---|---|---|---|
| 3 m | Shielded cable, **4-core, 24 AWG (0.22 mm²)**, foil + drain | For the spindle encoder cable (+5 V, GND, A, B) | Amazon / Mouser, search `4 core shielded cable 24AWG` | 6 (E) | Keep under 3 m |
| 3 m | Shielded cable, **4-core, 18-20 AWG (0.5-0.75 mm²)**, braided | Motor extension (A+, A-, B+, B-) | Same, search `4 core shielded cable 18AWG` | 12 (E) | Motor rated 4.2 A |
| 2 m | Encoder extension | Use the kit cable (1.7 m). Do not splice it unless you have to | (in kit) | 0 | If you must splice it, keep the A/B pairs twisted and the shield continuous |
| 2 m | Wire 16 AWG (1.5 mm²), red and black | 48 V DC distribution, PSU, fuse, K1, driver | Any | 4 (E) | Use tinned, high-strand |
| 2 m | Wire 18 AWG (0.75-1 mm²), 3 colours | Mains L, N, PE (brown/blue/green-yellow, or black/white/green) | Any | 4 (E) | Rated >= 300 V |
| 10 m | Hook-up wire 22-26 AWG, assorted colours | Logic wiring, buttons, TFT | Any | 6 (E) | Silicone insulation is easier to dress |
| 4 | Cable gland **PG7** | M12 thread, 3-6.5 mm cable | Amazon, search `PG7 cable gland` | 4 (E) | Spindle encoder, knob/panel leads |
| 2 | Cable gland **PG9** (or PG11) | 4-8 mm cable | Amazon | 3 (E) | Mains and motor cable. Use metal gland for a shielded cable |
| 2 pairs | **GX16-5** aviation connector, 5-pin, panel and cable | GX16 (16 mm) | Amazon, search `GX16 5 pin aviation connector` | 8 (E) | Spindle encoder (4 conductors + shield) and the motor power (4 + shield) |
| 1 pair | **GX16-7** aviation connector, 7-pin | GX16 | Amazon, search `GX16 7 pin` | 5 (E) | Only if you break the motor's encoder cable. Prefer the unbroken kit cable |
| 1 | Enclosure | Metal (steel or aluminium), about 250x200x100 mm, IP54 or better, with mounting plate | Amazon / Hammond / Bud, search `metal junction box 250x200x100` | 25-40 (E) | A metal box bonds to PE and shields the driver. Plastic is possible if everything inside is class II except the PSU (which needs PE) |
| 1 | Terminal blocks (mains) | 3-way (L, N, PE) screw or lever block, rated >= 16 A | Any | 3 (E) | Plus a transparent safety cover |
| 1 | Ferrules, assorted | 0.25 to 2.5 mm² with crimper | Amazon | 8 (E) | Use on every wire in a screw terminal |
| 1 | Heat-shrink assortment | 2:1 and adhesive-lined | Any | 5 (E) | Mains terminations |
| 1 | Cable ties, spiral wrap, adhesive mounts | | Any | 5 (E) | Separate the motor wires from the signal wires |
| 1 | Grounding ring terminals + star washer | M5 | Any | 2 (E) | PE star point on the enclosure |

---

## 6. Tools & consumables

| Qty | Part | Exact spec | Example source | Approx USD | Notes |
|---|---|---|---|---|---|
| 1 | Dial indicator with magnetic base | 0.01 mm resolution, 10-25 mm travel | Any | 25-40 (E) | Needed for calibration (INSTALL 8) |
| 1 | Calipers | 150 mm, 0.01 mm | Any | 15 (E) | Leadscrew pitch, bores |
| 1 | Multimeter | DC V, continuity, resistance | Any | 20 (E) | Essential for the bring-up in WIRING |
| 1 | Soldering iron, solder, flux | 60/40 or lead-free, 0.8 mm | Any | 30 (E) | SOIC-14 adapter needs a fine tip |
| 1 | Crimp tool | Ferrule and Dupont | Any | 20 (E) | |
| 1 | Screwdriver and hex key set | | Any | 10 (E) | |
| 1 | Drill, taps, reamer set | As needed for the motor plate | Shop | n/a | |
| 1 | Oscilloscope (optional) | Any 20 MHz | | n/a | Very useful for checking encoder and STEP edges |
| 1 | 3D printer | PETG/ASA capable | | n/a | Or order printed parts |
| 1 | Thread pitch gauges | 8 TPI, metric | Any | 10 (E) | Measure the leadscrew |
| 1 | Test scrap | 20-25 mm aluminium or free-cutting steel rod | Local | 5 (E) | First-thread test (INSTALL 9) |
| 1 | Isolating transformer or RCD / GFCI outlet | | | 20-40 (E) | Strongly recommended for the first mains power-up |

---

## 7. Totals

> **Roher TBL-20/520 layout:** the spindle hub is gone, one GT2 20T/60T/200 mm kit covers the encoder drive, and the base plate replaces the motor bracket. The totals below barely change. The motor sticks out through a window in the 65 mm gear door. That limits it to about 95 mm long, so use the cheaper **1.2 Nm kit** (1-CL57T-S12-V41, 55.82) rather than the 3 Nm one.

Prices are line totals added up from the tables above. They exclude shipping, tax and any
import duty. They also exclude tools you already own.

### Minimum build (about 385 USD)

* Teensy, LVC14, AHCT125, TFT, EC11, 9x 16 mm buttons (about 2 each), cheap NUT button,
  generic 2NC E-stop, K1 relay, LRS-350-48, LM2596HV buck, encoder via AliExpress (15), small parts.
  Electronics about **167**.
* CL57T kit 64, cheapest pulleys 25, GT2 pair + belt 12. Motion about **101**.
* Screws, plate, filament about **50**. Wiring, enclosure about **53**. Consumables about **12**.

Total **about 385 USD**. You can trim with a pre-owned PSU, but do not trim the E-stop or the fuses.

### Recommended build (about 590 USD, plus about 80 for tools if you have none)

* Eaton E-stop (35.54), IRM-20-5 instead of the buck (9.10), better buttons (about 4 each),
  encoder from a US seller (44.50), mains filter inlet, TVS and NTC options, PCB.
  Electronics about **273**.
* CL57T kit 64.34, Mädler 20 T + 40 T pulleys (17.05 + 24.81), belts, GT2 pair and spare belt.
  Motion about **134**.
* Hardware, aluminium, inserts, filament about **80**.
* Metal enclosure, GX16 connectors, cable, glands, ferrules about **105**.

Total **about 590 USD**. Tools (dial indicator, multimeter, crimper, pitch gauges, isolating transformer
or RCD), if you have none: add **about 80**.

---

## 8. What I could not verify online

* **CL57T-V41 on its own**: price not found (kit only). **CL57T V4.1 manual**: the PDF was not readable
  (HTTP 403). I used the **V4.0 manual** (Oyostepper copy) for all switch tables; read WIRING 4 before
  trusting SW6.
* **Motor datasheet and connector pinout/wire colours**: the StepperOnline datasheet PDF returned 403.
  The motor/encoder pin numbers in WIRING come from the StepperOnline UK page (motor pins 1-4 = A+/A-/B+/B-,
  encoder pins 1 = EA+, 2 = VCC, 3 = GND, 11 = EB+, 12 = EB-, 13 = EA-). Wire colours are **not**
  confirmed. Check them with a multimeter.
* **Prices marked (E)** in every table: EC11, Teensy header kit shipping, resistor/capacitor kits, fuses, relay
  socket, transistors, TVS, NTC, mains inlet, cable, glands, GX16 connectors, enclosure, screws, inserts,
  filament, tools, hub stock, motor plate, HTD-3M belt, GT2 belt, 22 mm NUT button, FAULT LED, encoder via AliExpress.
* **No URL found, and no price seen**: HTD-3M 15 mm closed-loop belt (any length), GT2 6 mm belt
  prices, BEMONOC 20 T pulley price, 74LVC14 SOIC price, AliExpress prices for anything.
* **Mean Well LRS-350-48 on DigiKey US**: no current US page in the results; I used Mouser (V) and
  an older DigiKey figure.
* **Teensy 4.1 at PJRC**: PJRC's store page shows no price and sends buyers to SparkFun. The price above is
  SparkFun / DigiKey.
* **Generic parts**: an ILI9341 module from a different vendor may have different pin order. Check the silkscreen.

## 9. Sources

* [CL57T V4.0 manual, Oyostepper copy](https://www.oyostepper.com/images/upload/File/CL57T_V4.0.pdf) (read in full)
* [StepperOnline kit 1-CL57T-S30A-V41](https://www.omc-stepperonline.com/ts-series-3-0-nm-424-92oz-in-1-axis-closed-loop-stepper-cnc-kit-nema-23-motor-driver-1-cl57t-s30a-v41)
* [StepperOnline motor 23HS45-4204D-E1000](https://www.omc-stepperonline.com/nema-23-closed-loop-stepper-motor-3-0nm-424oz-in-encoder-1000ppr-4000cpr-23hs45-4204d-e1000) (search result only; page returned 403)
* [StepperOnline UK 23HS45-4204D-E1000](https://www.stepperonline.co.uk/nema-23-closed-loop-stepper-motor-3-0nm-424-83oz-in-encoder-1000ppr-4000cpr-23hs45-4204d-e1000.html) (shaft, pinout)
* [SparkFun Teensy 4.1](https://www.sparkfun.com/teensy-4-1.html), [PJRC Teensy 4.1](https://www.pjrc.com/store/teensy41.html)
* [Mouser LRS-350-48](https://www.mouser.com/en/ProductDetail/MEAN-WELL/LRS-350-48?qs=ah3jBNVE1PSzhibo2xPJuA%3D%3D), [DigiKey IRM-20-5](https://www.digikey.com/en/products/detail/mean-well-usa-inc/IRM-20-5/7704667)
* [TI SN74LVC14A](https://www.ti.com/product/SN74LVC14A), [DigiKey SN74AHCT125N](https://www.digikey.com/en/products/detail/texas-instruments/SN74AHCT125N/375798)
* [DigiKey Omron G2R-2 DC5](https://www.digikey.com/en/products/detail/omron-electronics-inc-emc-div/G2R-2-DC5/368768)
* [Eaton M22-PVT-K02 at IMC Direct](https://www.imc-direct.com/products/m22-pvt-k02)
* [ShillehTek ILI9341 2.8 in](https://shillehtek.com/products/2-8-spi-tft-lcd-touch-screen-module-240x320-ili9341-for-arduino)
