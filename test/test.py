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
    """Log DUT signal states"""
    dut._log.info(
        f"[{tag}] START={int(dut.ui_in.value[0])}, "
        f"AUTO={int(dut.ui_in.value[1])}, "
        f"MAN={int(dut.ui_in.value[2])}, "
        f"ENA={int(dut.ena.value)}, "
        f"Control={int(dut.uo_out.value[0])}"
    )


@cocotb.test()
async def test_manual_mode(dut):
    """Test manual mode (immediate Control HIGH)"""
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)

    #Apply MAN=1, START=1
    dut.ui_in.value = 0b00000101
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

  #  log_signals(dut, "ManualMode-Active")
    control = int(dut.uo_out.value[0])
    assert control == 1, "Manual mode failed: Control should be HIGH"

    # Release start
    dut.ui_in.value = 0b00000100
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    log_signals(dut, "ManualMode-Release")
    control = int(dut.uo_out.value[0])
    assert control == 0, "Manual mode release failed: Control should be LOW"


@cocotb.test()
async def test_auto_mode(dut):
    """Test auto mode (Control HIGH after delay)"""
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)

    #Apply AUTO=1, START=1
    dut.ui_in.value = 0b00000011
    await RisingEdge(dut.clk)
    log_signals(dut, "AutoMode-Start")

    # Wait > preset (20 in sim)
    for i in range(25):
        await RisingEdge(dut.clk)

    log_signals(dut, "AutoMode-AfterDelay")
    control = int(dut.uo_out.value[0])
    assert control == 1, "Auto mode failed: Control should be HIGH after delay"

    # Release start
    dut.ui_in.value = 0b00000010
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    log_signals(dut, "AutoMode-Release")
    control = int(dut.uo_out.value[0])
    assert control == 0, "Auto mode release failed: Control should be LOW"


@cocotb.test()
async def test_reset(dut):
    """Test that reset clears Control"""
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)

    # Apply manual start
    dut.ui_in.value = 0b00000101  # MAN=1, START=1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Read values before reset
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

    assert control_after == 0, "Reset failed: Control should be LOW"
