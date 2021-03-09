import unittest

import cv2

from processor import darknet
from processor.object_to_string import convert_from_objects_to_string, normalize_expression, convert_infix_to_latex
from solver import solve
import os


def image_detection(image, network, class_names, class_colors, thresh):
    width = darknet.network_width(network)
    height = darknet.network_height(network)
    darknet_image = darknet.make_image(width, height, 3)

    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (width, height),
                               interpolation=cv2.INTER_LINEAR)

    darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())
    detections = darknet.detect_image(network, class_names, darknet_image, thresh=thresh)
    darknet.free_image(darknet_image)
    image = darknet.draw_boxes(detections, image_resized, class_colors)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB), detections


def process(image):
    network, class_names, class_colors = darknet.load_network(
        "yolo.cfg",
        "yolo.data",
        "./weights/31-01.weights",
        1
    )
    processed_image, detections = image_detection(
        image, network, class_names, class_colors, .25
    )
    expression = convert_from_objects_to_string(detections)
    expression = normalize_expression(expression)
    latex = convert_infix_to_latex(expression)
    print(expression)

    roots = solve.parse_and_solve_and_round(expression, 0.00001)
    print(roots)

    return latex, roots


class Tests(unittest.TestCase):

    def test_process(self):
        image = cv2.imread("../../testing-images/testing.png")
        process(image)
