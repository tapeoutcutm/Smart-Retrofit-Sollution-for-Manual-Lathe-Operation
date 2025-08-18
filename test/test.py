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
    cocotb.log.info(f"Manual Mode: ui_in={dut.ui_in.value.bin}, expected Control=1")

    await RisingEdge(dut.clk)
    cocotb.log.info(f"Control={dut.uo_out.value.bin}")
    assert dut.uo_out.value.integer & 1 == 1, "Manual mode failed: Control should be 1 immediately"

    # Stop start
    dut.ui_in.value = 0b100  # MAN=1, start=0
    await RisingEdge(dut.clk)
    cocotb.log.info(f"Manual Mode stop: ui_in={dut.ui_in.value.bin}, Control={dut.uo_out.value.bin}")
    assert dut.uo_out.value.integer & 1 == 0, "Manual mode failed: Control should clear when start=0"
