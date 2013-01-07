#!/usr/bin/env python
"""Calculate expected value of various variable-length non-negative integer
encodings."""

from __future__ import division
from benchtools.stats import Sample
import math
from random import Random

def ScarabLength(x):
    # http://casbah.org/Scarab/binary-serialization.html
    return max(1, math.ceil(math.log(x+1, 2)/7))

def BERLength(x):
    # http://en.wikipedia.org/wiki/Basic_Encoding_Rules
    return 1 + max(1, math.ceil(math.log(x+1, 2)/8))

def CakeCountLength(x):
    # http://www.cakem.net/basictypes.html#count_detail
    if x < 222:
        return 1
    elif x < 8415:
        return 2
    else:
        return 1 + math.ceil(math.log(x+1, 2)/8)

r = Random()
n = 50000
print 'Expected lengths (calculated with sample size %d):' % (n,)
print '%-32sScarab\tBER\tCake' % ('Distribution')
for distroname, distrofunc in \
    (
     ("paretovariate(alpha=1)",         lambda _: r.paretovariate(alpha=1)),
     ("paretovariate(alpha=1/2)",       lambda _: r.paretovariate(alpha=1/2)),
     ("paretovariate(alpha=1/5)",       lambda _: r.paretovariate(alpha=1/5)),
     ("paretovariate(alpha=1/10)",      lambda _: r.paretovariate(alpha=1/10)),
     ("expovariate(lambd=1)",           lambda _: r.expovariate(lambd=1)),
     ("expovariate(lambd=1/10)",        lambda _: r.expovariate(lambd=1/10)),
     ("expovariate(lambd=1/100)",       lambda _: r.expovariate(lambd=1/100)),
     ("expovariate(lambd=1/1000)",      lambda _: r.expovariate(lambd=1/1000)),
     ("expovariate(lambd=1/10000)",     lambda _: r.expovariate(lambd=1/10000)),
     ("lognormvariate(mu=0,sigma=1)",   lambda _: r.lognormvariate(mu=0,sigma=1)),
     ("lognormvariate(mu=0,sigma=10)",  lambda _: r.lognormvariate(mu=0,sigma=10)),
     ("lognormvariate(mu=0,sigma=100)", lambda _: r.lognormvariate(mu=0,sigma=100)),
     ("lognormvariate(mu=1,sigma=1)",   lambda _: r.lognormvariate(mu=1,sigma=1)),
     ("lognormvariate(mu=1,sigma=10)",  lambda _: r.lognormvariate(mu=1,sigma=10)),
     ("lognormvariate(mu=1,sigma=100)", lambda _: r.lognormvariate(mu=1,sigma=100)),
     ("lognormvariate(mu=2,sigma=1)",   lambda _: r.lognormvariate(mu=2,sigma=1)),
     ("lognormvariate(mu=2,sigma=10)",  lambda _: r.lognormvariate(mu=2,sigma=10)),
     ("lognormvariate(mu=2,sigma=100)", lambda _: r.lognormvariate(mu=2,sigma=100)),
    ):
    costs = [Sample(), Sample(), Sample()]
    for i in range(n):
        v = int(distrofunc(None))
        costs[0].append(ScarabLength(v))
        costs[1].append(BERLength(v))
        costs[2].append(CakeCountLength(v))
    print '%-32s%.2f\t%.2f\t%.2f' \
          % (distroname, costs[0].mean, costs[1].mean, costs[2].mean)
