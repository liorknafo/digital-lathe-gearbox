// Motion-core tests: run with `pio test -e native`.
#include <unity.h>

#include <algorithm>
#include <cmath>
#include <cstdio>

#include "els.h"

using namespace els;

namespace {

const int kCpr = 2400;
const float kTickHz = 100000.0f;

// Encoder counts per spindle rev for the next Rig; setUp() resets it to 1:1.
Ratio g_cpr = {kCpr, 1};
double cprD() { return (double)g_cpr.num / (double)g_cpr.den; }

MachineConfig defaultConfig() {
  MachineConfig c;
  c.countsPerRev = g_cpr;
  c.stepsPerMm = leadscrewStepsPerMm(1600, 20, 40, 1, 1, pitchFromTpiX10(80));  // 8 TPI
  c.tickHz = kTickHz;
  c.maxSpeedMmS = 40;
  c.accelMmS2 = 600;
  c.jogSpeedMmS = 20;
  c.trackingGainPerS = 200;
  return c;
}

// A lathe in a box: a spindle with finite acceleration driving the controller.
struct Rig {
  Controller els;
  double angleCounts = 0;  // spindle position, encoder counts (continuous)
  double rpm = 0;
  double rpmTarget = 0;
  double spindleAccelRpmS = 2000;
  bool estop = false;
  bool alarm = false;
  int lastStepTick = -10;
  int tickNo = 0;
  bool consecutiveSteps = false;

  explicit Rig(Mode mode = Mode::Thread, int metricIndexValueUm = 1500) {
    Settings s;
    s.mode = mode;
    s.units = Units::Metric;
    s.towardTailstock = false;
    for (int m = 0; m < 2; ++m)
      for (int u = 0; u < 2; ++u) s.index[m][u] = (uint8_t)defaultPitchIndex((Mode)m, (Units)u);
    els.begin(defaultConfig(), &s);
    setMetric(metricIndexValueUm);
    run(0.3);  // driver enable settle time
  }

  // Selects a metric pitch / feed by value via the knob.
  void setMetric(int um) {
    const Mode m = els.settings().mode;
    for (int i = 0; i < pitchTableSize(m, Units::Metric); ++i) {
      Ratio p = pitchAt(m, Units::Metric, i);
      if (p.num * 1000 == (int64_t)um * p.den) {
        els.knob(i - (int)els.settings().index[(int)m][0]);
        return;
      }
    }
    TEST_FAIL_MESSAGE("pitch not in table");
  }

  int64_t spindle() const { return (int64_t)std::floor(angleCounts); }

  void tick() {
    const double dt = 1.0 / kTickHz;
    const double dv = spindleAccelRpmS * dt;
    if (rpm < rpmTarget) rpm = std::min(rpm + dv, rpmTarget);
    if (rpm > rpmTarget) rpm = std::max(rpm - dv, rpmTarget);
    angleCounts += rpm / 60.0 * cprD() * dt;
    const int8_t st = els.tick(spindle(), estop, alarm);
    if (st != 0) {
      if (tickNo - lastStepTick < 2) consecutiveSteps = true;
      lastStepTick = tickNo;
    }
    ++tickNo;
  }

  void run(double seconds) {
    const int n = (int)(seconds * kTickHz);
    for (int i = 0; i < n; ++i) tick();
  }

  template <typename Pred>
  bool runUntil(Pred p, double maxSeconds) {
    const int n = (int)(maxSeconds * kTickHz);
    for (int i = 0; i < n; ++i) {
      if (p()) return true;
      tick();
    }
    return p();
  }

  float stepsPerMm() const { return toFloat(els.config().stepsPerMm); }
  int32_t mm(float v) const { return (int32_t)std::lround(v * stepsPerMm()); }
};

// Distance from `pos` to the nearest groove of the helix defined by (s0, z0, ratio),
// in steps. The helix repeats every spindle rev, i.e. every |ratio|*cpr steps.
double grooveError(const Rig& r, int64_t s0, int64_t z0, int64_t s, int32_t pos) {
  const Ratio q = r.els.stepsPerCount();
  const double ideal = (double)z0 + (double)(s - s0) * (double)q.num / (double)q.den;
  const double period = std::fabs((double)q.num / (double)q.den) * cprD();
  double d = std::fmod((double)pos - ideal, period);
  if (d > period / 2) d -= period;
  if (d < -period / 2) d += period;
  return d;
}

}  // namespace

void setUp() { g_cpr = {kCpr, 1}; }
void tearDown() {}

// ---------------------------------------------------------------------------

void test_steps_per_mm_is_exact() {
  // 1600 steps * 40/20 belt = 3200 steps per rev of an 8 TPI (3.175 mm) leadscrew.
  Ratio spm = defaultConfig().stepsPerMm;
  TEST_ASSERT_EQUAL_INT64(128000, spm.num);
  TEST_ASSERT_EQUAL_INT64(127, spm.den);
  // Roher TBL-20/520: 3 mm leadscrew -> exactly 3200/3 steps/mm (no rounding).
  Ratio roher = leadscrewStepsPerMm(1600, 20, 40, 1, 1, pitchFromMicrons(3000));
  TEST_ASSERT_EQUAL_INT64(3200, roher.num);
  TEST_ASSERT_EQUAL_INT64(3, roher.den);
}

void test_metric_thread_on_imperial_screw_has_no_drift() {
  Rig r(Mode::Thread, 1250);
  r.els.press(BTN_NUT);  // anchor at spindle 0, position 0
  const int64_t revs = 100000;  // 125 m of thread
  const int64_t t = r.els.targetAt(revs * kCpr);
  // Exactly floor(-1.25 mm * revs * 128000/127) steps: no accumulated rounding.
  TEST_ASSERT_EQUAL_INT64(floorDiv(-125 * revs * 128000, 100 * 127), t);
}

void test_pitch_labels() {
  char b[16];
  pitchLabel(Mode::Thread, Units::Metric, defaultPitchIndex(Mode::Thread, Units::Metric), b, 16);
  TEST_ASSERT_EQUAL_STRING("1.50 mm", b);
  pitchLabel(Mode::Thread, Units::Imperial, defaultPitchIndex(Mode::Thread, Units::Imperial), b, 16);
  TEST_ASSERT_EQUAL_STRING("20 TPI", b);
  pitchLabel(Mode::Feed, Units::Imperial, defaultPitchIndex(Mode::Feed, Units::Imperial), b, 16);
  TEST_ASSERT_EQUAL_STRING("0.0040 in/r", b);
  pitchLabel(Mode::Feed, Units::Metric, defaultPitchIndex(Mode::Feed, Units::Metric), b, 16);
  TEST_ASSERT_EQUAL_STRING("0.100 mm/r", b);
}

void test_feed_tracks_spindle_tightly() {
  Rig r(Mode::Feed, 200);
  r.rpmTarget = 600;
  r.run(0.5);  // spindle up to speed
  r.els.press(BTN_NUT);
  r.run(0.3);  // let the follower lock
  double worst = 0;
  for (int i = 0; i < 100000; ++i) {
    r.tick();
    const double err = (double)r.els.positionSteps() - (double)r.els.targetAt(r.spindle());
    worst = std::max(worst, std::fabs(err));
  }
  TEST_ASSERT_TRUE_MESSAGE(worst <= 3.0, "tracking error above 3 steps (3 um)");
  // 0.2 mm/rev at 600 rpm = 2 mm/s toward the headstock.
  TEST_ASSERT_FLOAT_WITHIN(0.1f, -2.0f, r.els.status().velocityMmS);
  TEST_ASSERT_FALSE(r.consecutiveSteps);
}

void test_stop_is_never_crossed_and_nut_opens() {
  Rig r(Mode::Feed, 1000);
  r.rpmTarget = 1000;  // 1 mm/rev at 1000 rpm = 16.7 mm/s
  r.run(0.6);
  const int32_t lo = -r.mm(10);
  // Put the left stop 10 mm toward the headstock by moving there with the knob in 1 mm jog mode.
  r.els.press(BTN_KNOB);
  r.els.press(BTN_KNOB);
  r.els.press(BTN_KNOB);  // Pitch -> .01 -> .1 -> 1.0
  r.els.knob(-10);
  TEST_ASSERT_TRUE(r.runUntil([&] { return !r.els.status().moving && r.els.positionSteps() == lo; }, 3));
  r.els.press(BTN_STOP_L);
  r.els.knob(10);
  TEST_ASSERT_TRUE(r.runUntil([&] { return !r.els.status().moving && r.els.positionSteps() == 0; }, 3));

  r.els.press(BTN_NUT);
  int32_t minPos = 0;
  const bool opened = r.runUntil(
      [&] {
        minPos = std::min(minPos, r.els.positionSteps());
        return r.els.nut() == Nut::Open;
      },
      3);
  TEST_ASSERT_TRUE(opened);
  TEST_ASSERT_TRUE(minPos >= lo);
  TEST_ASSERT_EQUAL_INT32(lo, r.els.positionSteps());
  TEST_ASSERT_EQUAL(Msg::AtStop, r.els.status().msg);
  r.run(0.2);
  TEST_ASSERT_EQUAL_INT32(lo, r.els.positionSteps());  // stays parked with the spindle running
}

// Threading to a shoulder, three passes: RETURN, a jog to an arbitrary spot, and a
// different spindle speed. Every pass must land in the same groove, within
// `tolSteps`. The nut may wait up to `syncRevs` spindle revs for the groove.
void threadToShoulder(double tolSteps, int syncRevs) {
  Rig r(Mode::Thread, 1500);
  r.rpmTarget = 300;
  r.run(0.5);

  r.els.press(BTN_STOP_R);  // start at 0
  r.els.press(BTN_KNOB);
  r.els.press(BTN_KNOB);
  r.els.press(BTN_KNOB);  // knob = 1 mm jog
  r.els.knob(-15);
  TEST_ASSERT_TRUE(r.runUntil([&] { return !r.els.status().moving; }, 3));
  r.els.press(BTN_STOP_L);  // shoulder at -15 mm
  r.els.press(BTN_RETURN);
  TEST_ASSERT_TRUE(r.runUntil([&] { return !r.els.status().moving; }, 3));
  TEST_ASSERT_EQUAL_INT32(0, r.els.positionSteps());

  // Pass 1 defines the thread.
  r.els.press(BTN_NUT);
  TEST_ASSERT_EQUAL(Nut::Engaged, r.els.nut());
  const int64_t s0 = r.els.anchorSpindle();
  const int64_t z0 = r.els.anchorPosition();
  const int32_t lockAfter = r.mm(-2);  // past the acceleration lag
  const int32_t lockBefore = r.mm(-13);

  auto cutPass = [&](const char* name) {
    double worst = 0;
    int samples = 0;
    const bool done = r.runUntil(
        [&] {
          const int32_t p = r.els.positionSteps();
          if (r.els.nut() == Nut::Engaged && p < lockAfter && p > lockBefore) {
            worst = std::max(worst, std::fabs(grooveError(r, s0, z0, r.spindle(), p)));
            ++samples;
          }
          return r.els.nut() == Nut::Open && !r.els.status().moving;
        },
        10);
    char msg[96];
    std::snprintf(msg, sizeof msg, "%s: worst groove error %.2f steps over %d samples", name,
                  worst, samples);
    TEST_MESSAGE(msg);
    TEST_ASSERT_TRUE_MESSAGE(done, msg);
    TEST_ASSERT_TRUE_MESSAGE(samples > 1000, msg);
    TEST_ASSERT_TRUE_MESSAGE(worst <= tolSteps, msg);
    TEST_ASSERT_EQUAL_INT32(r.mm(-15), r.els.positionSteps());
  };
  cutPass("pass 1");

  // Pass 2: RETURN to the start stop, re-arm.
  r.els.press(BTN_RETURN);
  TEST_ASSERT_TRUE(r.runUntil([&] { return !r.els.status().moving; }, 5));
  r.els.press(BTN_NUT);
  TEST_ASSERT_EQUAL(Nut::Armed, r.els.nut());
  TEST_ASSERT_TRUE(r.runUntil([&] { return r.els.nut() == Nut::Engaged; }, syncRevs * 0.2 + 0.05));
  cutPass("pass 2");

  // Pass 3: clear the start stop, knob to an odd start point beyond it, slower spindle.
  r.els.longPress(BTN_STOP_R);
  r.els.press(BTN_KNOB);
  r.els.press(BTN_KNOB);  // 1 mm -> pitch -> .01 mm
  r.els.knob(1537);       // +15.37 mm
  TEST_ASSERT_TRUE(r.runUntil([&] { return !r.els.status().moving; }, 5));
  TEST_ASSERT_EQUAL_INT32(r.mm(0.37f), r.els.positionSteps());
  r.rpmTarget = 180;
  r.run(0.3);
  r.els.press(BTN_NUT);
  TEST_ASSERT_TRUE(r.runUntil([&] { return r.els.nut() == Nut::Engaged; }, syncRevs / 3.0 + 0.07));
  cutPass("pass 3");
}

void test_nut_resync_keeps_thread_phase() { threadToShoulder(3.0, 1); }

// An encoder geared to the spindle at a ratio that gives a fractional count per rev:
// 2 turns per 9 spindle turns = 533.3 counts per rev. Counts come out whole every 3
// revs, so the nut may wait up to 3 revs; one count is 2.8 steps at 1.5 mm pitch, so
// allow 2 counts.
void test_fractional_encoder_ratio_keeps_thread_phase() {
  g_cpr = spindleCountsPerRev(kCpr, 2, 9);
  TEST_ASSERT_EQUAL_INT64(1600, g_cpr.num);
  TEST_ASSERT_EQUAL_INT64(3, g_cpr.den);
  threadToShoulder(6.0, 3);
}

void test_arm_with_spindle_stopped_then_reverse() {
  Rig r(Mode::Thread, 1000);
  r.rpmTarget = 200;
  r.run(0.3);
  r.els.press(BTN_NUT);  // pass 1 anchor
  const int64_t s0 = r.els.anchorSpindle();
  const int64_t z0 = r.els.anchorPosition();
  r.run(1.0);
  r.els.press(BTN_NUT);  // open mid-thread
  r.rpmTarget = 0;
  r.run(0.5);
  r.els.press(BTN_RETURN);
  r.run(1.0);
  r.els.press(BTN_NUT);
  TEST_ASSERT_EQUAL(Nut::Armed, r.els.nut());
  // Spindle now runs in reverse: the nut must re-plan and still find the groove.
  r.rpmTarget = -200;
  TEST_ASSERT_TRUE(r.runUntil([&] { return r.els.nut() == Nut::Engaged; }, 1.0));
  r.run(0.5);
  TEST_ASSERT_TRUE(r.els.positionSteps() > 0);  // moving toward the tailstock
  const double err = grooveError(r, s0, z0, r.spindle(), r.els.positionSteps());
  TEST_ASSERT_TRUE_MESSAGE(std::fabs(err) <= 3.0, "reverse re-sync lost the groove");
}

// Pressing NUT while RETURN is still travelling must not engage until the carriage is parked.
void test_arm_during_return_waits_for_carriage() {
  Rig r(Mode::Thread, 2000);
  r.rpmTarget = 400;
  r.run(0.4);
  r.els.press(BTN_NUT);  // pass 1 from 0
  const int64_t s0 = r.els.anchorSpindle();
  const int64_t z0 = r.els.anchorPosition();
  r.run(2.0);  // ~ -26 mm
  r.els.press(BTN_NUT);
  r.run(0.2);
  r.els.press(BTN_RETURN);
  r.run(0.05);  // still on the way back
  TEST_ASSERT_TRUE(r.els.status().moving);
  r.els.press(BTN_NUT);
  bool engagedEarly = false;
  const bool engaged = r.runUntil(
      [&] {
        if (r.els.nut() == Nut::Engaged && r.els.positionSteps() != 0 &&
            std::abs(r.els.positionSteps()) > 50 && r.els.status().velocityMmS > 0)
          engagedEarly = true;
        return r.els.nut() == Nut::Engaged;
      },
      3);
  TEST_ASSERT_TRUE(engaged);
  TEST_ASSERT_FALSE(engagedEarly);
  r.run(1.0);
  const double err = grooveError(r, s0, z0, r.spindle(), r.els.positionSteps());
  TEST_ASSERT_TRUE_MESSAGE(std::fabs(err) <= 3.0, "lost the groove after arming mid-return");
}

void test_overspeed_faults_and_stops() {
  Rig r(Mode::Thread, 6000);  // 6 mm pitch: max ~360 rpm at 40 mm/s
  r.rpmTarget = 200;
  r.run(0.3);
  r.els.press(BTN_NUT);
  r.rpmTarget = 1500;
  TEST_ASSERT_TRUE(r.runUntil([&] { return r.els.fault() == Fault::Overspeed; }, 2));
  TEST_ASSERT_EQUAL(Nut::Open, r.els.nut());
  TEST_ASSERT_TRUE(r.runUntil([&] { return !r.els.status().moving; }, 1));
  TEST_ASSERT_TRUE(r.els.driverEnabled());  // decelerated, not dropped
  r.els.press(BTN_MODE);                    // any key acknowledges
  TEST_ASSERT_EQUAL(Fault::None, r.els.fault());
}

void test_estop_disables_and_drops_sync() {
  Rig r(Mode::Thread, 1500);
  r.rpmTarget = 300;
  r.run(0.3);
  r.els.press(BTN_NUT);
  r.run(0.3);
  r.estop = true;
  r.run(0.01);
  TEST_ASSERT_EQUAL(Fault::EStop, r.els.fault());
  TEST_ASSERT_FALSE(r.els.driverEnabled());
  const int32_t p = r.els.positionSteps();
  r.run(0.2);
  TEST_ASSERT_EQUAL_INT32(p, r.els.positionSteps());  // no steps while stopped
  r.els.press(BTN_NUT);  // can't clear while held
  TEST_ASSERT_EQUAL(Fault::EStop, r.els.fault());
  r.estop = false;
  r.run(0.01);
  r.els.press(BTN_NUT);  // clears only
  TEST_ASSERT_EQUAL(Fault::None, r.els.fault());
  TEST_ASSERT_EQUAL(Nut::Open, r.els.nut());
  TEST_ASSERT_TRUE(r.els.driverEnabled());
  TEST_ASSERT_FALSE(r.els.anchorValid());
  // No motion for 250 ms after re-enabling (CL57T ENA -> DIR/PUL setup time).
  r.els.press(BTN_JOG_R);
  r.run(0.2);
  TEST_ASSERT_EQUAL_INT32(p, r.els.positionSteps());
  r.els.release(BTN_JOG_R);
  r.run(0.1);
  r.els.press(BTN_JOG_R);
  r.run(0.2);
  TEST_ASSERT_TRUE(r.els.positionSteps() > p);
}

void test_mode_change_blocked_while_engaged() {
  Rig r(Mode::Feed, 100);
  r.els.press(BTN_NUT);
  r.els.press(BTN_MODE);
  r.els.release(BTN_MODE);
  TEST_ASSERT_EQUAL(Mode::Feed, r.els.settings().mode);
  TEST_ASSERT_EQUAL(Msg::Busy, r.els.status().msg);
  r.els.press(BTN_NUT);
  r.run(0.1);
  r.els.press(BTN_MODE);
  r.els.release(BTN_MODE);
  TEST_ASSERT_EQUAL(Mode::Thread, r.els.settings().mode);
}

void test_jog_respects_stops() {
  Rig r(Mode::Feed, 100);
  r.els.press(BTN_STOP_L);
  r.els.press(BTN_JOG_L);
  r.run(0.5);
  TEST_ASSERT_EQUAL_INT32(0, r.els.positionSteps());
  r.els.release(BTN_JOG_L);
  r.els.longPress(BTN_STOP_L);  // clear
  r.els.press(BTN_JOG_L);
  r.run(0.5);
  r.els.release(BTN_JOG_L);
  r.run(0.2);
  TEST_ASSERT_TRUE(r.els.positionSteps() < -r.mm(5));
  TEST_ASSERT_FALSE(r.els.status().moving);
}

// ---------------------------------------------------------------------------
// The digital gearbox must reproduce the lathe's own change-gear table
// (Roher TBL-20/520 manual p.13, identical to the Axminster BV20M's). G1 sits on the
// change-gear stud, G4 on the leadscrew; with no G3, G2 is just an idler (G1/G4).
// The encoder replaces G1 (1:1 on the stud), the motor replaces G4.

struct GearRow {
  int pitch;  // um for metric rows, TPI for imperial rows
  int g1, g2, g3, g4;
};

const GearRow kMetricGearTable[] = {
    {250, 30, 50, 0, 80},    {300, 45, 35, 0, 100},  {350, 21, 80, 0, 40},
    {400, 30, 65, 0, 50},    {450, 45, 50, 60, 80},  {500, 30, 80, 0, 40},
    {600, 45, 60, 0, 50},    {700, 63, 45, 0, 60},   {750, 45, 65, 0, 40},
    {800, 60, 55, 0, 50},    {1000, 45, 80, 0, 30},  {1250, 45, 80, 0, 24},
    {1500, 63, 42, 60, 40},  {1750, 63, 60, 0, 24},  {2000, 63, 65, 0, 21},
    {2500, 45, 40, 100, 30}, {3000, 63, 40, 100, 35},
};
const GearRow kImperialGearTable[] = {
    {48, 50, 55, 0, 63},  {40, 60, 50, 0, 63},  {32, 60, 63, 50, 40}, {28, 60, 63, 50, 35},
    {26, 50, 65, 80, 42}, {24, 50, 63, 80, 40}, {22, 50, 55, 80, 42}, {20, 40, 80, 0, 21},
    {19, 60, 63, 80, 38}, {18, 50, 63, 80, 30}, {16, 50, 80, 0, 21},  {14, 50, 42, 80, 35},
    {12, 50, 60, 80, 21}, {11, 50, 55, 80, 21}, {10, 60, 42, 80, 30}, {9, 40, 45, 100, 21},
    {8, 60, 42, 100, 30},
};

// Leadscrew turns per stud turn for a row of the table.
Ratio gearRatio(const GearRow& r) {
  return r.g3 ? makeRatio((int64_t)r.g1 * r.g3, (int64_t)r.g2 * r.g4) : makeRatio(r.g1, r.g4);
}

// Machine: encoder (2400 counts) turning `encTurns` per `spindleTurns`, 1600-step
// motor, 20:40 belt, leadscrew of `leadUm`.
MachineConfig machine(int encTurns, int spindleTurns, int leadUm) {
  MachineConfig c = defaultConfig();
  c.countsPerRev = spindleCountsPerRev(kCpr, encTurns, spindleTurns);
  c.stepsPerMm = leadscrewStepsPerMm(1600, 20, 40, 1, 1, pitchFromMicrons(leadUm));
  return c;
}

// Motor steps per encoder count the controller uses for a thread from its table.
Ratio coreStepsPerCount(const MachineConfig& c, Units units, Ratio pitch) {
  Settings s;
  s.mode = Mode::Thread;
  s.units = units;
  s.towardTailstock = true;  // positive sign
  for (int m = 0; m < 2; ++m)
    for (int u = 0; u < 2; ++u) s.index[m][u] = (uint8_t)defaultPitchIndex((Mode)m, (Units)u);
  int idx = -1;
  for (int i = 0; i < pitchTableSize(Mode::Thread, units); ++i) {
    const Ratio p = pitchAt(Mode::Thread, units, i);
    if (p.num == pitch.num && p.den == pitch.den) idx = i;
  }
  TEST_ASSERT_TRUE_MESSAGE(idx >= 0, "thread missing from the controller's pitch table");
  s.index[(int)Mode::Thread][(int)units] = (uint8_t)idx;
  Controller e;
  e.begin(c, &s);
  return e.stepsPerCount();
}

void test_matches_original_change_gear_table() {
  // Encoder 1:1 on the stud (2 turns per 9 spindle turns), 3 mm leadscrew.
  const MachineConfig roher = machine(2, 9, 3000);
  // Mechanical: steps per count = leadscrew turns per stud turn * 3200 steps per
  // leadscrew turn / 2400 counts per stud turn.
  const Ratio perStudTurn = makeRatio(3200, kCpr);

  for (const GearRow& row : kMetricGearTable) {
    const Ratio want = mul(gearRatio(row), perStudTurn);
    const Ratio got = coreStepsPerCount(roher, Units::Metric, pitchFromMicrons(row.pitch));
    char msg[64];
    std::snprintf(msg, sizeof msg, "metric %d um", row.pitch);
    // Metric rows are exact.
    TEST_ASSERT_EQUAL_INT64_MESSAGE(want.num, got.num, msg);
    TEST_ASSERT_EQUAL_INT64_MESSAGE(want.den, got.den, msg);
  }
  for (const GearRow& row : kImperialGearTable) {
    const double want = toDouble(mul(gearRatio(row), perStudTurn));
    const double got = toDouble(coreStepsPerCount(roher, Units::Imperial, pitchFromTpiX10(row.pitch * 10)));
    char msg[64];
    std::snprintf(msg, sizeof msg, "%d TPI: gears %.6f, ELS %.6f", row.pitch, want, got);
    // The change gears only approximate inch threads (within 0.05%); the ELS is exact.
    TEST_ASSERT_TRUE_MESSAGE(std::fabs(got / want - 1.0) < 5e-4, msg);
  }
}

// Thread pitch only depends on (stud ratio x leadscrew pitch) = 2/3 mm, so the real
// machine (3 mm screw, 2:9 stud) and a 4 mm / 1:6 one cut identical threads; the split
// still matters for the mm readout/jog/stops and for which spindle turn the NUT may
// re-engage on.
void test_thread_ratio_depends_only_on_gear_table_constant() {
  const MachineConfig a = machine(2, 9, 3000);
  const MachineConfig b = machine(1, 6, 4000);
  for (const GearRow& row : kMetricGearTable) {
    const Ratio ra = coreStepsPerCount(a, Units::Metric, pitchFromMicrons(row.pitch));
    const Ratio rb = coreStepsPerCount(b, Units::Metric, pitchFromMicrons(row.pitch));
    TEST_ASSERT_EQUAL_INT64(ra.num, rb.num);
    TEST_ASSERT_EQUAL_INT64(ra.den, rb.den);
  }
  TEST_ASSERT_FALSE(a.stepsPerMm.num * b.stepsPerMm.den == b.stepsPerMm.num * a.stepsPerMm.den);
}


int main() {
  UNITY_BEGIN();
  RUN_TEST(test_steps_per_mm_is_exact);
  RUN_TEST(test_metric_thread_on_imperial_screw_has_no_drift);
  RUN_TEST(test_pitch_labels);
  RUN_TEST(test_matches_original_change_gear_table);
  RUN_TEST(test_thread_ratio_depends_only_on_gear_table_constant);
  RUN_TEST(test_feed_tracks_spindle_tightly);
  RUN_TEST(test_stop_is_never_crossed_and_nut_opens);
  RUN_TEST(test_nut_resync_keeps_thread_phase);
  RUN_TEST(test_fractional_encoder_ratio_keeps_thread_phase);
  RUN_TEST(test_arm_with_spindle_stopped_then_reverse);
  RUN_TEST(test_arm_during_return_waits_for_carriage);
  RUN_TEST(test_overspeed_faults_and_stops);
  RUN_TEST(test_estop_disables_and_drops_sync);
  RUN_TEST(test_mode_change_blocked_while_engaged);
  RUN_TEST(test_jog_respects_stops);
  return UNITY_END();
}
