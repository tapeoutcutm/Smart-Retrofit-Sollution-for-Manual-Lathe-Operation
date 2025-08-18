import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def test_manual_mode(dut):
    """Test MAN mode (Control should go high on next clk edge)"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # MAN mode: start=1, MAN=1 (ui_in[2]=1, ui_in[0]=1 → b101 = 5)
    dut.ui_in.value = 0b101
    dut._log.info("Testing MAN mode")

    # Wait 2 cycles to allow synchronous update
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    assert int(dut.uo_out.value & 0x1) == 1, "MAN mode failed: Control not set"


@cocotb.test()
async def test_auto_mode(dut):
    """Test AUTO mode (Control should go high after TON_PRESET cycles)"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # AUTO mode: start=1, AUTO=1 (ui_in[1]=1, ui_in[0]=1 → b011 = 3)
    dut.ui_in.value = 0b011
    dut._log.info("Testing AUTO mode")

    # Wait for preset cycles
    preset = dut.TON_PRESET.value.integer
    for _ in range(preset + 2):
        await RisingEdge(dut.clk)

    assert int(dut.uo_out.value & 0x1) == 1, "AUTO mode failed: Control not set"


@cocotb.test()
async def test_reset(dut):
    """Check reset clears Control"""

    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Drive MAN mode first
    dut.rst_n.value = 1
    dut.ui_in.value = 0b101
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    assert int(dut.uo_out.value & 0x1) == 1

    # Apply reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    assert int(dut.uo_out.value & 0x1) == 0, "Reset failed: Control not cleared"
