# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


@cocotb.test()
async def test_project(dut):
    dut._log.info("Start PLC_PRG test")

    # Clock setup: 50 MHz → 20 ns period
    clock = Clock(dut.clk, 20, units="ns")
    cocotb.start_soon(clock.start())

    # Reset and enable
    dut.ena.value = 1
    dut.rst_n.value = 0
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1

    # Helper aliases for outputs
    def control(): return int(dut.uo_out.value & 0b00000001)
    def q():       return int((dut.uo_out.value >> 1) & 0b1)

    # -----------------------------
    # Test 1: AUTO mode with START
    # -----------------------------
    dut._log.info("Test 1: AUTO mode with START")
    dut.ui_in.value = 0
    dut.ui_in.value = (1 << 5)  # AUTO=1
    dut.ui_in.value |= (1 << 2)  # START=1
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value &= ~(1 << 2)  # release START

    # Wait for short TON (simulation friendly: reduce counter in RTL)
    await ClockCycles(dut.clk, 30)

    assert control() == 1, f"Expected Control=1 in AUTO mode, got {control()}"

    # -----------------------------
    # Test 2: AUTO → STOP resets latch
    # -----------------------------
    dut._log.info("Test 2: STOP signal resets latch")
    dut.ui_in.value |= (1 << 3)  # STOP=1
    await ClockCycles(dut.clk, 2)
    dut.ui_in.value &= ~(1 << 3)
    await ClockCycles(dut.clk, 5)

    assert control() == 0, f"Expected Control=0 after STOP, got {control()}"

    # -----------------------------
    # Test 3: MANUAL mode follows START
    # -----------------------------
    dut._log.info("Test 3: MANUAL mode follows START input")
    dut.ui_in.value = (1 << 6)  # MAN=1
    await ClockCycles(dut.clk, 2)

    dut.ui_in.value |= (1 << 2)  # START=1
    await ClockCycles(dut.clk, 2)
    assert control() == 1, f"Expected Control=1 in MANUAL mode, got {control()}"

    dut.ui_in.value &= ~(1 << 2)  # START=0
    await ClockCycles(dut.clk, 2)
    assert control() == 0, f"Expected Control=0 after START=0 in MANUAL, got {control()}"

    # -----------------------------
    # Test 4: CTU increments on TON done
    # -----------------------------
    dut._log.info("Test 4: CTU increments after TON done pulses")
    dut.ui_in.value = (1 << 5)  # AUTO=1
    for i in range(6):  # preset=5, so after 5 TON pulses Q=1
        dut.ui_in.value |= (1 << 2)  # START=1
        await ClockCycles(dut.clk, 2)
        dut.ui_in.value &= ~(1 << 2)
        await ClockCycles(dut.clk, 25)  # wait for TON
    assert q() == 1, f"Expected Q=1 after 5 TON events, got {q()}"

    dut._log.info("All test cases passed ")
