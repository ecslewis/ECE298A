/*
 * 8-bit programmable binary counter core
 *
 * Features:
 *   - Asynchronous, active-low reset (rst_n)
 *   - Synchronous parallel load (load)
 *   - Count enable (ce) and up/down direction control (up)
 *
 * Priority: reset > load > count.
 *
 * Note: the tri-state output driver is NOT in this module. Inside an ASIC
 * you cannot synthesise a `z` value on an internal net; the high-impedance
 * state only exists at the chip pads. This core therefore exposes the count
 * value plus an output-enable, and the top level (project.v) drives the
 * Tiny Tapeout pad enable (uio_oe) to create the real tri-state bus.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

`default_nettype none

module counter8 (
    input  wire       clk,    // clock, rising edge active
    input  wire       rst_n,  // ASYNCHRONOUS reset, active low
    input  wire       load,   // SYNCHRONOUS parallel load enable
    input  wire       ce,     // count enable (1 = count, 0 = hold)
    input  wire       up,     // 1 = count up, 0 = count down
    input  wire [7:0] d,      // parallel load data
    output reg  [7:0] q       // counter value
);

  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      // Asynchronous reset: takes effect immediately, no clock needed
      q <= 8'h00;
    end else if (load) begin
      // Synchronous load: only on the rising clock edge
      q <= d;
    end else if (ce) begin
      // Binary up/down count, wraps 0xFF -> 0x00 and 0x00 -> 0xFF
      q <= up ? (q + 8'd1) : (q - 8'd1);
    end
    // else: hold current value
  end

endmodule

`default_nettype wire
