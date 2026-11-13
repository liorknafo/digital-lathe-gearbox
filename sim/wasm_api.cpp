// WebAssembly shim: the real firmware core + UI, a simulated spindle, and a flat
// C API for sim/web/sim.js. Built freestanding (no libc) by sim/build.sh.
#include "els.h"
#include "ui.h"

#define EXPORT extern "C" __attribute__((visibility("default")))
#define IMPORT(name) extern "C" __attribute__((import_module("env"), import_name(name)))

IMPORT("js_fill_rect") void js_fill_rect(int x, int y, int w, int h, int color);
IMPORT("js_text") void js_text(int x, int y, const char* s, int size, int fg, int bg);

// Freestanding runtime bits the compiler may call.
extern "C" {
void* memcpy(void* d, const void* s, unsigned long n) {
  auto* dd = (unsigned char*)d;
  auto* ss = (const unsigned char*)s;
  while (n--) *dd++ = *ss++;
  return d;
}
void* memset(void* d, int v, unsigned long n) {
  auto* dd = (unsigned char*)d;
  while (n--) *dd++ = (unsigned char)v;
  return d;
}
void* memmove(void* d, const void* s, unsigned long n) {
  auto* dd = (unsigned char*)d;
  auto* ss = (const unsigned char*)s;
  if (dd < ss) {
    while (n--) *dd++ = *ss++;
  } else {
    dd += n;
    ss += n;
    while (n--) *--dd = *--ss;
  }
  return d;
}
void __cxa_pure_virtual() { __builtin_trap(); }
}

namespace {

// Same defaults as firmware/include/lathe_config.h.
// Roher TBL-20/520: encoder driven from the change-gear stud (2/9 spindle speed) by a
// GT2 60T:20T belt, so 2 turns per 3 spindle turns.
const els::Ratio kCountsPerRev = els::spindleCountsPerRev(2400, 2, 3);
const double kCpr = (double)kCountsPerRev.num / (double)kCountsPerRev.den;
const float kTickHz = 100000.0f;

class WasmGfx : public els::Gfx {
 public:
  void fillRect(int x, int y, int w, int h, uint16_t c) override { js_fill_rect(x, y, w, h, c); }
  void text(int x, int y, const char* s, int size, uint16_t fg, uint16_t bg) override {
    js_text(x, y, s, size, fg, bg);
  }
};

els::Controller g_els;
els::Ui g_ui;
WasmGfx g_gfx;

double g_angle = 0;  // spindle position in encoder counts
double g_rpm = 0;
double g_rpmTarget = 0;
double g_spindleAccel = 600;  // rpm/s
bool g_estop = false;
bool g_alarm = false;

struct Sample {
  double revs;   // spindle revolutions since start
  float posMm;   // carriage
  int32_t nut;   // els::Nut
};
const int kMaxSamples = 8192;
Sample g_samples[kMaxSamples];
int g_sampleCount = 0;

}  // namespace

EXPORT void sim_init(float maxSpeed, float accel, int leadscrewPitchUm) {
  els::MachineConfig cfg;
  cfg.countsPerRev = kCountsPerRev;
  cfg.stepsPerMm = els::leadscrewStepsPerMm(1600, 20, 40, 1, 1, els::pitchFromMicrons(leadscrewPitchUm));
  cfg.tickHz = kTickHz;
  cfg.maxSpeedMmS = maxSpeed;
  cfg.accelMmS2 = accel;
  cfg.jogSpeedMmS = 20;
  cfg.trackingGainPerS = 200;
  g_els.begin(cfg, nullptr);
  g_angle = 0;
  g_rpm = 0;
}

EXPORT void sim_set_spindle(double rpmTarget, double accelRpmS) {
  g_rpmTarget = rpmTarget;
  g_spindleAccel = accelRpmS;
}
EXPORT void sim_set_inputs(int estop, int alarm) {
  g_estop = estop != 0;
  g_alarm = alarm != 0;
}

// Advance the simulation; records one sample per millisecond.
EXPORT int sim_run(double ms) {
  const int ticks = (int)(ms * kTickHz / 1000.0);
  const double dt = 1.0 / kTickHz;
  const int perSample = (int)(kTickHz / 1000.0f);
  g_sampleCount = 0;
  for (int i = 0; i < ticks; ++i) {
    const double dv = g_spindleAccel * dt;
    if (g_rpm < g_rpmTarget) g_rpm = (g_rpm + dv > g_rpmTarget) ? g_rpmTarget : g_rpm + dv;
    if (g_rpm > g_rpmTarget) g_rpm = (g_rpm - dv < g_rpmTarget) ? g_rpmTarget : g_rpm - dv;
    g_angle += g_rpm / 60.0 * kCpr * dt;
    const int64_t counts = (int64_t)els::floorD(g_angle);
    g_els.tick(counts, g_estop, g_alarm);
    if (i % perSample == 0 && g_sampleCount < kMaxSamples) {
      Sample& s = g_samples[g_sampleCount++];
      s.revs = g_angle / kCpr;
      s.posMm = (float)g_els.positionSteps() / els::toFloat(g_els.config().stepsPerMm);
      s.nut = (int32_t)g_els.nut();
    }
  }
  return g_sampleCount;
}
EXPORT const Sample* sim_samples() { return g_samples; }

EXPORT void sim_press(int b) { g_els.press((els::Button)b); }
EXPORT void sim_release(int b) { g_els.release((els::Button)b); }
EXPORT void sim_long(int b) { g_els.longPress((els::Button)b); }
EXPORT void sim_knob(int d) { g_els.knob(d); }

EXPORT void sim_render(double nowMs, int force) {
  g_ui.render(g_gfx, g_els.status(), (uint32_t)(int64_t)nowMs, force != 0);
}

// Flat status for the lathe drawing.
static float g_statusOut[16];
EXPORT const float* sim_status() {
  const els::Status st = g_els.status();
  g_statusOut[0] = st.positionMm;
  g_statusOut[1] = st.spindleRpm;
  g_statusOut[2] = (float)st.nut;
  g_statusOut[3] = (float)st.fault;
  g_statusOut[4] = st.hasLeftStop ? 1.0f : 0.0f;
  g_statusOut[5] = st.leftStopMm;
  g_statusOut[6] = st.hasRightStop ? 1.0f : 0.0f;
  g_statusOut[7] = st.rightStopMm;
  g_statusOut[8] = (float)st.mode;
  g_statusOut[9] = (float)(g_angle / kCpr - els::floorD(g_angle / kCpr));  // spindle angle 0..1
  // Signed carriage travel per spindle rev (mm), for the thread-phase plot.
  const els::Ratio r = g_els.stepsPerCount();
  g_statusOut[10] = (float)((double)r.num / (double)r.den * kCpr /
                            els::toDouble(g_els.config().stepsPerMm));
  g_statusOut[11] = st.synced ? 1.0f : 0.0f;
  g_statusOut[12] = st.velocityMmS;
  g_statusOut[13] = (float)g_rpm;
  g_statusOut[14] = st.maxRpm;
  g_statusOut[15] = g_els.driverEnabled() ? 1.0f : 0.0f;
  return g_statusOut;
}
