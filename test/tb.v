`default_nettype none
`timescale 1ns / 1ps

/* Testbench for tt_um_ecslewis_counter8.
   It instantiates the module, makes convenient wires for the cocotb test
   in test.py, and models the Tiny Tapeout uio pads so that the real
   high-impedance (z) behaviour of the tri-state bus is visible in the
   waveform and can be checked by the test.
*/
module tb ();

  // Dump the signals to a FST file. You can view it with gtkwave or surfer.
  initial begin
    $dumpfile("tb.fst");
    $dumpvars(0, tb);
    #1;
  end

  // Wire up the inputs and outputs:
  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;
`ifdef GL_TEST
  wire VPWR = 1'b1;
  wire VGND = 1'b0;
`endif

  // Model of the bidirectional pads: each uio pin drives uio_out when its
  // uio_oe bit is high, and is high-impedance otherwise. uio_bus therefore
  // shows the true tri-state behaviour of the chip's pins.
  wire [7:0] uio_bus;
  genvar i;
  generate
    for (i = 0; i < 8; i = i + 1) begin : gen_pad
      assign uio_bus[i] = uio_oe[i] ? uio_out[i] : 1'bz;
    end
  endgenerate

  tt_um_ecslewis_counter8 user_project (

      // Include power ports for the Gate Level test:
`ifdef GL_TEST
      .VPWR(VPWR),
      .VGND(VGND),
`endif

      .ui_in  (ui_in),    // Dedicated inputs
      .uo_out (uo_out),   // Dedicated outputs
      .uio_in (uio_in),   // IOs: Input path
      .uio_out(uio_out),  // IOs: Output path
      .uio_oe (uio_oe),   // IOs: Enable path (active high: 0=input, 1=output)
      .ena    (ena),      // enable - goes high when design is selected
      .clk    (clk),      // clock
      .rst_n  (rst_n)     // not reset
  );

endmodule
