# Edge Impulse - OpenMV FOMO Object Detection Example
#
# This work is licensed under the MIT license.
# Copyright (c) 2013-2024 OpenMV LLC. All rights reserved.
# https://github.com/openmv/openmv/blob/master/LICENSE

import sensor, image, time, os, ml, math, uos, gc
from ulab import numpy as np
from machine import UART
from modbus import ModbusRTU

uart = UART(1, 115200, parity=None, stop=1, timeout=1, timeout_char=4)
modbus = ModbusRTU(uart, register_num=9999)

sensor.reset()                         # Reset and initialize the sensor.
sensor.set_pixformat(sensor.RGB565)    # Set pixel format to RGB565 (or GRAYSCALE)
sensor.set_framesize(sensor.QVGA)      # Set frame size to QVGA (320x240)
sensor.set_windowing((240, 240))       # Set 240x240 window.
sensor.skip_frames(time=2000)          # Let the camera adjust.

net = None
labels = None
min_confidence = 0.5

try:
    # load the model, alloc the model file on the heap if we have at least 64K free after loading
    net = ml.Model("trained.tflite", load_to_fb=uos.stat('trained.tflite')[6] > (gc.mem_free() - (64*1024)))
except Exception as e:
    raise Exception('Failed to load "trained.tflite", did you copy the .tflite and labels.txt file onto the mass-storage device? (' + str(e) + ')')

try:
    labels = [line.rstrip('\n') for line in open("labels.txt")]
except Exception as e:
    raise Exception('Failed to load "labels.txt", did you copy the .tflite and labels.txt file onto the mass-storage device? (' + str(e) + ')')

colors = [ # Add more colors if you are detecting more than 7 types of classes at once.
    (255,   0,   0),
    (  0, 255,   0),
    (255, 255,   0),
    (  0,   0, 255),
    (255,   0, 255),
    (  0, 255, 255),
    (255, 255, 255),
]

threshold_list = [(math.ceil(min_confidence * 255), 255)]

def fomo_post_process(model, inputs, outputs):
    ob, oh, ow, oc = model.output_shape[0]

    x_scale = inputs[0].roi[2] / ow
    y_scale = inputs[0].roi[3] / oh

    scale = min(x_scale, y_scale)

    x_offset = ((inputs[0].roi[2] - (ow * scale)) / 2) + inputs[0].roi[0]
    y_offset = ((inputs[0].roi[3] - (ow * scale)) / 2) + inputs[0].roi[1]

    l = [[] for i in range(oc)]

    for i in range(oc):
        img = image.Image(outputs[0][0, :, :, i] * 255)
        blobs = img.find_blobs(
            threshold_list, x_stride=1, y_stride=1, area_threshold=1, pixels_threshold=1
        )
        for b in blobs:
            rect = b.rect()
            x, y, w, h = rect
            score = (
                img.get_statistics(thresholds=threshold_list, roi=rect).l_mean() / 255.0
            )
            x = int((x * scale) + x_offset)
            y = int((y * scale) + y_offset)
            w = int(w * scale)
            h = int(h * scale)
            l[i].append((x, y, w, h, score))
    return l

clock = time.clock()
while(True):
    clock.tick()

    if modbus.any():
        modbus.handle(debug = True)

    img = sensor.snapshot()

    leftmost_object = None  # To keep track of the leftmost object
    leftmost_x = float('inf')  # Initialize leftmost x-coordinate as infinity

    for i, detection_list in enumerate(net.predict([img], callback=fomo_post_process)):
        if i == 0: continue  # Skip the background class
        if len(detection_list) == 0: continue  # No detections for this class?

        print("********** %s **********" % labels[i])
        for x, y, w, h, score in detection_list:
            center_x = math.floor(x + (w / 2))
            center_y = math.floor(y + (h / 2))
            print(f"x {center_x}\ty {center_y}\tscore {score}")

            # Check if this is the leftmost object
            if center_x < leftmost_x:
                leftmost_x = center_x
                leftmost_object = (labels[i], center_x, center_y, score)  # Store the label and coordinates

            img.draw_circle((center_x, center_y, 12), color=colors[i])

    # After processing all objects, print the leftmost object if detected
    if leftmost_object:
        label, left_x, left_y, left_score = leftmost_object
        print(f"Leftmost Object: {label}, x: {left_x}, y: {left_y}, score: {left_score}")
        modbus.REGISTER[0] = 0
        if label == "red":
            modbus.REGISTER[1] = 1
        else:
            modbus.REGISTER[1] = 0
        modbus.REGISTER[2] = left_x
        modbus.REGISTER[3] = left_y
    else:
        modbus.REGISTER[0] = 1
        modbus.REGISTER[1] = 3
        modbus.REGISTER[2] = 0
        modbus.REGISTER[3] = 0

    print(clock.fps(), "fps", end="\n\n")
