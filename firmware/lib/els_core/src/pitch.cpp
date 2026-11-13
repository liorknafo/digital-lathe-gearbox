#include "pitch.h"

namespace els {

namespace {

const int16_t kMetricThreadUm[] = {200,  250,  300,  350,  400,  450,  500,  600,
                                   700,  750,  800,  1000, 1250, 1500, 1750, 2000,
                                   2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000};
const int16_t kTpiX10[] = {800, 720, 640, 600, 560, 480, 440, 400, 360, 320, 280,
                           270, 260, 240, 220, 200, 190, 180, 160, 140, 130, 120,
                           115, 110, 100, 90,  80,  70,  60,  50,  45,  40};
const int16_t kMetricFeedUm[] = {10,  20,  30,  40,  50,  60,  70,  80,  90,  100, 120,
                                 150, 180, 200, 250, 300, 350, 400, 500, 600, 800, 1000};
const int16_t kImperialFeedTenthThou[] = {5,  10, 15, 20,  25,  30,  35,  40,  50, 60,
                                          70, 80, 100, 120, 150, 200, 250, 300, 400};

template <typename T, int N>
constexpr int countOf(const T (&)[N]) {
  return N;
}

const int16_t* table(Mode mode, Units units, int* size) {
  if (mode == Mode::Thread) {
    if (units == Units::Metric) {
      *size = countOf(kMetricThreadUm);
      return kMetricThreadUm;
    }
    *size = countOf(kTpiX10);
    return kTpiX10;
  }
  if (units == Units::Metric) {
    *size = countOf(kMetricFeedUm);
    return kMetricFeedUm;
  }
  *size = countOf(kImperialFeedTenthThou);
  return kImperialFeedTenthThou;
}

int indexOf(Mode mode, Units units, int16_t value) {
  int n = 0;
  const int16_t* t = table(mode, units, &n);
  for (int k = 0; k < n; ++k)
    if (t[k] == value) return k;
  return 0;
}

int clampIndex(Mode mode, Units units, int index) {
  int n = pitchTableSize(mode, units);
  return index < 0 ? 0 : (index >= n ? n - 1 : index);
}

}  // namespace

int pitchTableSize(Mode mode, Units units) {
  int n = 0;
  table(mode, units, &n);
  return n;
}

int defaultPitchIndex(Mode mode, Units units) {
  if (mode == Mode::Thread) return indexOf(mode, units, units == Units::Metric ? 1500 : 200);
  return indexOf(mode, units, units == Units::Metric ? 100 : 40);
}

Ratio pitchAt(Mode mode, Units units, int index) {
  int n = 0;
  const int16_t* t = table(mode, units, &n);
  int16_t v = t[clampIndex(mode, units, index)];
  if (mode == Mode::Thread) return units == Units::Metric ? pitchFromMicrons(v) : pitchFromTpiX10(v);
  return units == Units::Metric ? pitchFromMicrons(v) : pitchFromTenthThou(v);
}

void pitchLabel(Mode mode, Units units, int index, char* buf, int cap) {
  int n = 0;
  const int16_t* t = table(mode, units, &n);
  int16_t v = t[clampIndex(mode, units, index)];
  Str out(buf, cap);
  if (mode == Mode::Thread) {
    if (units == Units::Metric) {
      out.fixed(v / 10, 2).s(" mm");
    } else if (v % 10 == 0) {
      out.i(v / 10).s(" TPI");
    } else {
      out.fixed(v, 1).s(" TPI");
    }
  } else if (units == Units::Metric) {
    out.fixed(v, 3).s(" mm/r");
  } else {
    out.fixed(v, 4).s(" in/r");
  }
}

// ---- Str ----

Str& Str::ch(char c) {
  if (len + 1 < cap) {
    buf[len++] = c;
    buf[len] = 0;
  }
  return *this;
}

Str& Str::s(const char* t) {
  while (*t) ch(*t++);
  return *this;
}

Str& Str::i(int64_t v) {
  char tmp[24];
  int n = 0;
  bool neg = v < 0;
  uint64_t u = neg ? (uint64_t)(-(v + 1)) + 1 : (uint64_t)v;
  do {
    tmp[n++] = (char)('0' + (u % 10));
    u /= 10;
  } while (u);
  if (neg) ch('-');
  while (n) ch(tmp[--n]);
  return *this;
}

Str& Str::fixed(int64_t scaled, int decimals) {
  int64_t p = 1;
  for (int k = 0; k < decimals; ++k) p *= 10;
  if (scaled < 0) {
    ch('-');
    scaled = -scaled;
  }
  i(scaled / p);
  if (decimals > 0) {
    ch('.');
    int64_t frac = scaled % p;
    for (int64_t d = p / 10; d > 0; d /= 10) ch((char)('0' + (frac / d) % 10));
  }
  return *this;
}

Str& Str::f(float v, int decimals) {
  float p = 1;
  for (int k = 0; k < decimals; ++k) p *= 10;
  float scaled = v * p;
  int64_t r = (int64_t)(scaled < 0 ? scaled - 0.5f : scaled + 0.5f);
  if (r == 0 && v < 0) r = 0;  // avoid "-0.00"
  return fixed(r, decimals);
}

Str& Str::padLeft(int width) {
  if (len >= width || width >= cap) return *this;
  int shift = width - len;
  for (int k = len; k >= 0; --k) buf[k + shift] = buf[k];
  for (int k = 0; k < shift; ++k) buf[k] = ' ';
  len = width;
  return *this;
}

}  // namespace els
