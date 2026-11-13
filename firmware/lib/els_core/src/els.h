// Electronic leadscrew controller: modes, the electronic half-nut, thread sync,
// stops, jog/return and faults. Hardware independent; the IO layer calls tick()
// from the motion interrupt and the button/knob handlers from the main loop
// (with interrupts masked around each call).
#pragma once
#include <stdint.h>

#include "els_math.h"
#include "follower.h"
#include "pitch.h"

namespace els {

struct MachineConfig {
  // Encoder counts per spindle revolution. May be fractional when the encoder is
  // geared to the spindle (e.g. 2400 * 2/9); see spindleCountsPerRev().
  Ratio countsPerRev;
  Ratio stepsPerMm;             // motor steps per mm of carriage travel
  float tickHz;                 // rate tick() is called at
  float maxSpeedMmS;            // fastest synchronised / rapid carriage speed
  float accelMmS2;
  float jogSpeedMmS;
  float trackingGainPerS;       // position loop gain; 150-300 is sensible
};

// Counts per spindle rev for an encoder with `encoderCpr` counts per its own rev
// (quadrature) that turns `encoderTurns` times for every `spindleTurns` spindle turns.
Ratio spindleCountsPerRev(int32_t encoderCpr, int32_t encoderTurns, int32_t spindleTurns);

// steps/mm for: motor (steps/rev) -> belt (motorTeeth:leadTeeth) -> gearbox
// (gbNum input revs per gbDen leadscrew revs) -> leadscrew (pitch mm/rev).
Ratio leadscrewStepsPerMm(int32_t motorStepsPerRev, int32_t motorPulleyTeeth,
                          int32_t leadscrewPulleyTeeth, int32_t gearboxNum,
                          int32_t gearboxDen, Ratio leadscrewPitchMm);

enum class Nut : uint8_t { Open, Armed, Engaged };
enum class Fault : uint8_t { None, EStop, DriverAlarm, Overspeed };
enum class KnobMode : uint8_t { Pitch, Jog001, Jog01, Jog1 };
enum class Msg : uint8_t {
  None,
  NewThread,     // thread sync reset
  SyncKept,      // armed: waiting for the matching spindle angle
  AtStop,        // nut opened at a stop
  NoReturnPoint, // RETURN with nothing to return to
  Busy,          // key ignored while the nut is closed
  TooFast,       // spindle too fast for this pitch
  FaultCleared,
};

enum Button : uint8_t {
  BTN_NUT,
  BTN_MODE,
  BTN_UNITS,
  BTN_DIR,
  BTN_STOP_L,
  BTN_STOP_R,
  BTN_JOG_L,
  BTN_JOG_R,
  BTN_RETURN,
  BTN_KNOB,
  BTN_COUNT
};

// User choices worth keeping across power cycles.
struct Settings {
  Mode mode;
  Units units;
  bool towardTailstock;  // false = normal (carriage moves toward the headstock / RH thread)
  uint8_t index[2][2];   // [mode][units] table index
};

struct Status {
  Mode mode;
  Units units;
  bool towardTailstock;
  Nut nut;
  Fault fault;
  KnobMode knobMode;
  bool synced;        // a thread phase is stored (thread mode)
  bool moving;
  bool jogging;
  char pitchText[16];
  float positionMm;   // carriage, +X toward tailstock
  float velocityMmS;
  bool hasLeftStop, hasRightStop;
  float leftStopMm, rightStopMm;
  float spindleRpm;
  float maxRpm;       // fastest spindle speed this pitch can be followed at
  Msg msg;
  uint16_t msgSeq;    // increments on every new message
};

class Controller {
 public:
  void begin(const MachineConfig& cfg, const Settings* saved);

  // Motion interrupt. Returns -1/0/+1 step to emit.
  int8_t tick(int64_t spindleCount, bool estopTripped, bool driverAlarm);
  bool driverEnabled() const { return driverEnabled_; }

  void press(Button b);
  void release(Button b);
  void longPress(Button b);  // fired once while still held (~1 s)
  void knob(int detents);

  Status status() const;
  const Settings& settings() const { return settings_; }
  uint16_t settingsVersion() const { return settingsVersion_; }

  // Test / simulator visibility.
  int32_t positionSteps() const { return follower_.position(); }
  int64_t targetAt(int64_t spindleCount) const;
  Ratio stepsPerCount() const { return ratio_; }
  bool anchorValid() const { return anchorValid_; }
  int64_t anchorSpindle() const { return anchorS_; }
  int64_t anchorPosition() const { return anchorZ_; }
  Nut nut() const { return nut_; }
  Fault fault() const { return fault_; }
  float spindleCountsPerSec() const { return spindleRate_; }
  const MachineConfig& config() const { return cfg_; }

 private:
  enum class Motion : uint8_t { Hold, Jog, Stopping };

  void applySettings(bool keepAnchor);
  void updateLimits();
  void setMsg(Msg m);
  void raiseFault(Fault f);
  bool tryClearFault();
  void openNut();
  void engage(int64_t s0, int64_t z0);
  void arm();
  void jog(int dir);
  int32_t mmToSteps(float mm) const;
  float stepsToMm(float steps) const;
  float maxTargetSpeed() const;  // steps/s the follower may be asked to synchronise at

  MachineConfig cfg_{};
  Settings settings_{};
  uint16_t settingsVersion_ = 0;
  Follower follower_;
  bool driverEnabled_ = true;
  int32_t enableSettle_ = 0;  // ticks to wait after enabling the driver before stepping

  Ratio ratio_{0, 1};  // signed steps per spindle count

  // Spindle.
  int64_t spindle_ = 0;
  float spindleRate_ = 0;  // counts/s
  int spindleDir_ = 1;     // last confidently seen direction
  static const int kRateSlots = 64;
  static const int kRateDecim = 16;
  int64_t rateRing_[kRateSlots] = {};
  int rateHead_ = 0;
  int rateFill_ = 0;
  int rateDecim_ = 0;

  // Nut / thread phase.
  Nut nut_ = Nut::Open;
  bool anchorValid_ = false;
  int64_t anchorS_ = 0;
  int64_t anchorZ_ = 0;
  int64_t armS0_ = 0;
  int armDir_ = 1;
  int32_t armPos_ = 0;

  // Open-nut motion.
  Motion motion_ = Motion::Hold;
  int64_t holdPos_ = 0;
  int jogDir_ = 0;
  bool hasPassStart_ = false;
  int32_t passStart_ = 0;

  bool hasLo_ = false, hasHi_ = false;
  int32_t lo_ = 0, hi_ = 0;

  Fault fault_ = Fault::None;
  bool lastEstop_ = false;
  bool lastAlarm_ = false;
  bool longFired_[BTN_COUNT] = {};
  KnobMode knobMode_ = KnobMode::Pitch;
  Msg msg_ = Msg::None;
  uint16_t msgSeq_ = 0;
};

}  // namespace els
