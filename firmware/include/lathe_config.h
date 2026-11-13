// ===========================================================================
//  Machine configuration — edit this file for your lathe.
//  See docs/INSTALL.md for how to measure / calibrate each value.
// ===========================================================================
#pragma once

// ---- Spindle encoder -------------------------------------------------------
// Counts per revolution of the encoder itself, after quadrature (600 PPR = 2400).
#define ENCODER_CPR 2400
// How the encoder is driven: it turns ENCODER_TURNS times for every SPINDLE_TURNS
// turns of the chuck. Any ratio works, fractional included.
// Roher TBL-20/520: the change-gear stud under the spindle turns 2 times per 9 chuck
// turns (counted; the manual's gear table gives stud ratio x leadscrew pitch = 2/3 mm,
// and 2/9 x 3 mm = 2/3). The encoder is driven from the stud by a GT2 60T:20T belt
// (cad/), so it turns 2/9 x 3 = 2/3 as fast as the chuck: 1600 counts per chuck turn.
// Check after fitting the encoder: the RPM on the screen must match the speed chart.
#define ENCODER_TURNS 2
#define SPINDLE_TURNS 3
// Set to 1 if the position readout counts DOWN when the spindle runs forward.
#define INVERT_SPINDLE 0

// ---- Leadscrew drive -------------------------------------------------------
// Driver pulses per motor revolution (CL57T DIP switches).
#define MOTOR_STEPS_PER_REV 1600
#define MOTOR_PULLEY_TEETH 20
#define LEADSCREW_PULLEY_TEETH 40
// Feed gearbox (if the motor drives through it): input-shaft revolutions per
// leadscrew revolution as a fraction. Motor drives the leadscrew directly: 1/1.
#define GEARBOX_RATIO_NUM 1
#define GEARBOX_RATIO_DEN 1
// Leadscrew pitch: set LEADSCREW_TPI for imperial screws, or set LEADSCREW_TPI to 0
// and LEADSCREW_PITCH_UM for metric screws.
// Roher TBL-20/520: 3 mm (confirmed by the user; matches the 2:9 stud count and the
// manual's gear table). Fine-tune with the calibration run in docs/INSTALL.md.
#define LEADSCREW_TPI 0
#define LEADSCREW_PITCH_UM 3000
// Set to 1 if JOG -> moves the carriage toward the headstock.
#define INVERT_DIR 0

// ---- Motion limits ---------------------------------------------------------
#define MAX_SPEED_MM_S 40.0f   // fastest threading / rapid speed
#define ACCEL_MM_S2 600.0f     // keep modest: the carriage is heavy
#define JOG_SPEED_MM_S 20.0f
#define TRACKING_GAIN 200.0f   // 1/s, position loop gain
#define MOTION_TICK_HZ 100000  // motion interrupt rate (max step rate = half of this)

// ---- Driver signal polarity -----------------------------------------------
// Level on PIN_ENABLE that lets the motor run. CL57T: ENA opto ON (pin HIGH
// through the 74AHCT125) disables the motor, so "enabled" is LOW.
#define ENABLE_ACTIVE_LEVEL LOW
// CL57T ALM output pulls low through its opto transistor on alarm (check your driver).
#define ALARM_ACTIVE_LEVEL LOW
// Step pulses are one motion tick wide (10 us; CL57T needs >= 2.5 us). After a
// direction change the next pulse waits this many ticks (CL57T DIR setup >= 5 us).
#define DIR_SETUP_TICKS 1
