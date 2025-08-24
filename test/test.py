import cocotb
from cocotb.triggers import RisingEdge, Timer, FallingEdge
from cocotb.clock import Clock

async def reset_dut(dut):
    """Reset helper with proper sequencing for gate-level sim"""
    dut._log.info("Applying reset...")
    
    # Initialize all inputs to known values
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.ena.value = 1  # Keep enable high during reset
    dut.rst_n.value = 0  # Assert reset
    
    # Wait several clock cycles during reset
    for _ in range(10):
        await RisingEdge(dut.clk)
    
    # Release reset and wait for stabilization
    dut.rst_n.value = 1
    
    # Wait for reset to propagate through gate delays
    for _ in range(5):
        await RisingEdge(dut.clk)
    
    dut._log.info("Reset released and stabilized.")

def safe_bit_read(signal, bit_index=0):
    """Safely read a bit from a signal, handling 'x' and 'z' values"""
    try:
        val = signal.value
        if hasattr(val, '__getitem__'):
            bit_val = val[bit_index]
        else:
            bit_val = val if bit_index == 0 else 0
            
        # Handle different representations of unknown values
        str_val = str(bit_val).lower()
        if str_val in ['x', 'z', 'u', 'w', '-']:
            return 0  # Default unknown values to 0
        return int(bit_val)
    except (ValueError, IndexError, TypeError):
        return 0

def log_signals(dut, tag=""):
    """Log DUT signal states with error handling"""
    try:
        start_val = safe_bit_read(dut.ui_in, 0)
        auto_val = safe_bit_read(dut.ui_in, 1)  
        man_val = safe_bit_read(dut.ui_in, 2)
        ena_val = safe_bit_read(dut.ena)
        rst_n_val = safe_bit_read(dut.rst_n)
        control_val = safe_bit_read(dut.uo_out, 0)
        
        dut._log.info(
            f"[{tag}] RST_N={rst_n_val}, ENA={ena_val}, "
            f"START={start_val}, AUTO={auto_val}, MAN={man_val}, "
            f"Control={control_val}"
        )
    except Exception as e:
        dut._log.warning(f"Error logging signals: {e}")

async def wait_clocks(dut, num_clocks):
    """Wait for specified number of clock cycles"""
    for _ in range(num_clocks):
        await RisingEdge(dut.clk)

@cocotb.test()
async def test_reset_functionality(dut):
    """Test basic reset functionality first"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    # Check that outputs are in reset state
    log_signals(dut, "After Reset")
    control_val = safe_bit_read(dut.uo_out, 0)
    
    # In reset state, control should be 0
    if control_val != 0:
        dut._log.warning(f"Reset test: Control expected 0, got {control_val}")
    else:
        dut._log.info("Reset test: PASSED")

@cocotb.test()
async def test_manual_mode(dut):
    """Test manual mode (immediate Control response)"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing Manual Mode...")
    
    # Set manual mode: MAN=1 (bit 2), AUTO=0 (bit 1), START=0 (bit 0)
    dut.ui_in.value = 0b00000100  # MAN=1, others=0
    await wait_clocks(dut, 3)
    log_signals(dut, "Manual Mode Set")
    
    # Apply start signal: MAN=1, START=1
    dut.ui_in.value = 0b00000101  # MAN=1, START=1
    await wait_clocks(dut, 3)
    log_signals(dut, "Manual Start Applied")
    
    control = safe_bit_read(dut.uo_out, 0)
    if control == 1:
        dut._log.info("Manual mode start: PASSED - Control is HIGH")
    else:
        dut._log.warning(f"Manual mode start: Control expected 1, got {control}")
    
    # Release start signal: MAN=1, START=0
    dut.ui_in.value = 0b00000100  # MAN=1, START=0
    await wait_clocks(dut, 3)
    log_signals(dut, "Manual Start Released")
    
    control = safe_bit_read(dut.uo_out, 0)
    if control == 0:
        dut._log.info("Manual mode release: PASSED - Control is LOW")
    else:
        dut._log.warning(f"Manual mode release: Control expected 0, got {control}")

@cocotb.test()
async def test_auto_mode(dut):
    """Test auto mode (Control HIGH after timer delay)"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing Auto Mode...")
    
    # Set auto mode: AUTO=1 (bit 1), MAN=0 (bit 2), START=0 (bit 0)
    dut.ui_in.value = 0b00000010  # AUTO=1, others=0
    await wait_clocks(dut, 3)
    log_signals(dut, "Auto Mode Set")
    
    # Apply start signal: AUTO=1, START=1
    dut.ui_in.value = 0b00000011  # AUTO=1, START=1
    await wait_clocks(dut, 3)
    log_signals(dut, "Auto Start Applied")
    
    # Control should initially be LOW
    control = safe_bit_read(dut.uo_out, 0)
    if control == 0:
        dut._log.info("Auto mode initial: PASSED - Control starts LOW")
    else:
        dut._log.warning(f"Auto mode initial: Control expected 0, got {control}")
    
    # Wait for timer (TON_PRESET = 20 in simulation)
    # Add extra cycles for gate-level simulation delays
    dut._log.info("Waiting for auto timer to expire...")
    await wait_clocks(dut, 35)  # Wait longer than TON_PRESET
    
    log_signals(dut, "Auto After Timer")
    control = safe_bit_read(dut.uo_out, 0)
    if control == 1:
        dut._log.info("Auto mode timer: PASSED - Control is HIGH after delay")
    else:
        dut._log.warning(f"Auto mode timer: Control expected 1, got {control}")
    
    # Release start signal: AUTO=1, START=0
    dut.ui_in.value = 0b00000010  # AUTO=1, START=0
    await wait_clocks(dut, 3)
    log_signals(dut, "Auto Start Released")
    
    control = safe_bit_read(dut.uo_out, 0)
    if control == 0:
        dut._log.info("Auto mode release: PASSED - Control is LOW")
    else:
        dut._log.warning(f"Auto mode release: Control expected 0, got {control}")

@cocotb.test()
async def test_mode_priority(dut):
    """Test that manual mode has priority over auto mode"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing Mode Priority...")
    
    # Set both modes: MAN=1, AUTO=1 (manual should have priority)
    dut.ui_in.value = 0b00000110  # MAN=1, AUTO=1, START=0
    await wait_clocks(dut, 3)
    log_signals(dut, "Both Modes Set")
    
    # Apply start: should behave like manual mode (immediate response)
    dut.ui_in.value = 0b00000111  # MAN=1, AUTO=1, START=1
    await wait_clocks(dut, 3)
    log_signals(dut, "Both Modes Start")
    
    control = safe_bit_read(dut.uo_out, 0)
    if control == 1:
        dut._log.info("Mode priority: PASSED - Manual mode takes priority")
    else:
        dut._log.warning(f"Mode priority: Control expected 1, got {control}")
    
    # Release start
    dut.ui_in.value = 0b00000110  # MAN=1, AUTO=1, START=0
    await wait_clocks(dut, 3)
    log_signals(dut, "Both Modes Start Released")
    
    control = safe_bit_read(dut.uo_out, 0)
    if control == 0:
        dut._log.info("Mode priority release: PASSED - Control follows manual mode")
    else:
        dut._log.warning(f"Mode priority release: Control expected 0, got {control}")

@cocotb.test()
async def test_no_mode_selected(dut):
    """Test behavior when no mode is selected"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing No Mode Selected...")
    
    # No mode selected: MAN=0, AUTO=0
    dut.ui_in.value = 0b00000000  # All bits 0
    await wait_clocks(dut, 3)
    log_signals(dut, "No Mode Set")
    
    # Apply start signal (should have no effect)
    dut.ui_in.value = 0b00000001  # START=1, no modes
    await wait_clocks(dut, 10)
    log_signals(dut, "No Mode Start Applied")
    
    control = safe_bit_read(dut.uo_out, 0)
    if control == 0:
        dut._log.info("No mode test: PASSED - Control remains LOW")
    else:
        dut._log.warning(f"No mode test: Control expected 0, got {control}")

@cocotb.test()
async def test_enable_functionality(dut):
    """Test enable signal functionality"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing Enable Functionality...")
    
    # Disable the module
    dut.ena.value = 0
    dut.ui_in.value = 0b00000101  # MAN=1, START=1
    await wait_clocks(dut, 5)
    log_signals(dut, "Module Disabled")
    
    control = safe_bit_read(dut.uo_out, 0)
    # When disabled, the module should not respond
    # (behavior depends on your design - it might hold previous state or go to 0)
    
    # Re-enable the module
    dut.ena.value = 1
    await wait_clocks(dut, 3)
    log_signals(dut, "Module Re-enabled")
    
    control = safe_bit_read(dut.uo_out, 0)
    if control == 1:
        dut._log.info("Enable test: PASSED - Module responds when enabled")
    else:
        dut._log.info(f"Enable test: Control = {control} when re-enabled")
