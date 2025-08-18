import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


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
    await RisingEdge(dut.clk)  # wait 1 cycle after ena

    # Apply Manual Mode
    dut.ui_in.value = 0b101  # [2]=MAN=1, [1]=AUTO=0, [0]=start=1
    cocotb.log.info(f"[MANUAL] ui_in={dut.ui_in.value.bin}, expected Control=1")

    await RisingEdge(dut.clk)
    cocotb.log.info(f"[MANUAL] Control={dut.uo_out.value.bin}")
    assert dut.uo_out.value.integer & 1 == 1, "Manual mode failed: Control should be 1 immediately"

    # Stop start
    dut.ui_in.value = 0b100  # MAN=1, start=0
    await RisingEdge(dut.clk)
    cocotb.log.info(f"[MANUAL STOP] ui_in={dut.ui_in.value.bin}, Control={dut.uo_out.value.bin}")
    assert dut.uo_out.value.integer & 1 == 0, "Manual mode failed: Control should clear when start=0"


@cocotb.test()
async def test_auto_mode(dut):
    """Check auto mode sets Control after TON_PRESET cycles."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Reset DUT
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)

    # Enable DUT
    dut.ena.value = 1
    await RisingEdge(dut.clk)

    # Apply Auto Mode
    dut.ui_in.value = 0b011  # [2]=MAN=0, [1]=AUTO=1, [0]=start=1
    cocotb.log.info(f"[AUTO] ui_in={dut.ui_in.value.bin}, waiting for Control=1 after delay")

    # Wait for enough cycles to reach TON_PRESET
    for _ in range(25):  # preset is 20 cycles in simulation
        await RisingEdge(dut.clk)

    cocotb.log.info(f"[AUTO] Control={dut.uo_out.value.bin}")
    assert dut.uo_out.value.integer & 1 == 1, "Auto mode failed: Control should be 1 after delay"


@cocotb.test()
async def test_reset(dut):
    """Check reset clears Control."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply Manual Mode first
    dut.ena.value = 1
    dut.ui_in.value = 0b101  # MAN=1, start=1
    await RisingEdge(dut.clk)
    assert dut.uo_out.value.integer & 1 == 1, "Precondition failed: Control should be set"

    # Apply Reset
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    cocotb.log.info(f"[RESET] Control={dut.uo_out.value.bin}")
    assert dut.uo_out.value.integer & 1 == 0, "Reset failed: Control should clear"
    dut.rst_n.value = 1
