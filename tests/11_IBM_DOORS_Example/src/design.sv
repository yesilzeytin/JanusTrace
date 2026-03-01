module doors_wrapper;
  // [PROJ-PLD-1] Reset logic
  
  // [PROJ-PLD-135] State machine
  // Note: PROJ-PLD-5 is Information so we don't trace it here, 
  // but if the tool imports it, it will show as MISSING unless filtered.
  // Current tool implementation scans ALL rows. 
  // Future feature: Filter by column 'Type' == 'Requirement'.
endmodule
