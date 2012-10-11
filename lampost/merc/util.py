from random import randint

def scale32(value, range_st, range_end):
    return range_st + value * (range_end - range_st) / 32

nudge_values = [-1, 0, 0, 1]

def nudge(value):
    return max(1, value + nudge_values[randint(0, 3)])

def range_limit(min_value, calc_value, max_value):
    if calc_value < min_value:
        return min_value
    return min(calc_value, max_value)
