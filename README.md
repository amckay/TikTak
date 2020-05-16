# TikTak
Python implementation of Guvenen's TikTak optimization routine.  This is a multi-restart global minimization routine.

Requirements: numpy and nlopt.

## Quick start

The user supplies an objective function to minimize and lower and upper bounds on each dimension of the parameter space.

```python
import TikTak
n = 5  # dimension of parameter sapce
f = lambda x: (x**2).sum()  # objective function
lower_bounds = -np.ones(n)   # lower bound on each dimension
upper_bounds = np.ones(n)    # upper bound on each dimension

computation_options = { "num_workers" : 4,        # use four processes in parallel
                        "working_dir" : "working" # where to save results in progress (in case interrupted)
                       }

global_search_options = { "num_points" : 10000}  # number of points in global pre-test

local_search_options = {  "algorithm"    : "BOBYQA", # local search algorithm 
                                                     # can be either BOBYQA from NLOPT or Nelder-Mead from scipy
                          "num_restarts" : 200,      # how many local searches to do
                          "shrink_after" : 30        # after the first [shrink_after] restarts we begin searching 
                                                     # near the best point we have found so far
                       }
                                                 
opt = TikTak.TTOptimizer(computation_options, global_search_options, local_search_options)
x,fx = opt.minimize(f,lower_bounds,upperbounds)
```
