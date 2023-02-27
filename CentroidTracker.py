# import the necessary packages
from scipy.spatial import distance as dist
import numpy as np


class CentroidTracker:
    def __init__(self, gate_name,maxDisappeared=50, maxDistance=50,
                 minNeighbor=50, minStartEndPos=50, maxage=30):
        # initialize the next unique object ID along with two ordered
        # dictionaries used to keep track of mapping a given object
        # ID to its centroid and number of consecutive frames it has
        # been marked as "disappeared", respectively
        self.nextObjectID = 0
        self.objects = {}
        # store the number of maximum consecutive frames a given
        # object is allowed to be marked as "disappeared" until we
        # need to deregister the object from tracking
        self.maxDisappeared = maxDisappeared

        # store the maximum distance between centroids to associate
        # an object -- if the distance is larger than this maximum
        # distance we'll start to mark the object as "disappeared"
        self.maxDistance = maxDistance

        # store the minimum distance between two neighbor centroids
        # if two objects are closer than minimum one of then is deleted
        self.minNeighbor = minNeighbor

        # based on the start and end center of object we
        # can detect if it moves up or down
        self.minStartEndPos = minStartEndPos
        self.maxage = maxage
        self.UPS = 0
        self.DOWNS = 0
        self.last_status = False

    def register(self, centroid):
        objectCentroids = [c['center'] for c in self.objects.values()]
        if len(objectCentroids) > 0:
            D_Neighbor = dist.cdist(np.array(objectCentroids),
                                    np.array([centroid]))
            if np.any(D_Neighbor < self.minNeighbor):
                return

        # when registering an object we use the next available object
        # ID to store the centroid
        self.objects[self.nextObjectID] = {
                'center' : centroid, 
                'disappeared' : 0,
                'startcentroid' : centroid,
                'age' : 0}
        self.nextObjectID += 1

    def deregister(self, objectID):
        # to deregister an object ID we delete the object ID from
        # both of our respective dictionaries
        temp = self.objects[objectID]['center'][1] - self.objects[objectID]['startcentroid'][1]
        if temp > self.minStartEndPos:
            self.DOWNS += 1
            self.last_status = True
        elif temp < -1*self.minStartEndPos:
            self.UPS += 1
            self.last_status = True

        del self.objects[objectID]
    
    def exceded_age(self):
        ages = [a['age'] for a in self.objects.values()]
        for curr_age in ages:
            if curr_age > self.maxage:
                return True
        return False

    def update_skip_frames(self):
        for objectID in list(self.objects.keys()):
            self.objects[objectID]['disappeared'] += 1
            self.objects[objectID]['age'] += 1
            # if we have reached a maximum number of consecutive
            # frames where a given object has been marked as
            # missing, deregister it
            if self.objects[objectID]['disappeared'] > self.maxDisappeared:
                self.deregister(objectID)

    def update(self, rects):
        # check to see if the list of input bounding box rectangles
        # is empty
        if len(rects) == 0:
            # loop over any existing tracked objects and mark them
            # as disappeared
            self.update_skip_frames()
            # return early as there are no centroids or tracking info
            # to update
            return self.objects

        # initialize an array of input centroids for the current frame
        inputCentroids = np.zeros((len(rects), 2), dtype="int")

        # loop over the bounding box rectangles
        for (i, (startX, startY, endX, endY)) in enumerate(rects):
            # use the bounding box coordinates to derive the centroid
            cX = int((startX + endX) / 2.0)
            cY = int((startY + endY) / 2.0)
            inputCentroids[i] = (cX, cY)
        
        # if we are currently not tracking any objects take the input
        # centroids and register each of them
        if len(self.objects) == 0:
            for i in range(0, len(inputCentroids)):
                self.register(inputCentroids[i])

        # otherwise, we are currently tracking objects so we need to
        # try to match the input centroids to existing object
        # centroids
        else:
        # grab the set of object IDs and corresponding centroids
            objectIDs = list(self.objects.keys())
            objectCentroids = [c['center'] for c in self.objects.values()]

            # compute the distance between each pair of object
            # centroids and input centroids, respectively -- our
            # goal will be to match an input centroid to an existing
            # object centroid
            D = dist.cdist(np.array(objectCentroids), inputCentroids)

            # in order to perform this matching we must (1) find the
            # smallest value in each row and then (2) sort the row
            # indexes based on their minimum values so that the row
            # with the smallest value as at the *front* of the index
            # list
            rows = D.min(axis=1).argsort()

            # next, we perform a similar process on the columns by
            # finding the smallest value in each column and then
            # sorting using the previously computed row index list
            cols = D.argmin(axis=1)[rows]

            # in order to determine if we need to update, register,
            # or deregister an object we need to keep track of which
            # of the rows and column indexes we have already examined
            usedRows = set()
            usedCols = set()

            # loop over the combination of the (row, column) index
            # tuples
            for (row, col) in zip(rows, cols):
                # if we have already examined either the row or
                # column value before, ignore it
                if row in usedRows or col in usedCols:
                    continue

                # if the distance between centroids is greater than
                # the maximum distance, do not associate the two
                # centroids to the same object
                if D[row, col] > self.maxDistance:
                    continue

                # otherwise, grab the object ID for the current row,
                # set its new centroid, and reset the disappeared
                # counter
                objectID = objectIDs[row]
                self.objects[objectID]['center'] = inputCentroids[col]
                self.objects[objectID]['disappeared'] = 0
                self.objects[objectID]['age'] += 1

                # indicate that we have examined each of the row and
                # column indexes, respectively
                usedRows.add(row)
                usedCols.add(col)

            # compute both the row and column index we have NOT yet
            # examined
            unusedRows = set(range(0, D.shape[0])).difference(usedRows)
            unusedCols = set(range(0, D.shape[1])).difference(usedCols)

            # in the event that the number of object centroids is
            # equal or greater than the number of input centroids
            # we need to check and see if some of these objects have
            # potentially disappeared
            if D.shape[0] >= D.shape[1]:
                # loop over the unused row indexes
                for row in unusedRows:
                    # grab the object ID for the corresponding row
                    # index and increment the disappeared counter
                    objectID = objectIDs[row]
                    self.objects[objectID]['disappeared'] += 1
                    self.objects[objectID]['age'] += 1
                    # check to see if the number of consecutive
                    # frames the object has been marked "disappeared"
                    # for warrants deregistering the object
                    if self.objects[objectID]['disappeared'] > self.maxDisappeared:
                        self.deregister(objectID)

            # otherwise, if the number of input centroids is greater
            # than the number of existing object centroids we need to
            # register each new input centroid as a trackable object
            else:
                for col in unusedCols:
                    self.register(inputCentroids[col])

        # return the set of trackable objects
        return self.objects
