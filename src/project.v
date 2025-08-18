`timescale 1ns/1ps
`default_nettype none

module tt_um_plc_prg (
    input  wire [7:0] ui_in,    // Inputs:
                                //   ui_in[0] = start
                                //   ui_in[1] = AUTO
                                //   ui_in[2] = MAN
    output wire [7:0] uo_out,   // Outputs:
                                //   uo_out[0] = Control
    input  wire [7:0] uio_in,   // IOs: Input path (used here to set SIM preset)
    output wire [7:0] uio_out,  // IOs: Output path (unused)
    output wire [7:0] uio_oe,   // IOs: Enable path (unused)
    input  wire       ena,      // 1 when design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // async active-low reset
);

    // -----------------------------
    // Bit mapping
    // -----------------------------
    wire start = ui_in[0];
    wire AUTO  = ui_in[1];
    wire MAN   = ui_in[2];

    // -----------------------------
    // Output(s)
    // -----------------------------
    reg Control;

    // -----------------------------
    // Preset handling
    //   - If uio_in != 0 at reset -> use it as preset (SIM)
    //   - Else use HW preset (3s @ 50MHz)
    // -----------------------------
    localparam integer HW_PRESET     = 150_000_000;
    localparam integer PRESET_WIDTH  = $clog2(HW_PRESET+1);

    reg [PRESET_WIDTH-1:0] preset;   // active preset (latched at reset)
    reg [PRESET_WIDTH-1:0] counter;  // timer counter
    reg                    timer_done;

    // Async reset, synchronous logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Latch preset from uio_in (if nonzero), else hardware preset
            preset     <= (uio_in != 8'd0) ? uio_in[7:0] : HW_PRESET[PRESET_WIDTH-1:0];
            counter    <= {PRESET_WIDTH{1'b0}};
            timer_done <= 1'b0;
            Control    <= 1'b0;
        end else if (ena) begin
            // Manual mode: immediate control
            if (MAN && start) begin
                Control    <= 1'b1;
                timer_done <= 1'b1;     // mark as done to avoid counting artifacts
                counter    <= {PRESET_WIDTH{1'b0}};
            end
            // Auto mode: TON delay
            else if (AUTO && start) begin
                if (!timer_done) begin
                    if (counter + 1 >= preset) begin
                        timer_done <= 1'b1;
                        Control    <= 1'b1;
                    end else begin
                        counter <= counter + 1'b1;
                        Control <= 1'b0;
                    end
                end
            end
            // Otherwise: idle / clear
            else begin
                counter    <= {PRESET_WIDTH{1'b0}};
                timer_done <= 1'b0;
                Control    <= 1'b0;
            end
        end
    end

    // -----------------------------
    // Unused IOs
    // -----------------------------
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // -----------------------------
    // Output mapping
    // -----------------------------
    assign uo_out[0]   = Control;
    assign uo_out[7:1] = 7'b0;

endmodule

`default_nettype wire
