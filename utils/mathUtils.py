from typing import List
from math import *


def stdev(data: List[float]) -> float:
    m = average(data)
    dividend = 0.0
    for i in data:
        dividend += pow(i - m, 2)
    return sqrt(dividend)


def average(data: List[float]) -> float:
    ans = 0.0
    for i in data:
        ans += i
    return ans / len(data)
