#include "els.h"

namespace els {

namespace {

// Spindle slower than this (rev/s) is treated as "not turning" for direction sensing.
const float kDirThresholdRevS = 0.05f;
// CL57T wants ENA asserted ~200 ms before the first DIR/PUL edge.
const float kEnableSettleS = 0.25f;
// Rebase the thread anchor before (s - s0) * num could get anywhere near int64 overflow.
const int64_t kRebaseCounts = (int64_t)1 << 36;

}  // namespace

Ratio spindleCountsPerRev(int32_t encoderCpr, int32_t encoderTurns, int32_t spindleTurns) {
  return makeRatio((int64_t)encoderCpr * encoderTurns, spindleTurns);
}

Ratio leadscrewStepsPerMm(int32_t motorStepsPerRev, int32_t motorPulleyTeeth,
                          int32_t leadscrewPulleyTeeth, int32_t gearboxNum,
                          int32_t gearboxDen, Ratio leadscrewPitchMm) {
  Ratio stepsPerLeadscrewRev =
      makeRatio((int64_t)motorStepsPerRev * leadscrewPulleyTeeth * gearboxNum,
                (int64_t)motorPulleyTeeth * gearboxDen);
  return div(stepsPerLeadscrewRev, leadscrewPitchMm);
}

// ---------------------------------------------------------------------------
// Setup

void Controller::begin(const MachineConfig& cfg, const Settings* saved) {
  cfg_ = cfg;
  const float spm = toFloat(cfg.stepsPerMm);
  follower_.configure(cfg.tickHz, cfg.maxSpeedMmS * spm, cfg.accelMmS2 * spm, cfg.trackingGainPerS);
  follower_.reset(0);
  holdPos_ = 0;
  enableSettle_ = (int32_t)(kEnableSettleS * cfg.tickHz);

  settings_.mode = Mode::Thread;
  settings_.units = Units::Metric;
  settings_.towardTailstock = false;
  for (int m = 0; m < 2; ++m)
    for (int u = 0; u < 2; ++u)
      settings_.index[m][u] = (uint8_t)defaultPitchIndex((Mode)m, (Units)u);

  if (saved && (uint8_t)saved->mode <= 1 && (uint8_t)saved->units <= 1) {
    bool ok = true;
    for (int m = 0; m < 2; ++m)
      for (int u = 0; u < 2; ++u)
        if (saved->index[m][u] >= pitchTableSize((Mode)m, (Units)u)) ok = false;
    if (ok) settings_ = *saved;
  }
  applySettings(false);
}

void Controller::applySettings(bool keepAnchor) {
  const Ratio pitch = pitchAt(settings_.mode, settings_.units,
                              settings_.index[(int)settings_.mode][(int)settings_.units]);
  Ratio r = div(mul(pitch, cfg_.stepsPerMm), cfg_.countsPerRev);
  // Spindle forward normally drives the carriage toward the headstock (-X).
  if (!settings_.towardTailstock) r.num = -r.num;
  ratio_ = r;
  if (!keepAnchor) anchorValid_ = false;
  ++settingsVersion_;
}

void Controller::updateLimits() { follower_.setLimits(hasLo_, lo_, hasHi_, hi_); }

void Controller::setMsg(Msg m) {
  msg_ = m;
  ++msgSeq_;
}

int32_t Controller::mmToSteps(float mm) const {
  float s = mm * toFloat(cfg_.stepsPerMm);
  return (int32_t)(s < 0 ? s - 0.5f : s + 0.5f);
}

float Controller::stepsToMm(float steps) const { return steps / toFloat(cfg_.stepsPerMm); }

float Controller::maxTargetSpeed() const {
  // Keep 10% in hand so the follower can still close a small lag.
  return follower_.maxVelocity() * 0.9f;
}

int64_t Controller::targetAt(int64_t s) const {
  return anchorZ_ + floorDiv((s - anchorS_) * ratio_.num, ratio_.den);
}

// ---------------------------------------------------------------------------
// Nut

void Controller::openNut() {
  nut_ = Nut::Open;
  motion_ = Motion::Stopping;
  jogDir_ = 0;
}

void Controller::engage(int64_t s0, int64_t z0) {
  anchorS_ = s0;
  anchorZ_ = z0;
  if (settings_.mode == Mode::Thread) anchorValid_ = true;
  nut_ = Nut::Engaged;
  motion_ = Motion::Hold;
  passStart_ = follower_.position();
  hasPassStart_ = true;
}

// The thread is periodic in whole spindle revolutions, so the stored phase may be
// shifted by any whole number of revolutions that is also a whole number of counts:
// countsPerRev.num counts = countsPerRev.den revolutions (1 rev for an integer CPR;
// 3 revs = 1600 counts for a 2400-count encoder at 2/9 spindle speed). Pick the shift whose target next passes
// the parked carriage in the direction the spindle is turning.
void Controller::arm() {
  const int64_t period = cfg_.countsPerRev.num;
  const double sCross =
      (double)anchorS_ + (double)(armPos_ - anchorZ_) * (double)ratio_.den / (double)ratio_.num;
  const double behind = ((double)spindle_ - sCross) / (double)period;
  armDir_ = spindleDir_;
  const double k = armDir_ > 0 ? floorD(behind) + 1.0 : ceilD(behind) - 1.0;
  armS0_ = anchorS_ + (int64_t)k * period;
  nut_ = Nut::Armed;
}

// ---------------------------------------------------------------------------
// Faults

void Controller::raiseFault(Fault f) {
  fault_ = f;
  if (f == Fault::Overspeed) {
    openNut();
    return;
  }
  // E-stop / driver alarm: the motor may have moved without us, so the thread
  // phase can no longer be trusted.
  follower_.halt();
  nut_ = Nut::Open;
  motion_ = Motion::Hold;
  holdPos_ = follower_.position();
  jogDir_ = 0;
  anchorValid_ = false;
  driverEnabled_ = false;
}

bool Controller::tryClearFault() {
  if (fault_ == Fault::EStop && lastEstop_) return false;
  if (fault_ == Fault::DriverAlarm && lastAlarm_) return false;
  fault_ = Fault::None;
  driverEnabled_ = true;
  enableSettle_ = (int32_t)(kEnableSettleS * cfg_.tickHz);
  if (motion_ != Motion::Stopping) {
    motion_ = Motion::Hold;
    holdPos_ = follower_.position();
  }
  setMsg(Msg::FaultCleared);
  return true;
}

// ---------------------------------------------------------------------------
// Motion tick

int8_t Controller::tick(int64_t s, bool estop, bool alarm) {
  spindle_ = s;
  lastEstop_ = estop;
  lastAlarm_ = alarm;

  // Spindle speed: count difference over a ~10 ms sliding window.
  if (++rateDecim_ >= kRateDecim) {
    rateDecim_ = 0;
    rateRing_[rateHead_] = s;
    rateHead_ = (rateHead_ + 1) % kRateSlots;
    if (rateFill_ < kRateSlots) ++rateFill_;
    if (rateFill_ >= 2) {
      const int oldest = rateFill_ < kRateSlots ? 0 : rateHead_;
      spindleRate_ = (float)(s - rateRing_[oldest]) * cfg_.tickHz /
                     (float)((rateFill_ - 1) * kRateDecim);
    }
    const float thr = kDirThresholdRevS * toFloat(cfg_.countsPerRev);
    if (spindleRate_ > thr) spindleDir_ = 1;
    if (spindleRate_ < -thr) spindleDir_ = -1;
  }

  if (estop) {
    if (fault_ != Fault::EStop) raiseFault(Fault::EStop);
  } else if (alarm && fault_ != Fault::EStop && fault_ != Fault::DriverAlarm) {
    raiseFault(Fault::DriverAlarm);
  }
  if (fault_ == Fault::EStop || fault_ == Fault::DriverAlarm) {
    driverEnabled_ = false;
    return 0;
  }
  if (enableSettle_ > 0) {
    --enableSettle_;
    return 0;
  }

  const float ratioF = toFloat(ratio_);
  const float targetVel = ratioF * spindleRate_;

  if (nut_ == Nut::Engaged) {
    if ((s - anchorS_) > kRebaseCounts || (anchorS_ - s) > kRebaseCounts) {
      const int64_t m = (s - anchorS_) / ratio_.den;
      anchorS_ += m * ratio_.den;
      anchorZ_ += m * ratio_.num;
    }
    if (absf(targetVel) > maxTargetSpeed()) {
      raiseFault(Fault::Overspeed);
      setMsg(Msg::TooFast);
    } else {
      const int64_t t = targetAt(s);
      follower_.commandPosition(t, targetVel);
      // Parked on a stop the target wants to go past: the nut opens itself.
      const float x = follower_.exactPosition();
      const float slow = 0.02f * follower_.maxVelocity();
      const bool atHi = hasHi_ && t > hi_ && absf(x - (float)hi_) < 0.5f;
      const bool atLo = hasLo_ && t < lo_ && absf(x - (float)lo_) < 0.5f;
      if ((atHi || atLo) && absf(follower_.velocity()) < slow) {
        nut_ = Nut::Open;
        motion_ = Motion::Hold;
        holdPos_ = atHi ? hi_ : lo_;
        setMsg(Msg::AtStop);
      }
    }
  }

  if (nut_ == Nut::Armed) {
    if (spindleDir_ != armDir_) arm();
    const int64_t t = anchorZ_ + floorDiv((s - armS0_) * ratio_.num, ratio_.den);
    const int sg = (ratio_.num > 0 ? 1 : -1) * armDir_;
    if ((t - armPos_) * sg >= 0) {
      const int64_t slack = 2 + (int64_t)(4.0f * absf(targetVel) / cfg_.tickHz);
      if (absf(targetVel) > maxTargetSpeed()) {
        setMsg(Msg::TooFast);
        arm();  // try again next revolution
      } else if (abs64(t - armPos_) > slack || follower_.position() != armPos_ ||
                 !follower_.atRest()) {
        arm();  // carriage not parked yet (or spindle jumped): never lunge, wait a rev
      } else {
        engage(armS0_, anchorZ_);
        follower_.commandPosition(t, targetVel);
      }
    }
    if (nut_ == Nut::Armed) follower_.commandPosition(armPos_, 0);
  }

  if (nut_ == Nut::Open) {
    if (motion_ == Motion::Jog) {
      follower_.commandVelocity((float)jogDir_ * cfg_.jogSpeedMmS * toFloat(cfg_.stepsPerMm));
    } else if (motion_ == Motion::Stopping) {
      follower_.commandVelocity(0);
      if (follower_.atRest()) {
        motion_ = Motion::Hold;
        holdPos_ = follower_.position();
      }
    }
    if (motion_ == Motion::Hold) follower_.commandPosition(holdPos_, 0);
  }

  return follower_.step();
}

// ---------------------------------------------------------------------------
// Buttons

void Controller::jog(int dir) {
  motion_ = Motion::Jog;
  jogDir_ = dir;
}

void Controller::press(Button b) {
  longFired_[b] = false;
  if (fault_ != Fault::None) {
    tryClearFault();
    return;
  }
  if (enableSettle_ > 0) return;  // driver still settling after enable
  const bool open = nut_ == Nut::Open;

  switch (b) {
    case BTN_NUT:
      if (nut_ == Nut::Engaged) {
        openNut();
      } else if (nut_ == Nut::Armed) {
        nut_ = Nut::Open;
        motion_ = Motion::Hold;
        holdPos_ = armPos_;
      } else if (motion_ == Motion::Jog) {
        setMsg(Msg::Busy);
      } else {
        // While a stop is still being ramped down, engage where the carriage will rest.
        if (motion_ == Motion::Stopping) {
          const float v = follower_.velocity();
          const float a = cfg_.accelMmS2 * toFloat(cfg_.stepsPerMm);
          const float rest = follower_.exactPosition() + v * absf(v) / (2.0f * a);
          holdPos_ = (int64_t)(rest < 0 ? rest - 0.5f : rest + 0.5f);
          motion_ = Motion::Hold;
        }
        if (settings_.mode == Mode::Thread && anchorValid_) {
          armPos_ = (int32_t)holdPos_;
          arm();
          setMsg(Msg::SyncKept);
        } else {
          if (settings_.mode == Mode::Thread) setMsg(Msg::NewThread);
          engage(spindle_, holdPos_);
        }
      }
      break;

    case BTN_MODE:
      break;  // acts on release (long press = new thread)

    case BTN_UNITS:
      if (!open) {
        setMsg(Msg::Busy);
        break;
      }
      settings_.units = settings_.units == Units::Metric ? Units::Imperial : Units::Metric;
      applySettings(false);
      break;

    case BTN_DIR:
      if (!open) {
        setMsg(Msg::Busy);
        break;
      }
      settings_.towardTailstock = !settings_.towardTailstock;
      applySettings(false);
      break;

    case BTN_STOP_L:
    case BTN_STOP_R: {
      // Put the stop where we can actually stop if we are moving toward it.
      const float v = follower_.velocity();
      const float a = cfg_.accelMmS2 * toFloat(cfg_.stepsPerMm);
      float x = follower_.exactPosition();
      const bool towardIt = (b == BTN_STOP_L) ? v < 0 : v > 0;
      if (towardIt) x += v * absf(v) / (2.0f * a * 0.85f);
      const int32_t p = (int32_t)(x < 0 ? x - 0.5f : x + 0.5f);
      if (b == BTN_STOP_L) {
        hasLo_ = true;
        lo_ = (hasHi_ && p > hi_) ? hi_ : p;
      } else {
        hasHi_ = true;
        hi_ = (hasLo_ && p < lo_) ? lo_ : p;
      }
      updateLimits();
      break;
    }

    case BTN_JOG_L:
    case BTN_JOG_R:
      if (!open) {
        setMsg(Msg::Busy);
        break;
      }
      jog(b == BTN_JOG_L ? -1 : 1);
      break;

    case BTN_RETURN: {
      if (!open || motion_ == Motion::Jog) {
        setMsg(Msg::Busy);
        break;
      }
      // Start of pass = the stop opposite the feed direction.
      const bool startIsRight = !settings_.towardTailstock;
      if (startIsRight && hasHi_) {
        holdPos_ = hi_;
      } else if (!startIsRight && hasLo_) {
        holdPos_ = lo_;
      } else if (hasPassStart_) {
        holdPos_ = passStart_;
      } else {
        setMsg(Msg::NoReturnPoint);
        break;
      }
      motion_ = Motion::Hold;
      break;
    }

    case BTN_KNOB:
      knobMode_ = (KnobMode)(((uint8_t)knobMode_ + 1) % 4);
      break;

    default:
      break;
  }
}

void Controller::release(Button b) {
  const bool wasLong = longFired_[b];
  longFired_[b] = false;
  if (fault_ != Fault::None) return;

  if ((b == BTN_JOG_L && jogDir_ < 0) || (b == BTN_JOG_R && jogDir_ > 0)) {
    if (motion_ == Motion::Jog) {
      motion_ = Motion::Stopping;
      jogDir_ = 0;
    }
  }

  if (b == BTN_MODE && !wasLong) {
    if (nut_ != Nut::Open) {
      setMsg(Msg::Busy);
      return;
    }
    settings_.mode = settings_.mode == Mode::Thread ? Mode::Feed : Mode::Thread;
    applySettings(false);
  }
}

void Controller::longPress(Button b) {
  longFired_[b] = true;
  if (fault_ != Fault::None) return;
  switch (b) {
    case BTN_STOP_L:
      hasLo_ = false;
      updateLimits();
      break;
    case BTN_STOP_R:
      hasHi_ = false;
      updateLimits();
      break;
    case BTN_MODE:
      if (nut_ != Nut::Open) {
        setMsg(Msg::Busy);
        break;
      }
      anchorValid_ = false;
      hasPassStart_ = false;
      setMsg(Msg::NewThread);
      break;
    default:
      break;
  }
}

void Controller::knob(int detents) {
  if (detents == 0 || fault_ != Fault::None) return;

  if (knobMode_ == KnobMode::Pitch) {
    const bool feedLive = nut_ == Nut::Engaged && settings_.mode == Mode::Feed;
    if (nut_ != Nut::Open && !feedLive) {
      setMsg(Msg::Busy);
      return;
    }
    uint8_t& idx = settings_.index[(int)settings_.mode][(int)settings_.units];
    int next = (int)idx + detents;
    const int n = pitchTableSize(settings_.mode, settings_.units);
    next = next < 0 ? 0 : (next >= n ? n - 1 : next);
    if (next == idx) return;
    idx = (uint8_t)next;
    if (feedLive) {
      // Change feed rate on the fly: re-anchor at the current target so it stays continuous.
      const int64_t t = targetAt(spindle_);
      applySettings(true);
      anchorS_ = spindle_;
      anchorZ_ = t;
    } else {
      applySettings(false);
    }
    return;
  }

  if (nut_ != Nut::Open || motion_ == Motion::Jog) {
    setMsg(Msg::Busy);
    return;
  }
  int64_t um = 10;
  if (knobMode_ == KnobMode::Jog01) um = 100;
  if (knobMode_ == KnobMode::Jog1) um = 1000;
  if (settings_.units == Units::Imperial) um = um * 254 / 100;  // 0.001 / 0.01 / 0.1 in
  const Ratio steps = mul(makeRatio(um * detents, 1000), cfg_.stepsPerMm);
  if (motion_ == Motion::Stopping) holdPos_ = follower_.position();
  motion_ = Motion::Hold;
  holdPos_ += floorDiv(2 * steps.num + steps.den, 2 * steps.den);  // nearest step: +n then -n returns home
  if (hasLo_ && holdPos_ < lo_) holdPos_ = lo_;
  if (hasHi_ && holdPos_ > hi_) holdPos_ = hi_;
}

// ---------------------------------------------------------------------------

Status Controller::status() const {
  Status st;
  st.mode = settings_.mode;
  st.units = settings_.units;
  st.towardTailstock = settings_.towardTailstock;
  st.nut = nut_;
  st.fault = fault_;
  st.knobMode = knobMode_;
  st.synced = settings_.mode == Mode::Thread && anchorValid_;
  st.moving = !follower_.atRest() || motion_ == Motion::Jog ||
              (nut_ == Nut::Open && motion_ == Motion::Hold && holdPos_ != follower_.position());
  st.jogging = motion_ == Motion::Jog;
  pitchLabel(settings_.mode, settings_.units,
             settings_.index[(int)settings_.mode][(int)settings_.units], st.pitchText,
             (int)sizeof(st.pitchText));
  st.positionMm = stepsToMm(follower_.exactPosition());
  st.velocityMmS = stepsToMm(follower_.velocity());
  st.hasLeftStop = hasLo_;
  st.hasRightStop = hasHi_;
  st.leftStopMm = stepsToMm((float)lo_);
  st.rightStopMm = stepsToMm((float)hi_);
  st.spindleRpm = spindleRate_ * 60.0f / toFloat(cfg_.countsPerRev);
  const float stepsPerRev = absf(toFloat(ratio_)) * toFloat(cfg_.countsPerRev);
  st.maxRpm = stepsPerRev > 0 ? maxTargetSpeed() / stepsPerRev * 60.0f : 0;
  st.msg = msg_;
  st.msgSeq = msgSeq_;
  return st;
}

}  // namespace els
