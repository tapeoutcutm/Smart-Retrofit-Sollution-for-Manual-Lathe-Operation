`timescale 1ns/1ps
`define COCOTB_SIM  // Enable short timer for simulation

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
    
    // Input assignments matching your design
    wire start = ui_in[0];  // Correct mapping
    wire AUTO  = ui_in[1];  // Correct mapping  
    wire MAN   = ui_in[2];  // Correct mapping
    
    // Output assignments
    wire Control = uo_out[0];
    
    // Test stimulus
    initial begin
        // Initialize
        clk    = 0;
        rst_n  = 0;  // Start with reset active (active-low)
        ena    = 1;
        ui_in  = 8'b0;
        uio_in = 8'b0;
        
        // Release reset
        #50;
        rst_n = 1;
        #20;
        
        $display("=== Testing AUTO Mode ===");
        // Set AUTO mode
        ui_in[1] = 1; // AUTO = 1
        ui_in[2] = 0; // MAN = 0
        #20;
        
        // Apply START signal
        ui_in[0] = 1; // start = 1
        #20;
        
        // Wait for timer to expire (TON_PRESET = 20 in simulation)
        #500; // Should be enough for 20 clock cycles + margin
        
        // Remove start signal
        ui_in[0] = 0;
        #100;
        
        $display("=== Testing MANUAL Mode ===");
        // Switch to MANUAL mode
        ui_in[1] = 0; // AUTO = 0
        ui_in[2] = 1; // MAN = 1
        #20;
        
        // Apply START signal - should immediately activate Control
        ui_in[0] = 1; // start = 1
        #50;
        
        // Remove start signal - should immediately deactivate Control
        ui_in[0] = 0;
        #50;
        
        $display("=== Testing Mode Priority ===");
        // Test that MAN has priority over AUTO
        ui_in[1] = 1; // AUTO = 1
        ui_in[2] = 1; // MAN = 1 (should have priority)
        #20;
        
        ui_in[0] = 1; // start = 1
        #50;
        ui_in[0] = 0;
        #50;
        
        $display("=== Testing No Mode Selected ===");
        // Test with no mode selected
        ui_in[1] = 0; // AUTO = 0
        ui_in[2] = 0; // MAN = 0
        #20;
        
        ui_in[0] = 1; // start = 1 (should have no effect)
        #100;
        ui_in[0] = 0;
        #50;
        
        $display("=== Test Complete ===");
        #1000000 $finish;
    end
    
    // Monitor key signals
    initial begin
        $dumpfile("tb_tt_um_plc_prg.vcd");
        $dumpvars(0, tb_tt_um_plc_prg);
        
        $display("Time\tRst_n\tStart\tAUTO\tMAN\tControl\tCounter");
        $monitor("%0t\t%b\t%b\t%b\t%b\t%b\t",$time, rst_n, start, AUTO, MAN, Control);
    end
    
    // Check expected behavior
    initial begin
        #1; // Wait for initial values
        
        // Wait for reset release and mode setup
        wait(rst_n == 1);
        wait(AUTO == 1 && MAN == 0);
        
        // Test AUTO mode behavior
        wait(start == 1);
        $display("AUTO Mode: Start signal applied at time %0t", $time);
        
        wait(Control == 1);
        $display("AUTO Mode: Control activated at time %0t",$time);
        
        // Wait for manual mode test
        wait(MAN == 1 && AUTO == 0);
        wait(start == 1);
        #1; // Small delay to see the immediate response
        if (Control == 1) begin
            $display("MANUAL Mode: Control immediately active - PASS");
        end else begin
            $display("MANUAL Mode: Control not immediately active - FAIL");
        end
        #100000;
    end
    
endmodule
