`timescale 1ns / 1ps

module tt_um_plc_prg (
    input  wire clk,
    input  wire reset,
    input  wire start,
    input  wire AUTO,
    input  wire MAN,
    output reg  Control
);

    // Timer preset (different in simulation vs hardware)
`ifdef COCOTB_SIM
    parameter TON_PRESET = 20;              // Short delay for cocotb sim
`else
    parameter TON_PRESET = 150_000_000;     // 3s delay at 50MHz (real HW)
`endif

    reg [$clog2(TON_PRESET):0] counter;
    reg timer_done;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            counter     <= 0;
            timer_done  <= 0;
            Control     <= 0;
        end else begin
            if (AUTO && start) begin
                // Timer ON delay
                if (!timer_done) begin
                    if (counter < TON_PRESET) begin
                        counter <= counter + 1;
                    end else begin
                        timer_done <= 1;
                        Control    <= 1;
                    end
                end
            end else if (MAN && start) begin
                // Manual mode: immediate control
                Control    <= 1;
                timer_done <= 1;
            end else begin
                // No start: reset outputs
                counter     <= 0;
                timer_done  <= 0;
                Control     <= 0;
            end
        end
    end

endmodule

