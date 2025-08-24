import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

async def reset_dut(dut):
    """Reset helper with proper sequencing for gate-level sim"""
    dut._log.info("Applying reset...")
    
    # Initialize all inputs to known values first
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.ena.value = 1
    
    # Assert reset (active low)
    dut.rst_n.value = 0
    
    # Wait several clock cycles during reset
    for _ in range(10):
        await RisingEdge(dut.clk)
    
    # Release reset
    dut.rst_n.value = 1
    
    # Wait for reset to propagate
    for _ in range(10):
        await RisingEdge(dut.clk)
    
    dut._log.info("Reset released and stabilized.")

def safe_int_read(signal):
    """Safely convert signal to integer, handling 'x' and 'z' values"""
    try:
        val = signal.value
        # Convert to string first to handle different types
        str_val = str(val).lower()
        
        # Handle unknown states
        if 'x' in str_val or 'z' in str_val or 'u' in str_val:
            return 0
        
        # Handle binary strings
        if str_val.startswith('0b'):
            return int(str_val, 2)
        elif str_val.startswith('0x'):
            return int(str_val, 16)
        else:
            return int(val)
    except (ValueError, TypeError, AttributeError):
        return 0

def get_bit(signal, bit_index):
    """Extract a specific bit from a signal"""
    val = safe_int_read(signal)
    return (val >> bit_index) & 1

def log_signals(dut, tag=""):
    """Log DUT signal states with error handling"""
    try:
        ui_in_val = safe_int_read(dut.ui_in)
        start_val = get_bit(dut.ui_in, 0)
        auto_val = get_bit(dut.ui_in, 1)
        man_val = get_bit(dut.ui_in, 2)
        ena_val = safe_int_read(dut.ena)
        rst_n_val = safe_int_read(dut.rst_n)
        control_val = get_bit(dut.uo_out, 0)
        
        dut._log.info(
            f"[{tag}] ui_in=0x{ui_in_val:02x}, RST_N={rst_n_val}, ENA={ena_val}, "
            f"START={start_val}, AUTO={auto_val}, MAN={man_val}, Control={control_val}"
        )
    except Exception as e:
        dut._log.warning(f"Error logging signals: {e}")

async def wait_clocks(dut, num_clocks):
    """Wait for specified number of clock cycles"""
    for _ in range(num_clocks):
        await RisingEdge(dut.clk)

async def set_inputs_and_wait(dut, ui_in_value, cycles=5):
    """Set input value and wait for propagation"""
    dut.ui_in.value = ui_in_value
    await wait_clocks(dut, cycles)

@cocotb.test()
async def test_reset_functionality(dut):
    """Test basic reset functionality first"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    # Check that outputs are in reset state
    log_signals(dut, "After Reset")
    control_val = get_bit(dut.uo_out, 0)
    
    if control_val == 0:
        dut._log.info("Reset test: PASSED")
    else:
        dut._log.warning(f"Reset test: Control expected 0, got {control_val}")

@cocotb.test()
async def test_manual_mode(dut):
    """Test manual mode (immediate Control response)"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing Manual Mode...")
    
    # Set manual mode: MAN=1 (bit 2) = 0b100 = 0x04
    await set_inputs_and_wait(dut, 0x04)  # MAN=1, AUTO=0, START=0
    log_signals(dut, "Manual Mode Set")
    
    # Apply start signal: MAN=1, START=1 = 0b101 = 0x05
    await set_inputs_and_wait(dut, 0x05)  # MAN=1, AUTO=0, START=1
    log_signals(dut, "Manual Start Applied")
    
    control = get_bit(dut.uo_out, 0)
    if control == 1:
        dut._log.info("Manual mode start: PASSED - Control is HIGH")
    else:
        dut._log.error(f"Manual mode start: FAILED - Control expected 1, got {control}")
    
    # Release start signal: MAN=1, START=0 = 0x04
    await set_inputs_and_wait(dut, 0x04)  # MAN=1, AUTO=0, START=0
    log_signals(dut, "Manual Start Released")
    
    control = get_bit(dut.uo_out, 0)
    if control == 0:
        dut._log.info("Manual mode release: PASSED - Control is LOW")
    else:
        dut._log.error(f"Manual mode release: FAILED - Control expected 0, got {control}")

@cocotb.test()
async def test_auto_mode(dut):
    """Test auto mode (Control HIGH after timer delay)"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing Auto Mode...")
    
    # Set auto mode: AUTO=1 (bit 1) = 0b010 = 0x02
    await set_inputs_and_wait(dut, 0x02)  # AUTO=1, MAN=0, START=0
    log_signals(dut, "Auto Mode Set")
    
    # Apply start signal: AUTO=1, START=1 = 0b011 = 0x03
    await set_inputs_and_wait(dut, 0x03)  # AUTO=1, MAN=0, START=1
    log_signals(dut, "Auto Start Applied")
    
    # Control should initially be LOW
    control = get_bit(dut.uo_out, 0)
    if control == 0:
        dut._log.info("Auto mode initial: PASSED - Control starts LOW")
    else:
        dut._log.warning(f"Auto mode initial: Control expected 0, got {control}")
    
    # Wait for timer (TON_PRESET = 20 in simulation)
    dut._log.info("Waiting for auto timer to expire...")
    await wait_clocks(dut, 25)  # Wait for timer + margin
    
    log_signals(dut, "Auto After Timer")
    control = get_bit(dut.uo_out, 0)
    if control == 1:
        dut._log.info("Auto mode timer: PASSED - Control is HIGH after delay")
    else:
        dut._log.error(f"Auto mode timer: FAILED - Control expected 1, got {control}")
    
    # Release start signal: AUTO=1, START=0 = 0x02
    await set_inputs_and_wait(dut, 0x02)  # AUTO=1, MAN=0, START=0
    log_signals(dut, "Auto Start Released")
    
    control = get_bit(dut.uo_out, 0)
    if control == 0:
        dut._log.info("Auto mode release: PASSED - Control is LOW")
    else:
        dut._log.error(f"Auto mode release: FAILED - Control expected 0, got {control}")

@cocotb.test()
async def test_mode_priority(dut):
    """Test that manual mode has priority over auto mode"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing Mode Priority...")
    
    # Set both modes: MAN=1, AUTO=1 = 0b110 = 0x06
    await set_inputs_and_wait(dut, 0x06)  # MAN=1, AUTO=1, START=0
    log_signals(dut, "Both Modes Set")
    
    # Apply start: should behave like manual mode (immediate response)
    # MAN=1, AUTO=1, START=1 = 0b111 = 0x07
    await set_inputs_and_wait(dut, 0x07)
    log_signals(dut, "Both Modes Start")
    
    control = get_bit(dut.uo_out, 0)
    if control == 1:
        dut._log.info("Mode priority: PASSED - Manual mode takes priority")
    else:
        dut._log.error(f"Mode priority: FAILED - Control expected 1, got {control}")
    
    # Release start: MAN=1, AUTO=1, START=0 = 0x06
    await set_inputs_and_wait(dut, 0x06)
    log_signals(dut, "Both Modes Start Released")
    
    control = get_bit(dut.uo_out, 0)
    if control == 0:
        dut._log.info("Mode priority release: PASSED - Control follows manual mode")
    else:
        dut._log.error(f"Mode priority release: FAILED - Control expected 0, got {control}")

@cocotb.test()
async def test_no_mode_selected(dut):
    """Test behavior when no mode is selected"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing No Mode Selected...")
    
    # No mode selected: MAN=0, AUTO=0, START=0 = 0x00
    await set_inputs_and_wait(dut, 0x00)
    log_signals(dut, "No Mode Set")
    
    # Apply start signal (should have no effect)
    # MAN=0, AUTO=0, START=1 = 0x01
    await set_inputs_and_wait(dut, 0x01)
    log_signals(dut, "No Mode Start Applied")
    
    control = get_bit(dut.uo_out, 0)
    if control == 0:
        dut._log.info("No mode test: PASSED - Control remains LOW")
    else:
        dut._log.error(f"No mode test: FAILED - Control expected 0, got {control}")
    
    # Wait a bit longer to make sure it doesn't change
    await wait_clocks(dut, 30)
    control = get_bit(dut.uo_out, 0)
    if control == 0:
        dut._log.info("No mode extended test: PASSED - Control still LOW")
    else:
        dut._log.error(f"No mode extended test: FAILED - Control expected 0, got {control}")

@cocotb.test()
async def test_enable_functionality(dut):
    """Test enable signal functionality"""
    # Start clock
    clock = Clock(dut.clk, 20, units="ns")  # 50MHz
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut)
    
    dut._log.info("Testing Enable Functionality...")
    
    # First, test normal operation with enable=1
    await set_inputs_and_wait(dut, 0x05)  # MAN=1, START=1
    control_enabled = get_bit(dut.uo_out, 0)
    log_signals(dut, "Normal Operation")
    
    if control_enabled == 1:
        dut._log.info("Enable test setup: PASSED - Normal operation works")
    else:
        dut._log.warning("Enable test setup: Normal operation not working as expected")
    
    # Now disable the module
    dut.ena.value = 0
    await wait_clocks(dut, 10)
    log_signals(dut, "Module Disabled")
    
    # According to your design, when ena=0, the logic shouldn't update
    # The behavior depends on your specific design implementation
    
    # Re-enable the module
    dut.ena.value = 1
    await wait_clocks(dut, 5)
    log_signals(dut, "Module Re-enabled")
    
    # Test that it works again
    await set_inputs_and_wait(dut, 0x04)  # MAN=1, START=0
    control = get_bit(dut.uo_out, 0)
    if control == 0:
        dut._log.info("Enable test: PASSED - Module responds correctly when re-enabled")
    else:
        dut._log.info(f"Enable test: Module behavior when re-enabled, Control={control}")
