import unittest

import cv2

from processor import darknet
from processor.object_to_string import convert_detections_to_expression, normalize_expression, convert_infix_to_latex
from solver import solve
from solver.error import ExpressionSyntaxError, EvaluationError
from solver.solve import INFINITE_NUMBER_OF_ROOTS


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


def normalize_before_solve(expression: str):
    first_char = next((x for x in expression if x.isalpha()), None)
    next_char = next((x for x in expression if x.isalpha() and x != first_char), None)

    if next_char:
        raise EvaluationError("More than one variable is not supported")
    elif first_char:
        expression = expression.replace(first_char, "x")

    return expression, first_char


def process(image):
    network, class_names, class_colors = darknet.load_network(
        "yolo.cfg",
        "yolo.data",
        "./weights/latest.weights",
        1
    )
    processed_image, detections = image_detection(
        image, network, class_names, class_colors, .5
    )
    darknet.free_network_ptr(network)
    expression = convert_detections_to_expression(detections)
    expression = normalize_expression(expression)
    print(expression)
    valid = False
    roots = []
    latex = ""
    message = ""
    try:
        latex = convert_infix_to_latex(expression)
        try:
            expression_to_solve, variable = normalize_before_solve(expression)
            roots = solve.parse_and_solve_and_round(expression_to_solve, 0.00001)
            if roots:
                if roots != [INFINITE_NUMBER_OF_ROOTS]:
                    roots = list(map(lambda x: variable + " = " + str(x), roots))
            else:
                roots = ["No roots"]
            valid = True
            print(roots)
        except (ExpressionSyntaxError, EvaluationError) as e:
            message = str(e)
    except RecursionError:
        message = "Maximum power exceeded"
    except (SyntaxError, IndexError, Exception) as e:
        print(e)
        message = "Unrecognized expression"

    return valid, message, expression, latex, roots


class Tests(unittest.TestCase):

    def test_process(self):
        image = cv2.imread("../../testing-images/testing.png")
        process(image)
