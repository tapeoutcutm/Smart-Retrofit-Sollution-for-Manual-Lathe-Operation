import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    """PLC_PRG smoke test"""

    dut._log.info("Start PLC_PRG smoke test")

    # Start clock (10ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Apply reset
    dut.reset.value = 1
    dut.start.value = 0
    dut.AUTO.value = 0
    dut.MAN.value = 0
    await ClockCycles(dut.clk, 5)
    dut.reset.value = 0

    # --- Test 1: AUTO mode with START ---
    dut._log.info("Test 1: AUTO mode with START")

    dut.AUTO.value = 1
    dut.start.value = 1

    # Wait enough cycles for TON to finish (preset=20 in sim)
    await ClockCycles(dut.clk, 25)

    control = int(dut.Control.value)
    dut._log.info(f"[Check] Control={control} (expected 1 in AUTO after TON)")
    assert control == 1, f"FAIL: Expected Control=1 in AUTO after TON, got {control}"

    # --- Test 2: MAN mode with START ---
    dut._log.info("Test 2: MAN mode with START")

    # Reset first
    dut.reset.value = 1
    await ClockCycles(dut.clk, 2)
    dut.reset.value = 0

    dut.MAN.value = 1
    dut.start.value = 1
    await ClockCycles(dut.clk, 2)

    control = int(dut.Control.value)
    dut._log.info(f"[Check] Control={control} (expected 1 in MAN mode immediately)")
    assert control == 1, f"FAIL: Expected Control=1 in MAN mode, got {control}"

    # --- Test 3: Reset clears Control ---
    dut._log.info("Test 3: Reset clears Control")

    dut.reset.value = 1
    await ClockCycles(dut.clk, 2)
    dut.reset.value = 0

    control = int(dut.Control.value)
    dut._log.info(f"[Check] Control={control} (expected 0 after reset)")
    assert control == 0, f"FAIL: Expected Control=0 after reset, got {control}"
