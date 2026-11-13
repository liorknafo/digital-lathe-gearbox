// Step generator that chases a position (or velocity) command under accel / speed
// limits and never runs through a soft stop. One call to step() = one motion tick.
#pragma once
#include <stdint.h>

namespace els {

class Follower {
 public:
  // All units are steps, steps/s, steps/s^2. kp is the position-error gain in 1/s.
  void configure(float tickHz, float vmax, float amax, float kp);
  void reset(int32_t position);

  void setLimits(bool hasLo, int32_t lo, bool hasHi, int32_t hi);

  // Track `target` which itself moves at `targetVel` (feed-forward). Call every tick.
  void commandPosition(int64_t target, float targetVel);
  // Run at a constant velocity (jog, or 0 to decelerate to a stop).
  void commandVelocity(float vel);
  // Fault: stop dead (driver is disabled, no point ramping).
  void halt();

  // Advance one tick. Returns -1, 0 or +1 step. Never two steps in consecutive ticks.
  int8_t step();

  int32_t position() const { return pos_; }
  float exactPosition() const { return (float)pos_ + frac_; }
  float velocity() const { return vel_; }
  float maxVelocity() const { return vmax_; }
  bool atRest() const { return vel_ == 0.0f; }

 private:
  float dt_ = 1e-5f;
  float vmax_ = 1000;
  float amax_ = 1000;
  float kp_ = 200;

  int32_t pos_ = 0;
  float frac_ = 0;  // sub-step position in [-0.5, 0.5)
  float vel_ = 0;

  bool velocityMode_ = true;
  int64_t target_ = 0;
  float targetVel_ = 0;
  float cmdVel_ = 0;

  bool hasLo_ = false, hasHi_ = false;
  int32_t lo_ = 0, hi_ = 0;
};

}  // namespace els
