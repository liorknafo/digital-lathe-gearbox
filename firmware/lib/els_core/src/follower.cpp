#include "follower.h"

#include "els_math.h"

namespace els {

// Braking curves use a little less than the real accel so the discrete ramp can follow them.
static const float kBrakeMargin = 0.85f;

void Follower::configure(float tickHz, float vmax, float amax, float kp) {
  dt_ = 1.0f / tickHz;
  // At most half a step per tick: guarantees at least one idle tick between steps,
  // which is what lets the IO layer emit a full-width pulse on every step.
  vmax_ = minf(vmax, 0.45f * tickHz);
  amax_ = amax;
  kp_ = kp;
}

void Follower::reset(int32_t position) {
  pos_ = position;
  frac_ = 0;
  vel_ = 0;
  velocityMode_ = true;
  cmdVel_ = 0;
}

void Follower::setLimits(bool hasLo, int32_t lo, bool hasHi, int32_t hi) {
  hasLo_ = hasLo;
  lo_ = lo;
  hasHi_ = hasHi;
  hi_ = hi;
}

void Follower::commandPosition(int64_t target, float targetVel) {
  velocityMode_ = false;
  target_ = target;
  targetVel_ = targetVel;
}

void Follower::commandVelocity(float vel) {
  velocityMode_ = true;
  cmdVel_ = vel;
}

void Follower::halt() {
  vel_ = 0;
  frac_ = 0;
  velocityMode_ = true;
  cmdVel_ = 0;
}

int8_t Follower::step() {
  const float x = (float)pos_ + frac_;
  float want;

  if (velocityMode_) {
    want = cmdVel_;
  } else {
    // A target past a stop is held at the stop, standing still.
    int64_t t = target_;
    float tv = targetVel_;
    if (hasHi_ && t > hi_) {
      t = hi_;
      tv = 0;
    }
    if (hasLo_ && t < lo_) {
      t = lo_;
      tv = 0;
    }
    const float e = (float)(t - pos_) - frac_;
    const float ae = absf(e);
    // Arrived at a stationary target: settle exactly instead of decaying forever.
    if (tv == 0 && ae < 0.02f && absf(vel_) <= kp_ * 0.02f) {
      vel_ = 0;
      frac_ = 0;
      return 0;
    }
    // Linear near the target (smooth lock), time-optimal sqrt braking far away.
    const float corr = minf(kp_ * ae, sqrtf_(2.0f * amax_ * kBrakeMargin * ae));
    want = tv + (e >= 0 ? corr : -corr);
  }

  // Never plan to arrive at a stop faster than we can brake.
  if (hasHi_) {
    const float room = (float)hi_ - x;
    const float lim = room > 0 ? sqrtf_(2.0f * amax_ * kBrakeMargin * room) : 0.0f;
    if (want > lim) want = lim;
  }
  if (hasLo_) {
    const float room = x - (float)lo_;
    const float lim = room > 0 ? sqrtf_(2.0f * amax_ * kBrakeMargin * room) : 0.0f;
    if (want < -lim) want = -lim;
  }

  want = clampf(want, -vmax_, vmax_);
  const float dvMax = amax_ * dt_;
  vel_ += clampf(want - vel_, -dvMax, dvMax);

  frac_ += vel_ * dt_;
  if (frac_ >= 0.5f) {
    frac_ -= 1.0f;
    ++pos_;
    return 1;
  }
  if (frac_ < -0.5f) {
    frac_ += 1.0f;
    --pos_;
    return -1;
  }
  return 0;
}

}  // namespace els
