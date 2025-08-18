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
    dut._log.info(
        f"[{tag}] start={int(dut.ui_in.value[0])} "
        f"AUTO={int(dut.ui_in.value[1])} "
        f"MAN={int(dut.ui_in.value[2])} "
        f"Control={int(dut.uo_out.value[0])} "
        f"ena={int(dut.ena.value)} "
        f"rst_n={int(dut.rst_n.value)}"
    )

@cocotb.test()
async def test_manual_mode(dut):
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)
    
    # Test manual mode activation
    dut.ui_in.value = 0b00000101  # MAN=1, START=1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    log_signals(dut, "ManualMode-Active")
    assert dut.uo_out.value[0] == 1, f"Manual mode failed: Control should be HIGH, got {int(dut.uo_out.value[0])}"
    
    # Test manual mode deactivation
    dut.ui_in.value = 0b00000100  # MAN=1, START=0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    log_signals(dut, "ManualMode-Inactive")
    assert dut.uo_out.value[0] == 0, f"Manual mode release failed: Control should be LOW, got {int(dut.uo_out.value[0])}"

@cocotb.test()
async def test_auto_mode(dut):
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)
    
    # Test auto mode - should start LOW
    dut.ui_in.value = 0b00000011  # AUTO=1, START=1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    log_signals(dut, "AutoMode-Start")
    assert dut.uo_out.value[0] == 0, f"Auto mode start: Control should be LOW initially, got {int(dut.uo_out.value[0])}"
    
    # Wait for timer to complete (TON_PRESET=20 + margin)
    for i in range(25):
        await RisingEdge(dut.clk)
        if i == 22:  # Check near the end
            log_signals(dut, f"AutoMode-Cycle{i}")
    
    log_signals(dut, "AutoMode-Final")
    assert dut.uo_out.value[0] == 1, f"Auto mode failed: Control should be HIGH after delay, got {int(dut.uo_out.value[0])}"
    
    # Test auto mode deactivation
    dut.ui_in.value = 0b00000010  # AUTO=1, START=0
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    log_signals(dut, "AutoMode-Release")
    assert dut.uo_out.value[0] == 0, f"Auto mode release failed: Control should be LOW, got {int(dut.uo_out.value[0])}"

@cocotb.test()
async def test_reset(dut):
    cocotb.start_soon(clock_gen(dut))
    await reset_dut(dut)
    
    # First verify we can set Control HIGH in manual mode
    log_signals(dut, "Initial")
    
    dut.ui_in.value = 0b00000101  # MAN=1, START=1
    await RisingEdge(dut.clk)
    log_signals(dut, "After1stClock")
    
    await RisingEdge(dut.clk)
    log_signals(dut, "BeforeAssert")
    
    # Debug the specific values
    control_val = int(dut.uo_out.value[0])
    start_val = int(dut.ui_in.value[0])
    man_val = int(dut.ui_in.value[2])
    ena_val = int(dut.ena.value)
    
    dut._log.info(f"DEBUG: Control={control_val}, start={start_val}, MAN={man_val}, ena={ena_val}")
    
    assert control_val == 1, f"Setup failed: Control should be HIGH before reset. Control={control_val}, inputs: MAN={man_val}, START={start_val}, ena={ena_val}"
    
    # Now test reset functionality
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    log_signals(dut, "DuringReset")
    assert dut.uo_out.value[0] == 0, "Reset failed: Control should be LOW during reset"
    
    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    log_signals(dut, "AfterReset")
    assert dut.uo_out.value[0] == 0, "Reset failed: Control should remain LOW after reset"
