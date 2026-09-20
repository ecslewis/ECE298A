![](../../workflows/gds/badge.svg) ![](../../workflows/docs/badge.svg) ![](../../workflows/test/badge.svg) ![](../../workflows/fpga/badge.svg)

# 8-bit Programmable Binary Counter — Tiny Tapeout (GF180MCU)

An 8-bit binary up/down counter with **asynchronous reset**, **synchronous
parallel load** and **tri-state outputs**, hardened for the GlobalFoundries
180 nm (`gf180mcuD`) process through the Tiny Tapeout flow.

- Full datasheet: [docs/info.md](docs/info.md)

## Design

| File | Contents |
| --- | --- |
| [`src/counter8.v`](src/counter8.v) | The counter core — 8-bit register with asynchronous clear, synchronous load, count enable and up/down control. Priority: reset > load > count. |
| [`src/project.v`](src/project.v) | Tiny Tapeout top level `tt_um_ecslewis_counter8`. Decodes the control inputs and drives the pad output-enable to form the tri-state bus. |
| [`test/test.py`](test/test.py) | cocotb testbench, 16 tests. |
| [`test/tb.v`](test/tb.v) | Verilog testbench wrapper; models the `uio` pads so the real high-impedance state is visible. |

### Pin map

| Pin | Name | Function |
| --- | --- | --- |
| `ui[0]` | `OE` | Tri-state output enable (1 = drive bus, 0 = Hi-Z) |
| `ui[1]` | `LOAD` | Synchronous parallel load |
| `ui[2]` | `CE` | Count enable (1 = count, 0 = hold) |
| `ui[3]` | `UP` | 1 = count up, 0 = count down |
| `uio[7:0]` | `D/Q` | Bidirectional tri-state bus: count out when `OE = 1`, load data in when `OE = 0` |
| `uo[7:0]` | `Q` | Count value, always driven (monitor port) |
| `rst_n` | `RESET` | Asynchronous reset, active low |

### Why the tri-state is on `uio`

High impedance cannot be synthesised on a net inside an ASIC — `z` only
exists at the pads. Tiny Tapeout exposes the pad drivers through `uio_oe`, so
the design asserts `uio_oe = {8{OE}}` to place the 8-bit output bus in
high-impedance. That is a real tri-state bus at the package pins.

## Running the tests

Requires [Icarus Verilog](https://steveicarus.github.io/iverilog/) and
[cocotb](https://www.cocotb.org/):

```bash
cd test
pip install -r requirements.txt
make -B
```

Expected result: `TESTS=16 PASS=16 FAIL=0 SKIP=0`.

The tests cover:

1. Reset clears the counter to `0x00`
2. Reset is genuinely asynchronous (clears with no clock edge)
3. Reset has priority over load and count
4. Load is genuinely synchronous (nothing happens until the clock edge)
5. Loading `0x00`, `0x01`, `0x7F`, `0x80`, `0xAA`, `0x55`, `0xFF`
6. Load has priority over counting
7. Counting up
8. Counting down
9. `0xFF → 0x00` rollover
10. `0x00 → 0xFF` underflow
11. Count enable holds and resumes
12. Full 256-state sweep
13. Bus is high-impedance when `OE = 0`
14. Bus drives the count when `OE = 1`
15. Enabled bus tracks the count; `OE` has no side effects
16. Full end-to-end scenario

A waveform is written to `test/tb.fst` and can be opened with GTKWave or
Surfer. The `uio_bus` signal shows the tri-state pins including the `z` state.

## Building the chip

Pushing to this repository runs the GitHub Actions workflows:

- **test** — the cocotb RTL simulation above
- **gds** — synthesis, place and route with LibreLane for `gf180mcuD`,
  followed by the Tiny Tapeout precheck and a gate-level simulation of the
  same testbench against the post-layout netlist
- **docs** — builds the datasheet from `docs/info.md` and `info.yaml`
- **fpga** — an FPGA build of the same RTL

The layout viewer is published to this repository's GitHub Pages site.

## What is Tiny Tapeout?

Tiny Tapeout is an educational project that makes it easier and cheaper to
get digital and analog designs manufactured on a real chip.
See <https://tinytapeout.com>.

## Resources

- [FAQ](https://tinytapeout.com/faq/)
- [Digital design lessons](https://tinytapeout.com/digital_design/)
- [Join the community](https://tinytapeout.com/discord)
- [Build your design locally](https://www.tinytapeout.com/guides/local-hardening/)
