import cocotb
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    """Reset helper"""
    dut._log.info("Applying reset...")
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    dut._log.info("Reset released.")


async def clock_gen(dut):
    """Clock generator"""
    while True:
        dut.clk.value = 0
        await Timer(10, units="ns")
        dut.clk.value = 1
        await Timer(10, units="ns")


def log_signals(dut, tag=""):
    """Helper to print DUT state for debugging"""
    dut._log.info(
        f"[{tag}] start={int(dut.ui_in.value[0])} "
        f"AUTO={int(dut.ui_in.value[1])} "
        f"MAN={int(dut.ui_in.value[2])} "
        f"Control={int(dut.uo_out.value[0])}"
    )


@cocotb.test()
async def test_manual_mode(dut):
    """Check manual mode -> Control goes high immediately"""
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)

    # Set MAN=1, start=1
    dut.ui_in.value = 0b00000101
    await RisingEdge(dut.clk)
    log_signals(dut, "ManualMode-1")

    assert dut.uo_out.value[0] == 1, "Manual mode failed: Control should be HIGH immediately"

    # Release start
    dut.ui_in.value = 0b00000100
    await RisingEdge(dut.clk)
    log_signals(dut, "ManualMode-2")

    assert dut.uo_out.value[0] == 0, "Manual mode release failed: Control should be LOW"


@cocotb.test()
async def test_auto_mode(dut):
    """Check auto mode -> Control goes high after delay"""
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)

    # Set AUTO=1, start=1
    dut.ui_in.value = 0b00000011
    log_signals(dut, "AutoMode-start")

    for i in range(25):  # should be > TON_PRESET (20 for sim)
        await RisingEdge(dut.clk)
        log_signals(dut, f"AutoMode-{i}")

    assert dut.uo_out.value[0] == 1, "Auto mode failed: Control should be HIGH after preset delay"


@cocotb.test()
async def test_reset(dut):
    """Check reset clears Control"""
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)

    # Drive manual high first
    dut.ui_in.value = 0b00000101
    await RisingEdge(dut.clk)
    log_signals(dut, "BeforeReset")

    assert dut.uo_out.value[0] == 1, "Setup failed: Control should be HIGH before reset"

    # Now reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    log_signals(dut, "AfterReset")

    assert dut.uo_out.value[0] == 0, "Reset failed: Control should be LOW"
