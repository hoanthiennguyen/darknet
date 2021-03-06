import copy
import unittest
from typing import List

from solver.error import EvaluationError, ExpressionSyntaxError
from solver.convert_to_postfix import convert_infix_to_postfix
from solver.convert_to_token_list import convert_to_token_list
from solver.util import check_is_a_number, is_unary_operator, is_operand, is_binary_operator


def parse_operand(operand: str):
    if operand == 'x':
        dictionary = {1: 1}
    else:
        dictionary = {0: float(operand)}
    return Polynomial(dictionary)


def evaluate_postfix(token_list: List[str]):
    operand_stack = []
    for token in token_list:
        if is_operand(token):
            operand_stack.append(parse_operand(token))
        else:
            if is_unary_operator(token) and len(operand_stack) >= 1:
                op1 = operand_stack.pop()
                if token == "neg":
                    result = op1.neg()
                elif token == "pos":
                    result = op1
                else:
                    raise ExpressionSyntaxError("Not supported operator: " + token)
            elif is_binary_operator(token) and len(operand_stack) >= 2:
                op2 = operand_stack.pop()
                op1 = operand_stack.pop()
                if token == "+":
                    result = op1.plus(op2)
                elif token == "-":
                    result = op1.minus(op2)
                elif token == "*":
                    result = op1.multiply(op2)
                elif token == "/":
                    result = op1.divide(op2)
                elif token == "^":
                    result = op1.power(op2)
                else:
                    raise ExpressionSyntaxError("Not supported operator: " + token)
            else:
                raise ExpressionSyntaxError("Invalid expression")

            operand_stack.append(result)
    if len(operand_stack) == 1:
        return operand_stack.pop()
    else:
        raise ExpressionSyntaxError("Invalid expression")


def parse_to_polynomial(expression):
    token_list = convert_to_token_list(expression)
    postfix_token_list = convert_infix_to_postfix(token_list)
    return evaluate_postfix(postfix_token_list).simplify()


class Polynomial:
    def __init__(self, dictionary):
        self.dictionary = dictionary

    def __eq__(self, other):
        if isinstance(other, Polynomial):
            return self.dictionary == other.dictionary
        else:
            return False

    def __str__(self):
        result = ""
        if len(self.dictionary) == 0:
            return "0"

        for degree in self.dictionary:
            if degree == 0:
                result += "{} + ".format(self.get_coefficient(degree))
            elif degree == 1:
                if self.get_coefficient(degree) == 1:
                    result += "x + "
                else:
                    result += "{}x + ".format(self.dictionary[degree])
            else:
                if self.get_coefficient(degree) == 1:
                    result += "x^{} + ".format(degree)
                else:
                    result += "{}x^{} + ".format(self.get_coefficient(degree), degree)

        return result[0:len(result) - 3]

    def __repr__(self):
        return self.__str__()

    def plus(self, other):
        if not isinstance(other, Polynomial):
            raise TypeError("Parameter is not a Polynomial")

        for degree in other.dictionary:
            self.dictionary[degree] = self.dictionary.get(degree, 0) + other.dictionary[degree]

        return self.simplify()

    def minus(self, other):
        if not isinstance(other, Polynomial):
            raise TypeError("Parameter is not a Polynomial")

        for degree in other.dictionary:
            self.dictionary[degree] = self.dictionary.get(degree, 0) - other.dictionary[degree]

        return self.simplify()

    def multiply(self, other):
        if not isinstance(other, Polynomial):
            raise TypeError("Parameter is not a Polynomial")
        result = {}
        for d1 in self.dictionary:
            for d2 in other.dictionary:
                result[d1 + d2] = result.get(d1 + d2, 0) + self.dictionary.get(d1) * other.dictionary.get(d2)

        return Polynomial(result).simplify()

    def neg(self):
        result = copy.deepcopy(self)
        for degree in result.dictionary:
            result.dictionary[degree] = -(result.dictionary[degree])
        return result

    @staticmethod
    def from_constant(number):
        return Polynomial({0: number})

    def simplify(self):
        zero_coefficient = []
        for degree in self.dictionary:
            if self.dictionary[degree] == 0:
                zero_coefficient.append(degree)
        
        for degree in zero_coefficient:
            self.dictionary.pop(degree)

        return self

    def get_full_coefficient(self):
        coefficients = []
        max_degree = 0
        for degree in self.dictionary:
            if degree > max_degree:
                max_degree = degree

        for degree in reversed(range(0, max_degree + 1)):
            coefficients.append(self.dictionary.get(degree, 0))

        return coefficients

    def derivative(self):
        result = {}
        for degree, coefficient in self.dictionary.items():
            if degree >= 1:
                result[degree - 1] = coefficient * degree

        return Polynomial(result)

    def eval(self, x):
        if x == float('inf'):
            return self.get_lim_at_inf()
        if x == float('-inf'):
            return self.get_lim_at_minus_inf()
        
        result = 0
        for degree, coefficient in self.dictionary.items():
            result += coefficient * x ** degree

        return result

    def get_highest_degree(self):
        max_degree = 0
        for degree in self.dictionary:
            if degree > max_degree:
                max_degree = degree

        return max_degree

    def get_coefficient(self, degree):
        return self.dictionary.get(degree, 0)
    
    def get_lim_at_inf(self):
        highest_degree = self.get_highest_degree()
        if self.dictionary[highest_degree] > 0:
            return float('inf')
        else:
            return float('-inf')

    def get_lim_at_minus_inf(self):
        highest_degree = self.get_highest_degree()
        if highest_degree % 2 == 0:
            if self.dictionary[highest_degree] > 0:
                return float('inf')
            else:
                return float('-inf')
        else:
            if self.dictionary[highest_degree] > 0:
                return float('-inf')
            else:
                return float('inf')

    def divide(self, op2):
        if isinstance(op2, Polynomial) and op2.is_constant():
            denominator = op2.get_coefficient(0)
        elif check_is_a_number(op2):
            denominator = op2
        else:
            raise EvaluationError("Denominator must be a number")

        if denominator == 0:
            raise EvaluationError("Divided by zero")
        result = copy.deepcopy(self)
        for degree in range(result.get_highest_degree() + 1):
            if result.get_coefficient(degree) != 0:
                result.dictionary[degree] = result.get_coefficient(degree) / denominator
        return result

    def is_constant(self):
        return self.get_highest_degree() == 0

    def power(self, op2):
        if isinstance(op2, Polynomial) and op2.is_constant():
            degree = op2.get_coefficient(0)
        elif check_is_a_number(op2):
            degree = op2
        else:
            raise EvaluationError("Denominator must be a number")
        if int(degree) == degree:
            degree = int(degree)
            if degree >= 0:
                result = Polynomial({0: 1})
                for i in range(degree):
                    result = result.multiply(self)
                return result
            else:
                raise EvaluationError("Negative power is not supported: " + str(degree))
        else:
            raise EvaluationError("Not integer power is not supported: " + str(degree))


class Tests(unittest.TestCase):

    def test_parse(self):
        self.assertEqual(parse_to_polynomial("1"), Polynomial({0: 1}))
        self.assertEqual(parse_to_polynomial("x"), Polynomial({1: 1}))
        self.assertEqual(parse_to_polynomial("+x"), Polynomial({1: 1}))
        self.assertEqual(parse_to_polynomial("-x"), Polynomial({1: -1}))
        self.assertEqual(parse_to_polynomial("--x"), Polynomial({1: 1}))
        self.assertEqual(parse_to_polynomial("++x"), Polynomial({1: 1}))
        self.assertEqual(parse_to_polynomial("-+x"), Polynomial({1: -1}))
        self.assertEqual(parse_to_polynomial("+-x"), Polynomial({1: -1}))
        self.assertEqual(parse_to_polynomial("(-x)^2"), Polynomial({2: 1}))
        self.assertEqual(parse_to_polynomial("-x^2"), Polynomial({2: -1}))
        self.assertEqual(parse_to_polynomial("(+x)^2"), Polynomial({2: 1}))
        self.assertEqual(parse_to_polynomial("-x^2+3*2"), Polynomial({2: -1, 0: 6}))
        self.assertEqual(parse_to_polynomial("x-x"), Polynomial({}))
        self.assertEqual(parse_to_polynomial("x*x"), Polynomial({2: 1}))
        self.assertEqual(parse_to_polynomial("x*-x"), Polynomial({2: -1}))
        self.assertEqual(parse_to_polynomial("-x*x"), Polynomial({2: -1}))
        self.assertEqual(parse_to_polynomial("-x*-x"), Polynomial({2: 1}))
        self.assertEqual(parse_to_polynomial("20*x"), Polynomial({1: 20}))
        self.assertEqual(parse_to_polynomial("3*20*x"), Polynomial({1: 60}))
        self.assertEqual(parse_to_polynomial("1/3*x^3-x"), Polynomial({3: 1 / 3, 1: -1}))
        self.assertEqual(parse_to_polynomial("x^3/3-x"), Polynomial({3: 1 / 3, 1: -1}))
        self.assertEqual(parse_to_polynomial("3*2*x-5*x"), Polynomial({1: 1}))
        self.assertEqual(parse_to_polynomial("x+3*x^2+1"), Polynomial({2: 3, 1: 1, 0: 1}))
        self.assertEqual(parse_to_polynomial("3*x^2-x+1"), Polynomial({2: 3, 1: -1, 0: 1}))
        self.assertEqual(parse_to_polynomial("3*x^2-x+1+9*x-3"), Polynomial({2: 3, 1: 8, 0: -2}))
        self.assertEqual(parse_to_polynomial("-3*x^2-x+1+9*x-3"), Polynomial({2: -3, 1: 8, 0: -2}))

        expression = "3+4*5"
        self.assertEqual(parse_to_polynomial(expression), Polynomial.from_constant(23))

        expression = "3+4*5^2"
        self.assertEqual(parse_to_polynomial(expression), Polynomial.from_constant(103))

        expression = "1+2^2^3"
        self.assertEqual(parse_to_polynomial(expression), Polynomial.from_constant(257))

        expression = "2*x-5+3*x"
        self.assertEqual(parse_to_polynomial(expression), parse_to_polynomial("5*x-5"))

        expression = "10-2*(x+1)"
        self.assertEqual(parse_to_polynomial(expression), parse_to_polynomial("8-2*x"))

        expression = "(x+2)^2-4"
        self.assertEqual(parse_to_polynomial(expression), parse_to_polynomial("x^2+4*x"))

        expression = "2*(x+2)^2-4"
        self.assertEqual(parse_to_polynomial(expression), parse_to_polynomial("2*x^2+8*x+4"))

        expression = "10-3*(x+1)^2"
        self.assertEqual(parse_to_polynomial(expression), parse_to_polynomial("7-3*x^2-6*x"))

        expression = "(x+1)^3"
        self.assertEqual(parse_to_polynomial(expression), parse_to_polynomial("x^3+3*x^2+3*x+1"))

        expression = "(-x+1)^2"
        self.assertEqual(parse_to_polynomial(expression), parse_to_polynomial("x^2-2*x+1"))

        expression = "-(x+1)*2+4"
        self.assertEqual(parse_to_polynomial(expression), parse_to_polynomial("2-2*x"))

        expression = "(x+2*(x+1))^2+1"
        self.assertEqual(parse_to_polynomial(expression), parse_to_polynomial("9*x^2+12*x+5"))

    def test_get_full_coefficient(self):
        self.assertEqual(parse_to_polynomial("x^2-1").get_full_coefficient(), [1, 0, -1])
        self.assertEqual(parse_to_polynomial("x^2-2*x-1").get_full_coefficient(), [1, -2, -1])
        self.assertEqual(parse_to_polynomial("x^2-2*x").get_full_coefficient(), [1, -2, 0])
        self.assertEqual(parse_to_polynomial("x^2").get_full_coefficient(), [1, 0, 0])

    def test_plus(self):
        self.assertEqual(parse_to_polynomial("2*x-3").plus(parse_to_polynomial("3*x+5")), parse_to_polynomial("5*x+2"))
        self.assertEqual(parse_to_polynomial("2*x+1").plus(parse_to_polynomial("0")), parse_to_polynomial("2*x+1"))
        self.assertEqual(parse_to_polynomial("0").plus(parse_to_polynomial("2*x+1")), parse_to_polynomial("2*x+1"))
        self.assertEqual(parse_to_polynomial("0").plus(parse_to_polynomial("0")), parse_to_polynomial("0"))
        self.assertEqual(parse_to_polynomial("2*x-3").plus(parse_to_polynomial("3*x+5-x^2")),
                         parse_to_polynomial("5*x+2-x^2"))

    def test_minus(self):
        self.assertEqual(parse_to_polynomial("2*x+1").minus(parse_to_polynomial("0")), parse_to_polynomial("2*x+1"))
        self.assertEqual(parse_to_polynomial("0").minus(parse_to_polynomial("2*x+1")), Polynomial({1: -2, 0: -1}))
        self.assertEqual(parse_to_polynomial("0").minus(parse_to_polynomial("0")), Polynomial({}))
        self.assertEqual(parse_to_polynomial("2*x-3").minus(parse_to_polynomial("3*x+5")), Polynomial({1: -1, 0: -8}))
        self.assertEqual(parse_to_polynomial("2*x-3").minus(parse_to_polynomial("3*x+5-x^2")),
                         parse_to_polynomial("x^2-x-8"))

    def test_multiply(self):
        self.assertEqual(parse_to_polynomial("2").multiply(parse_to_polynomial("3")), parse_to_polynomial("6"))
        self.assertEqual(parse_to_polynomial("2").multiply(parse_to_polynomial("x")), parse_to_polynomial("2*x"))
        self.assertEqual(parse_to_polynomial("x").multiply(parse_to_polynomial("x+1")), parse_to_polynomial("x^2+x"))
        self.assertEqual(parse_to_polynomial("x+1").multiply(parse_to_polynomial("x+2")),
                         parse_to_polynomial("x^2+3*x+2"))
        self.assertEqual(parse_to_polynomial("x+1").multiply(parse_to_polynomial("x-1")), parse_to_polynomial("x^2-1"))
        self.assertEqual(parse_to_polynomial("x+1").multiply(parse_to_polynomial("0")), parse_to_polynomial("0"))

    def test_diff(self):
        self.assertEqual(parse_to_polynomial("10").derivative(), parse_to_polynomial("0"))
        self.assertEqual(parse_to_polynomial("x+1").derivative(), parse_to_polynomial("1"))
        self.assertEqual(parse_to_polynomial("2*x^2+3*x+1").derivative(), parse_to_polynomial("4*x+3"))

    def test_eval(self):
        self.assertEqual(parse_to_polynomial("0").eval(10), 0)
        self.assertEqual(parse_to_polynomial("x").eval(10), 10)
        self.assertEqual(parse_to_polynomial("2*x+10").eval(10), 30)
        self.assertEqual(parse_to_polynomial("2.5*x+10").eval(10), 35)
        self.assertEqual(parse_to_polynomial("x^2+2*x+1").eval(3), 16)
        self.assertEqual(parse_to_polynomial("3*x^4+8*x^3-6*x^2-24*x").eval(float('inf')), float('inf'))
        self.assertEqual(parse_to_polynomial("3*x^4+8*x^3-6*x^2-24*x").eval(float('-inf')), float('inf'))

    def test_lim_at_inf(self):
        self.assertEqual(parse_to_polynomial("3*x^4+8*x^3-6*x^2-24*x").get_lim_at_inf(), float('inf'))
        self.assertEqual(parse_to_polynomial("-3*x^4+8*x^3-6*x^2-24*x").get_lim_at_inf(), float('-inf'))

        self.assertEqual(parse_to_polynomial("3*x^3-6*x^2-24*x").get_lim_at_inf(), float('inf'))
        self.assertEqual(parse_to_polynomial("-3*x^3-6*x^2-24*x").get_lim_at_inf(), float('-inf'))

    def test_lim_at_minus_inf(self):
        self.assertEqual(parse_to_polynomial("3*x^4+8*x^3-6*x^2-24*x").get_lim_at_minus_inf(), float('inf'))
        self.assertEqual(parse_to_polynomial("-3*x^4+8*x^3-6*x^2-24*x").get_lim_at_minus_inf(), float('-inf'))

        self.assertEqual(parse_to_polynomial("3*x^3-6*x^2-24*x").get_lim_at_minus_inf(), float('-inf'))
        self.assertEqual(parse_to_polynomial("-3*x^3-6*x^2-24*x").get_lim_at_minus_inf(), float('inf'))

    def test_get_coefficient(self):
        self.assertEqual(parse_to_polynomial("x^2+1").get_coefficient(2), 1)
        self.assertEqual(parse_to_polynomial("x^2+1").get_coefficient(1), 0)
        self.assertEqual(parse_to_polynomial("x^2-1").get_coefficient(0), -1)

    def test_divide(self):
        self.assertEqual(Polynomial({2: 2, 0: -3}).divide(Polynomial.from_constant(2)), Polynomial({2: 1, 0: -3/2}))
        self.assertEqual(Polynomial({2: 2, 0: -3}).divide(Polynomial.from_constant(1)), Polynomial({2: 2, 0: -3}))

    def test_power(self):
        self.assertEqual(parse_to_polynomial("x+1").power(Polynomial.from_constant(0)), parse_to_polynomial("1"))
        self.assertEqual(parse_to_polynomial("x+1").power(Polynomial.from_constant(1)), parse_to_polynomial("x+1"))
        self.assertEqual(parse_to_polynomial("x+1").power(Polynomial.from_constant(2)),
                         parse_to_polynomial("x^2+2*x+1"))
        self.assertEqual(parse_to_polynomial("x+1").power(Polynomial.from_constant(3)),
                         parse_to_polynomial("x^3+3*x^2+3*x+1"))
        self.assertEqual(parse_to_polynomial("x+2").power(Polynomial.from_constant(3)),
                         parse_to_polynomial("x^3+6*x^2+12*x+8"))


if __name__ == '__main__':
    unittest.main()
