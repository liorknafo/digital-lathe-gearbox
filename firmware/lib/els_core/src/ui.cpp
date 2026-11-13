#include "ui.h"

namespace els {

namespace {

const uint16_t kBg = rgb565(16, 18, 24);
const uint16_t kPanel = rgb565(34, 38, 50);
const uint16_t kText = rgb565(230, 232, 238);
const uint16_t kDim = rgb565(130, 136, 150);
const uint16_t kAccent = rgb565(90, 170, 255);
const uint16_t kGreen = rgb565(40, 200, 90);
const uint16_t kYellow = rgb565(250, 200, 40);
const uint16_t kRed = rgb565(235, 60, 50);
const uint16_t kBlack = rgb565(0, 0, 0);

const char* msgText(Msg m) {
  switch (m) {
    case Msg::NewThread: return "NEW THREAD - SYNC SET";
    case Msg::SyncKept: return "ARMED - WAITING FOR SYNC";
    case Msg::AtStop: return "AT STOP - NUT OPENED";
    case Msg::NoReturnPoint: return "NO START POINT";
    case Msg::Busy: return "OPEN THE NUT FIRST";
    case Msg::TooFast: return "SPINDLE TOO FAST";
    case Msg::FaultCleared: return "FAULT CLEARED";
    default: return "";
  }
}

bool same(const char* a, const char* b) {
  while (*a && *a == *b) {
    ++a;
    ++b;
  }
  return *a == *b;
}

void copy(char* dst, const char* src, int cap) {
  int k = 0;
  for (; k + 1 < cap && src[k]; ++k) dst[k] = src[k];
  dst[k] = 0;
}

// Position in the display units.
void fmtLength(Str& s, float mm, Units u) {
  if (u == Units::Metric)
    s.f(mm, 3);
  else
    s.f(mm / 25.4f, 4);
}

}  // namespace

void Ui::field(Gfx& g, int id, int x, int y, int w, int size, const char* text, uint16_t fg,
               uint16_t bg, bool force) {
  Field& f = last_[id];
  if (!force && f.fg == fg && f.bg == bg && same(f.text, text)) return;
  g.fillRect(x, y, w, 8 * size, bg);
  g.text(x, y, text, size, fg, bg);
  copy(f.text, text, (int)sizeof(f.text));
  f.fg = fg;
  f.bg = bg;
}

void Ui::render(Gfx& g, const Status& st, uint32_t nowMs, bool force) {
  if (!painted_) force = true;
  if (force) {
    g.fillRect(0, 0, kWidth, kHeight, kBg);
    g.fillRect(0, 0, kWidth, 30, kPanel);
    g.fillRect(0, 196, kWidth, 44, kPanel);
    painted_ = true;
  }
  char buf[32];
  const bool metric = st.units == Units::Metric;

  // Header: mode, units, feed direction.
  field(g, 0, 6, 7, 110, 2, st.mode == Mode::Thread ? "THREAD" : "FEED", kAccent, kPanel, force);
  field(g, 1, 128, 7, 60, 2, metric ? "mm" : "inch", kText, kPanel, force);
  field(g, 2, 206, 7, 110, 2, st.towardTailstock ? "TAIL ->" : "<- HEAD",
        st.towardTailstock ? kYellow : kText, kPanel, force);

  // Pitch, the big number.
  field(g, 3, 8, 40, 304, 4, st.pitchText, kText, kBg, force);

  // Spindle.
  {
    Str s(buf, sizeof buf);
    s.s("RPM ").i((int64_t)(st.spindleRpm < 0 ? -st.spindleRpm + 0.5f : st.spindleRpm + 0.5f));
    if (st.spindleRpm < -0.5f) s.s(" REV");
    const bool over = (st.spindleRpm < 0 ? -st.spindleRpm : st.spindleRpm) > st.maxRpm;
    field(g, 4, 8, 82, 180, 2, buf, over ? kRed : kText, kBg, force);
    Str m(buf, sizeof buf);
    m.s("max ").i((int64_t)st.maxRpm);
    field(g, 5, 196, 82, 120, 2, buf, kDim, kBg, force);
  }

  // Carriage position.
  {
    Str s(buf, sizeof buf);
    s.s("X ");
    fmtLength(s, st.positionMm, st.units);
    field(g, 6, 8, 108, 304, 3, buf, st.moving ? kAccent : kText, kBg, force);
  }

  // Stops.
  {
    Str s(buf, sizeof buf);
    s.s("L ");
    if (st.hasLeftStop)
      fmtLength(s, st.leftStopMm, st.units);
    else
      s.s("---");
    s.s("  R ");
    if (st.hasRightStop)
      fmtLength(s, st.rightStopMm, st.units);
    else
      s.s("---");
    field(g, 7, 8, 140, 304, 2, buf, kYellow, kBg, force);
  }

  // Knob function + sync flag.
  {
    Str s(buf, sizeof buf);
    s.s("KNOB ");
    switch (st.knobMode) {
      case KnobMode::Pitch: s.s(st.mode == Mode::Thread ? "PITCH" : "FEED"); break;
      case KnobMode::Jog001: s.s(metric ? "JOG .01" : "JOG .001\""); break;
      case KnobMode::Jog01: s.s(metric ? "JOG 0.1" : "JOG .01\""); break;
      case KnobMode::Jog1: s.s(metric ? "JOG 1.0" : "JOG 0.1\""); break;
    }
    if (st.mode == Mode::Thread) s.s(st.synced ? "  SYNC" : "  ----");
    field(g, 8, 8, 166, 304, 2, buf, kDim, kBg, force);
  }

  // Status bar: nut state, faults and transient messages.
  if (st.msgSeq != seenMsgSeq_) {
    seenMsgSeq_ = st.msgSeq;
    shownMsg_ = st.msg;
    msgUntilMs_ = nowMs + 2500;
  }
  const bool showMsg = shownMsg_ != Msg::None && (int32_t)(msgUntilMs_ - nowMs) > 0;

  const char* label;
  uint16_t fg = kBlack, bg;
  if (st.fault != Fault::None) {
    bg = kRed;
    fg = kText;
    label = st.fault == Fault::EStop        ? "E-STOP"
            : st.fault == Fault::DriverAlarm ? "DRIVER ALARM"
                                             : "TOO FAST - ANY KEY";
  } else if (showMsg) {
    bg = shownMsg_ == Msg::Busy || shownMsg_ == Msg::TooFast ? kYellow : kAccent;
    label = msgText(shownMsg_);
  } else if (st.nut == Nut::Engaged) {
    bg = kGreen;
    label = "NUT ENGAGED";
  } else if (st.nut == Nut::Armed) {
    bg = kYellow;
    label = "NUT ARMED";
  } else {
    bg = kPanel;
    fg = kText;
    label = st.jogging ? "JOG" : "NUT OPEN";
  }
  {
    if (force || last_[9].bg != bg) g.fillRect(0, 196, kWidth, 44, bg);
    Str s(buf, sizeof buf);
    s.ch(' ').s(label);
    field(g, 9, 0, 210, kWidth, 2, buf, fg, bg, force);
  }
}

}  // namespace els
