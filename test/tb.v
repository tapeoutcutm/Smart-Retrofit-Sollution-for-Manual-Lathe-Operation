`timescale 1ns/1ps

module tb_tt_um_plc_prg;
    reg  [7:0] ui_in;
    wire [7:0] uo_out;
    reg  [7:0] uio_in;
    wire [7:0] uio_out;
    wire [7:0] uio_oe;
    reg clk, rst_n, ena;

    // Instantiate DUT (Device Under Test)
    tt_um_plc_prg dut (
        .ui_in(ui_in),
        .uo_out(uo_out),
        .uio_in(uio_in),
        .uio_out(uio_out),
        .uio_oe(uio_oe),
        .clk(clk),
        .rst_n(rst_n),
        .ena(ena)
    );

    // Clock generation (20ns period = 50MHz)
    always #10 clk = ~clk;

    // Input assignments for readability
    wire clk_in   = ui_in[0];
    wire rst      = ui_in[1];
    wire start    = ui_in[2];
    wire stop     = ui_in[3];
    wire sel0     = ui_in[4];
    wire AUTO     = ui_in[5];
    wire MAN      = ui_in[6];

    // Test stimulus
    initial begin
        // Initialize
        clk    = 0;
        rst_n  = 1;
        ena    = 1;
        ui_in  = 8'b0;
        uio_in = 8'b0;

        // Apply reset
        ui_in[1] = 1; // rst high
        #50;
        ui_in[1] = 0; // release reset

        // Start in AUTO mode
        ui_in[5] = 1; // AUTO = 1
        ui_in[6] = 0; // MAN = 0

        // Apply START signal (latch set)
        ui_in[2] = 1;
        #20;
        ui_in[2] = 0;

        // Wait enough cycles for TON (counter reduced in simulation)
        #1000;

        // Apply STOP signal (latch reset)
        ui_in[3] = 1;
        #20;
        ui_in[3] = 0;

        // Switch to MANUAL mode
        #100;
        ui_in[5] = 0; // AUTO = 0
        ui_in[6] = 1; // MAN = 1

        // Trigger START again in MAN mode
        ui_in[2] = 1;
        #50;
        ui_in[2] = 0;

        #500;
        $finish;
    end

    // Monitor key signals
    initial begin
        $dumpfile("tb_tt_um_plc_prg.vcd");
        $dumpvars(0, tb_tt_um_plc_prg);

        $display("Time\tclk start stop AUTO MAN Control Q");
        $monitor("%0t\t%b   %b     %b    %b    %b    %b       %b",
                  $time, clk, ui_in[2], ui_in[3], ui_in[5], ui_in[6],
                  uo_out[0], uo_out[1]);
    end

endmodule
