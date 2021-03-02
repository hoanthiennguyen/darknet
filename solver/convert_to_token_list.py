import unittest

from util import peek, check_is_a_number, is_operator, is_opening_bracket


def convert_to_token_list(expression):
    # TODO: consider handling sign +/-
    result = []
    for i in range(len(expression)):
        character = expression[i]
        if check_is_part_of_number(character) and len(result) > 0:
            last_token = peek(result)
            if check_is_a_number(last_token):
                result[len(result) - 1] = last_token + character
            else:
                result.append(character)
        else:
            result.append(character)

    # replace - sign with neg operator
    for i in range(len(result)):
        if i == 0 or i > 0 and (is_opening_bracket(result[i-1]) or is_operator(result[i-1])):
            if result[i] == "-":
                result[i] = "neg"
            elif result[i] == "+":
                result[i] = "pos"

    return result


def check_is_part_of_number(character):
    return character in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."]


class Tests(unittest.TestCase):

    def test_convert_to_token_list(self):
        self.assertEqual(convert_to_token_list("x"), ["x"])
        self.assertEqual(convert_to_token_list("x+1"), ["x", "+", "1"])
        self.assertEqual(convert_to_token_list("x+10"), ["x", "+", "10"])
        self.assertEqual(convert_to_token_list("x^2+10"), ["x", "^", "2", "+", "10"])
        self.assertEqual(convert_to_token_list("1.2*x^2+10"), ["1.2", "*", "x", "^", "2", "+", "10"])
        self.assertEqual(convert_to_token_list("1.25*x^2+100"), ["1.25", "*", "x", "^", "2", "+", "100"])
        self.assertEqual(convert_to_token_list("-x+10"), ["neg", "x", "+", "10"])
        self.assertEqual(convert_to_token_list("+x+10"), ["pos", "x", "+", "10"])
        self.assertEqual(convert_to_token_list("-x^2+1"), ["neg", "x", "^", "2", "+", "1"])
