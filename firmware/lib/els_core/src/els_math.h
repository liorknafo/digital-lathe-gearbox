// Exact integer helpers shared by the motion core.
// Freestanding: no libc, so the same code builds for Teensy, native tests and wasm.
#pragma once
#include <stdint.h>

namespace els {

// A rational number num/den with den > 0, always kept reduced.
struct Ratio {
  int64_t num;
  int64_t den;
};

inline int64_t abs64(int64_t v) { return v < 0 ? -v : v; }

inline int64_t gcd64(int64_t a, int64_t b) {
  a = abs64(a);
  b = abs64(b);
  while (b != 0) {
    int64_t t = a % b;
    a = b;
    b = t;
  }
  return a == 0 ? 1 : a;
}

inline Ratio makeRatio(int64_t num, int64_t den) {
  if (den < 0) {
    num = -num;
    den = -den;
  }
  int64_t g = gcd64(num, den);
  return Ratio{num / g, den / g};
}

// Multiplies two ratios, cross-reducing first to keep the intermediates small.
inline Ratio mul(Ratio a, Ratio b) {
  int64_t g1 = gcd64(a.num, b.den);
  int64_t g2 = gcd64(b.num, a.den);
  return makeRatio((a.num / g1) * (b.num / g2), (a.den / g2) * (b.den / g1));
}

inline Ratio div(Ratio a, Ratio b) { return mul(a, makeRatio(b.den, b.num)); }

// floor(a / b) for b > 0, correct for negative a (C++ '/' truncates toward zero).
inline int64_t floorDiv(int64_t a, int64_t b) {
  int64_t q = a / b;
  if ((a % b != 0) && (a < 0)) --q;
  return q;
}

inline float toFloat(Ratio r) { return (float)r.num / (float)r.den; }
inline double toDouble(Ratio r) { return (double)r.num / (double)r.den; }

inline float absf(float v) { return v < 0 ? -v : v; }
inline float sqrtf_(float v) { return v <= 0 ? 0.0f : __builtin_sqrtf(v); }
inline float minf(float a, float b) { return a < b ? a : b; }
inline float maxf(float a, float b) { return a > b ? a : b; }
inline float clampf(float v, float lo, float hi) { return v < lo ? lo : (v > hi ? hi : v); }

inline double floorD(double v) {
  int64_t i = (int64_t)v;
  return (double)((v < (double)i) ? i - 1 : i);
}
inline double ceilD(double v) {
  int64_t i = (int64_t)v;
  return (double)((v > (double)i) ? i + 1 : i);
}

}  // namespace els
