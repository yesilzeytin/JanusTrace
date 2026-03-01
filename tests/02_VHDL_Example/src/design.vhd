library IEEE;
use IEEE.STD_LOGIC_1164.ALL;

entity controller is
    Port ( clk : in STD_LOGIC;
           rst : in STD_LOGIC;
           data_out : out STD_LOGIC_VECTOR (7 downto 0));
end controller;

architecture Behavioral of controller is
begin
    -- [REQ-VHDL-01]
    -- Process to handle reset and clock
    process(clk, rst)
    begin
        if rst = '1' then
            -- [REQ-VHDL-02] Asynchronous reset
            data_out <= (others => '0');
        elsif rising_edge(clk) then
            data_out <= "11111111";
        end if;
    end process;
end Behavioral;
