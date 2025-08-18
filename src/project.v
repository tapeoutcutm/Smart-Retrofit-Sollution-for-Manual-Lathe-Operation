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
    wire reset = ~rst_n;   // active high reset internally
    wire start = ui_in[0];
    wire AUTO  = ui_in[1];
    wire MAN   = ui_in[2];
    reg Control;
    
    // Timer preset
`ifdef COCOTB_SIM
    parameter TON_PRESET = 20;              // Short delay for cocotb sim
`else
    parameter TON_PRESET = 150_000_000;     // 3s delay at 50MHz (real HW)
`endif
    
    reg [$clog2(TON_PRESET):0] counter;
    reg timer_done;
    reg start_prev;
    wire start_edge = start && !start_prev;
    
    always @(posedge clk or posedge reset) begin
        if (reset) begin
            counter     <= 0;
            timer_done  <= 0;
            Control     <= 0;
            start_prev  <= 0;
        end else if (ena) begin
            start_prev <= start;
            
            if (MAN && start) begin
                // Manual mode: immediate control when start is high
                Control <= 1;
                timer_done <= 1;
                counter <= 0;
            end else if (AUTO) begin
                if (start_edge) begin
                    // Auto mode: start timer on rising edge of start
                    counter <= 0;
                    timer_done <= 0;
                    Control <= 0;
                end else if (start && !timer_done) begin
                    // Continue counting while start is high and timer not done
                    if (counter < TON_PRESET) begin
                        counter <= counter + 1;
                        Control <= 0;
                    end else begin
                        timer_done <= 1;
                        Control <= 1;
                    end
                end else if (!start) begin
                    // Reset when start goes low
                    counter <= 0;
                    timer_done <= 0;
                    Control <= 0;
                end
                // If start is high and timer_done is true, maintain Control = 1
            end else begin
                // Neither MAN nor AUTO active: reset everything
                counter <= 0;
                timer_done <= 0;
                Control <= 0;
            end
        end
    end
    
    // Map output
    assign uo_out[0] = Control;  // only using bit[0]
    assign uo_out[7:1] = 7'b0;
    
    // Not using bidirectional IOs
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;
    
endmodule
