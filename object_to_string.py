import unittest
import re
import pytexit

superscript_threshold = 1 / 2
subscript_threshold = 3 / 4
left_and_right_threshold = 1 / 4
next_label_threshold = 1 / 2


def convert_from_objects_to_string(detections: list) -> str:
    """
     detections : list of detection = [(label, confidence, bbox)]
     bbox = (center_x,center_y,w,h)
     """
    detections.sort(key=lambda x: x[2][0] - x[2][2] / 2)
    list_all_fraction = get_all_fractions(detections)
    # all index for get exponent
    list_all_index_fraction = get_all_index_fraction(list_all_fraction)
    result = ""
    length = len(detections)
    end_of_fraction = -1
    remove_list = []
    for i in range(0, length):
        if i not in remove_list:
            fraction = next((x for x in list_all_fraction if x[1] == i), [])
            if fraction:
                end_of_fraction = fraction[2]
                fraction_label = fraction[0]
                fraction_box = get_box_fraction(detections, i, end_of_fraction)
                is_super = False
                if 1 != 0 and end_of_fraction != length - 1:
                    # if fraction is exponent
                    if is_super_script(detections[i - 1][2], fraction_box):
                        is_super = True
                        # after fraction still is exponent
                        if is_in_line(fraction_box, detections[end_of_fraction + 1][2]):
                            script, end_of_script = get_exponent(detections, end_of_fraction + 1,
                                                                 list_all_index_fraction)

                            remove_list = remove_list + list(range(i, end_of_script + 1))
                            next_label = detections[end_of_fraction + 1][0]

                            if should_add_bracket("", next_label):
                                fraction_label = f"({fraction_label}){script}"

                        # add () for exponent, Ex x^x+1 = > x^(x+1)
                        if re.search('[+*/=-]', fraction_label):
                            fraction_label = f'({fraction_label})'
                        fraction_label = f"^{fraction_label}"

                if not is_super:
                    # add () for fraction, Ex x/2*3 => (x/2)*3
                    remove_list = remove_list + list(range(i, end_of_fraction + 1))
                    next_label = detections[end_of_fraction + 1][0] if end_of_fraction != length - 1 else ""
                    previous_label = detections[i - 1][0] if i != 0 else ""
                    if should_add_bracket(previous_label, next_label):
                        fraction_label = f"({fraction_label})"
                result += fraction_label
            else:
                if i != 0:
                    # not after fraction
                    if i != end_of_fraction + 1:
                        previous_label = detections[i - 1][0]
                        # Add pow
                        if is_super_script(detections[i - 1][2], detections[i][2]) and not is_comma(previous_label):
                            # get exponent
                            script, end_of_script = get_exponent(detections, i, list_all_index_fraction)

                            remove_list = remove_list + list(range(i, end_of_script + 1))
                            # Except -^2
                            if not is_operators(detections[i - 1][0]):
                                # add () for exponent, Ex x^x+1 = > x^(x+1)
                                if re.search('[+*/=-]', script):
                                    script = f'({script})'
                                result += f'^{script}'
                            else:
                                result += script
                        else:
                            result += detections[i][0]
                    else:
                        result += detections[i][0]
                else:
                    result = detections[0][0]
    return result


def get_all_index_fraction(list_fraction: list):
    result = []
    for item in list_fraction:
        result += list(range(item[1], item[2] + 1))

    return result


def is_next_label(previous_box, current_box):
    current_x, current_y, current_w, current_h = current_box
    previous_x, previous_y, previous_w, previous_h = previous_box

    right_previous = previous_x + previous_w
    left_current = current_x - current_h

    if left_current >= right_previous - previous_h * next_label_threshold:
        return False
    return True


def is_super_script(previous_box, current_box):
    current_x, current_y, current_w, current_h = current_box
    previous_x, previous_y, previous_w, previous_h = previous_box
    bottom_current = current_y + current_h / 2
    top_previous = previous_y - previous_h / 2
    #     2  current
    #    3   previous
    if bottom_current <= top_previous + previous_h * superscript_threshold:
        return True
    return False


def is_in_line(previous_box, current_box):
    if is_super_script(previous_box, current_box):
        return False
    if is_sub_script(previous_box, current_box):
        return False
    return True


def is_sub_script(previous_box, current_box):
    current_x, current_y, current_w, current_h = current_box
    previous_x, previous_y, previous_w, previous_h = previous_box
    top_current = current_y - current_h / 2
    bottom_previous = previous_y + previous_h / 2
    #   2    previous
    #    3   current
    if bottom_previous <= top_current + current_h * subscript_threshold:
        return True
    return False


def get_box_fraction(detections: list, begin: int, end: int) -> (int, int, int, int):
    begin_x, begin_y, begin_w, begin_h = detections[begin][2]

    left = begin_x - begin_w / 2
    right = begin_x + begin_w / 2
    top = begin_y - begin_h / 2
    bottom = begin_y + begin_h / 2

    for i in range(begin + 1, end + 1):
        current_x, current_y, current_w, current_h = detections[i][2]
        current_top = current_y - current_h / 2
        current_bottom = current_y + current_h / 2
        current_right = current_x + begin_w / 2
        if current_top < top:
            top = current_top
        if current_bottom > bottom:
            bottom = current_bottom
        if current_right > right:
            right = current_right

    w = right - left
    h = bottom - top
    x = left + w / 2
    y = top + h / 2
    return x, y, w, h


def get_exponent(detections: list, index: int, list_all_fraction: list) -> (str, int):
    end_of_script = start_of_script = index
    length = len(detections)
    list_exponent = [detections[index]]
    # get subscript or superscript
    # Ex: 2^11 => script = 11
    while True:
        if end_of_script >= length - 1:
            break

        previous_box = detections[start_of_script][2]
        current_box = detections[end_of_script + 1][2]
        if is_sub_script(previous_box, current_box) and (end_of_script + 1) not in list_all_fraction:
            current_label = detections[end_of_script + 1][0]
            if is_comma(current_label) and end_of_script + 2 <= length - 1:
                next_box = detections[end_of_script + 2][2]
                if not is_in_line(previous_box, next_box):
                    break
            else:
                break

        end_of_script += 1
        list_exponent.append(detections[end_of_script])

    script = convert_from_objects_to_string(list_exponent)
    return script, end_of_script


def normalize_expression(polynomial: str) -> str:
    result = polynomial[0]
    for i in range(1, len(polynomial)):
        current_label = polynomial[i]
        previous_label = polynomial[i - 1]
        # add *
        # Ex: 2x => 2*x
        if should_add_multiply_operator(previous_label, current_label):
            result += "*"
        result += polynomial[i]
    return result.replace(".", "*").replace(",", ".")


def should_add_multiply_operator(previous_label: str, current_label: str) -> bool:
    # "2x" => "2*x"
    if previous_label.isdigit() and current_label.isalpha():
        return True
    # "x2" => "x*2"
    if previous_label.isalpha() and current_label.isdigit():
        return True
    # "xx" => "x*x"
    if previous_label.isalpha() and current_label.isalpha():
        return True
    # "2(" => "2*("
    if previous_label.isdigit() and is_opening_bracket(current_label):
        return True
    # "x(" => "x*("
    if previous_label.isalpha() and is_opening_bracket(current_label):
        return True
    # ")(" => ")*("
    if is_closing_bracket(previous_label) and is_opening_bracket(current_label):
        return True
    # ")2" => ")*2"
    if is_closing_bracket(previous_label) and current_label.isdigit():
        return True
    # ")x" => ")*x"
    if is_closing_bracket(previous_label) and current_label.isalpha():
        return True

    return False


def should_add_bracket(left_token: str, right_token: str) -> bool:
    if right_token.isalpha():
        return True
    if right_token in ["*", ":", "/"]:
        return True
    if is_opening_bracket(right_token):
        return True
    if is_closing_bracket(left_token):
        return True
    if left_token in [":", "/"]:
        return True

    return False


def is_operators(token: str) -> bool:
    return token in ["+", "*", "/", "=", "-", "^", ":"]


def is_comma(token: str) -> bool:
    return token in [",", "."]


def is_closing_bracket(token: str) -> bool:
    return token in ["}", "]", ")"]


def is_opening_bracket(token: str) -> bool:
    return token in ["{", "[", "("]


def get_all_fractions(detections: list) -> list:
    length = len(detections)
    list_fractions = []
    list_unique_min_index = []
    removed_list = []
    # get all fraction by '-' token
    for i in range(0, length):
        label = detections[i][0]
        if label == '-':
            numerator, denominator, min_index, max_index = get_all_numerator_and_denominator(detections, i)
            if numerator != '':
                fraction = f'{numerator}/{denominator}'
                list_fractions.append((fraction, min_index, max_index))

    # add the sub fraction in supper fraction to removed_list
    for item in list_fractions:
        if item not in removed_list:
            between_item = []
            for x in list_fractions:
                if item[1] <= x[1] and x[2] <= item[2] and x not in removed_list and x != item:
                    between_item.append(x)
            removed_list = removed_list + between_item

    # remove fraction in removed_list
    for item in list_fractions:
        if item not in removed_list:
            list_unique_min_index.append(item)

    return list_unique_min_index


def get_all_numerator_and_denominator(detections: list, index_of_fraction_sign: int) -> (str, str, list):
    length = len(detections)
    fraction_sign_x, fraction_sign_y, fraction_sign_w, fraction_sign_h = detections[index_of_fraction_sign][2]
    left_fraction_sign = fraction_sign_x - fraction_sign_w / 2
    right_fraction_sign = fraction_sign_x + fraction_sign_w / 2

    numerator = ""
    denominator = ""
    numerator_detections = []
    denominator_detections = []
    min_index = index_of_fraction_sign
    max_index = index_of_fraction_sign
    for i in range(0, length):
        if i != index_of_fraction_sign:
            current_x, current_y, current_w, current_h = detections[i][2]

            if current_y < fraction_sign_y and left_fraction_sign <= current_x <= right_fraction_sign:
                if i < min_index:
                    min_index = i
                if i > max_index:
                    max_index = i
                numerator_detections.append(detections[i])

            if current_y > fraction_sign_y and left_fraction_sign <= current_x <= right_fraction_sign:
                if i < min_index:
                    min_index = i
                if i > max_index:
                    max_index = i
                denominator_detections.append(detections[i])

    if len(numerator_detections) != 0 and len(denominator_detections) != 0:
        numerator = convert_from_objects_to_string(numerator_detections)
        denominator = convert_from_objects_to_string(denominator_detections)

    if re.search('[+*/=^-]', numerator):
        numerator = f'({numerator})'

    if re.search('[+*/=^-]', denominator):
        denominator = f'({denominator})'

    return numerator, denominator, min_index, max_index


def convert_infix_to_latex(polynomial: str) -> str:
    polynomial = normalize_expression(polynomial)
    polynomial = polynomial.replace("^", "**")
    result = ""
    list_polynomial = polynomial.split("=")
    length = len(list_polynomial)
    for i in range(0, length):
        polynomial = pytexit.py2tex(list_polynomial[i], print_latex=False, print_formula=False)
        end = len(polynomial) - 2
        if i == 0:
            result = f"{polynomial[2:end]}"
        else:
            result = f"{result}={polynomial[2:end]}"

    return f'$${result}$$'


# print(pytexit.py2tex("2*x**2-3*(x+1)"))
# print(convert_infix_to_latex("2*x**2-3*(x+1)"))


class Tests(unittest.TestCase):

    def test_convert_from_object_to_string_fractions(self):
        # frac
        detections = [
            ("1", 0.4, (0.065308, 0.124321, 0.031348, 0.094463)),
            ("-", 0.4, (0.073145, 0.179696, 0.060606, 0.016287)),
            ("2", 0.4, (0.073406, 0.228556, 0.040230, 0.066232)),
            ("x", 0.4, (0.144462, 0.185125, 0.046499, 0.066232)),
            ("2", 0.4, (0.189655, 0.143865, 0.036573, 0.064061)),
            ("-", 0.4, (0.238245, 0.193811, 0.034483, 0.040174)),
            ("1", 0.4, (0.297806, 0.190554, 0.020899, 0.094463)),
            ("+", 0.4, (0.348746, 0.192182, 0.049634, 0.089034)),
            ("x", 0.4, (0.428945, 0.122150, 0.045977, 0.051031)),
            ("-", 0.4, (0.437827, 0.173724, 0.107628, 0.032573)),
            ("3", 0.4, (0.437565, 0.247557, 0.048589, 0.102063)),
            ("2", 0.4, (0.467085, 0.096091, 0.036573, 0.051031)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "(1/2)x^2-1+(x^2)/3")

        # frac2
        detections = [
            ("x", 0.4, (0.022205, 0.132465, 0.031870, 0.056460)),
            ("2", 0.4, (0.042059, 0.095548, 0.013062, 0.043431)),
            ("2", 0.4, (0.084117, 0.207926, 0.032393, 0.079262)),
            ("+", 0.4, (0.052508, 0.141694, 0.014107, 0.038002)),
            ("-", 0.4, (0.090125, 0.146580, 0.046499, 0.017372)),
            ("1", 0.4, (0.093783, 0.090662, 0.020376, 0.077090)),
            ("x", 0.4, (0.146813, 0.135722, 0.040752, 0.060803)),
            ("-", 0.4, (0.217346, 0.137351, 0.033438, 0.022801)),
            ("x", 0.4, (0.307732, 0.080347, 0.031348, 0.049946)),
            ("2", 0.4, (0.330460, 0.046688, 0.014107, 0.039088)),
            ("3", 0.4, (0.308255, 0.192725, 0.029258, 0.053203)),
            ("2", 0.4, (0.306949, 0.265472, 0.028736, 0.057546)),
            ("-", 0.4, (0.307210, 0.227470, 0.039707, 0.018458)),
            ("x", 0.4, (0.355016, 0.223670, 0.022466, 0.039088)),
            ("3", 0.4, (0.372257, 0.194897, 0.016196, 0.044517)),
            ("-", 0.4, (0.405956, 0.220413, 0.020899, 0.010858)),
            ("1", 0.4, (0.432602, 0.210098, 0.011494, 0.053203)),
            ("-", 0.4, (0.373041, 0.141694, 0.201672, 0.022801)),
            ("+", 0.4, (0.372780, 0.080347, 0.038140, 0.049946)),
            ("1", 0.4, (0.410136, 0.045603, 0.010449, 0.049946)),
            ("x", 0.4, (0.411703, 0.102063, 0.018809, 0.032573)),
            ("-", 0.4, (0.413532, 0.075461, 0.021421, 0.009772)),
            ("x", 0.4, (0.439133, 0.069490, 0.022466, 0.032573)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "x^2+(1/2)x-(x^2+(1/x)x)/((3/2)x^3-1)")

        # frac3
        detections = [
            ("3", 0.4, (0.143678, 0.090662, 0.036573, 0.074919)),
            ("+", 0.4, (0.187304, 0.092834, 0.022466, 0.057546)),
            ("x", 0.4, (0.227011, 0.097720, 0.029781, 0.045603)),
            ("2", 0.4, (0.249478, 0.063518, 0.020376, 0.035831)),
            ("-", 0.4, (0.289969, 0.087405, 0.025078, 0.022801)),
            ("1", 0.4, (0.340387, 0.035288, 0.018286, 0.064061)),
            ("-", 0.4, (0.337513, 0.073833, 0.048067, 0.015201)),
            ("2", 0.4, (0.339864, 0.110749, 0.036050, 0.056460)),
            ("x", 0.4, (0.375914, 0.077090, 0.028736, 0.049946)),
            ("-", 0.4, (0.280303, 0.159066, 0.329676, 0.033659)),
            ("3", 0.4, (0.125653, 0.199240, 0.041275, 0.061889)),
            ("-", 0.4, (0.130617, 0.231813, 0.054336, 0.018458)),
            ("x", 0.4, (0.126698, 0.274701, 0.026646, 0.030402)),
            ("3", 0.4, (0.145246, 0.254072, 0.012539, 0.026059)),
            ("+", 0.4, (0.202194, 0.233442, 0.024033, 0.039088)),
            ("2", 0.4, (0.241902, 0.237242, 0.025078, 0.066232)),
            ("x", 0.4, (0.274817, 0.245928, 0.028213, 0.048860)),
            ("-", 0.4, (0.313741, 0.242671, 0.019331, 0.020630)),
            ("3", 0.4, (0.345350, 0.236699, 0.031348, 0.060803)),
            ("+", 0.4, (0.379310, 0.237785, 0.025078, 0.039088)),
            ("5", 0.4, (0.405956, 0.236156, 0.025078, 0.055375)),
            ("x", 0.4, (0.430773, 0.242671, 0.027691, 0.055375)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "(3+x^2-(1/2)x)/(3/(x^3)+2x-3+5x)")

        # frac4
        detections = [
            ("1", 0.4, (0.268128, 0.217224, 0.091062, 0.218509)),
            ("+", 0.4, (0.434233, 0.235219, 0.156830, 0.197943)),
            ("a", 0.4, (0.612985, 0.150386, 0.086003, 0.110540)),
            ("b", 0.4, (0.612985, 0.339332, 0.072513, 0.154242)),
            ("-", 0.4, (0.611298, 0.237789, 0.092749, 0.028278)),
            ("-", 0.4, (0.447723, 0.449871, 0.693086, 0.041131)),
            ("1", 0.4, (0.153457, 0.641388, 0.087690, 0.218509)),
            ("+", 0.4, (0.319562, 0.665810, 0.136594, 0.221080)),
            ("1", 0.4, (0.610455, 0.555270, 0.070826, 0.149100)),
            ("-", 0.4, (0.610455, 0.661954, 0.323777, 0.038560)),
            ("1", 0.4, (0.494098, 0.785347, 0.067454, 0.161954)),
            ("+", 0.4, (0.593592, 0.800771, 0.111298, 0.161954)),
            ("1", 0.4, (0.707420, 0.727506, 0.045531, 0.107969)),
            ("-", 0.4, (0.709106, 0.799486, 0.086003, 0.030848)),
            ("a", 0.4, (0.706577, 0.888175, 0.070826, 0.095116))
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "(1+a/b)/(1+1/(1+1/a))")

        # frac5
        detections = [
            ("3", 0.4, (0.079154, 0.087948, 0.021421, 0.067318)),
            ("x", 0.4, (0.105799, 0.099349, 0.025601, 0.044517)),
            ("-", 0.4, (0.093260, 0.133008, 0.090387, 0.016287)),
            ("3", 0.4, (0.093260, 0.173724, 0.029781, 0.062975)),
            ("-", 0.4, (0.169279, 0.135722, 0.025078, 0.017372)),
            ("1", 0.4, (0.204284, 0.128122, 0.016719, 0.054289)),
            ("+", 0.4, (0.236416, 0.128664, 0.018286, 0.029316)),
            ("3", 0.4, (0.254702, 0.067861, 0.023511, 0.064061)),
            ("+", 0.4, (0.281870, 0.061346, 0.021421, 0.040174)),
            ("2", 0.4, (0.318443, 0.064061, 0.030825, 0.062975)),
            ("x", 0.4, (0.355799, 0.070033, 0.028213, 0.042345)),
            ("2", 0.4, (0.381661, 0.039631, 0.018286, 0.040174)),
            ("+", 0.4, (0.406217, 0.070575, 0.023511, 0.030402)),
            ("3", 0.4, (0.439394, 0.031488, 0.017764, 0.045603)),
            ("-", 0.4, (0.437565, 0.054832, 0.027691, 0.014115)),
            ("5", 0.4, (0.440178, 0.077633, 0.019331, 0.040174)),
            ("-", 0.4, (0.349791, 0.129207, 0.194880, 0.019544)),
            ("1", 0.4, (0.264368, 0.175353, 0.017764, 0.048860)),
            ("-", 0.4, (0.261233, 0.206840, 0.040752, 0.014115)),
            ("6", 0.4, (0.260711, 0.242128, 0.017764, 0.056460)),
            ("-", 0.4, (0.320794, 0.210641, 0.020899, 0.015201)),
            ("5", 0.4, (0.371735, 0.194354, 0.031870, 0.065147)),
            ("+", 0.4, (0.481452, 0.126493, 0.027691, 0.055375)),
            ("1", 0.4, (0.554859, 0.092834, 0.015674, 0.072747)),
            ("-", 0.4, (0.551463, 0.136265, 0.038140, 0.020630)),
            ("6", 0.4, (0.545455, 0.178067, 0.021944, 0.054289)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "3x/3-1+(3+2x^2+3/5)/(1/6-5)+1/6")

        # frac6
        detections = [
            ("m", 0.4, (0.127482, 0.135722, 0.052247, 0.036916)),
            ("x", 0.4, (0.197231, 0.090119, 0.047544, 0.056460)),
            ("-", 0.4, (0.193312, 0.139522, 0.077325, 0.031488)),
            ("2", 0.4, (0.189916, 0.204669, 0.062173, 0.092291)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "mx/2")

        # frac6
        detections = [
            ("m", 0.4, (0.127482, 0.135722, 0.052247, 0.036916)),
            ("x", 0.4, (0.197231, 0.090119, 0.047544, 0.056460)),
            ("-", 0.4, (0.193312, 0.139522, 0.077325, 0.031488)),
            ("2", 0.4, (0.189916, 0.204669, 0.062173, 0.092291)),
            (":", 0.4, (0.150731, 0.134093, 0.004702, 0.046688)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "m:(x/2)")

        detections = [
            ("m", 0.4, (0.127482, 0.135722, 0.052247, 0.036916)),
            ("x", 0.4, (0.197231, 0.090119, 0.047544, 0.056460)),
            ("-", 0.4, (0.193312, 0.139522, 0.077325, 0.031488)),
            ("2", 0.4, (0.189916, 0.204669, 0.062173, 0.092291)),
            ("/", 0.4, (0.150731, 0.134093, 0.004702, 0.046688)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "m/(x/2)")

        detections = [
            ("m", 0.4, (0.127482, 0.135722, 0.052247, 0.036916)),
            ("x", 0.4, (0.197231, 0.090119, 0.047544, 0.056460)),
            ("-", 0.4, (0.193312, 0.139522, 0.077325, 0.031488)),
            ("2", 0.4, (0.189916, 0.204669, 0.062173, 0.092291)),
            (".", 0.4, (0.150731, 0.134093, 0.004702, 0.046688)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "m.x/2")

        detections = [
            ("m", 0.4, (0.127482, 0.135722, 0.052247, 0.036916)),
            ("x", 0.4, (0.197231, 0.090119, 0.047544, 0.056460)),
            ("-", 0.4, (0.214995, 0.138979, 0.120690, 0.030402)),
            ("2", 0.4, (0.189916, 0.204669, 0.062173, 0.092291)),
            (".", 0.4, (0.150731, 0.134093, 0.004702, 0.046688)),
            ("+", 0.4, (0.234065, 0.092834, 0.013584, 0.038002)),
            ("7", 0.4, (0.254702, 0.093377, 0.014107, 0.0521172)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "m.(x+7)/2")

        detections = [
            ("m", 0.4, (0.127482, 0.135722, 0.052247, 0.036916)),
            ("x", 0.4, (0.197231, 0.090119, 0.047544, 0.056460)),
            ("-", 0.4, (0.214995, 0.138979, 0.120690, 0.030402)),
            ("2", 0.4, (0.189916, 0.204669, 0.062173, 0.092291)),
            (":", 0.4, (0.150731, 0.134093, 0.004702, 0.046688)),
            ("+", 0.4, (0.234065, 0.092834, 0.013584, 0.038002)),
            ("7", 0.4, (0.254702, 0.093377, 0.014107, 0.0521172)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "m:((x+7)/2)")

        # frac7
        detections = [
            ("(", 0.4, (0.042842, 0.232356, 0.084639, 0.258415)),
            ("x", 0.4, (0.069488, 0.251900, 0.062696, 0.112921)),
            ("-", 0.4, (0.125131, 0.276330, 0.027691, 0.027144)),
            ("2", 0.4, (0.187827, 0.254615, 0.055904, 0.131379)),
            (")", 0.4, (0.254180, 0.266558, 0.068443, 0.255157)),
            ("m", 0.4, (0.373824, 0.144408, 0.099791, 0.123779)),
            ("-", 0.4, (0.380878, 0.237242, 0.156740, 0.051031)),
            ("3", 0.4, (0.373824, 0.350163, 0.067398, 0.148751)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "(x-2)(m/3)")

        # frac7
        detections = [
            ("(", 0.4, (0.042842, 0.232356, 0.084639, 0.258415)),
            ("x", 0.4, (0.069488, 0.251900, 0.062696, 0.112921)),
            ("-", 0.4, (0.125131, 0.276330, 0.027691, 0.027144)),
            ("2", 0.4, (0.187827, 0.254615, 0.055904, 0.131379)),
            (")", 0.4, (0.254180, 0.266558, 0.068443, 0.255157)),
            ("m", 0.4, (0.373824, 0.144408, 0.099791, 0.123779)),
            ("-", 0.4, (0.380878, 0.237242, 0.156740, 0.051031)),
            ("3", 0.4, (0.373824, 0.350163, 0.067398, 0.148751)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "(x-2)(m/3)")

        # frac8s
        detections = [
            ("1", 0.4, (0.192529, 0.098806, 0.047544, 0.110749)),
            ("-", 0.4, (0.190178, 0.167210, 0.071055, 0.026059)),
            ("2", 0.4, (0.188088, 0.239957, 0.041797, 0.082519)),
            ("2", 0.4, (0.267764, 0.062432, 0.060084, 0.094463)),
            (")", 0.4, (0.235110, 0.161781, 0.018809, 0.247557)),
            ("(", 0.4, (0.135841, 0.167752, 0.024033, 0.266015)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "(1/2)^2")

        # frac9
        detections = [
            ("3", 0.4, (0.057210, 0.279587, 0.061129, 0.122693)),
            ("+", 0.4, (0.109457, 0.286102, 0.028736, 0.051031)),
            ("1", 0.4, (0.182863, 0.188382, 0.031348, 0.111835)),
            ("-", 0.4, (0.181557, 0.277416, 0.071578, 0.033659)),
            ("2", 0.4, (0.180773, 0.343648, 0.066876, 0.114007)),
            ("x", 0.4, (0.259404, 0.125407, 0.049634, 0.090119)),
            ("x", 0.4, (0.313480, 0.061889, 0.045977, 0.067318)),
            ("+", 0.4, (0.349791, 0.059718, 0.016196, 0.041260)),
            ("1", 0.4, (0.382445, 0.029859, 0.009404, 0.048860)),
            ("-", 0.4, (0.381139, 0.052117, 0.035005, 0.026059)),
            ("2", 0.4, (0.382184, 0.092834, 0.032915, 0.055375)),
            ("x", 0.4, (0.432341, 0.058632, 0.040230, 0.056460)),
            ("-", 0.4, (0.499478, 0.110749, 0.032393, 0.030402)),
            ("1", 0.4, (0.556426, 0.096634, 0.028213, 0.084691)),
            (")", 0.4, (0.225183, 0.267644, 0.013584, 0.337676)),
            ("(", 0.4, (0.136886, 0.271987, 0.013584, 0.348534)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "3+(1/2)^(x^(x+(1/2)x)-1)")

        # frac9
        detections = [
            ("3", 0.4, (0.057210, 0.279587, 0.061129, 0.122693)),
            ("+", 0.4, (0.109457, 0.286102, 0.028736, 0.051031)),
            ("1", 0.4, (0.182863, 0.188382, 0.031348, 0.111835)),
            ("-", 0.4, (0.181557, 0.277416, 0.071578, 0.033659)),
            ("2", 0.4, (0.180773, 0.343648, 0.066876, 0.114007)),
            ("x", 0.4, (0.259404, 0.125407, 0.049634, 0.090119)),
            ("x", 0.4, (0.313480, 0.061889, 0.045977, 0.067318)),
            ("+", 0.4, (0.349791, 0.059718, 0.016196, 0.041260)),
            ("1", 0.4, (0.382445, 0.029859, 0.009404, 0.048860)),
            ("-", 0.4, (0.381139, 0.052117, 0.035005, 0.026059)),
            ("2", 0.4, (0.382184, 0.092834, 0.032915, 0.055375)),
            ("x", 0.4, (0.432341, 0.058632, 0.040230, 0.056460)),
            ("-", 0.4, (0.499478, 0.110749, 0.032393, 0.030402)),
            ("1", 0.4, (0.556426, 0.096634, 0.028213, 0.084691)),
            (")", 0.4, (0.225183, 0.267644, 0.013584, 0.337676)),
            ("(", 0.4, (0.136886, 0.271987, 0.013584, 0.348534)),
            ("(", 0.4, (0.287879, 0.064604, 0.011494, 0.090119)),
            (")", 0.4, (0.459770, 0.059175, 0.007315, 0.096634)),
            ("3", 0.4, (0.475183, 0.020087, 0.017241, 0.038002)),
        ]

        self.assertEqual(convert_from_objects_to_string(detections), "3+(1/2)^(x^((x+(1/2)x)^3)-1)")

    def test_convert_from_objects_to_string(self):
        detections = [("=", 0.4, (0.398438, 0.509766, 0.312500, 0.097656)),
                      ("x", 0.4, (0.720703, 0.500000, 0.222656, 0.250000)),
                      ("2", 0.4, (0.921875, 0.423828, 0.140625, 0.128906)),
                      ("4", 0.4, (0.080078, 0.529297, 0.152344, 0.269531))]
        self.assertEqual(convert_from_objects_to_string(detections), "4=x^2")

        # IMG_2151_1.png
        detections = [("2", 0.4, (0.081727, 0.655028, 0.109483, 0.388268)),
                      ("x", 0.4, (0.173863, 0.712291, 0.070162, 0.268156)),
                      ("2", 0.4, (0.237471, 0.512570, 0.053971, 0.192737)),
                      ("-", 0.4, (0.361218, 0.639665, 0.062452, 0.139665)),
                      ("3", 0.4, (0.459522, 0.553073, 0.074017, 0.329609)),
                      ("(", 0.4, (0.533539, 0.560056, 0.049345, 0.455307)),
                      ("x", 0.4, (0.597533, 0.574022, 0.055513, 0.287709)),
                      ("+", 0.4, (0.669237, 0.539106, 0.050887, 0.212291)),
                      ("1", 0.4, (0.740170, 0.519553, 0.041635, 0.307263)),
                      (")", 0.4, (0.792213, 0.501397, 0.040864, 0.494413)),
                      ("=", 0.4, (0.874711, 0.526536, 0.056284, 0.203911)),
                      ("0", 0.4, (0.941789, 0.467877, 0.060910, 0.343575)),
                      ]
        self.assertEqual(convert_from_objects_to_string(detections), "2x^2-3(x+1)=0")

        detections = [("=", 0.4, (0.398438, 0.509766, 0.312500, 0.097656)),
                      ("x", 0.4, (0.720703, 0.500000, 0.222656, 0.250000)),
                      ("2", 0.4, (0.921875, 0.423828, 0.140625, 0.228906)),
                      ("4", 0.4, (0.080078, 0.529297, 0.152344, 0.269531))]
        self.assertEqual(convert_from_objects_to_string(detections), "4=x2")

        # test.png
        detections = [("(", 0.4, (0.014786, 0.205150, 0.028478, 0.290698)),
                      ("x", 0.4, (0.052300, 0.209302, 0.055312, 0.149502)),
                      ("+", 0.4, (0.097755, 0.195183, 0.029025, 0.084718)),
                      ("1", 0.4, (0.135268, 0.198505, 0.032859, 0.161130)),
                      (")", 0.4, (0.164841, 0.213455, 0.035049, 0.313953)),
                      ("(", 0.4, (0.212212, 0.217608, 0.035597, 0.275748)),
                      ("x", 0.4, (0.276287, 0.237542, 0.068456, 0.192691)),
                      ("-", 0.4, (0.328861, 0.205980, 0.047645, 0.076412)),
                      ("2", 0.4, (0.379518, 0.197674, 0.049288, 0.152824)),
                      (")", 0.4, (0.416758, 0.186047, 0.036145, 0.212625)),
                      (".", 0.4, (0.437021, 0.248339, 0.012048, 0.064784)),
                      ("2", 0.4, (0.483023, 0.189369, 0.072289, 0.209302)),
                      (",", 0.4, (0.526287, 0.276578, 0.018620, 0.051495)),
                      ("5", 0.4, (0.544633, 0.186877, 0.022453, 0.187708)),
                      ("-", 0.4, (0.566539, 0.188538, 0.029025, 0.041528)),
                      ("3", 0.4, (0.625685, 0.196013, 0.071742, 0.219269)),
                      ("(", 0.4, (0.675794, 0.191030, 0.035049, 0.199336)),
                      ("x", 0.4, (0.701260, 0.230066, 0.038883, 0.094684)),
                      ("2", 0.4, (0.722892, 0.144518, 0.031763, 0.099668)),
                      ("-", 0.4, (0.740416, 0.205980, 0.029573, 0.059801)),
                      ("1", 0.4, (0.771632, 0.183555, 0.015334, 0.141196)),
                      (")", 0.4, (0.793812, 0.190199, 0.035597, 0.224252)),
                      ("2", 0.4, (0.848302, 0.193522, 0.082147, 0.280731)),
                      ("=", 0.4, (0.922508, 0.229236, 0.073932, 0.152824)),
                      ("0", 0.4, (0.978094, 0.226744, 0.043812, 0.227575)),
                      ]
        self.assertEqual(convert_from_objects_to_string(detections), "(x+1)(x-2).2,5-3(x^2-1)2=0")

    def test_convert_from_objects_to_string_with_exponential_polynomial(self):
        # Untitled.png
        detections = [("x", 0.4, (0.138007, 0.516611, 0.147864, 0.199336)),
                      ("1", 0.4, (0.230011, 0.382890, 0.024096, 0.234219)),
                      ("1", 0.4, (0.261227, 0.382890, 0.030668, 0.237542)),
                      ("+", 0.4, (0.343373, 0.524917, 0.043812, 0.156146)),
                      ("2", 0.4, (0.426068, 0.502492, 0.044907, 0.297342)),
                      ("x", 0.4, (0.484392, 0.566445, 0.038883, 0.199336)),
                      ("x", 0.4, (0.543264, 0.417774, 0.040526, 0.137874)),
                      ("+", 0.4, (0.606243, 0.421927, 0.037240, 0.106312)),
                      ("1", 0.4, (0.661008, 0.418605, 0.040526, 0.205980))
                      ]
        self.assertEqual(convert_from_objects_to_string(detections), "x^11+2x^(x+1)")
        # Untitled.png
        detections = [("x", 0.4, (0.138007, 0.516611, 0.147864, 0.199336)),
                      ("1", 0.4, (0.230011, 0.382890, 0.024096, 0.234219)),
                      ("1", 0.4, (0.261227, 0.382890, 0.030668, 0.237542)),
                      ("+", 0.4, (0.343373, 0.524917, 0.043812, 0.156146)),
                      ("2", 0.4, (0.426068, 0.502492, 0.044907, 0.297342)),
                      ("x", 0.4, (0.484392, 0.566445, 0.038883, 0.199336)),
                      ("x", 0.4, (0.543264, 0.417774, 0.040526, 0.137874)),
                      ("+", 0.4, (0.606243, 0.421927, 0.037240, 0.106312)),
                      ("1", 0.4, (0.661008, 0.418605, 0.040526, 0.205980)),
                      ("+", 0.4, (0.720975, 0.539867, 0.042169, 0.156146)),
                      ("2", 0.4, (0.795728, 0.510797, 0.049288, 0.284053)),
                      ("2", 0.4, (0.853231, 0.343023, 0.030668, 0.167774)),
                      ("2", 0.4, (0.889376, 0.235050, 0.021906, 0.147841))
                      ]
        self.assertEqual(convert_from_objects_to_string(detections), "x^11+2x^(x+1)+2^2^2")
        # Untitled2.png
        detections = [("x", 0.4, (0.138007, 0.516611, 0.147864, 0.199336)),
                      ("1", 0.4, (0.230011, 0.382890, 0.024096, 0.234219)),
                      ("1", 0.4, (0.261227, 0.382890, 0.030668, 0.237542)),
                      ("+", 0.4, (0.360350, 0.501661, 0.072289, 0.149502)),
                      ("x", 0.4, (0.455641, 0.493355, 0.082147, 0.139535)),
                      ("x", 0.4, (0.512596, 0.400332, 0.036145, 0.099668)),
                      ("2", 0.4, (0.545181, 0.352159, 0.031216, 0.093023)),
                      ("+", 0.4, (0.581599, 0.380399, 0.027382, 0.076412)),
                      ("2", 0.4, (0.612815, 0.376246, 0.029573, 0.111296)),
                      ("x", 0.4, (0.641292, 0.403654, 0.031763, 0.083056)),
                      ("+", 0.4, (0.672234, 0.389535, 0.032311, 0.071429)),
                      ("1", 0.4, (0.699069, 0.382890, 0.014786, 0.114618)),
                      ]
        self.assertEqual(convert_from_objects_to_string(detections), "x^11+x^(x^2+2x+1)")
        # Untitled2.png
        detections = [
            ("x", 0.4, (0.455641, 0.493355, 0.082147, 0.139535)),
            ("x", 0.4, (0.512596, 0.400332, 0.036145, 0.099668)),
            ("2", 0.4, (0.544907, 0.342193, 0.030668, 0.112957)),
            ("+", 0.4, (0.582968, 0.381229, 0.024644, 0.074751)),
            ("2", 0.4, (0.612815, 0.376246, 0.029573, 0.111296)),
            ("x", 0.4, (0.641292, 0.403654, 0.031763, 0.083056)),
            ("+", 0.4, (0.672234, 0.389535, 0.032311, 0.071429)),
            ("1", 0.4, (0.699069, 0.382890, 0.014786, 0.114618)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "x^(x^2+2x+1)")

        # Untitled3.png
        detections = [
            ("x", 0.4, (0.041895, 0.427741, 0.050931, 0.121262)),
            ("y", 0.4, (0.092552, 0.338040, 0.043812, 0.091362)),
            ("z", 0.4, (0.127327, 0.275748, 0.035597, 0.093023)),
            ("+", 0.4, (0.160460, 0.274917, 0.024096, 0.078073)),
            ("2", 0.4, (0.188938, 0.257475, 0.027382, 0.099668)),
            ("-", 0.4, (0.236857, 0.317276, 0.031216, 0.066445)),
            ("3", 0.4, (0.275465, 0.316445, 0.041621, 0.124585)),
            ("+", 0.4, (0.321742, 0.308970, 0.046550, 0.109635)),
            ("3", 0.4, (0.368291, 0.313953, 0.038883, 0.156146)),
            ("x", 0.4, (0.406900, 0.344684, 0.042716, 0.114618)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "x^(y^(z+2)-3+3x)")
        # Untitled5.png
        detections = [
            ("x", 0.4, (0.180997, 0.372924, 0.081599, 0.167774)),
            ("y", 0.4, (0.242881, 0.265781, 0.033406, 0.146179)),
            ("2", 0.4, (0.270537, 0.161130, 0.031763, 0.102990)),
            ("+", 0.4, (0.306681, 0.242525, 0.032859, 0.059801)),
            ("3", 0.4, (0.354053, 0.211794, 0.043264, 0.134551)),
            ("y", 0.4, (0.398686, 0.247508, 0.027382, 0.119601)),
            ("+", 0.4, (0.432640, 0.240033, 0.027382, 0.091362)),
            ("1", 0.4, (0.466867, 0.216777, 0.025739, 0.124585)),
            ("-", 0.4, (0.504929, 0.361296, 0.040526, 0.048173)),
            ("3", 0.4, (0.561062, 0.348837, 0.044359, 0.146179)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "x^(y^2+3y+1)-3")

        # exponent.png
        detections = [
            ("x", 0.4, (0.065831, 0.191097, 0.072100, 0.080347)),
            ("1", 0.4, (0.113636, 0.061889, 0.018286, 0.062975)),
            ("-", 0.4, (0.115726, 0.099349, 0.032915, 0.009772)),
            ("2", 0.4, (0.114681, 0.135722, 0.030825, 0.058632)),
            ("x", 0.4, (0.154911, 0.106406, 0.031870, 0.054289)),
            ("2", 0.4, (0.188871, 0.071661, 0.023511, 0.041260)),
            ("-", 0.4, (0.220742, 0.092834, 0.015152, 0.020630)),
            ("3", 0.4, (0.269854, 0.047774, 0.022466, 0.054289)),
            ("-", 0.4, (0.267764, 0.086862, 0.048589, 0.023887)),
            ("2", 0.4, (0.263062, 0.119978, 0.043365, 0.035831)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "x^((1/2)x^2-3/2)")

        # exponent3
        detections = [
            ("x", 0.4, (0.264368, 0.152009, 0.072100, 0.093377)),
            ("3", 0.4, (0.323145, 0.065147, 0.041275, 0.089034)),
            ("-", 0.4, (0.371735, 0.062975, 0.023511, 0.023887)),
            ("x", 0.4, (0.421630, 0.026059, 0.032393, 0.041260)),
            ("-", 0.4, (0.425549, 0.054832, 0.048589, 0.022801)),
            ("2", 0.4, (0.423459, 0.092834, 0.040230, 0.057546)),
            ("-", 0.4, (0.381923, 0.258415, 0.342738, 0.047774)),
            ("x", 0.4, (0.261755, 0.387622, 0.062696, 0.082519)),
            ("2", 0.4, (0.299373, 0.347991, 0.027168, 0.057546)),
            ("+", 0.4, (0.343783, 0.375679, 0.035528, 0.067318)),
            ("1", 0.4, (0.394201, 0.346363, 0.032915, 0.104235)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "(x^(3-x/2))/(x^2+1)")

        # dot.png
        detections = [
            ("2", 0.4, (0.157262, 0.230185, 0.044932, 0.080347)),
            ("2", 0.4, (0.199060, 0.177524, 0.030303, 0.051031)),
            (",", 0.4, (0.220481, 0.208469, 0.007315, 0.023887)),
            ("3", 0.4, (0.245037, 0.184039, 0.027168, 0.042345)),
            ("x", 0.4, (0.277168, 0.188925, 0.027691, 0.026059)),
            ("-", 0.4, (0.311912, 0.187839, 0.015674, 0.010858)),
            ("1", 0.4, (0.340909, 0.182953, 0.007837, 0.046688)),
            (".", 0.4, (0.354493, 0.201954, 0.005747, 0.010858)),
            ("x", 0.4, (0.384013, 0.185668, 0.032393, 0.039088)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "2^(2,3x-1.x)")

        # dot2.png
        detections = [
            ("2", 0.4, (0.232236, 0.268730, 0.064263, 0.100977)),
            ("3", 0.4, (0.297544, 0.180782, 0.030825, 0.053203)),
            (",", 0.4, (0.326803, 0.218241, 0.012017, 0.028230)),
            ("2", 0.4, (0.364159, 0.173724, 0.037618, 0.058632)),
            ("+", 0.4, (0.414316, 0.245928, 0.020899, 0.024973)),
            ("1", 0.4, (0.448015, 0.249186, 0.016196, 0.070575)),
            (".", 0.4, (0.470481, 0.280130, 0.010972, 0.015201)),
            ("2", 0.4, (0.511755, 0.245385, 0.041275, 0.071661)),
        ]
        self.assertEqual(convert_from_objects_to_string(detections), "2^3,2+1.2")

    def test_normalize_polynomial(self):
        polynomial = "4=x^2"
        self.assertEqual(normalize_expression(polynomial), "4=x^2")

        polynomial = "2x^2-3(x+1)=0"
        self.assertEqual(normalize_expression(polynomial), "2*x^2-3*(x+1)=0")

        polynomial = "4=x2"
        self.assertEqual(normalize_expression(polynomial), "4=x*2")

        polynomial = "(x+1)(x-2)2,5-3(x^2-1)2=0"
        self.assertEqual(normalize_expression(polynomial), "(x+1)*(x-2)*2.5-3*(x^2-1)*2=0")

        polynomial = "a(3-2x)b-3m"
        self.assertEqual(normalize_expression(polynomial), "a*(3-2*x)*b-3*m")

        polynomial = "(1/2)x^2-1+((x^2)/3)"
        self.assertEqual(normalize_expression(polynomial), "(1/2)*x^2-1+((x^2)/3)")

    def test_should_add_multiply_operator(self):
        self.assertTrue(should_add_multiply_operator("2", "x"))
        self.assertTrue(should_add_multiply_operator("x", "2"))
        self.assertTrue(should_add_multiply_operator("x", "x"))
        self.assertTrue(should_add_multiply_operator("2", "("))
        self.assertTrue(should_add_multiply_operator("x", "("))
        self.assertTrue(should_add_multiply_operator(")", "("))
        self.assertTrue(should_add_multiply_operator(")", "2"))
        self.assertTrue(should_add_multiply_operator(")", "x"))

    def test_get_exponent(self):
        # Untitled4.png
        detections = [
            ("x", 0.4, (0.118291, 0.325581, 0.058050, 0.116279)),
            ("1", 0.4, (0.152793, 0.239203, 0.018620, 0.116279)),
            ("2", 0.4, (0.181271, 0.235050, 0.033954, 0.114618)),
        ]
        self.assertEqual(get_exponent(detections, 1, []), ("12", 2))
        # Untitled5.png
        detections = [
            ("x", 0.4, (0.180997, 0.372924, 0.081599, 0.167774)),
            ("y", 0.4, (0.242881, 0.265781, 0.033406, 0.146179)),
            ("2", 0.4, (0.270537, 0.161130, 0.031763, 0.102990)),
            ("+", 0.4, (0.306681, 0.242525, 0.032859, 0.059801)),
            ("3", 0.4, (0.354053, 0.211794, 0.043264, 0.134551)),
            ("y", 0.4, (0.398686, 0.247508, 0.027382, 0.119601)),
            ("+", 0.4, (0.432640, 0.240033, 0.027382, 0.091362)),
            ("1", 0.4, (0.466867, 0.216777, 0.025739, 0.124585)),
            ("-", 0.4, (0.504929, 0.361296, 0.040526, 0.048173)),
            ("3", 0.4, (0.561062, 0.348837, 0.044359, 0.146179)),
        ]
        self.assertEqual(get_exponent(detections, 1, []), ("y^2+3y+1", 7))

    def test_get_all_numerator_and_denominator(self):
        # frac1
        detections = [
            ("1", 0.4, (0.065308, 0.124321, 0.031348, 0.094463)),
            ("-", 0.4, (0.073145, 0.179696, 0.060606, 0.016287)),
            ("2", 0.4, (0.073406, 0.228556, 0.040230, 0.066232)),
            ("x", 0.4, (0.144462, 0.185125, 0.046499, 0.066232)),
            ("2", 0.4, (0.189655, 0.143865, 0.036573, 0.064061)),
            ("-", 0.4, (0.238245, 0.193811, 0.034483, 0.040174)),
            ("1", 0.4, (0.297806, 0.190554, 0.020899, 0.094463)),
            ("+", 0.4, (0.348746, 0.192182, 0.049634, 0.089034)),
            ("x", 0.4, (0.428945, 0.122150, 0.045977, 0.051031)),
            ("-", 0.4, (0.437827, 0.173724, 0.107628, 0.032573)),
            ("3", 0.4, (0.437565, 0.247557, 0.048589, 0.102063)),
            ("2", 0.4, (0.467085, 0.096091, 0.036573, 0.051031)),
        ]
        detections.sort(key=lambda x: x[2][0] - x[2][2] / 2)

        self.assertEqual(get_all_numerator_and_denominator(detections, 0), ("1", "2", 0, 2))

        self.assertEqual(get_all_numerator_and_denominator(detections, 5), ("", "", 5, 5))

        self.assertEqual(get_all_numerator_and_denominator(detections, 8), ("(x^2)", "3", 8, 11))

        # frac2
        detections = [
            ("x", 0.4, (0.022205, 0.132465, 0.031870, 0.056460)),
            ("2", 0.4, (0.042059, 0.095548, 0.013062, 0.043431)),
            ("2", 0.4, (0.084117, 0.207926, 0.032393, 0.079262)),
            ("+", 0.4, (0.052508, 0.141694, 0.014107, 0.038002)),
            ("-", 0.4, (0.090125, 0.146580, 0.046499, 0.017372)),
            ("1", 0.4, (0.093783, 0.090662, 0.020376, 0.077090)),
            ("x", 0.4, (0.146813, 0.135722, 0.040752, 0.060803)),
            ("-", 0.4, (0.217346, 0.137351, 0.033438, 0.022801)),
            ("x", 0.4, (0.307732, 0.080347, 0.031348, 0.049946)),
            ("2", 0.4, (0.330460, 0.046688, 0.014107, 0.039088)),
            ("3", 0.4, (0.308255, 0.192725, 0.029258, 0.053203)),
            ("2", 0.4, (0.306949, 0.265472, 0.028736, 0.057546)),
            ("-", 0.4, (0.307210, 0.227470, 0.039707, 0.018458)),
            ("x", 0.4, (0.355016, 0.223670, 0.022466, 0.039088)),
            ("3", 0.4, (0.372257, 0.194897, 0.016196, 0.044517)),
            ("-", 0.4, (0.405956, 0.220413, 0.020899, 0.010858)),
            ("1", 0.4, (0.432602, 0.210098, 0.011494, 0.053203)),
            ("-", 0.4, (0.373041, 0.141694, 0.201672, 0.022801)),
            ("+", 0.4, (0.372780, 0.080347, 0.038140, 0.049946)),
            ("1", 0.4, (0.410136, 0.045603, 0.010449, 0.049946)),
            ("x", 0.4, (0.411703, 0.102063, 0.018809, 0.032573)),
            ("-", 0.4, (0.413532, 0.075461, 0.021421, 0.009772)),
            ("x", 0.4, (0.439133, 0.069490, 0.022466, 0.032573)),
        ]
        detections.sort(key=lambda x: x[2][0] - x[2][2] / 2)

        self.assertEqual(get_all_numerator_and_denominator(detections, 8),
                         ("(x^2+(1/x)x)", "((3/2)x^3-1)", 8, 22))
        # frac3
        detections = [
            ("3", 0.4, (0.143678, 0.090662, 0.036573, 0.074919)),
            ("+", 0.4, (0.187304, 0.092834, 0.022466, 0.057546)),
            ("x", 0.4, (0.227011, 0.097720, 0.029781, 0.045603)),
            ("2", 0.4, (0.249478, 0.063518, 0.020376, 0.035831)),
            ("-", 0.4, (0.289969, 0.087405, 0.025078, 0.022801)),
            ("1", 0.4, (0.340387, 0.035288, 0.018286, 0.064061)),
            ("-", 0.4, (0.337513, 0.073833, 0.048067, 0.015201)),
            ("2", 0.4, (0.339864, 0.110749, 0.036050, 0.056460)),
            ("x", 0.4, (0.375914, 0.077090, 0.028736, 0.049946)),
            ("-", 0.4, (0.280303, 0.159066, 0.329676, 0.033659)),
            ("3", 0.4, (0.125653, 0.199240, 0.041275, 0.061889)),
            ("-", 0.4, (0.130617, 0.231813, 0.054336, 0.018458)),
            ("x", 0.4, (0.126698, 0.274701, 0.026646, 0.030402)),
            ("3", 0.4, (0.145246, 0.254072, 0.012539, 0.026059)),
            ("+", 0.4, (0.202194, 0.233442, 0.024033, 0.039088)),
            ("2", 0.4, (0.241902, 0.237242, 0.025078, 0.066232)),
            ("x", 0.4, (0.274817, 0.245928, 0.028213, 0.048860)),
            ("-", 0.4, (0.313741, 0.242671, 0.019331, 0.020630)),
            ("3", 0.4, (0.345350, 0.236699, 0.031348, 0.060803)),
            ("+", 0.4, (0.379310, 0.237785, 0.025078, 0.039088)),
            ("5", 0.4, (0.405956, 0.236156, 0.025078, 0.055375)),
            ("x", 0.4, (0.430773, 0.242671, 0.027691, 0.055375)),
        ]
        detections.sort(key=lambda x: x[2][0] - x[2][2] / 2)
        self.assertEqual(get_all_numerator_and_denominator(detections, 3), ("(3+x^2-(1/2)x)", "(3/(x^3)+2x-3+5x)", 0,
                                                                            21))

    def test_get_all_fractions(self):
        # frac1
        detections = [
            ("1", 0.4, (0.065308, 0.124321, 0.031348, 0.094463)),
            ("-", 0.4, (0.073145, 0.179696, 0.060606, 0.016287)),
            ("2", 0.4, (0.073406, 0.228556, 0.040230, 0.066232)),
            ("x", 0.4, (0.144462, 0.185125, 0.046499, 0.066232)),
            ("2", 0.4, (0.189655, 0.143865, 0.036573, 0.064061)),
            ("-", 0.4, (0.238245, 0.193811, 0.034483, 0.040174)),
            ("1", 0.4, (0.297806, 0.190554, 0.020899, 0.094463)),
            ("+", 0.4, (0.348746, 0.192182, 0.049634, 0.089034)),
            ("x", 0.4, (0.428945, 0.122150, 0.045977, 0.051031)),
            ("-", 0.4, (0.437827, 0.173724, 0.107628, 0.032573)),
            ("3", 0.4, (0.437565, 0.247557, 0.048589, 0.102063)),
            ("2", 0.4, (0.467085, 0.096091, 0.036573, 0.051031)),
        ]
        detections.sort(key=lambda x: x[2][0] - x[2][2] / 2)

        self.assertEqual(get_all_fractions(detections), [("1/2", 0, 2), ("(x^2)/3", 8, 11)])

        # frac2
        detections = [
            ("x", 0.4, (0.022205, 0.132465, 0.031870, 0.056460)),
            ("2", 0.4, (0.042059, 0.095548, 0.013062, 0.043431)),
            ("2", 0.4, (0.084117, 0.207926, 0.032393, 0.079262)),
            ("+", 0.4, (0.052508, 0.141694, 0.014107, 0.038002)),
            ("-", 0.4, (0.090125, 0.146580, 0.046499, 0.017372)),
            ("1", 0.4, (0.093783, 0.090662, 0.020376, 0.077090)),
            ("x", 0.4, (0.146813, 0.135722, 0.040752, 0.060803)),
            ("-", 0.4, (0.217346, 0.137351, 0.033438, 0.022801)),
            ("x", 0.4, (0.307732, 0.080347, 0.031348, 0.049946)),
            ("2", 0.4, (0.330460, 0.046688, 0.014107, 0.039088)),
            ("3", 0.4, (0.308255, 0.192725, 0.029258, 0.053203)),
            ("2", 0.4, (0.306949, 0.265472, 0.028736, 0.057546)),
            ("-", 0.4, (0.307210, 0.227470, 0.039707, 0.018458)),
            ("x", 0.4, (0.355016, 0.223670, 0.022466, 0.039088)),
            ("3", 0.4, (0.372257, 0.194897, 0.016196, 0.044517)),
            ("-", 0.4, (0.405956, 0.220413, 0.020899, 0.010858)),
            ("1", 0.4, (0.432602, 0.210098, 0.011494, 0.053203)),
            ("-", 0.4, (0.373041, 0.141694, 0.201672, 0.022801)),
            ("+", 0.4, (0.372780, 0.080347, 0.038140, 0.049946)),
            ("1", 0.4, (0.410136, 0.045603, 0.010449, 0.049946)),
            ("x", 0.4, (0.411703, 0.102063, 0.018809, 0.032573)),
            ("-", 0.4, (0.413532, 0.075461, 0.021421, 0.009772)),
            ("x", 0.4, (0.439133, 0.069490, 0.022466, 0.032573)),
        ]
        self.assertEqual(get_all_fractions(detections),
                         [("1/2", 2, 5), ("(x^2+(1/x)x)/((3/2)x^3-1)", 8, 22)])

        # frac3
        detections = [
            ("3", 0.4, (0.143678, 0.090662, 0.036573, 0.074919)),
            ("+", 0.4, (0.187304, 0.092834, 0.022466, 0.057546)),
            ("x", 0.4, (0.227011, 0.097720, 0.029781, 0.045603)),
            ("2", 0.4, (0.249478, 0.063518, 0.020376, 0.035831)),
            ("-", 0.4, (0.289969, 0.087405, 0.025078, 0.022801)),
            ("1", 0.4, (0.340387, 0.035288, 0.018286, 0.064061)),
            ("-", 0.4, (0.337513, 0.073833, 0.048067, 0.015201)),
            ("2", 0.4, (0.339864, 0.110749, 0.036050, 0.056460)),
            ("x", 0.4, (0.375914, 0.077090, 0.028736, 0.049946)),
            ("-", 0.4, (0.280303, 0.159066, 0.329676, 0.033659)),
            ("3", 0.4, (0.125653, 0.199240, 0.041275, 0.061889)),
            ("-", 0.4, (0.130617, 0.231813, 0.054336, 0.018458)),
            ("x", 0.4, (0.126698, 0.274701, 0.026646, 0.030402)),
            ("3", 0.4, (0.145246, 0.254072, 0.012539, 0.026059)),
            ("+", 0.4, (0.202194, 0.233442, 0.024033, 0.039088)),
            ("2", 0.4, (0.241902, 0.237242, 0.025078, 0.066232)),
            ("x", 0.4, (0.274817, 0.245928, 0.028213, 0.048860)),
            ("-", 0.4, (0.313741, 0.242671, 0.019331, 0.020630)),
            ("3", 0.4, (0.345350, 0.236699, 0.031348, 0.060803)),
            ("+", 0.4, (0.379310, 0.237785, 0.025078, 0.039088)),
            ("5", 0.4, (0.405956, 0.236156, 0.025078, 0.055375)),
            ("x", 0.4, (0.430773, 0.242671, 0.027691, 0.055375)),
        ]
        detections.sort(key=lambda x: x[2][0] - x[2][2] / 2)
        self.assertEqual(get_all_fractions(detections),
                         [("(3+x^2-(1/2)x)/(3/(x^3)+2x-3+5x)", 0, 21)])

        # frac4
        detections = [
            ("1", 0.4, (0.268128, 0.217224, 0.091062, 0.218509)),
            ("+", 0.4, (0.434233, 0.235219, 0.156830, 0.197943)),
            ("a", 0.4, (0.612985, 0.150386, 0.086003, 0.110540)),
            ("b", 0.4, (0.612985, 0.339332, 0.072513, 0.154242)),
            ("-", 0.4, (0.611298, 0.237789, 0.092749, 0.028278)),
            ("-", 0.4, (0.447723, 0.449871, 0.693086, 0.041131)),
            ("1", 0.4, (0.153457, 0.641388, 0.087690, 0.218509)),
            ("+", 0.4, (0.319562, 0.665810, 0.136594, 0.221080)),
            ("1", 0.4, (0.610455, 0.555270, 0.070826, 0.149100)),
            ("-", 0.4, (0.610455, 0.661954, 0.323777, 0.038560)),
            ("1", 0.4, (0.494098, 0.785347, 0.067454, 0.161954)),
            ("+", 0.4, (0.593592, 0.800771, 0.111298, 0.161954)),
            ("1", 0.4, (0.707420, 0.727506, 0.045531, 0.107969)),
            ("-", 0.4, (0.709106, 0.799486, 0.086003, 0.030848)),
            ("a", 0.4, (0.706577, 0.888175, 0.070826, 0.095116))
        ]
        detections.sort(key=lambda x: x[2][0] - x[2][2] / 2)
        self.assertEqual(get_all_fractions(detections),
                         [("(1+a/b)/(1+1/(1+1/a))", 0, 14)])

        # frac5
        detections = [
            ("3", 0.4, (0.079154, 0.087948, 0.021421, 0.067318)),
            ("x", 0.4, (0.105799, 0.099349, 0.025601, 0.044517)),
            ("-", 0.4, (0.093260, 0.133008, 0.090387, 0.016287)),
            ("3", 0.4, (0.093260, 0.173724, 0.029781, 0.062975)),
            ("-", 0.4, (0.169279, 0.135722, 0.025078, 0.017372)),
            ("1", 0.4, (0.204284, 0.128122, 0.016719, 0.054289)),
            ("+", 0.4, (0.236416, 0.128664, 0.018286, 0.029316)),
            ("3", 0.4, (0.254702, 0.067861, 0.023511, 0.064061)),
            ("+", 0.4, (0.281870, 0.061346, 0.021421, 0.040174)),
            ("2", 0.4, (0.318443, 0.064061, 0.030825, 0.062975)),
            ("x", 0.4, (0.355799, 0.070033, 0.028213, 0.042345)),
            ("2", 0.4, (0.381661, 0.039631, 0.018286, 0.040174)),
            ("+", 0.4, (0.406217, 0.070575, 0.023511, 0.030402)),
            ("3", 0.4, (0.439394, 0.031488, 0.017764, 0.045603)),
            ("-", 0.4, (0.437565, 0.054832, 0.027691, 0.014115)),
            ("5", 0.4, (0.440178, 0.077633, 0.019331, 0.040174)),
            ("-", 0.4, (0.349791, 0.129207, 0.194880, 0.019544)),
            ("1", 0.4, (0.264368, 0.175353, 0.017764, 0.048860)),
            ("-", 0.4, (0.261233, 0.206840, 0.040752, 0.014115)),
            ("6", 0.4, (0.260711, 0.242128, 0.017764, 0.056460)),
            ("-", 0.4, (0.320794, 0.210641, 0.020899, 0.015201)),
            ("5", 0.4, (0.371735, 0.194354, 0.031870, 0.065147)),
            ("+", 0.4, (0.481452, 0.126493, 0.027691, 0.055375)),
            ("1", 0.4, (0.554859, 0.092834, 0.015674, 0.072747)),
            ("-", 0.4, (0.551463, 0.136265, 0.038140, 0.020630)),
            ("6", 0.4, (0.545455, 0.178067, 0.021944, 0.054289)),
        ]
        detections.sort(key=lambda x: x[2][0] - x[2][2] / 2)
        self.assertEqual(get_all_fractions(detections),
                         [("3x/3", 0, 3), ("(3+2x^2+3/5)/(1/6-5)", 7, 21), ("1/6", 23, 25)])

    def test_convert_infix_to_latex(self):
        polynomial = "4=x^2"
        self.assertEqual(convert_infix_to_latex(polynomial), "$$4=x^2$$")

        polynomial = "2x^2-3(x+1)=0"
        self.assertEqual(convert_infix_to_latex(polynomial), "$$2x^2-3\left(x+1\\right)=0$$")

        polynomial = "x^11+x^(x^2+2x+1)"
        self.assertEqual(convert_infix_to_latex(polynomial), "$$x^{11}+x^{x^2+2x+1}$$")

        polynomial = "(x^(3-x/2))/(x^2+1)"
        self.assertEqual(convert_infix_to_latex(polynomial), "$$\\frac{x^{3-\\frac{x}{2}}}{x^2+1}$$")

        polynomial = "3x/3-1+(3+2x^2+3/5)/(1/6-5)+1/6"
        self.assertEqual(convert_infix_to_latex(polynomial),
                         "$$\\frac{3x}{3}-1+\\frac{3+2x^2+\\frac{3}{5}}{\\frac{1}{6}-5}+\\frac{1}{6}$$")

        polynomial = "2^3,2+1.2"
        self.assertEqual(convert_infix_to_latex(polynomial),
                         "$$2^{3.2}+1\\times2$$")

        polynomial = "3x"
        self.assertEqual(convert_infix_to_latex(polynomial),
                         "$$3x$$")
