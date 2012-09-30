from random import randint

def scale32(value, range_st, range_end):
    return range_st + value * (range_end - range_st) / 32

nudge_vals = [-1, 0, 0, 1]

def nudge(value):
    return max(1, value + nudge_vals[randint(0, 3)])
