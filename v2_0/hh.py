
def compute_ddr_access_clk(msg_size, ddr_type="DDR3"):
    """The unit of msg size is bit, default DDR type is DDR3 and clock is 1ns"""
    clk = 1e9
    DDR_access_rate = {'DDR':2e9, 'DDR2':4e9, 'DDR3':8e9, 'DDR4':16e9} # unit Byte/s\
    assert(ddr_type in DDR_access_rate)
    access_time = msg_size / (8*DDR_access_rate[ddr_type])
    
    return int(access_time*clk)


print(compute_ddr_access_clk(64*8, 'DDR'))