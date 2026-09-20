/*
 * Tiny Tapeout wrapper for the 8-bit programmable binary counter.
 *
 * Copyright (c) 2026 Ella Lewis
 * SPDX-License-Identifier: Apache-2.0
 *
 * Pin map
 * -------
 *   ui_in[0]   oe    tri-state output enable (1 = drive bus, 0 = Hi-Z)
 *   ui_in[1]   load  synchronous parallel load
 *   ui_in[2]   ce    count enable
 *   ui_in[3]   up    1 = count up, 0 = count down
 *   ui_in[7:4]       unused
 *
 *   uio[7:0]         bidirectional tri-state data bus
 *                      oe = 1 -> pads drive the counter value Q out
 *                      oe = 0 -> pads are Hi-Z inputs and carry the
 *                                parallel load data D into the counter
 *
 *   uo_out[7:0]      counter value Q, always driven (monitor port, so the
 *                    count is observable even while the bus is Hi-Z)
 *
 *   rst_n            asynchronous reset, active low
 */

`default_nettype none

module tt_um_ecslewis_counter8 (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

  // ---- control decode -------------------------------------------------
  wire oe   = ui_in[0];
  wire load = ui_in[1];
  wire ce   = ui_in[2];
  wire up   = ui_in[3];

  // ---- counter core ---------------------------------------------------
  wire [7:0] q;

  counter8 u_counter8 (
      .clk  (clk),
      .rst_n(rst_n),   // asynchronous reset
      .load (load),    // synchronous load
      .ce   (ce),
      .up   (up),
      .d    (uio_in),  // load data arrives on the bidirectional bus
      .q    (q)
  );

  // ---- tri-state output bus -------------------------------------------
  // uio_oe = 1 turns the pad into an output driver, uio_oe = 0 leaves the
  // pad high-impedance. This is how Tiny Tapeout implements tri-state.
  assign uio_out = q;
  assign uio_oe  = {8{oe}};

  // ---- always-driven monitor port -------------------------------------
  assign uo_out = q;

  // List all unused inputs to prevent warnings
  wire _unused = &{ena, ui_in[7:4], 1'b0};

endmodule

`default_nettype wire
