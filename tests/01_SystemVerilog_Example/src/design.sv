module traffic_light (
    input logic clk,
    input logic rst_n,
    output logic [2:0] light
);

    // [REQ-001]
    // Traffic light controller implementation
    typedef enum logic [1:0] {RED, YELLOW, GREEN} state_t;
    state_t current_state, next_state;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            current_state <= RED; // [REQ-002] Default state is RED
        else
            current_state <= next_state;
    end

    // [REQ-003] State transition logic
    always_comb begin
        case (current_state)
            RED: next_state = GREEN;
            GREEN: next_state = YELLOW;
            YELLOW: next_state = RED;
        endcase
    end

endmodule
