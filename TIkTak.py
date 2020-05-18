import numpy as np
import multiprocessing
import os
from scipy.optimize import minimize as scipy_minimize
import nlopt
import sobol
import time

class TTOptimizer:
    """"Optimizer for the TikTak algorithm."""

    def __init__(self,computation_options, global_search_options, local_search_options):
        self.computation_options   = computation_options
        self.global_search_options = global_search_options
        self.local_search_options = local_search_options
        self.SRF = os.path.join(computation_options["working_dir"],"searchResults.dat")
        self.XSF = os.path.join(computation_options["working_dir"],"xstarts.dat")

        if self.local_search_options['algorithm'].lower() == 'bobyqa':
            self.minimizer = BOBYQA
        elif self.local_search_options['algorithm'].lower() == 'neldermead':
            self.minimizer = NelderMead
        else:
            raise RunTimeError("local search algorithm not recognized")


    def minimize(self,f,lower_bounds,upper_bounds):
        self.f = f
        self.lower_bounds = lower_bounds
        self.upper_bounds = upper_bounds
        self.initial_step = 0.1*(upper_bounds-lower_bounds)
        self.nparam = len(lower_bounds)

        self.mppool = multiprocessing.Pool(processes=self.computation_options["num_workers"])
        self.xstarts = list(self.GlobalSearch())
        best = self.LocalSearch()
        # print the last value of best
        print(f'best value {best[1]}')
        print(f'best point {best[0]}')
        return best

    def GlobalSearch(self):

        nsobol = self.global_search_options["num_points"]

        SOBOLSKIP = 2

        # ---- generate Sobol points ----
        xstarts = sobol.i4_sobol_generate ( self.nparam, nsobol, SOBOLSKIP ).T
        # scale accoring to the bounds
        xstarts = self.lower_bounds[np.newaxis,:] + (self.upper_bounds-self.lower_bounds)[np.newaxis,:]*xstarts


        # --- evaluate f on many points ----
        y = np.array(self.mppool.map(self.f,xstarts))


        # sort the results
        I = np.argsort(y)
        xstarts = xstarts[I]
        y = y[I]

        # take the best Imax
        xstarts = xstarts[:self.local_search_options["num_restarts"]]

        return xstarts


    def LocalSearch(self):
        """Function to manage the local searches.  Each local start is given to a consumer process that
        does the search.

        Parameters
        ~~~~~~~~~~~
        taskq       queue to submit tasks
        resultq     queue to receive results
        xstarts     the points at which we start in order
        best        best found so far (used if restarting after interuption )
        StartAt     how far into xstarts do we start  (used if restarting after interuption )
          """


        manager = multiprocessing.Manager()
        self.resultsq = manager.Queue()

        num_workers = self.computation_options["num_workers"]
        self.num_jobs = len(self.xstarts)




        self.best_so_far = (0.0, 1e10)


        self.result_trackers = []
        self.submit_counter = 0
        for i in range(num_workers):
            self.SubmitLocalResult()

        # the submissions happen recursively through the callback
        # here we wait until we have submitted all jobs
        while self.submit_counter < self.num_jobs:
            time.sleep(1)

        # here we wait until all jobs are done.
        [r.wait() for r in self.result_trackers]


        return self.best_so_far


    def SubmitLocalResult(self):
        i = self.submit_counter
        ishrink = self.local_search_options["shrink_after"]
        newtask = self.xstarts.pop()
        if i >= ishrink: # shrink towards best so far
            theta = 0.02 + (0.98-0.02)*float(i-ishrink)/float(self.num_jobs-ishrink)  # when i = ishrink, place 2% weight on best, when i = Imax place 98% weight on max
            newtask = theta*self.best_so_far[0] + (1-theta)*newtask

        self.result_trackers.append(self.mppool.apply_async(localworker,
                (self.minimizer,
                (self.f,newtask,self.initial_step,self.lower_bounds,self.upper_bounds,self.local_search_options["xtol_rel"],self.local_search_options["ftol_rel"]),
                self.resultsq),
                callback = self.ProcessLocalResult,
                error_callback = self.ErrorCallback ) )

        self.submit_counter += 1


    def ProcessLocalResult(self,result):

        with open(self.SRF,"a") as srf:
            srf.write(str(result[1]) + ' ' + str(result[0]) + '\n')

        if result[1] < self.best_so_far[1] :
            print( 'best so far %f' % result[1])
            self.best_so_far = result

        if len(self.xstarts) > 0:
            self.SubmitLocalResult()

    def ErrorCallback(self,e):
        print('Error found in local search:')
        print(e)
        if len(self.xstarts) > 0:
            self.SubmitLocalResult()





def localworker(f,x,resultsq):
    answer = f(*x)
    resultsq.put( answer )
    return answer


def BOBYQA(f,x,initial_step,lower_bounds,upper_bounds,xtol_rel,ftol_rel):
    opt = nlopt.opt(nlopt.LN_BOBYQA, len(x))
    fwrapped = lambda x,grad: f(x)
    opt.set_min_objective(fwrapped)
    opt.set_xtol_rel(xtol_rel)
    opt.set_ftol_rel(ftol_rel)

    if not initial_step is None:
        opt.set_initial_step(initial_step)

    if not lower_bounds is None:
        opt.set_lower_bounds(lower_bounds)

    if not upper_bounds is None:
        opt.set_upper_bounds(upper_bounds)

    xopt = opt.optimize(x)
    minf = opt.last_optimum_value()
    return (xopt, minf)



def NelderMead(f,x,initial_step,lower_bounds,upper_bounds,xtol_rel,ftol_rel):
    """Note that NM doesn't impose bounds on optimization.
    The arguments initial_step, lower_bounds, and upper_bounds are not used.
    """
    res =  scipy_minimize(f, x, method='nelder-mead',
            options={'frtol': ftol_rel, 'xrtol': xtol_rel, 'disp': False})
    return (res.x, res.fun)
