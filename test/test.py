import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

# Use the same preset as EFFECTIVE_PRESET in Verilog when COCOTB_SIM is defined
SIM_TON_PRESET = 20

@cocotb.test()
async def test_manual_mode(dut):
    """Check manual mode sets Control immediately when start is high."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset DUT
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Enable DUT
    dut.ena.value = 1

    # Apply Manual Mode
    dut.ui_in.value = 0b100  # MAN=1
    dut.ui_in.value |= 0b001  # start=1

    await RisingEdge(dut.clk)
    assert dut.uo_out.value.integer & 1 == 1, "Manual mode failed: Control should be 1 immediately"

    # Stop start
    dut.ui_in.value = 0b100
    await RisingEdge(dut.clk)
    assert dut.uo_out.value.integer & 1 == 0, "Manual mode failed: Control should clear when start=0"


@cocotb.test()
async def test_auto_mode(dut):
    """Check auto mode sets Control after TON_PRESET delay."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset DUT
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Enable DUT
    dut.ena.value = 1

    # Apply Auto Mode with start=1
    dut.ui_in.value = 0b011  # AUTO=1, start=1

    # Control should NOT be high immediately
    await RisingEdge(dut.clk)
    assert dut.uo_out.value.integer & 1 == 0, "Auto mode failed: Control set too early"

    # Wait until preset cycles
    for _ in range(SIM_TON_PRESET + 2):
        await RisingEdge(dut.clk)

    assert dut.uo_out.value.integer & 1 == 1, "Auto mode failed: Control not set after preset delay"


@cocotb.test()
async def test_reset(dut):
    """Check reset clears Control and counter."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Drive signals
    dut.ena.value = 1
    dut.ui_in.value = 0b011  # AUTO=1, start=1

    # Let it run some cycles
    for _ in range(5):
        await RisingEdge(dut.clk)

    # Assert reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)

    # Check Control is cleared
    assert dut.uo_out.value.integer & 1 == 0, "Reset failed: Control not cleared"

    # R
