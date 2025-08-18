import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


SIM_PRESET = 20  # cycles; loaded into DUT via uio_in at reset


async def reset_and_prep(dut, preset=SIM_PRESET):
    """Apply reset, set sim preset via uio_in, and enable DUT."""
    # Drive clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Set desired preset on uio_in *before* releasing reset
    dut.uio_in.value = preset

    # Assert reset (active low)
    dut.rst_n.value = 0
    dut.ena.value   = 0
    dut.ui_in.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)

    # Release reset, enable
    dut.rst_n.value = 1
    dut.ena.value   = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_manual_mode(dut):
    """MAN mode: Control should assert immediately when start=1."""
    await reset_and_prep(dut)

    # MAN=1, start=1 -> ui_in[2]=1, ui_in[0]=1
    dut.ui_in.value = 0b101
    await RisingEdge(dut.clk)

    assert (dut.uo_out.value.integer & 1) == 1, \
        f"Manual mode failed: expected Control=1, got {dut.uo_out.value.bin}"

    # Drop start -> Control must clear
    dut.ui_in.value = 0b100
    await RisingEdge(dut.clk)
    assert (dut.uo_out.value.integer & 1) == 0, \
        f"Manual clear failed: expected Control=0, got {dut.uo_out.value.bin}"


@cocotb.test()
async def test_auto_mode(dut):
    """AUTO mode: Control should assert after SIM_PRESET cycles with start=1."""
    await reset_and_prep(dut, preset=SIM_PRESET)

    # AUTO=1, start=1 -> ui_in[1]=1, ui_in[0]=1
    dut.ui_in.value = 0b011

    # Wait slightly more than the preset number of cycles
    for _ in range(SIM_PRESET + 2):
        await RisingEdge(dut.clk)

    assert (dut.uo_out.value.integer & 1) == 1, \
        f"AUTO mode failed: expected Control=1 after {SIM_PRESET} cycles, got {dut.uo_out.value.bin}"


@cocotb.test()
async def test_reset(dut):
    """Reset clears Control."""
    await reset_and_prep(dut)

    # First, assert control via manual mode
    dut.ui_in.value = 0b101  # MAN=1, start=1
    await RisingEdge(dut.clk)
    assert (dut.uo_out.value.integer & 1) == 1, "Precondition failed: Control should be 1"

    # Apply reset -> should clear
    dut.rst_n.value = 0
    for _ in range(2):
        await RisingEdge(dut.clk)
    assert (dut.uo_out.value.integer & 1) == 0, \
        f"Reset failed: expected Control=0, got {dut.uo_out.value.bin}"

    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
