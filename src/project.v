`timescale 1ns / 1ps

// Top-level TinyTapeout wrapper
module tt_um_plc_prg (
    input  [7:0] ui_in,     // Inputs from chip pads
                           // ui_in[0] = clk
                           // ui_in[1] = rst
                           // ui_in[2] = start
                           // ui_in[3] = stop
                           // ui_in[4] = sel0
                           // ui_in[5] = AUTO
                           // ui_in[6] = MAN
                           // ui_in[7] = unused
    output [7:0] uo_out,    // Outputs to chip pads
                           // uo_out[0] = Control
                           // uo_out[1] = Q
    input  [7:0] uio_in,    // Unused
    output [7:0] uio_out,   // Unused
    output [7:0] uio_oe,    // Unused
    input clk,              // Global clk (unused — using ui_in[0])
    input rst_n,            // Global rst (unused — using ui_in[1])
    input ena               // Enable (unused)
);

    // Tie off bidirectional IOs
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Input mapping
    wire clk_in   = ui_in[0];
    wire rst      = ui_in[1];
    wire start    = ui_in[2];
    wire stop     = ui_in[3];
    wire sel0     = ui_in[4];
    wire AUTO     = ui_in[5];
    wire MAN      = ui_in[6];

    // Outputs
    wire Control;
    wire Q;

    // Core PLC logic instantiation
    PLC_PRG core (
        .clk(clk_in),
        .rst(rst),
        .start(start),
        .stop(stop),
        .sel0(sel0),
        .AUTO(AUTO),
        .MAN(MAN),
        .Control(Control),
        .Q(Q)
    );

    // Output mapping
    assign uo_out[0] = Control;
    assign uo_out[1] = Q;
    assign uo_out[7:2] = 6'b0; // unused

endmodule


// Original PLC logic (unchanged)
module PLC_PRG (
    input  wire clk,        
    input  wire rst,        
    input  wire start,
    input  wire stop,
    input  wire sel0,
    input  wire AUTO,
    input  wire MAN,
    output reg  Control,
    output reg  Q
);
    // Internal signals
    reg latch_q;                 
    reg [27:0] ton_counter;      
    reg ton_done;                
    reg [3:0] ctu_count;         
    reg ctu_done;                

    reg ton_done_d;

    // SR Latch
    always @(posedge clk or posedge rst) begin
        if (rst)
            latch_q <= 1'b0;
        else if (start)
            latch_q <= 1'b1;
        else if (stop)
            latch_q <= 1'b0;
    end

    // TON delay (3s @ 50MHz)
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            ton_counter <= 0;
            ton_done    <= 0;
        end else if (latch_q) begin
            if (ton_counter < 150_000_000) begin
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

    // Edge detection
    always @(posedge clk or posedge rst) begin
        if (rst)
            ton_done_d <= 0;
        else
            ton_done_d <= ton_done;
    end
    wire ton_done_rise = ton_done & ~ton_done_d;

    // CTU counter (Preset = 5)
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

    // Control output
    always @(*) begin
        if (AUTO)
            Control = ton_done;
        else if (MAN)
            Control = start;
        else
            Control = 1'b0;
    end

    // Q output
    always @(*) begin
        Q = ctu_done;
    end

endmodule
