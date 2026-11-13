// 320x240 status screen, drawn through a tiny Gfx interface so the exact same
// layout runs on the ILI9341 and in the browser simulator.
#pragma once
#include <stdint.h>

#include "els.h"

namespace els {

// Text cells are 6*size x 8*size pixels (the classic 5x7 Adafruit/ILI9341_t3 font).
class Gfx {
 public:
  virtual void fillRect(int x, int y, int w, int h, uint16_t color) = 0;
  virtual void text(int x, int y, const char* s, int size, uint16_t fg, uint16_t bg) = 0;
};

constexpr uint16_t rgb565(uint8_t r, uint8_t g, uint8_t b) {
  return (uint16_t)(((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3));
}

class Ui {
 public:
  static const int kWidth = 320;
  static const int kHeight = 240;

  // Redraws only what changed since the last call; force=true repaints everything.
  void render(Gfx& g, const Status& st, uint32_t nowMs, bool force = false);

 private:
  static const int kFields = 10;
  struct Field {
    char text[28];
    uint16_t fg, bg;
  };
  void field(Gfx& g, int id, int x, int y, int w, int size, const char* text, uint16_t fg,
             uint16_t bg, bool force);

  Field last_[kFields] = {};
  uint16_t seenMsgSeq_ = 0;
  uint32_t msgUntilMs_ = 0;
  Msg shownMsg_ = Msg::None;
  bool painted_ = false;
};

}  // namespace els
