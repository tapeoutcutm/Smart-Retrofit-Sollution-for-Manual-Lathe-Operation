import cocotb
from cocotb.triggers import RisingEdge, Timer


async def reset_dut(dut):
    """Reset helper"""
    dut._log.info("Applying reset...")
    dut.rst_n.value = 0
    dut.ena.value = 0
    dut.ui_in.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    dut.ena.value = 1
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
    """Helper to log DUT inputs and outputs"""
    dut._log.info(
        f"[{tag}] START={int(dut.ui_in.value[0])} "
        f"AUTO={int(dut.ui_in.value[1])} "
        f"MAN={int(dut.ui_in.value[2])} "
        f"ENA={int(dut.ena.value)} "
        f"Control={int(dut.uo_out.value[0])}"
    )


@cocotb.test()
async def test_manual_mode(dut):
    """Manual mode should raise Control immediately on start"""
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)

    dut.ui_in.value = 0b00000101  # MAN=1, START=1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    control = int(dut.uo_out.value[0])
    log_signals(dut, "ManualMode-1")
    assert control == 1, f"Manual mode failed: Control={control}, expected 1"

    # Release start
    dut.ui_in.value = 0b00000100  # MAN=1, START=0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    control = int(dut.uo_out.value[0])
    log_signals(dut, "ManualMode-2")
    assert control == 0, f"Manual release failed: Control={control}, expected 0"


@cocotb.test()
async def test_auto_mode(dut):
    """Auto mode should raise Control after delay"""
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)

    dut.ui_in.value = 0b00000011  # AUTO=1, START=1
    await RisingEdge(dut.clk)
    log_signals(dut, "AutoMode-start")

    for i in range(25):  # wait > TON_PRESET
        await RisingEdge(dut.clk)

    control = int(dut.uo_out.value[0])
    log_signals(dut, "AutoMode-final")
    assert control == 1, f"Auto mode failed: Control={control}, expected 1"

    # Release start
    dut.ui_in.value = 0b00000010  # AUTO=1, START=0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    control = int(dut.uo_out.value[0])
    log_signals(dut, "AutoMode-release")
    assert control == 0, f"Auto release failed: Control={control}, expected 0"


@cocotb.test()
async def test_reset(dut):
    """Reset should clear Control"""
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)

    # Apply manual condition
    dut.ui_in.value = 0b00000101  # MAN=1, START=1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Capture values
    control_val = int(dut.uo_out.value[0])
    man_val = int(dut.ui_in.value[2])
    start_val = int(dut.ui_in.value[0])
    ena_val = int(dut.ena.value)

    log_signals(dut, "BeforeReset")

    assert control_val == 1, (
        f"Setup failed: Control should be HIGH before reset. "
        f"Control={control_val}, inputs: MAN={man_val}, START={start_val}, ena={ena_val}"
    )

    # Apply reset
    dut.rst_n.value = 0
    await Timer(20, units="ns")
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    control_after = int(dut.uo_out.value[0])
    log_signals(dut, "AfterReset")
    assert control_after == 0, f"Reset failed: Control={control_after}, expected 0"
