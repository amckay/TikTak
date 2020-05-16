import numpy as np
import multiprocessing
import os

class TTOptimizer:
  """"Optimizer for the TikTak algorithm."""
  
  def __init__(self,computation_options, global_search_options, local_search_options):
    self.computation_options   = computation_options
    self.global_search_options = global_search_options
    self.local_search_options = local_search_options
    self.SRF = os.path.join(computation_options["working_dir"],"searchResults.dat")
    self.XSF = os.path.join(computation_options["working_dir"],"xstarts.dat")
    


    def ProcessLocalResult(self,result,best):

        with open(self.SRF,"a") as srf:
            srf.write(str(result[1]) + ' ' + str(result[0]) + '\n')

        if result[1] < best[1] :
            print( 'best so far %f' % result[1])
            return result
        else:
            return best


 


    def LocalSearch(self,taskq,resultq,xstarts,best = None, StartAt = 0,**kwargs):
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

        num_workers = computation_options["num_workers"]
        num_jobs = len(xstarts)

        def SubmitTask(task):
          with open(self.XSF,"a") as xsf:
             xsf.write(str(task) + '\n')
         tasksq.put(task)


        # Enqueue jobs
        if best is None:
            best = (0.0, 1e10)
            
        # To start, give one job to each consumer
        for i in range(StartAt,StartAt + num_workers):
            SubmitTask(xstarts[i])

        # then wait for results and when a result comes in analyze it and send out a new job
        i =  StartAt + num_workers
        while i < num_jobs:

            best = self.ProcessResult(resultsq.get(),best)

            ishrink = self.local_search_options["shrink_after"]
            if i < ishrink:
                newtask = xstarts[i]
            else:
                # shrink towards best so far
                theta = 0.02 + (0.98-0.02)*float(i-ishrink)/float(num_jobs-ishrink)  # when i = ishrink, place 2% weight on best, when i = Imax place 98% weight on max
                newtask = theta*best[0] + (1-theta)*xstarts[i]

            SubmitTask(newtask,tasksq)

            i = i + 1


        # All jobs have been submitted.  Start closing down
        # Add a poison pill for each consumer
        for i in range(self.num_workers):
            tasksq.put(None)

        # Wait for all of the tasks to finish
        tasksq.join()

        # get any remainging results
        while not resultsq.empty():
            best = self.ProcessResult(resultsq.get(),best)

        # print the last value of best
        print( 'best value at the end %f' % best[1])
        return best
        
  def GlobalSearch():
    pass
  

    
class Consumer(multiprocessing.Process):

    def __init__(self, optimizer, task_queue, result_queue):
        multiprocessing.Process.__init__(self)
        self.optimizer = optimizer
        self.task_queue = task_queue
        self.result_queue = result_queue

    def run(self,local_or_global):
        proc_name = self.name
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                print('%s: Exiting' % proc_name)
                self.task_queue.task_done()
                break

            if local_or_global == 'local':
              answer = self.optimizer.minimize(self.optimizer.f, next_task,**self.kwargs)
            elif local_or_global == 'local':
              answer = self.optimizer.f(next_task)
            self.task_queue.task_done()
            self.result_queue.put(answer)
        return
        


#-----------------


        # Establish communication queues
        tasksq = multiprocessing.JoinableQueue()
        resultsq = multiprocessing.Queue()
        
        
        
        # Start consumers
        print( 'Creating %d consumers' % self.num_workers)
        consumers = [ Consumer(tasksq, resultsq,**kwargs)
                      for i in range(self.num_workers) ]
        for w in consumers:
            w.start()

    
