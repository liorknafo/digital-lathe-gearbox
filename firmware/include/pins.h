// Teensy 4.1 pin assignments. Keep in sync with docs/DESIGN.md and docs/WIRING.md.
#pragma once

// Spindle encoder (QuadEncoder channel 1 via XBAR — pins must be XBAR-capable).
#define PIN_SPINDLE_A 2
#define PIN_SPINDLE_B 3

// Stepper driver (through 74AHCT125 to 5 V levels).
#define PIN_STEP 5
#define PIN_DIR 6
#define PIN_ENABLE 7
#define PIN_DRIVER_ALARM 8

// ILI9341 TFT on SPI0 (MOSI 11, MISO 12, SCK 13).
#define PIN_TFT_DC 9
#define PIN_TFT_CS 10
#define PIN_TFT_RST 41

// Keypad: momentary switches to GND, internal pull-ups.
#define PIN_BTN_NUT 14
#define PIN_BTN_MODE 15
#define PIN_BTN_UNITS 16
#define PIN_BTN_DIR 17
#define PIN_BTN_STOP_L 18
#define PIN_BTN_STOP_R 19
#define PIN_BTN_JOG_L 20
#define PIN_BTN_JOG_R 21
#define PIN_BTN_RETURN 22

// E-stop sense: NC contact to GND, so HIGH = tripped (or wire broken).
#define PIN_ESTOP 23

#define PIN_LED_NUT 24
#define PIN_LED_FAULT 25

// Knob (EC11 or MPG through 74LVC14).
#define PIN_KNOB_A 30
#define PIN_KNOB_B 31
#define PIN_KNOB_SW 32
