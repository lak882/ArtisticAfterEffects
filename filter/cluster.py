# A k-means clustering class.
"""A class to support clustering into k groups.

The K-Means algorithm.  This algorithm seeks to take a collection of at
least "k" data "values", and assign each value to one of "k" different
clusters.  The assignment is based on minimizing the distance (computed by
"distFunction") between a particular value and the "label" associated with its
destination cluster.

The "values" to be clustered must support two important functions, specified
at cluster initialization: "distFunction(a,b)" which computes the distance
between values a and b, and "meanFunction(values)" which computes the mean of
a collection of values.  The meanFunction should return a reasonable value
even if values is empty.

At any point, the Clustering can be used to "classify" an arbitrary "value" to
the *index* of one of the "k" clusters. The value is not added to the cluster.

The "label[i]" method returns the label associated with a cluster index.

The "cluster[i]" method returns the values associated with a particular
cluster index.

The "variance" property returns the sum of the squares of the distances
between values and their cluster's label.

The "findClustering" function produces a tight k-clustering for a sequence
of values, provided appropriate functions for computing distance and mean.
"""
__all__ = ['Clustering', 'findClustering']

class Clustering(object):
    __slots__ = ['_mean', '_dist', '_label', '_cluster']

    def __init__(self, data, labels, meanFunction, distFunction):
        # remember the distance and mean functions
        self._mean = meanFunction
        self._dist = distFunction

        # set up labels
        self._label = tuple(labels)

        # start making clusters
        clusters = [ [] for _ in labels ]

        # classify all the data
        for d in data:
            i = self.classify(d)
            clusters[i].append(d)

        # save immutably:
        self._cluster = tuple( tuple(c) for c in clusters )

    @property
    def label(self):
        """The tuple of labels.  Each label is a representative data value
        for its corresponding cluster"""
        return self._label

    @property
    def cluster(self):
        """A tuple of k clusters.  Each cluster is a tuple of data values."""
        return self._cluster

    @property
    def k(self):
        """The number of clusters."""
        return len(self._label)

    def classify(self, v):
        """Return the index of the cluster whose label is closest to v."""
        # initalize closest index at 0
        closest = 0

        for i in range(len(self.label)):
            # get distance between v and label using distance function
            distance = self._dist(self.label[i], v)

            # if it's the first itteration, then it's the closest distance
            if i == 0:
                closestDistance = distance
            # if the distance is greater than the previous closest distance,
            # then it becomes the new closest ditances and it's indci is recorded
            elif distance < closestDistance:
                closestDistance = distance
                closest = i

        return closest

    @property
    def variance(self):
        """The sum of squared distances from values to their labels."""
        total = 0
        # get cluster index for label
        for i in range(len(self.cluster)):
            # go through each value in cluster
            for value in self.cluster[i]:
                # get distance between value and label using distance function
                distance = self._dist(self.label[i], value)
                # add square of distance to total
                total = total + (distance * distance)
        return total

    def recluster(self):
        """Generate a new clustering using means from the current clustering.
        This version uses current centers to classify all the data into new
        clusters."""

        # collect all the data into a list
        # get every cluster tuple into list
        clusterList = [ value for value in self.cluster ]

        # compute the means of the current clusters
        # get mean of every cluster tuple in previous list
        meanList = [ self._mean(cluster) for cluster in clusterList ]

        # set label and clusters equal to the two lists we just made
        self._label = tuple(meanList)
        self._cluster = tuple(clusterList)

        # return a *new* clustering of the data labeled with current means
        return self   # this is *not* correct; it's simply this clustering

    def __str__(self):
        """Printable version of c."""
        n = sum(len(c) for c in self.cluster)
        return "A {}-cluster of {} values with variance {}.".format(self.k,n,self.variance)

    def __repr__(self):
        return str(self)

# A factory that produces good clusterings.
def findClustering(vals,k, meanFunction, distFunction):
    """Generates a clustering of from a collection of data."""
    from random import shuffle

    # collect data, shuffle it, use k of the values as labels:
    vals = list(vals)
    shuffle(vals)
    labels = vals[:k]

    # build the cluster
    c = Clustering(vals, labels, meanFunction, distFunction)
    v = c.variance

    # keep generating clusters until the variance stops decreasing
    while True:
        # try to improve clustering
        nextC = c.recluster()
        nextV = nextC.variance
        # quit when improvement fails
        if nextV >= v:
            break
        # otherwise, go with new clustering
        c = nextC
        v = nextV
    return c
