'''
Created on Aug 22, 2012

@author: esaltmarsh
'''
#This code simulates a linear piecewise random variable given the function

import random
import math

def piecewise( function ):
    
    min_y = range(function['segments'])
    max_y = range(function['segments'])
    A = range(function['segments'])
    B = range(function['segments'])
    C = range(function['segments'])
    const_1 = range(function['segments'])
    const_2 = range(function['segments'])
    const_3 = range(function['segments'])
    sign = range(function['segments'])
    
    for i in range(function['segments']):
        min_string = "min " + `i + 1`
        max_string = "max " + `i + 1`
        slope_string = "slope " + `i + 1`
        int_string = "int " + `i + 1`
        
        #Transform x range to y range - lower bound
        if i == 0:
            min_y[i] = 0
        else:
            min_y[i] = max_y[i - 1]        
        
        #Integrate over the range
        A[i] = 0.5 * function[slope_string]
        B[i] = function[int_string]
        C[i] = min_y[i] - (A[i] * function[min_string] * function[min_string]) - B[i] * function[min_string]
        
        #Transform x range to y range - upper bound
        max_y[i] = A[i]*function[max_string]*function[max_string] + B[i]*function[max_string] + C[i]
        
        #Transform the range to invert the function
        if function[slope_string] < 0:
            const_1[i] = -B[i] / (2 * A[i])
            const_2[i] = ((B[i] * B[i]) - (4 * A[i] * C[i])) / (4 * A[i] * A[i])
            const_3[i] = 1 / A[i]
            sign[i] = -1
        elif function[slope_string] > 0:
            const_1[i] = -B[i] / (2 * A[i])
            const_2[i] = ((B[i] * B[i]) - (4 * A[i] * C[i])) / (4 * A[i] * A[i])
            const_3[i] = 1 / A[i]
            sign[i] = 1
        else:
            const_1[i] = 1 / B[i]
            const_2[i] = C[i] / B[i]
            const_3[i] = 0
            sign[i] = -1
        
    #return simulated
    num = random.random()
    for i in range(function['segments']):
        if num >= min_y[i] and num < max_y[i]:
            if const_3[i] == 0:
                special_num = const_1[i]*num + sign[i]*const_2[i]
            else:
                special_num = const_1[i] + sign[i]*math.sqrt(const_2[i]+const_3[i]*num)
    return special_num