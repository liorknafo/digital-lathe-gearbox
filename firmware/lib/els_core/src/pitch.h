// Thread / feed tables. Every entry is an exact rational number of mm per spindle rev.
#pragma once
#include <stdint.h>

#include "els_math.h"

namespace els {

enum class Mode : uint8_t { Feed = 0, Thread = 1 };
enum class Units : uint8_t { Metric = 0, Imperial = 1 };

// Exact pitch helpers.
inline Ratio pitchFromMicrons(int64_t um) { return makeRatio(um, 1000); }
// tpiX10 = threads per inch * 10 (so 11.5 TPI = 115). 25.4 mm / tpi = 254 / tpiX10.
inline Ratio pitchFromTpiX10(int64_t tpiX10) { return makeRatio(254, tpiX10); }
// Feed in tenths of a thou per rev: 0.0001 in = 0.00254 mm.
inline Ratio pitchFromTenthThou(int64_t tenths) { return makeRatio(tenths * 254, 100000); }

int pitchTableSize(Mode mode, Units units);
int defaultPitchIndex(Mode mode, Units units);
Ratio pitchAt(Mode mode, Units units, int index);
// Writes e.g. "1.25 mm", "13 TPI", "0.100 mm/r", "0.0040 in/r".
void pitchLabel(Mode mode, Units units, int index, char* buf, int cap);

// Tiny freestanding string builder used by the UI.
struct Str {
  char* buf;
  int cap;
  int len;
  Str(char* b, int c) : buf(b), cap(c), len(0) {
    if (cap > 0) buf[0] = 0;
  }
  Str& ch(char c);
  Str& s(const char* t);
  Str& i(int64_t v);
  // Prints value/10^decimals with a fixed number of decimals, e.g. fixed(1250, 3) = "1.250".
  Str& fixed(int64_t scaled, int decimals);
  // Prints a float with the given decimals (rounded).
  Str& f(float v, int decimals);
  // Right-aligns current content to `width` characters.
  Str& padLeft(int width);
};

}  // namespace els
