<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

This project is an **8-bit programmable binary up/down counter** with three
features required of a classic bus-oriented counter IC:

| Feature | Implementation |
| --- | --- |
| **Asynchronous reset** | `rst_n` appears in the sensitivity list of the counter's `always` block (`posedge clk or negedge rst_n`), so pulling it low clears the counter to `0x00` immediately, with no clock edge required. |
| **Synchronous load** | When `LOAD` is high the value on the data bus is captured into the counter **on the next rising clock edge only**. |
| **Tri-state outputs** | The 8-bit result is presented on the bidirectional `uio` pins. When `OE` is low the pad drivers are disabled (`uio_oe = 0x00`) and the pins are high-impedance, so the counter can share a bus with other devices. |

### Structure

- `src/counter8.v` — the counter core: an 8-bit register with asynchronous
  clear, synchronous parallel load, count enable and up/down control.
  Priority is **reset > load > count**; with `CE` low the counter holds.
- `src/project.v` — the Tiny Tapeout top level. It decodes the control bits
  from `ui_in`, instantiates the core, and drives the pad output-enable
  signal `uio_oe` to produce the tri-state bus.

A high-impedance value cannot be synthesised on a net *inside* an ASIC — the
`z` state only exists at the chip's pads. Tiny Tapeout exposes that through
the `uio_oe` signal: `uio_oe[n] = 1` turns pin `n` into an output driver,
`uio_oe[n] = 0` leaves it floating. The design therefore drives
`uio_oe = {8{OE}}`, which is a genuine 8-bit tri-state output bus at the
package pins.

### Pin map

| Pin | Name | Function |
| --- | --- | --- |
| `ui[0]` | `OE` | Tri-state output enable. 1 = drive the bus, 0 = Hi-Z. |
| `ui[1]` | `LOAD` | Synchronous parallel load enable. |
| `ui[2]` | `CE` | Count enable. 1 = count, 0 = hold. |
| `ui[3]` | `UP` | Direction. 1 = count up, 0 = count down. |
| `ui[7:4]` | — | Unused. |
| `uio[7:0]` | `D/Q` | Bidirectional tri-state bus. Drives the count `Q` when `OE = 1`; carries the parallel load data `D` into the chip when `OE = 0`. |
| `uo[7:0]` | `Q` | Count value, always driven. A monitor port so the count is observable even while the tri-state bus is floating. |
| `rst_n` | `RESET` | Asynchronous reset, active low. Clears the counter to `0x00`. |

### Behaviour

```
rst_n = 0                  -> Q <= 0x00          (immediately, asynchronous)
rising clk, LOAD = 1       -> Q <= D             (synchronous load)
rising clk, CE = 1, UP = 1 -> Q <= Q + 1         (wraps 0xFF -> 0x00)
rising clk, CE = 1, UP = 0 -> Q <= Q - 1         (wraps 0x00 -> 0xFF)
otherwise                  -> Q unchanged
```

## How to test

**Reset.** Pull `rst_n` low at any time; `uo[7:0]` goes to `0x00` straight
away without a clock edge. This is what makes the reset asynchronous.

**Program (load) a value.** Set `OE = 0` so the `uio` pins are inputs, drive
the value you want onto `uio[7:0]`, set `LOAD = 1` (`ui[1]`), and apply one
rising clock edge. `uo[7:0]` now shows that value. Setting `LOAD` high alone
does nothing until the clock edge arrives, which is what makes the load
synchronous.

**Count.** Set `LOAD = 0`, `CE = 1` (`ui[2]`) and choose the direction with
`UP` (`ui[3]`). Every rising clock edge changes the count by one. Setting
`CE = 0` freezes the count.

**Read out over the tri-state bus.** Set `OE = 1` (`ui[0]`): the `uio` pins
drive the count. Set `OE = 0`: the pins go high-impedance and float, which is
visible as `z` in simulation and as a released bus on hardware.

**Simulation.** The cocotb testbench in `test/` covers all of this — run
`make -B` in the `test/` directory (Icarus Verilog + cocotb). There are 16
tests covering reset, asynchronous reset timing, reset priority, synchronous
load timing, loading every kind of value, load priority, counting up and
down, both rollover directions, count-enable hold, a full 256-state sweep,
and the tri-state bus in both the enabled and high-impedance states. The
waveform is written to `test/tb.fst`, viewable in GTKWave or Surfer — the
`uio_bus` signal in the testbench models the pads and shows the real `z`
state.

## External hardware

None. The design only needs the standard Tiny Tapeout inputs, outputs and
bidirectional pins — switches or a microcontroller on `ui[3:0]` and
`uio[7:0]`, and LEDs on `uo[7:0]` to watch the count.
