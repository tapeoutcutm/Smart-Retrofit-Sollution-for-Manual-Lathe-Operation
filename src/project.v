`timescale 1ns / 1ps
module PLC_PRG (
    input  wire clk,        // PLC scan → here we use a clock
    input  wire rst,        // async reset
    input  wire start,
    input  wire stop,
    input  wire sel0,
    input  wire AUTO,
    input  wire MAN,
    output reg  Control,
    output reg  Q
);
    // Internal signals
    reg latch_q;                 // SR latch output
    reg [27:0] ton_counter;      // Timer counter (28 bits for 150M count)
    reg ton_done;                // TON done flag
    reg [3:0] ctu_count;         // Counter up value
    reg ctu_done;                // Counter reached preset

    // For edge detection of ton_done
    reg ton_done_d;

    //----------------------------
    // SR Latch Logic
    //----------------------------
    always @(posedge clk or posedge rst) begin
        if (rst)
            latch_q <= 1'b0;
        else if (start)
            latch_q <= 1'b1;       // Set latch
        else if (stop)
            latch_q <= 1'b0;       // Reset latch
        else
            latch_q <= latch_q;    // Hold value (optional)
    end

    //----------------------------
    // TON 3s Delay (example for 50MHz clock)
    //----------------------------
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            ton_counter <= 0;
            ton_done    <= 0;
        end else if (latch_q) begin
            if (ton_counter < 150_000_000) begin // 3s @ 50MHz
                ton_counter <= ton_counter + 1;
                ton_done <= 1'b0;
            end else begin
                ton_done <= 1'b1;
            end
        end else begin
            ton_counter <= 0;
            ton_done    <= 0;
        end
    end

    // Edge detection for ton_done rising edge
    always @(posedge clk or posedge rst) begin
        if (rst)
            ton_done_d <= 0;
        else
            ton_done_d <= ton_done;
    end
    wire ton_done_rise = ton_done & ~ton_done_d;

    //----------------------------
    // CTU Counter Up (Preset = 5)
    //----------------------------
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            ctu_count <= 0;
            ctu_done  <= 0;
        end else if (ton_done_rise) begin
            if (ctu_count < 5) begin
                ctu_count <= ctu_count + 1;
                ctu_done <= 1'b0;
            end else begin
                ctu_done <= 1'b1;
            end
        end
    end

    //----------------------------
    // Control Logic Example
    //----------------------------
    always @(*) begin
        if (AUTO)
            Control = ton_done;
        else if (MAN)
            Control = start;
        else
            Control = 1'b0;
    end

    //----------------------------
    // Output Q Example
    //----------------------------
    always @(*) begin
        Q = ctu_done;
    end

endmodule
