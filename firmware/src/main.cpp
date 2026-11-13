// Teensy 4.1 IO layer for the electronic leadscrew. All decisions live in
// lib/els_core; this file only moves bits between the hardware and the core.
#include <Arduino.h>
#include <EEPROM.h>
#include <Encoder.h>
#include <ILI9341_t3.h>
#include <QuadEncoder.h>

#include "els.h"
#include "lathe_config.h"
#include "pins.h"
#include "ui.h"

namespace {

els::Controller g_els;
els::Ui g_ui;

QuadEncoder g_spindleEnc(1, PIN_SPINDLE_A, PIN_SPINDLE_B, 0);
IntervalTimer g_motionTimer;
Encoder g_knob(PIN_KNOB_A, PIN_KNOB_B);
ILI9341_t3 g_tft(PIN_TFT_CS, PIN_TFT_DC, PIN_TFT_RST);

// ---- Motion interrupt state (touched only inside the ISR) ----
int64_t g_spindleCount = 0;
uint32_t g_lastRaw = 0;
bool g_stepHigh = false;
bool g_dirPositive = true;
int g_dirWait = 0;
int32_t g_pendingSteps = 0;

FASTRUN void motionIsr() {
  // A pulse is high for exactly one tick, then low for at least one.
  const bool justLowered = g_stepHigh;
  if (g_stepHigh) {
    digitalWriteFast(PIN_STEP, LOW);
    g_stepHigh = false;
  }

  const uint32_t raw = (uint32_t)g_spindleEnc.read();
  g_spindleCount += (int32_t)(raw - g_lastRaw);  // wraps correctly across int32 overflow
  g_lastRaw = raw;
  const int64_t spindle = INVERT_SPINDLE ? -g_spindleCount : g_spindleCount;

  const bool estop = digitalReadFast(PIN_ESTOP) == HIGH;
  const bool alarm = digitalReadFast(PIN_DRIVER_ALARM) == ALARM_ACTIVE_LEVEL;
  g_pendingSteps += g_els.tick(spindle, estop, alarm);
  digitalWriteFast(PIN_ENABLE, g_els.driverEnabled() ? ENABLE_ACTIVE_LEVEL : !ENABLE_ACTIVE_LEVEL);

  if (justLowered) return;
  if (g_dirWait > 0) {
    --g_dirWait;
    return;
  }
  if (g_pendingSteps == 0) return;

  const bool positive = g_pendingSteps > 0;
  if (positive != g_dirPositive) {
    g_dirPositive = positive;
    digitalWriteFast(PIN_DIR, (positive != (bool)INVERT_DIR) ? HIGH : LOW);
    g_dirWait = DIR_SETUP_TICKS;
    return;
  }
  digitalWriteFast(PIN_STEP, HIGH);
  g_stepHigh = true;
  g_pendingSteps += positive ? -1 : 1;
}

// ---- Buttons ----
struct Key {
  uint8_t pin;
  els::Button button;
  bool down;
  uint8_t stableMs;
  uint32_t downAt;
  bool longSent;
};

Key g_keys[] = {
    {PIN_BTN_NUT, els::BTN_NUT, false, 0, 0, false},
    {PIN_BTN_MODE, els::BTN_MODE, false, 0, 0, false},
    {PIN_BTN_UNITS, els::BTN_UNITS, false, 0, 0, false},
    {PIN_BTN_DIR, els::BTN_DIR, false, 0, 0, false},
    {PIN_BTN_STOP_L, els::BTN_STOP_L, false, 0, 0, false},
    {PIN_BTN_STOP_R, els::BTN_STOP_R, false, 0, 0, false},
    {PIN_BTN_JOG_L, els::BTN_JOG_L, false, 0, 0, false},
    {PIN_BTN_JOG_R, els::BTN_JOG_R, false, 0, 0, false},
    {PIN_BTN_RETURN, els::BTN_RETURN, false, 0, 0, false},
    {PIN_KNOB_SW, els::BTN_KNOB, false, 0, 0, false},
};
const uint8_t kDebounceMs = 8;
const uint32_t kLongPressMs = 1000;
const int kKnobCountsPerDetent = 4;  // EC11: 4 quadrature counts per click

void scanKeys(uint32_t now) {
  for (Key& k : g_keys) {
    const bool raw = digitalReadFast(k.pin) == LOW;
    if (raw == k.down) {
      k.stableMs = 0;
    } else if (++k.stableMs >= kDebounceMs) {
      k.down = raw;
      k.stableMs = 0;
      noInterrupts();
      if (raw) {
        k.downAt = now;
        k.longSent = false;
        g_els.press(k.button);
      } else {
        g_els.release(k.button);
      }
      interrupts();
    }
    if (k.down && !k.longSent && now - k.downAt >= kLongPressMs) {
      k.longSent = true;
      noInterrupts();
      g_els.longPress(k.button);
      interrupts();
    }
  }
}

int32_t g_knobLast = 0;
void scanKnob() {
  const int32_t pos = g_knob.read();
  const int32_t detents = (pos - g_knobLast) / kKnobCountsPerDetent;
  if (detents == 0) return;
  g_knobLast += detents * kKnobCountsPerDetent;
  noInterrupts();
  g_els.knob((int)detents);
  interrupts();
}

// ---- Display ----
class TftGfx : public els::Gfx {
 public:
  explicit TftGfx(ILI9341_t3& t) : tft_(t) {}
  void fillRect(int x, int y, int w, int h, uint16_t c) override { tft_.fillRect(x, y, w, h, c); }
  void text(int x, int y, const char* s, int size, uint16_t fg, uint16_t bg) override {
    tft_.setTextSize(size);
    tft_.setTextColor(fg, bg);
    tft_.setCursor(x, y);
    tft_.print(s);
  }

 private:
  ILI9341_t3& tft_;
};
TftGfx g_gfx(g_tft);

// ---- Settings persistence ----
struct Stored {
  uint32_t magic;
  els::Settings settings;
};
const uint32_t kMagic = 0x454C5331;  // "ELS1"

void saveSettingsIfChanged(uint32_t now) {
  static uint16_t savedVersion = 0;
  static uint16_t seenVersion = 0;
  static uint32_t changedAt = 0;
  const uint16_t v = g_els.settingsVersion();
  if (v != seenVersion) {
    seenVersion = v;
    changedAt = now;
  }
  // Wait for the knob to settle so we don't wear the flash on every click.
  if (v != savedVersion && now - changedAt > 3000) {
    Stored s{kMagic, g_els.settings()};
    EEPROM.put(0, s);
    savedVersion = v;
  }
}

els::MachineConfig makeConfig() {
  const els::Ratio leadscrewPitch = LEADSCREW_TPI > 0
                                        ? els::pitchFromTpiX10((int64_t)LEADSCREW_TPI * 10)
                                        : els::pitchFromMicrons(LEADSCREW_PITCH_UM);
  els::MachineConfig cfg;
  cfg.countsPerRev = els::spindleCountsPerRev(ENCODER_CPR, ENCODER_TURNS, SPINDLE_TURNS);
  cfg.stepsPerMm = els::leadscrewStepsPerMm(MOTOR_STEPS_PER_REV, MOTOR_PULLEY_TEETH,
                                            LEADSCREW_PULLEY_TEETH, GEARBOX_RATIO_NUM,
                                            GEARBOX_RATIO_DEN, leadscrewPitch);
  cfg.tickHz = (float)MOTION_TICK_HZ;
  cfg.maxSpeedMmS = MAX_SPEED_MM_S;
  cfg.accelMmS2 = ACCEL_MM_S2;
  cfg.jogSpeedMmS = JOG_SPEED_MM_S;
  cfg.trackingGainPerS = TRACKING_GAIN;
  return cfg;
}

}  // namespace

void setup() {
  // Driver disabled until the core says otherwise.
  pinMode(PIN_ENABLE, OUTPUT);
  digitalWriteFast(PIN_ENABLE, !ENABLE_ACTIVE_LEVEL);
  pinMode(PIN_STEP, OUTPUT);
  pinMode(PIN_DIR, OUTPUT);
  digitalWriteFast(PIN_STEP, LOW);
  digitalWriteFast(PIN_DIR, INVERT_DIR ? LOW : HIGH);
  pinMode(PIN_DRIVER_ALARM, INPUT_PULLUP);
  pinMode(PIN_ESTOP, INPUT_PULLUP);
  pinMode(PIN_LED_NUT, OUTPUT);
  pinMode(PIN_LED_FAULT, OUTPUT);
  for (Key& k : g_keys) pinMode(k.pin, INPUT_PULLUP);

  Serial.begin(115200);

  g_spindleEnc.setInitConfig();
  g_spindleEnc.EncConfig.filterCount = 3;         // reject glitches shorter than ~4 samples
  g_spindleEnc.EncConfig.filterSamplePeriod = 4;  // of the 150 MHz IPG clock
  g_spindleEnc.init();
  g_lastRaw = (uint32_t)g_spindleEnc.read();

  Stored stored;
  EEPROM.get(0, stored);
  const els::MachineConfig cfg = makeConfig();
  g_els.begin(cfg, stored.magic == kMagic ? &stored.settings : nullptr);

  g_tft.begin();
  g_tft.setRotation(1);  // landscape 320x240
  g_ui.render(g_gfx, g_els.status(), millis(), true);

  g_knobLast = g_knob.read();
  g_motionTimer.priority(16);
  g_motionTimer.begin(motionIsr, 1000000.0f / (float)MOTION_TICK_HZ);
}

void loop() {
  static uint32_t lastScan = 0, lastDraw = 0, lastLog = 0;
  const uint32_t now = millis();

  if (now != lastScan) {
    lastScan = now;
    scanKeys(now);
    scanKnob();
  }

  if (now - lastDraw >= 50) {
    lastDraw = now;
    noInterrupts();
    const els::Status st = g_els.status();
    interrupts();
    g_ui.render(g_gfx, st, now);

    const bool blink = (now / 200) % 2;
    digitalWriteFast(PIN_LED_NUT, st.nut == els::Nut::Engaged || (st.nut == els::Nut::Armed && blink));
    digitalWriteFast(PIN_LED_FAULT, st.fault != els::Fault::None);

    if (Serial && now - lastLog >= 500) {
      lastLog = now;
      Serial.printf("rpm=%.1f x=%.3f nut=%d fault=%d %s\n", st.spindleRpm, st.positionMm,
                    (int)st.nut, (int)st.fault, st.pitchText);
    }
  }

  saveSettingsIfChanged(now);
}
