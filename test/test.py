import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def test_auto_mode(dut):
    """Test AUTO mode with timer delay"""

    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())  # 100 MHz

    # Apply reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # AUTO mode: ui_in[1] = 1, start = 1
    dut.ui_in.value = 0b011  # start=1, AUTO=1, MAN=0
    dut._log.info("Testing AUTO mode (with delay)")

    # Wait for timer to expire (20 cycles in sim)
    for _ in range(25):
        await RisingEdge(dut.clk)

    assert dut.uo_out.value & 0x1 == 1, "AUTO mode failed: Control not set after delay"


@cocotb.test()
async def test_manual_mode(dut):
    """Test MAN mode (immediate control)"""

    # Start clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # MAN mode: ui_in[2] = 1, start = 1
    dut.ui_in.value = 0b101  # start=1, AUTO=0, MAN=1
    dut._log.info("Testing MAN mode (immediate control)")

    await RisingEdge(dut.clk)

    assert dut.uo_out.value & 0x1 == 1, "MAN mode failed: Control not set immediately"
