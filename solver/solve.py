import unittest
from math import log

from polynomial import parse_to_polynomial


def convert_from_epsilon_to_n_digit(epsilon):
    return round(-log(epsilon, 10)) - 1


def try_round_root(polynomial, raw_root, n_digits):
    root = round(raw_root, n_digits)
    if abs(polynomial.eval(root)) <= abs(polynomial.eval(raw_root)):
        if int(root) == root:
            return int(root)
        else:
            return root
    else:
        return raw_root


def find_root_using_bisection(polynomial, epsilon, lower, upper):
    if polynomial.eval(lower) * polynomial.eval(upper) > 0:
        return None

    middle = (lower + upper) / 2
    while polynomial.eval(middle) != 0 and abs(upper - lower) > epsilon:
        if polynomial.eval(middle) * polynomial.eval(upper) > 0:
            upper = middle
        else:
            lower = middle
        middle = (lower + upper) / 2

    n_digits = convert_from_epsilon_to_n_digit(epsilon)
    middle = try_round_root(polynomial, middle, n_digits)
    return middle


def find_root(polynomial, epsilon, lower, upper):
    if polynomial.eval(lower) == 0:
        return None
    if polynomial.eval(upper) == 0:
        return upper
    if polynomial.eval(lower) * polynomial.eval(upper) > 0:
        return None

    if lower == float('-inf') and upper == float('inf'):
        lower = get_lower_bound_with_opposite_sign(polynomial, 0)
        upper = get_upper_bound_with_opposite_sign(polynomial, 0)
        
    elif lower == float('-inf'):
        lower = get_lower_bound_with_opposite_sign(polynomial, upper)
        
    elif upper == float('inf'):
        upper = get_upper_bound_with_opposite_sign(polynomial, lower)

    return find_root_using_bisection(polynomial, epsilon, lower, upper)


def get_lower_bound_with_opposite_sign(polynomial, upper, init_step=1):
    if polynomial.eval(float('-inf')) * polynomial.eval(upper) > 0:
        return None

    step = init_step
    lower = upper - step
    while polynomial.eval(lower) * polynomial.eval(upper) > 0:
        step = step * 2
        lower = lower - step

    return lower


def get_upper_bound_with_opposite_sign(polynomial, lower, init_step=1):
    if polynomial.eval(float('inf')) * polynomial.eval(lower) > 0:
        return None

    step = init_step
    upper = lower + step
    while polynomial.eval(lower) * polynomial.eval(upper) > 0:
        step = step * 2
        upper = upper + step

    return upper


def solve_from_derivative_roots(polynomial, epsilon, derivative_roots):
    roots = []
    check_points = derivative_roots.copy()
    check_points.insert(0, float('-inf'))
    check_points.append(float('inf'))

    for index in range(0, len(check_points) - 1):
        root = find_root(polynomial, epsilon, check_points[index], check_points[index + 1])
        if root is not None:
            roots.append(root)
        
    return roots


def solve_equation(polynomial, epsilon):
    if polynomial.get_highest_degree() == 0:
        if polynomial.get_coefficient(0) != 0:
            return []
        else:
            return ["Infinite roots"]

    if polynomial.get_highest_degree() == 1:
        [a, b] = polynomial.get_full_coefficient()
        return [-b / a]
    else:
        derivative = polynomial.derivative()
        derivative_roots = solve_equation(derivative, epsilon)
        return solve_from_derivative_roots(polynomial, epsilon, derivative_roots)


def parse_and_solve_and_round(expression, epsilon):
    if expression.find("=") < 0:
        roots = solve_equation(parse_to_polynomial(expression), epsilon)
    else:
        if expression.endswith("=0"):
            roots = solve_equation(parse_to_polynomial(expression[0:len(expression)-2]), epsilon)
        else:
            index_of_equal = expression.find("=")
            a = parse_to_polynomial(expression[0:index_of_equal])
            b = parse_to_polynomial(expression[index_of_equal+1:])
            roots = solve_equation(a.minus(b), epsilon)

    if roots == ["Infinite roots"]:
        return roots
    n_digits = convert_from_epsilon_to_n_digit(epsilon)
    return list(map(lambda root: round(root, n_digits), roots))


class Tests(unittest.TestCase):

    def test_get_lower_bound_with_opposite_sign(self):
        self.assertEqual(get_lower_bound_with_opposite_sign(parse_to_polynomial("x^3"), 1), 0)
        self.assertEqual(get_lower_bound_with_opposite_sign(parse_to_polynomial("x^2+9"), -2), None)

    def test_get_upper_bound_with_opposite_sign(self):
        self.assertEqual(get_upper_bound_with_opposite_sign(parse_to_polynomial("x^3"), 1), None)
        self.assertEqual(get_upper_bound_with_opposite_sign(parse_to_polynomial("x^3"), -10), 5)

    def test_bisect(self):
        epsilon = 0.00001
        n_digits = convert_from_epsilon_to_n_digit(epsilon)

        polynomial = parse_to_polynomial("x^3/3-x")
        root = find_root_using_bisection(polynomial, epsilon, 1, 10)
        self.assertEqual(round(root, n_digits), 1.7321)

        polynomial = parse_to_polynomial("x^2-x-2")
        root = find_root_using_bisection(polynomial, epsilon, -100, 0)
        self.assertEqual(round(root, n_digits), -1)

        polynomial = parse_to_polynomial("x^2-x-2")
        root = find_root_using_bisection(polynomial, epsilon, -100, -10)
        self.assertEqual(root, None)

    def test_solve_from_derivative_roots(self):
        epsilon = 0.00001
        n_digits = convert_from_epsilon_to_n_digit(epsilon)

        polynomial = parse_to_polynomial("x^3+x")
        derivative_roots = []
        roots = solve_from_derivative_roots(polynomial, epsilon, derivative_roots)
        expected_roots = [0]
        for index in range(len(roots)):
            self.assertEqual(round(roots[index], n_digits), expected_roots[index])

        polynomial = parse_to_polynomial("x^2-6*x+1")
        derivative_roots = [3]
        roots = solve_from_derivative_roots(polynomial, epsilon, derivative_roots)
        expected_roots = [0.1716, 5.8284]
        for index in range(len(roots)):
            self.assertEqual(round(roots[index], n_digits), expected_roots[index])

        polynomial = parse_to_polynomial("x^3-3*x^2+2*x-10")
        derivative_roots = [0.42, 1.57]
        roots = solve_from_derivative_roots(polynomial, epsilon, derivative_roots)
        expected_roots = [3.3089]
        for index in range(len(roots)):
            self.assertEqual(round(roots[index], n_digits), expected_roots[index])

    def test_solve_equation(self):
        epsilon = 0.0001

        polynomial = parse_to_polynomial("0*x+6")
        roots = solve_equation(polynomial, epsilon)
        self.assertEqual(roots, [])

        polynomial = parse_to_polynomial("0*x+0")
        roots = solve_equation(polynomial, epsilon)
        self.assertEqual(roots, ["Infinite roots"])

        polynomial = parse_to_polynomial("11*x+6")
        roots = solve_equation(polynomial, epsilon)
        expected_roots = [-6/11]
        self.assertEqual(len(roots), len(expected_roots))
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        polynomial = parse_to_polynomial("6*x^2+11*x+6")
        roots = solve_equation(polynomial, epsilon)
        expected_roots = []
        self.assertEqual(len(roots), len(expected_roots))
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        polynomial = parse_to_polynomial("x^3+6*x^2+11*x+6")
        roots = solve_equation(polynomial, epsilon)
        expected_roots = [-3, -2, -1]
        self.assertEqual(len(roots), len(expected_roots))
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        polynomial = parse_to_polynomial("x^2-1").multiply(parse_to_polynomial("x^2-4"))
        roots = solve_equation(polynomial, epsilon)
        expected_roots = [-2, -1, 1, 2]
        self.assertEqual(len(roots), len(expected_roots))
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])
            
    def test_parse_and_solve_and_round(self):
        epsilon = 0.00001
        
        expression = "x^2-1"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = [-1, 1]
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        expression = "x^2-1=0"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = [-1, 1]
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        expression = "x^2-1=8"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = [-3, 3]
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        expression = "x^2-1=-2*x+2"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = [-3, 1]
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        expression = "x^2+2.5*x+1.5"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = [-1.5, -1]
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        expression = "x^4-4*x^2+20*x-7"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = [-3.2788, 0.3775]
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        expression = "0*x-7"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = []
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        expression = "0*x+0"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = ["Infinite roots"]
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        expression = "x^5-5*x^3+4=0"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = [-2.3077, 1, 2.1433]
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])

        expression = "x^5-6*x^4+4=0"
        roots = parse_and_solve_and_round(expression, epsilon)
        expected_roots = [-0.8734, 0.9431, 5.9969]
        for index in range(len(roots)):
            self.assertEqual(roots[index], expected_roots[index])
