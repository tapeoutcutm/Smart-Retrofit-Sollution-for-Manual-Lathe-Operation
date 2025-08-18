`timescale 1ns / 1ps
module tb_PLC_PRG;

    // Inputs
    reg clk;
    reg rst;
    reg start;
    reg stop;
    reg sel0;     // not used in DUT logic now, but kept
    reg AUTO;
    reg MAN;

    // Outputs
    wire Control;
    wire Q;

    // Instantiate DUT
    PLC_PRG dut (
        .clk(clk),
        .rst(rst),
        .start(start),
        .stop(stop),
        .sel0(sel0),
        .AUTO(AUTO),
        .MAN(MAN),
        .Control(Control),
        .Q(Q)
    );

    // Clock generation: 50 MHz → 20ns period
    initial begin
        clk = 0;
        forever #10 clk = ~clk; // toggle every 10ns
    end

    // Apply stimulus
    initial begin
        // Initialize inputs
        rst   = 1;
        start = 0;
        stop  = 0;
        sel0  = 0;
        AUTO  = 0;
        MAN   = 0;

        // Apply reset for 50ns
        #50;
        rst = 0;
        $display("[%0t] Release reset", $time);

        // --------- MANUAL MODE TEST ---------
        MAN = 1;
        $display("[%0t] MAN mode active", $time);
        #50 start = 1;    // press start
        #100 start = 0;   // release start
        #500;
        stop = 1;         // press stop
        #50 stop = 0;

        // --------- AUTO MODE TEST ---------
        MAN  = 0;
        AUTO = 1;
        $display("[%0t] AUTO mode active", $time);

        #100 start = 1;   // set latch 
        #20 start = 0;

        // Wait time (simulate shorter time for TON)
        #200000; // ~200us (reduce ton preset in DUT for faster simulation if desired)

        stop = 1;         // reset latch
        #20 stop = 0;

        // --------- END SIMULATION ---------
        #1000;
        $display("[%0t] End simulation", $time);
        $stop;
    end

endmodule
