import cv2
import numpy as np
from CentroidTracker import CentroidTracker
import time
from datetime import datetime
from functools import reduce

class Gate:
    def __init__(self, gate_name, camera_url, maxDisappeared=4,
                 maxDistance=125, minNeighbor=120, minStartEndPos=40,
                 min_person_area=1400, frame_res=[640, 480],
                 low_end_thres=30, dilate_iter=1, erode_iter=8,
                 max_wait_cycles=10, wait_seconds=1, wait_diplay_frame=1, objectmaxage=10):
        self.camera_url = camera_url
        self.video = cv2.VideoCapture(camera_url)
        self.ct = CentroidTracker(gate_name, maxDisappeared, maxDistance, minNeighbor, minStartEndPos, objectmaxage)
        self.person_area = min_person_area
        self.max_wait_cycles = max_wait_cycles
        self.wait_seconds = wait_seconds
        self.last_waited_cycles = 0
        self.gate_name = gate_name
        self.frame_res = frame_res
        self.dilate_iter = dilate_iter
        self.erode_iter = erode_iter
        self.low_end_thres = low_end_thres
        self.check = False
        self.wait_diplay_frame = wait_diplay_frame
        self.printed = False
        while not self.check:
            self.check, self.cur_frame = self.video.read()
        self.cur_frame = cv2.resize(self.cur_frame, self.frame_res)
        gray_frame = cv2.cvtColor(self.cur_frame, cv2.COLOR_BGR2GRAY)
        self.initialState = cv2.GaussianBlur(gray_frame, (9, 9), 0)
        self.avg_fps = [0 for _ in range(10)]

    def update(self):
        self.check, self.cur_frame = self.video.read()
        if not self.check:
            if not self.printed:
                print('The Camera for Gate {} is not responding!'.format(self.gate_name))
                self.printed = True
            time.sleep(self.wait_seconds)
            self.last_waited_cycles += 1
            self.video = cv2.VideoCapture(self.camera_url)
            if self.last_waited_cycles >= self.max_wait_cycles:
                print("Camera at Gate {} Fail!".format(self.gate_name))
            else:
                return False
        else:
            self.last_waited_cycles = 0
            if self.printed:
                print('The Camera for Gate {} is back online.'.format(self.gate_name))
            self.printed = False
        # From colour images creating a gray frame
        
        self.cur_frame = cv2.resize(self.cur_frame, self.frame_res)
        gray_frame = cv2.cvtColor(self.cur_frame, cv2.COLOR_BGR2GRAY)

        # To find the changes creating a GaussianBlur from the gray image
        gray_frame = cv2.GaussianBlur(gray_frame, (9, 9), 0)
        
        if self.ct.exceded_age():
            self.initialState = gray_frame

        self.differ_frame = cv2.absdiff(self.initialState,gray_frame)

        thresh_frame = cv2.threshold(self.differ_frame, self.low_end_thres, 255,
                                     cv2.THRESH_BINARY)[1]

        self.thresh_frame = cv2.dilate(thresh_frame, None, iterations=self.dilate_iter)
        self.thresh_frame = cv2.erode(self.thresh_frame, None, iterations=self.erode_iter)

        self.cont = cv2.findContours(self.thresh_frame,
                                   cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)[0]

        rects = []
        for cur in self.cont:
            area = cv2.contourArea(cur)
            if area > self.person_area:
                (x, y, w, h) = cv2.boundingRect(cur)
                rects.append([x, y, x+w, y+h])

        self.objects = self.ct.update(rects)
        return True

    def read_result(self):
        d = {'Ups' : self.ct.UPS,
             'Downs' : self.ct.DOWNS,
             'Status' : self.ct.last_status}
        self.ct.last_status = False
        return d

    def display_video(self, disp_differ=True, disp_thres=True, disp_main_frame=True):
        if not self.check:
            return False

        if disp_main_frame:
            for cur in self.cont:
                area = cv2.contourArea(cur)

                if area > self.person_area:
                    (cur_x, cur_y, cur_w, cur_h) = cv2.boundingRect(cur)
                    cv2.rectangle(self.cur_frame, (cur_x, cur_y),
                                  (cur_x + cur_w, cur_y + cur_h),
                                  (0, 0, 255), 2)
            for (objectID, val) in self.objects.items():
                centroid = val['center']
                text = "ID {}".format(objectID)
                cv2.putText(self.cur_frame, text,
                            (centroid[0] - 10, centroid[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
            cv2.putText(self.cur_frame, 'Ups: ' + str(self.ct.UPS), (0, 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(self.cur_frame, 'Downs: ' + str(self.ct.DOWNS), (0, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            # Through the colour frame displaying the contour of the object
            cv2.imshow("Colour Frame: " + self.gate_name, self.cur_frame)

        if disp_differ:
            # difference between inital frame and the current frame
            cv2.imshow("inital static frame vs current frame: " + self.gate_name, self.differ_frame)
        if disp_thres:
            # on the frame screen the black and white images from the video
            cv2.imshow("Threshold Frame: " + self.gate_name, self.thresh_frame)

        wait_key = cv2.waitKey(self.wait_diplay_frame)

    def close(self):
        self.video.release()
        cv2.destroyAllWindows()
