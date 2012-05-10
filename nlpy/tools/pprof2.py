"""
A module to create and plot performance profiles.
"""


import re
from string import atof
import numpy as np

__docformat__ = 'restructuredtext'

default_options = {'datacol': 2, 'logscale': True, 'sep': '\s+', 'bw': False,
                   'title': 'Deathmatch'}

class PerformanceProfile(object):

    def __init__(self, solvers, **opts):
        """
        :parameters:
            :solvers: a list of file names containing solver statistics
                      Failures must be indicated with negative statistics
            :options: a dictionary of options. Currently recognized options are
                      listed below.

        :options:
            :datacol:  the (1-based) column index containing the relevant metric
                       in the solver files
            :logscale: True if log-scale ratios are requested
            :sep:      the column separator as a regexp (default: '\s+')
            :bw:       True if a black and white plot is requested
            :title:    string containing the plot title.

        :returns:
            A PerformanceProfile object on which `plot()` may be called.
        """

        self.solvers = solvers
        self.options = default_options.copy()
        for opt in opts:
            self.options[opt] = opts[opt]
        self.metrics = []       # A list of lists.
        self.ratios  = None

        map(self.add_solver, solvers)
        self.compute_ratios()

    def add_solver(self, fname):
        "Collect metrics for each solver."

        comment = re.compile(r'^[\s]*[%#]')
        column  = re.compile(self.options['sep'])

        # Grab the column from the file.
        metrics = []
        with open(fname, 'r') as fp:
            for line in fp:
                if not comment.match(line):
                    line = line.strip()
                    cols = column.split(line)
                    data = atof(cols[self.options['datacol'] - 1])
                    metrics.append(data)

        self.metrics.append(metrics)
        if len(metrics) != len(self.metrics[0]):
            raise ValueError('All solvers must have same number of problems.')

    def compute_ratios(self):
        "Compute performance ratios."

        self.ratios = np.array(self.metrics, dtype=np.float)
        nsolvs, nprobs = self.ratios.shape

        # Scale each problem metric by the best performance across solvers.
        for prob in range(nprobs):
            metrics = self.ratios[:,prob]
            try:
                # There are no > 0 vals if all solvers fail on this problem.
                best = metrics[metrics > 0].min()
                self.ratios[:,prob] /= best
            except:
                pass

        # Turn failures into large metrics.
        self.max_ratio = self.ratios.max()
        self.ratios[self.ratios < 0] = 2 * self.max_ratio

        # Sort the performance of each solver (in place).
        for solv in range(nsolvs):
            self.ratios[solv,:].sort()

    def plot(self):
        "Need we say more?"

        import matplotlib.pyplot as plt
        nsolvs, nprobs = self.ratios.shape
        y = np.arange(1, nprobs+1, dtype=np.float)/nprobs
        grays = ['0.0', '0.5', '0.8', '0.2', '0.6', '0.9', '0.4', '0.95']
        ngrays = len(grays)

        xmax = 1.1 * self.max_ratio
        if self.options['logscale']:
            xmax = max(xmax, 2)

        pltcmd = plt.semilogx if self.options['logscale'] else plt.plot
        for solv in range(nsolvs):
            pltargs = ()
            if self.options['bw']:
                pltargs = (grays[solv % ngrays],)
            # If all ratios are equal, horizontal line won't be draw.
            # This happens when a solver always dominates the others.
            # Adjust by moving the last abscissa to xmax.
            if reduce(lambda x,y: x==y, self.ratios[solv,:]):
                self.ratios[solv,-1] = xmax
            pltcmd(self.ratios[solv,:], y,
                   linewidth=2.5,
                   drawstyle='steps-pre',
                   antialiased=True,
                   *pltargs)

        plt.legend(self.solvers, 'lower right')
        ax = plt.gca()
        if self.options['logscale']:
            ax.set_xscale('log', basex=2)
            xmax = max(xmax, 2)
        ax.set_xlim([1, xmax])
        ax.set_ylim([0, 1.1])
        ax.set_xlabel('Within this factor of the best')
        ax.set_ylabel('Proportion of problems')
        if self.options['title'] is not None:
            ax.set_title(self.options['title'])
        plt.show()


if __name__ == '__main__':

    import sys
    # Only specify non-default options.
    options = {'bw': True}
    pprof = PerformanceProfile(sys.argv[1:], **options)
    pprof.plot()
