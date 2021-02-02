import unittest

operator_and_comma = ["+", "*", "/", "=", "-", "^", ","]
closing_bracket = ["}", "]", ")"]
opening_bracket = ["{", "[", "("]


def convert_from_objects_to_string(detections: list) -> str:
    """
     detections : list of detection = [(label, confidence, bbox)]
     bbox = (x,y,w,h)
     """
    detections.sort(key=lambda x: x[2][0])
    result = get_label(detections[0][0])
    for i in range(1, len(detections)):
        current_x, current_y, current_w, current_h = detections[i][2]
        previous_x, previous_y, previous_w, previous_h = detections[i - 1][2]
        bottom_current_y = current_y + current_h / 2

        # Add pow
        if bottom_current_y <= previous_y:
            result += "^"
        result += get_label(detections[i][0])
    return result


def normalize_polynomial(polynomial: str) -> str:
    result = polynomial[0]
    for i in range(1, len(polynomial)):
        current_label = polynomial[i]
        previous_label = polynomial[i - 1]
        # add *
        # Ex: 2x => 2*x
        if can_add_multiple_operator(previous_label, current_label):
            result += "*"
        result += polynomial[i]
    return result


def can_add_multiple_operator(previous_label: str, current_label: str) -> bool:
    # If previous and current are both numbers return false
    # Ex: '22','33','55'
    if previous_label.isdigit() and current_label.isdigit():
        return False
    # if previous or current are operator or comma return false
    # Ex: '2+','-2','=2','3,'
    if operator_and_comma.__contains__(previous_label) or operator_and_comma.__contains__(current_label):
        return False
    # if previous is opening bracket or current is closing bracket return false
    # Ex: '2)','9}','(3','[x'
    if closing_bracket.__contains__(current_label) or opening_bracket.__contains__(previous_label):
        return False
    return True


def get_label(value: str) -> str:
    if value == ".":
        value = "*"
    return value


class Tests(unittest.TestCase):

    def test_convert_from_objects_to_string(self):
        detections = [("=", 0.4, (0.398438, 0.509766, 0.312500, 0.097656)),
                      ("x", 0.4, (0.720703, 0.500000, 0.222656, 0.250000)),
                      ("2", 0.4, (0.921875, 0.423828, 0.140625, 0.128906)),
                      ("4", 0.4, (0.080078, 0.529297, 0.152344, 0.269531))]
        self.assertEqual(convert_from_objects_to_string(detections), "4=x^2")

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
        self.assertEqual(convert_from_objects_to_string(detections), "(x+1)(x-2)*2,5-3(x^2-1)2=0")

    def test_normalize_polynomial(self):
        polynomial = "4=x^2"
        self.assertEqual(normalize_polynomial(polynomial), "4=x^2")

        polynomial = "2x^2-3(x+1)=0"
        self.assertEqual(normalize_polynomial(polynomial), "2*x^2-3*(x+1)=0")

        polynomial = "4=x2"
        self.assertEqual(normalize_polynomial(polynomial), "4=x*2")

        polynomial = "(x+1)(x-2)2,5-3(x^2-1)2=0"
        self.assertEqual(normalize_polynomial(polynomial), "(x+1)*(x-2)*2,5-3*(x^2-1)*2=0")
