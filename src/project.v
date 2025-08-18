`timescale 1ns / 1ps
module tt_um_plc_prg (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (1=output)
    input  wire       ena,      // always 1 when your design is enabled
    input  wire       clk,      // clock
    input  wire       rst_n     // async active-low reset
);
    // Map UI bits
    wire reset = ~rst_n;
    wire start = ui_in[0];
    wire AUTO  = ui_in[1];
    wire MAN   = ui_in[2];
    
    // Timer preset
`ifdef COCOTB_SIM
    parameter TON_PRESET = 20;              // Short delay for cocotb sim
`else
    parameter TON_PRESET = 150_000_000;     // 3s delay at 50MHz (real HW)
`endif
    
    reg [$clog2(TON_PRESET):0] counter;
    reg Control;
    
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            counter <= 0;
            Control <= 0;
        end else if (ena) begin
            // Manual mode has priority over auto mode
            if (MAN) begin
                // Manual mode: Control follows start immediately
                Control <= start;
                counter <= 0;  // Reset counter in manual mode
            end else if (AUTO) begin
                // Auto mode: timer-based control
                if (start) begin
                    if (counter >= TON_PRESET) begin
                        // Timer expired, activate control
                        Control <= 1;
                    end else begin
                        // Still counting
                        counter <= counter + 1;
                        Control <= 0;
                    end
                end else begin
                    // Start not active in auto mode, reset
                    counter <= 0;
                    Control <= 0;
                end
            end else begin
                // No mode selected, reset everything
                counter <= 0;
                Control <= 0;
            end
        end
    end
    
    // Map outputs
    assign uo_out[0] = Control;
    assign uo_out[7:1] = 7'b0;
    
    // Not using bidirectional IOs
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;
    
endmodule
