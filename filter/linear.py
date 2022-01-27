# These functions are helpful for clustering numbers.
# When run as
#    python3 linear.py
# it prints a 4-clustering of 12 values.
# Ideally they have labels -17, -4, 1, and 9.

from cluster import *

def dist(a, b):
    """Compute the distance between values 'a' and 'b'."""
    return abs(a-b)

def mean(vals):
    """Compute the mean of values in 'values'.
    Returns 0 if list of values is empty.  This allows the labeling of empty
    clusters, if they occur."""
    return sum(vals) / len(vals) if vals else 0

if __name__ == "__main__":
    # run this script as follows:
    #   python3 cluster.py
    # should generate four clusters of values
    #   python3 cluster.py k val1 val2 val3 ...
    # generates a k-clustering of the values
    from sys import argv

    if len(argv) >= 3:
        k = int(argv[1])
        vals = [ int(val) for val in argv[2:] ]
    else:
        k = 4
        vals = [ -18, -17, -16,  -5, -4, -3,  0, 1, 2,  8, 9, 10 ]

    c = findClustering(vals,k,mean,dist)
    print(c)
    for i in range(c.k):
        print("Cluster with label {}: {}".format(c.label[i],c.cluster[i]))
