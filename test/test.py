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
    await RisingEdge(dut.clk)  # Extra clock cycle for stability
    dut._log.info("Reset released.")

async def clock_gen(dut):
    """Clock generator"""
    while True:
        dut.clk.value = 0
        await Timer(10, units="ns")
        dut.clk.value = 1
        await Timer(10, units="ns")

def log_signals(dut, tag=""):
    dut._log.info(
        f"[{tag}] start={int(dut.ui_in.value[0])} "
        f"AUTO={int(dut.ui_in.value[1])} "
        f"MAN={int(dut.ui_in.value[2])} "
        f"Control={int(dut.uo_out.value[0])}"
    )

@cocotb.test()
async def test_manual_mode(dut):
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)
    
    # Apply MAN=1, START=1
    dut.ui_in.value = 0b00000101  # MAN=1, START=1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Give more time for logic to settle
    log_signals(dut, "ManualMode-1")
    assert dut.uo_out.value[0] == 1, "Manual mode failed: Control should be HIGH"
    
    # Release start
    dut.ui_in.value = 0b00000100  # START=0, MAN=1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Give more time for logic to settle
    log_signals(dut, "ManualMode-2")
    assert dut.uo_out.value[0] == 0, "Manual mode release failed: Control should be LOW"

@cocotb.test()
async def test_auto_mode(dut):
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)
    
    # Apply AUTO=1, START=1
    dut.ui_in.value = 0b00000011  # AUTO=1, START=1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Give time for start edge detection
    log_signals(dut, "AutoMode-start")
    
    # Control should be LOW initially
    assert dut.uo_out.value[0] == 0, "Auto mode start: Control should be LOW initially"
    
    # Wait longer than TON_PRESET (20) + some margin
    for i in range(25):
        await RisingEdge(dut.clk)
    
    log_signals(dut, "AutoMode-final")
    assert dut.uo_out.value[0] == 1, "Auto mode failed: Control should be HIGH after delay"
    
    # Release start
    dut.ui_in.value = 0b00000010  # AUTO=1, START=0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Give more time for logic to settle
    log_signals(dut, "AutoMode-release")
    assert dut.uo_out.value[0] == 0, "Auto mode release failed: Control should be LOW"

@cocotb.test()
async def test_reset(dut):
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)
    
    # Apply MAN=1, START=1 to activate control
    dut.ui_in.value = 0b00000101  # MAN=1, START=1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Give more time for logic to settle
    log_signals(dut, "BeforeReset")
    assert dut.uo_out.value[0] == 1, "Setup failed: Control should be HIGH before reset"
    
    # Apply reset while keeping inputs active
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    log_signals(dut, "DuringReset")
    assert dut.uo_out.value[0] == 0, "Reset failed: Control should be LOW during reset"
    
    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)  # Give more time for logic to settle
    log_signals(dut, "AfterReset")
    assert dut.uo_out.value[0] == 0, "Reset failed: Control should remain LOW after reset"
