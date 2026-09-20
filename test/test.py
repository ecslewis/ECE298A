# Testbench for tt_um_ecslewis_counter8 - 8-bit programmable binary counter
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge, Timer

# ui_in bit positions (see src/project.v)
OE = 1 << 0  # tri-state output enable
LOAD = 1 << 1  # synchronous parallel load
CE = 1 << 2  # count enable
UP = 1 << 3  # 1 = count up, 0 = count down

CLK_PERIOD_US = 10  # 100 kHz


def q(dut):
    """Counter value, read from the always-driven monitor port."""
    return int(dut.uo_out.value)


async def start_clock(dut):
    cocotb.start_soon(Clock(dut.clk, CLK_PERIOD_US, unit="us").start())


async def reset(dut):
    """Drive a clean reset and leave the counter idle at 0x00."""
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await Timer(1, "ns")


async def step(dut, n=1):
    """Advance n clock edges and settle."""
    await ClockCycles(dut.clk, n)
    await Timer(1, "ns")


async def load_value(dut, value):
    """Synchronously load `value` over the bidirectional bus (oe = 0)."""
    dut.ui_in.value = LOAD  # oe = 0 -> bus is an input
    dut.uio_in.value = value
    await step(dut)
    dut.ui_in.value = 0
    assert q(dut) == value, f"load failed: got 0x{q(dut):02X}, want 0x{value:02X}"


# ---------------------------------------------------------------------------
# 1. Reset
# ---------------------------------------------------------------------------


@cocotb.test()
async def test_reset_clears_counter(dut):
    """rst_n low forces the counter to 0x00."""
    await start_clock(dut)
    await reset(dut)
    assert q(dut) == 0x00, f"after reset expected 0x00, got 0x{q(dut):02X}"
    dut._log.info("PASS: reset clears the counter to 0x00")


@cocotb.test()
async def test_reset_is_asynchronous(dut):
    """Reset must take effect WITHOUT a clock edge."""
    await start_clock(dut)
    await reset(dut)

    # Count up to a non-zero value first
    await load_value(dut, 0x5A)
    assert q(dut) == 0x5A

    # Line up just after a rising edge, then assert reset mid-cycle and
    # check the counter clears before the next rising edge arrives.
    await RisingEdge(dut.clk)
    await Timer(CLK_PERIOD_US // 4, "us")  # 1/4 period after the edge
    dut.rst_n.value = 0
    await Timer(100, "ns")  # still far from the next rising edge

    assert q(dut) == 0x00, (
        f"reset is not asynchronous: counter is 0x{q(dut):02X} instead of 0x00 "
        "after rst_n went low between clock edges"
    )
    dut._log.info("PASS: reset is asynchronous (cleared with no clock edge)")

    dut.rst_n.value = 1
    await step(dut)


@cocotb.test()
async def test_reset_overrides_load_and_count(dut):
    """Reset has priority over load and count enable."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0xFF)

    dut.ui_in.value = LOAD | CE | UP
    dut.uio_in.value = 0x3C
    dut.rst_n.value = 0
    await step(dut, 2)
    assert q(dut) == 0x00, f"reset did not override load/count, got 0x{q(dut):02X}"

    dut.rst_n.value = 1
    dut.ui_in.value = 0
    await step(dut)
    dut._log.info("PASS: reset has priority over load and count")


# ---------------------------------------------------------------------------
# 2. Synchronous load (programmable)
# ---------------------------------------------------------------------------


@cocotb.test()
async def test_load_is_synchronous(dut):
    """Asserting load must not change the counter until the clock edge."""
    await start_clock(dut)
    await reset(dut)

    await RisingEdge(dut.clk)
    await Timer(1, "ns")
    dut.ui_in.value = LOAD
    dut.uio_in.value = 0xA5
    await Timer(CLK_PERIOD_US // 4, "us")  # mid-cycle, no edge yet

    assert q(dut) == 0x00, (
        f"load is not synchronous: counter changed to 0x{q(dut):02X} "
        "before the clock edge"
    )

    await step(dut)  # now the edge happens
    assert q(dut) == 0xA5, f"load failed: got 0x{q(dut):02X}, want 0xA5"
    dut.ui_in.value = 0
    dut._log.info("PASS: load is synchronous and loads the correct value")


@cocotb.test()
async def test_load_various_values(dut):
    """The counter is programmable to any 8-bit value."""
    await start_clock(dut)
    await reset(dut)

    for value in (0x00, 0x01, 0x7F, 0x80, 0xAA, 0x55, 0xFF):
        await load_value(dut, value)
        dut._log.info(f"loaded 0x{value:02X} OK")

    dut._log.info("PASS: all test values load correctly")


@cocotb.test()
async def test_load_has_priority_over_count(dut):
    """With load and ce both high, load wins."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0x10)

    dut.ui_in.value = LOAD | CE | UP
    dut.uio_in.value = 0x77
    await step(dut)
    assert q(dut) == 0x77, f"load should beat count, got 0x{q(dut):02X}"

    dut.ui_in.value = 0
    dut._log.info("PASS: load has priority over counting")


# ---------------------------------------------------------------------------
# 3. Counting
# ---------------------------------------------------------------------------


@cocotb.test()
async def test_count_up(dut):
    """Counts up by one per clock while ce = 1, up = 1."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0x00)

    dut.ui_in.value = CE | UP
    for expected in range(1, 17):
        await step(dut)
        assert q(dut) == expected, f"expected 0x{expected:02X}, got 0x{q(dut):02X}"

    dut.ui_in.value = 0
    dut._log.info("PASS: counts up correctly")


@cocotb.test()
async def test_count_down(dut):
    """Counts down by one per clock while ce = 1, up = 0."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0x10)

    dut.ui_in.value = CE  # up = 0
    for expected in range(0x0F, -1, -1):
        await step(dut)
        assert q(dut) == expected, f"expected 0x{expected:02X}, got 0x{q(dut):02X}"

    dut.ui_in.value = 0
    dut._log.info("PASS: counts down correctly")


@cocotb.test()
async def test_rollover_up(dut):
    """0xFF + 1 wraps to 0x00."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0xFE)

    dut.ui_in.value = CE | UP
    await step(dut)
    assert q(dut) == 0xFF, f"expected 0xFF, got 0x{q(dut):02X}"
    await step(dut)
    assert q(dut) == 0x00, f"rollover failed: expected 0x00, got 0x{q(dut):02X}"
    await step(dut)
    assert q(dut) == 0x01, f"expected 0x01, got 0x{q(dut):02X}"

    dut.ui_in.value = 0
    dut._log.info("PASS: 0xFF -> 0x00 rollover works")


@cocotb.test()
async def test_rollover_down(dut):
    """0x00 - 1 wraps to 0xFF."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0x01)

    dut.ui_in.value = CE  # count down
    await step(dut)
    assert q(dut) == 0x00, f"expected 0x00, got 0x{q(dut):02X}"
    await step(dut)
    assert q(dut) == 0xFF, f"underflow failed: expected 0xFF, got 0x{q(dut):02X}"

    dut.ui_in.value = 0
    dut._log.info("PASS: 0x00 -> 0xFF underflow works")


@cocotb.test()
async def test_count_enable_holds(dut):
    """With ce = 0 the counter holds its value."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0x42)

    dut.ui_in.value = UP  # ce = 0
    await step(dut, 20)
    assert q(dut) == 0x42, f"counter should have held 0x42, got 0x{q(dut):02X}"

    # ... and resumes counting when ce goes high again
    dut.ui_in.value = CE | UP
    await step(dut)
    assert q(dut) == 0x43, f"expected 0x43, got 0x{q(dut):02X}"

    dut.ui_in.value = 0
    dut._log.info("PASS: count enable holds and resumes correctly")


@cocotb.test()
async def test_full_range_sweep(dut):
    """Count through all 256 states and back to the start."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0x00)

    dut.ui_in.value = CE | UP
    for i in range(1, 257):
        await step(dut)
        expected = i & 0xFF
        assert q(dut) == expected, f"at step {i}: expected 0x{expected:02X}, got 0x{q(dut):02X}"

    assert q(dut) == 0x00, "counter did not return to 0x00 after 256 counts"
    dut.ui_in.value = 0
    dut._log.info("PASS: full 256-state sweep is correct")


# ---------------------------------------------------------------------------
# 4. Tri-state outputs
# ---------------------------------------------------------------------------


@cocotb.test()
async def test_tristate_disabled_is_hiz(dut):
    """oe = 0 -> pad enables low and the bus floats (z)."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0xC3)

    dut.ui_in.value = 0  # oe = 0
    await Timer(1, "us")

    assert int(dut.uio_oe.value) == 0x00, (
        f"uio_oe should be 0x00 when oe = 0, got 0x{int(dut.uio_oe.value):02X}"
    )
    assert str(dut.uio_bus.value).lower() == "zzzzzzzz", (
        f"bus should be high-impedance, got {str(dut.uio_bus.value)}"
    )
    dut._log.info("PASS: outputs are high-impedance when oe = 0")


@cocotb.test()
async def test_tristate_enabled_drives_count(dut):
    """oe = 1 -> pad enables high and the bus drives the counter value."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0xC3)

    dut.ui_in.value = OE
    await Timer(1, "us")

    assert int(dut.uio_oe.value) == 0xFF, (
        f"uio_oe should be 0xFF when oe = 1, got 0x{int(dut.uio_oe.value):02X}"
    )
    assert int(dut.uio_out.value) == 0xC3, (
        f"bus should drive 0xC3, got 0x{int(dut.uio_out.value):02X}"
    )
    assert int(dut.uio_bus.value) == 0xC3, (
        f"pad value should be 0xC3, got {str(dut.uio_bus.value)}"
    )
    dut._log.info("PASS: outputs drive the counter value when oe = 1")


@cocotb.test()
async def test_tristate_tracks_counter_while_enabled(dut):
    """The enabled bus follows the count, and oe does not disturb counting."""
    await start_clock(dut)
    await reset(dut)
    await load_value(dut, 0x00)

    dut.ui_in.value = OE | CE | UP
    for expected in range(1, 9):
        await step(dut)
        assert int(dut.uio_bus.value) == expected, (
            f"bus expected 0x{expected:02X}, got {str(dut.uio_bus.value)}"
        )

    # Turning the bus off must not affect the stored count
    dut.ui_in.value = CE | UP
    await step(dut)
    assert q(dut) == 0x09, f"expected 0x09, got 0x{q(dut):02X}"
    assert int(dut.uio_oe.value) == 0x00

    dut.ui_in.value = 0
    dut._log.info("PASS: tri-state bus tracks the counter and oe is side-effect free")


# ---------------------------------------------------------------------------
# 5. End-to-end scenario
# ---------------------------------------------------------------------------


@cocotb.test()
async def test_full_scenario(dut):
    """Reset -> load -> count up -> hold -> count down -> read out -> reset."""
    await start_clock(dut)
    await reset(dut)
    assert q(dut) == 0x00

    # Program the counter with 0xF0 over the bidirectional bus
    await load_value(dut, 0xF0)

    # Count up 20 times: 0xF0 -> 0x04 (wraps through 0xFF)
    dut.ui_in.value = CE | UP
    await step(dut, 20)
    assert q(dut) == 0x04, f"expected 0x04, got 0x{q(dut):02X}"

    # Hold for 10 cycles
    dut.ui_in.value = 0
    await step(dut, 10)
    assert q(dut) == 0x04

    # Count down 4 times -> 0x00
    dut.ui_in.value = CE
    await step(dut, 4)
    assert q(dut) == 0x00

    # Read the value out over the tri-state bus
    dut.ui_in.value = OE
    await Timer(1, "us")
    assert int(dut.uio_bus.value) == 0x00

    # Asynchronous reset from a loaded value
    await load_value(dut, 0x99)
    dut.rst_n.value = 0
    await Timer(1, "us")
    assert q(dut) == 0x00
    dut.rst_n.value = 1

    dut._log.info("PASS: full scenario completed")
