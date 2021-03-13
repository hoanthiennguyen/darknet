import argparse
import glob
import os
import random
import cv2
import numpy as np
import time

import darknet
from object_to_string import *
from solver import solve


def parser():
    cmd_parser = argparse.ArgumentParser(description="YOLO Object Detection")
    cmd_parser.add_argument("--input", type=str, default="testing-images/testing.png",
                            help="testing image filename or a folder containing testing images")
    cmd_parser.add_argument("--output_dir", type=str, default="testing-labels",
                            help="folder to save labels")
    cmd_parser.add_argument("--batch_size", default=1, type=int,
                            help="number of images to be processed at the same time")
    cmd_parser.add_argument("--weights", default="weights/latest.weights",
                            help="yolo weights path")
    cmd_parser.add_argument("--dont_show", action='store_true',
                            help="windown inference display. For headless systems")
    cmd_parser.add_argument("--ext_output", action='store_true',
                            help="display bbox coordinates of detected objects")
    cmd_parser.add_argument("--save_labels", action='store_true',
                            help="save detections bbox for each image in yolo format")
    cmd_parser.add_argument("--config_file", default="yolo.cfg",
                            help="path to config file")
    cmd_parser.add_argument("--data_file", default="yolo.data",
                            help="path to data file")
    cmd_parser.add_argument("--thresh", type=float, default=.25,
                            help="remove detections with lower confidence")
    return cmd_parser.parse_args()


def check_arguments_errors(args):
    assert 0 < args.thresh < 1, "Threshold should be a float between zero and one (non-inclusive)"
    if not os.path.exists(args.config_file):
        raise (ValueError("Invalid config path {}".format(os.path.abspath(args.config_file))))
    if not os.path.exists(args.weights):
        raise (ValueError("Invalid weight path {}".format(os.path.abspath(args.weights))))
    if not os.path.exists(args.data_file):
        raise (ValueError("Invalid data file path {}".format(os.path.abspath(args.data_file))))
    if args.input and not os.path.exists(args.input):
        raise (ValueError("Invalid image path {}".format(os.path.abspath(args.input))))


def check_batch_shape(images, batch_size):
    """
        Image sizes should be the same width and height
    """
    shapes = [image.shape for image in images]
    if len(set(shapes)) > 1:
        raise ValueError("Images don't have same shape")
    if len(shapes) > batch_size:
        raise ValueError("Batch size higher than number of images")
    return shapes[0]


def load_images(images_path):
    """
    If image path is given, return it directly
    For txt file, read it and return each line as image path
    In other case, it's a folder, return a list with names of each
    jpg, jpeg and png file
    """
    input_path_extension = images_path.split('.')[-1]
    if input_path_extension in ['jpg', 'jpeg', 'png', 'PNG', 'JPG', "JPEG"]:
        return [images_path]
    elif input_path_extension == "txt":
        with open(images_path, "r") as f:
            return f.read().splitlines()
    else:
        return glob.glob(
            os.path.join(images_path, "*.jpg")) + \
               glob.glob(os.path.join(images_path, "*.png")) + \
               glob.glob(os.path.join(images_path, "*.jpeg")) + \
               glob.glob(os.path.join(images_path, "*.PNG")) + \
               glob.glob(os.path.join(images_path, "*.JPEG")) + \
               glob.glob(os.path.join(images_path, "*.JPG"))


def prepare_batch(images, network, channels=3):
    width = darknet.network_width(network)
    height = darknet.network_height(network)

    darknet_images = []
    for image in images:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image_resized = cv2.resize(image_rgb, (width, height),
                                   interpolation=cv2.INTER_LINEAR)
        custom_image = image_resized.transpose(2, 0, 1)
        darknet_images.append(custom_image)

    batch_array = np.concatenate(darknet_images, axis=0)
    batch_array = np.ascontiguousarray(batch_array.flat, dtype=np.float32) / 255.0
    darknet_images = batch_array.ctypes.data_as(darknet.POINTER(darknet.c_float))
    return darknet.IMAGE(width, height, channels, darknet_images)


def image_detection(image_path, network, class_names, class_colors, thresh):
    # Darknet doesn't accept numpy images.
    # Create one with image we reuse for each detect
    width = darknet.network_width(network)
    height = darknet.network_height(network)
    darknet_image = darknet.make_image(width, height, 3)

    image = cv2.imread(image_path)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (width, height),
                               interpolation=cv2.INTER_LINEAR)

    darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())
    detections = darknet.detect_image(network, class_names, darknet_image, thresh=thresh)
    darknet.free_image(darknet_image)
    image = darknet.draw_boxes(detections, image_resized, class_colors)
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB), detections


def batch_detection(network, images, class_names, class_colors,
                    thresh=0.25, hier_thresh=.5, nms=.45, batch_size=4):
    image_height, image_width, _ = check_batch_shape(images, batch_size)
    darknet_images = prepare_batch(images, network)
    batch_detections = darknet.network_predict_batch(network, darknet_images, batch_size, image_width,
                                                     image_height, thresh, hier_thresh, None, 0, 0)
    batch_predictions = []
    for idx in range(batch_size):
        num = batch_detections[idx].num
        detections = batch_detections[idx].dets
        if nms:
            darknet.do_nms_obj(detections, num, len(class_names), nms)
        predictions = darknet.remove_negatives(detections, class_names, num)
        images[idx] = darknet.draw_boxes(predictions, images[idx], class_colors)
        batch_predictions.append(predictions)
    darknet.free_batch_detections(batch_detections, batch_size)
    return images, batch_predictions


def image_classification(image, network, class_names):
    width = darknet.network_width(network)
    height = darknet.network_height(network)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image_resized = cv2.resize(image_rgb, (width, height),
                               interpolation=cv2.INTER_LINEAR)
    darknet_image = darknet.make_image(width, height, 3)
    darknet.copy_image_from_bytes(darknet_image, image_resized.tobytes())
    detections = darknet.predict_image(network, darknet_image)
    predictions = [(name, detections[idx]) for idx, name in enumerate(class_names)]
    darknet.free_image(darknet_image)
    return sorted(predictions, key=lambda x: -x[1])


def convert2relative(image, bbox):
    """
    YOLO format use relative coordinates for annotation
    """
    x, y, w, h = bbox
    height, width, _ = image.shape
    return x / width, y / height, w / width, h / height


def save_annotations(name, image, detections, class_names, output_dir):
    """
    Files saved with image_name.txt and relative coordinates
    """
    filename = name.split("/")[-1]
    filename_without_ext = filename.split(".")[0]
    file_name = output_dir + "/" + filename_without_ext + ".txt"
    print("Saving " + file_name)
    with open(file_name, "w") as f:
        for label, confidence, bbox in detections:
            x, y, w, h = convert2relative(image, bbox)
            label = class_names.index(label)
            f.write("{} {:.4f} {:.4f} {:.4f} {:.4f}\n".format(label, x, y, w, h, ))


def main():
    args = parser()
    check_arguments_errors(args)

    random.seed(3)  # deterministic bbox colors
    t = time.time()
    network, class_names, class_colors = darknet.load_network(
        args.config_file,
        args.data_file,
        args.weights,
        batch_size=args.batch_size
    )
    t1 = time.time()
    print("Load weight takes: {}s".format(t1 - t))
    image_names = load_images(args.input)
    output_dir = args.output_dir
    if len(image_names) > 1:
        print("Detecting for {} images".format(len(image_names)))
        for i in range(len(image_names)):
            image_name = image_names[i]
            image, detections = image_detection(
                image_name, network, class_names, class_colors, args.thresh
            )
            expression = convert_from_objects_to_string(detections)
            print(expression)

            save_annotations(image_name, image, detections, class_names, output_dir)

    elif len(image_names) == 1:
        image_name = image_names[0]
        image, detections = image_detection(
            image_name, network, class_names, class_colors, args.thresh
        )

        if args.save_labels:
            save_annotations(image_name, image, detections, class_names, output_dir)
        darknet.print_detections(detections, args.ext_output)
        if len(image_names) < 2 and not args.dont_show:
            cv2.imshow('Inference', image)
            cv2.waitKey()

        expression = convert_from_objects_to_string(detections)
        expression = normalize_expression(expression)
        print(expression)

        roots = solve.parse_and_solve_and_round(expression, 0.00001)
        print(roots)

        latex = convert_infix_to_latex(expression)

        print(latex)

    t2 = time.time()
    print("Detection takes: {}s".format(t2 - t1))


if __name__ == "__main__":
    main()
