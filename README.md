# TikTak
Python implementation of Guvenen's TikTak optimization routine described in [Benchmarking Global Optimizers](https://fguvenendotcom.files.wordpress.com/2019/09/agk2019-september-nber-submit.pdf) by Arnoud, Guvenen, and Kleineberg.  They write "TikTak belongs to the class of multistart algorithms, which conducts local searches from carefully selected points in the parameter space. The algorithm starts with a broad exploration of the (parameter) space and uses the information it accumulates to increasingly focus the search on the most promising region."  This implementation works in parallel making use of the Python multiprocessing module.  



Requirements: python 3.7+, numpy, and [nlopt](https://pypi.org/project/nlopt/).

## Quick start

The user supplies an objective function to minimize and lower and upper bounds on each dimension of the parameter space.

```python
import numpy as np
import TikTak

n = 10  # dimension of parameter space
# Rastrigin test function, global min at (0,0,0,...0) with function value of 1
def rastrigin(x):
   return np.sum(x*x - 10*np.cos(2*np.pi*x)) + 10*np.size(x)  + 1.0

lower_bounds = np.repeat(-5.12,10)  # lower bounds on each dimension
upper_bounds = np.repeat( 5.12,10)  # upper bounds on each dimension

computation_options = { "num_workers" : 4,        # use four processes in parallel
                        "working_dir" : "working" # where to save results in progress (in case interrupted)
                       }

global_search_options = { "num_points" : 10000}  # number of points in global pre-test

local_search_options = {  "algorithm"    : "BOBYQA", # local search algorithm
                                                     # can be either BOBYQA from NLOPT or NelderMead from scipy
                          "num_restarts" : 200,      # how many local searches to do
                          "shrink_after" : 30,       # after the first [shrink_after] restarts we begin searching
                                                     # near the best point we have found so far
                          "xtol_rel"     : 1e-8,     # relative tolerance on x
                          "ftol_rel"     : 1e-8     # relative tolerance on f
                       }

opt = TikTak.TTOptimizer(computation_options, global_search_options, local_search_options)
x,fx = opt.minimize(rastrigin,lower_bounds,upper_bounds)
print(f'The minimizer is {x}')
print(f'The objective value at the min is {fx}')
```
