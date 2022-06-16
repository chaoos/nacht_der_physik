#!/usr/bin/env python3

import numpy as np
import numpy.random
import argparse
import cv2
import os
import time
import tempfile
import subprocess
import commentjson
import json
from pyfiglet import figlet_format
from collections import deque
import logging
import datetime

opencvpg = "/home/roman/.local/bin/opencvpg"
green = (0, 255, 0)
orange = (0, 128, 255)
red = (255, 0, 0)
blue = (0, 0, 255)
lower_circle = (0, 72, 0)#(80, 30, 100)
upper_circle = (255, 255, 115)#(180, 100, 100)
lower_dots = (0, 32, 0)
upper_dots = (255, 255, 255)

circle_thickness = 2
rectangle_thickness = 2
dot_thickness = 2
circle_color = green
circle_center_color = red
rectangle_color = orange
dot_color = blue
text_color = orange

dots_filter_area = range(0, 400) # for findContours()

process = ['circle', 'dots', 'original', 'output']

def constant(x):
    return x

def expression(x):
    return x

def hinted_hook(obj):
    if '__type__' in obj:
        return eval(f"{obj['__type__']}({obj['item']})")
    else:
        return obj

def distance(x,y):
    return np.sqrt((x[0] - y[0])**2 + (x[1] - y[1])**2)

def pt_in_circle(pt, circle):
    center, radius = circle
    return distance(pt, center) < radius

def pt_in_rectangle(pt, rect):
    bottom_left, top_right = rect
    return bottom_left[0] < pt[0] < top_right[0] and bottom_left[1] < pt[1] < top_right[1]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = 'Estimating pi.',
        formatter_class = argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-u', '--url', help='the url to open the stream from', default = 0)
    #parser.add_argument('--max-circles', help='maximal number of circle to detect', type = int, default = 1)
    #parser.add_argument('-c', '--calibrate', help='launch calibration', default=False, action="store_true")
    parser.add_argument('-c', '--config', help='config file path', default="config.json")
    parser.add_argument('-o', '--outfile', help='output json file', default="web/output.json")
    required = parser.add_argument_group('required named arguments')
    args = parser.parse_args()

    with open(args.config) as f:
        data = commentjson.load(f, object_hook=hinted_hook)
        mtime = os.path.getmtime(args.config)
        data = argparse.Namespace(**data)
        data.config = argparse.Namespace(**data.config)

    logger = logging.getLogger("circle") # create a logger called root
    logger.setLevel(logging.DEBUG if data.config.debug else logging.INFO)
    ch = logging.StreamHandler()
    logger.addHandler(ch)

    # if args.calibrate:
    #     ret, frame = cap.read()
    #     output = frame.copy()
    #     tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    #     try:
    #         print(f"{tmp.name = }")
    #         cv2.imwrite(tmp.name, output) 
    #     finally:
    #         tmp.close()
    #     subprocess.run([opencvpg, "--image", tmp.name])
    #     exit()

    # Set up the blob detector with parameters
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 30 # in pixels
    params.maxArea = 150 # in pixels
    params.minDistBetweenBlobs = 2 # @see https://stackoverflow.com/a/32974766/2768341
    dot_detector = cv2.SimpleBlobDetector_create(params)

    image = {}
    cap = cv2.VideoCapture(args.url) # Set Capture Device, in case of a USB Webcam try 1, or give -1 to get a list of available devices

    store_size = 50
    store = {
        'timestamp': deque(maxlen = store_size),
        'pi_area': deque(maxlen = store_size),
        'pi_pts': deque(maxlen = store_size),
        'pts_in_rect': deque(maxlen = store_size),
        'pts_in_circ': deque(maxlen = store_size),
        'area_in_rect': deque(maxlen = store_size),
        'area_in_circ': deque(maxlen = store_size)
    }

    while(True):
        # Capture frame-by-frame
        cap = cv2.VideoCapture(args.url) # for the network camera
        ret, frame = cap.read()
        logger.info('-'*80)
        logger.info('Resolution: ' + str(frame.shape[0]) + ' x ' + str(frame.shape[1]))

        # load the image and clone it for output
        cap.release() # for the network camera
        for obj in process:
            image[obj] = frame.copy()
        
        # Adaptive Guassian Threshold is to detect sharp edges in the Image. For more information Google it.
        #gray  = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,11,3.5)
        #circle_image = cv2.inRange(circle_image, tuple([0,32,0]), tuple([255,255,115])) # now only the green circle remains
        #dots_image = cv2.inRange(dots_image, lower_dots, upper_dots) # now only the green circle remains

        for obj in process:
            if obj in data.images and 'methods' in data.images[obj]:
                if obj == 'circle' and 'detect' not in data.config.circle:
                    continue
                for name, cfg in data.images[obj]['methods'].items():
                    cfg = argparse.Namespace(**cfg)
                    if cfg.active:
                        pargs = list(cfg.args) if 'args' in cfg else []
                        kwargs = dict(cfg.kwargs) if 'kwargs' in cfg else {}
                        if '__comment__' in cfg:
                            logger.info(f"{obj}/{name}: {cfg.__comment__}")
                        logger.info(f"{obj}/{name}: applying {cfg.method} with {pargs = } and {kwargs = }")
                        image[obj] = getattr(cv2, cfg.method)(image[obj], *pargs, **kwargs)
        
        circles = np.array([[[]]])
        # draw circles in the image
        if 'draw' in data.config.circle:
            draw_circles = np.array(data.config.draw_circles)
            logger.debug(f"{draw_circles = }")
            circles = np.append(circles, draw_circles).reshape(1,-1,3)

        # detect circles in the image
        if 'detect' in data.config.circle:
            pargs = data.config.detect_circles['args']
            kwargs = data.config.detect_circles['kwargs']
            logger.info(f"circle/HoughCircles: calling HoughCircles with {pargs = } and {kwargs = }")
            detect_circles = cv2.HoughCircles(image['circle'], *pargs, **kwargs)
            logger.debug(f"{detect_circles = }")
            if detect_circles is not None:
                circles = np.append(circles, detect_circles).reshape(1,-1,3)

        logger.debug(f"{circles = }")

        # detect blobs in the image
        #keypoints = dot_detector.detect(gray)
        # draw the blobs
        #output = cv2.drawKeypoints(output, keypoints, np.array([]), dot_color, cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

        #th, threshed = cv2.threshold(gray2, 100, 255, cv2.THRESH_BINARY|cv2.THRESH_OTSU) # threshold for the dots
        dots = []
        if 'draw' in data.config.dots:
            pargs = data.config.draw_dots['args']
            kwargs = data.config.draw_dots['kwargs']
            logger.info(f"dots/draw: applying {data.config.draw_dots['method']} with {pargs = } and {kwargs = }")
            draw_dots = eval('{0}(*pargs, **kwargs)'.format(data.config.draw_dots['method']))
            draw_dots = draw_dots[0:data.config.max_dots]
            dots.extend(draw_dots)
            logger.debug(f"{len(draw_dots) = }")

        if 'detect' in data.config.dots:
            pargs = data.config.detect_dots['args']
            kwargs = data.config.detect_dots['kwargs']
            logger.info(f"dots/detect: calling findContours with {pargs = } and {kwargs = }")
            detect_dots, hierarchy = cv2.findContours(image['dots'], *pargs, **kwargs) # find dots
            dots.extend(detect_dots)
            logger.debug(f"{len(detect_dots) = }")

        logger.debug(f"{len(dots) = }")
        #logger.debug(f"{detected_dots = }")

        #dots = list(filter(lambda x: cv2.contourArea(x) in dots_filter_area, dots)) # filter dots by area
        #cv2.drawContours(output, dots, -1, dot_color, 3) # draw remaining dots

        for obj in process:
            if obj in data.images and 'filters' in data.images[obj]:
                for name, cfg in data.images[obj]['filters'].items():
                    cfg = argparse.Namespace(**cfg)
                    if cfg.active:
                        if '__comment__' in cfg:
                            logger.info(f"{obj}/{name}: {cfg.__comment__}")
                        logger.info(f"{obj}/{name}: filtering with {cfg.expression.format(cfg.method)}")
                        pre_filter = len(dots)
                        dots = list(filter(lambda x: eval(cfg.expression.format(getattr(cv2, cfg.method)(x))), dots))
                        post_filter = len(dots)
                        logger.info(f"{obj}/{name}: filtered {post_filter} elements out of {pre_filter}")

        # draw example minimal and maximal dots
        #minRadius = int(np.sqrt(params.minArea/np.pi))
        #maxRadius = int(np.sqrt(params.maxArea/np.pi))
        #cv2.circle(image['output'], (int(minRadius*1.1), int(minRadius*1.1)), minRadius, dot_color, cv2.FILLED)
        #cv2.circle(image['output'], (int((2*minRadius+maxRadius)*1.1), int(maxRadius*1.1)), maxRadius, dot_color, cv2.FILLED)

        # ensure at least some circles were found
        if circles.size != 0:
            # convert the (x, y) coordinates and radius of the circles to integers
            circles = np.round(circles[0,:]).astype("int")
            
            pts_in_circ = np.zeros(len(circles), np.int)
            pts_in_rect = np.zeros(len(circles), np.int)
            area_in_circ = np.zeros(len(circles), np.float64)
            area_in_rect = np.zeros(len(circles), np.float64)

            timestamp = datetime.datetime.timestamp(datetime.datetime.now())
            store_pi_area = []
            store_pi_pts = []
            store_pts_in_rect = []
            store_pts_in_circ = []
            store_area_in_rect = []
            store_area_in_circ = []

            # loop over the (x, y) coordinates and radius of the circles
            for i, (x, y, r) in enumerate(circles[0:data.config.max_circles]):

                # draw the circle in the output image, then draw a rectangle in the image
                # corresponding to the center of the circle
                cv2.circle(image['output'], (x, y), r, circle_color, circle_thickness)
                cv2.rectangle(image['output'], (x - 2, y - 2), (x + 2, y + 2), circle_center_color, cv2.FILLED)
                cv2.rectangle(image['output'], (x - r, y - r), (x + r, y + r), rectangle_color, rectangle_thickness)

                for dot in dots[0:data.config.max_dots]:
                    pt = dot[0,0]
                    if pt_in_circle(pt, ((x,y),r)):
                        pts_in_circ[i] += 1
                        area_in_circ[i] += cv2.contourArea(dot)
                    if pt_in_rectangle(pt, ((x-r,y-r),(x+r,y+r))):
                        pts_in_rect[i] += 1
                        area_in_rect[i] += cv2.contourArea(dot)

                # only dots in the rectangle
                dots_in_rect = list(filter(lambda dot: pt_in_rectangle(dot[0,0], ((x-r,y-r),(x+r,y+r))), dots[0:data.config.max_dots]))
                pargs = data.config.draw_contours['args']
                kwargs = data.config.draw_contours['kwargs']
                logger.info(f"dots/draw: drawing dots with drawContours with {pargs = } and {kwargs = }")
                cv2.drawContours(image['output'], dots_in_rect, *pargs, **kwargs) # draw remaining dots
                cv2.fillPoly(image['dots'], pts=dots_in_rect, color=(0,0,0))

                store_pi_area.append(4*area_in_circ[i]/area_in_rect[i] if area_in_rect[i] != 0 else None)
                store_pi_pts.append(4*pts_in_circ[i]/pts_in_rect[i] if pts_in_rect[i] != 0 else None)
                store_pts_in_rect.append(int(pts_in_rect[i]))
                store_pts_in_circ.append(int(pts_in_circ[i]))
                store_area_in_rect.append(int(area_in_rect[i]))
                store_area_in_circ.append(int(area_in_circ[i]))

                pi = np.float64(store_pi_area[-1] if data.config.area else store_pi_pts[-1])
                img_text = f"circle #{i+1}: {r = }"
                cv2.putText(image['output'], img_text, (x-r, y-r-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 1)
                if not np.isnan(pi):
                    text = f"circle #{i+1}: ({x=},{y=},{r=}), {pts_in_circ[i]=}, {pts_in_rect[i]=}, {area_in_circ[i]=}, {area_in_rect[i]=}, {pi=:.1f}"
                    logger.info(text)
                    if data.config.fancy:
                        print(figlet_format(f'{pi = :.5f}', font = 'starwars'), end = '\r')
                        logger.debug(f"{store_pi_area[-1] = }")
                        logger.debug(f"{store_pi_pts[-1] = }")

            store['timestamp'].append(timestamp)
            store['pi_area'].append(store_pi_area)
            store['pi_pts'].append(store_pi_pts)
            store['pts_in_rect'].append(store_pts_in_rect)
            store['pts_in_circ'].append(store_pts_in_circ)
            store['area_in_rect'].append(store_area_in_rect)
            store['area_in_circ'].append(store_area_in_circ)

        # Display the resulting frame
        for obj in process:
            if 'show' in data.images[obj] and data.images[obj]['show']:
                cv2.imshow(obj, image[obj])

        # Store the resulting frame
        for obj in process:
            if 'store' in data.images[obj] and data.images[obj]['store'] != False:
                logger.debug(f"Storing obj in file {data.images[obj]['store']}")
                cv2.imwrite(data.images[obj]['store'], image[obj]) 

        with open(args.outfile, 'w') as f:
            logger.debug(f"Storing json in {args.outfile}")
            output_json = {k: list(v) for k, v in store.items()}
            output_json['area'] = data.config.area
            commentjson.dump(output_json, f, indent=4)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            logger.info("quitting")
            break

        if mtime != os.path.getmtime(args.config):
            with open(args.config) as f:
                logger.info("Reloading config ...")
                try:
                    data = commentjson.load(f, object_hook=hinted_hook)
                    data = argparse.Namespace(**data)
                    data.config = argparse.Namespace(**data.config)
                    logger.info("Reload config successful")
                    logger.setLevel(logging.DEBUG if data.config.debug else logging.INFO)
                    mtime = os.path.getmtime(args.config)
                except:
                    logger.error("Failed to reload config")

        time.sleep(data.config.delay)

    # When everything done, release the capture
    cv2.destroyAllWindows()