
def peek(list_based_stack: list):
    if len(list_based_stack) == 0:
        return None
    return list_based_stack[len(list_based_stack) - 1]


def check_is_an_integer(token):
    try:
        int(token)
        return True
    except TypeError:
        return False
    except ValueError:
        return False


def check_is_a_number(token):
    try:
        float(token)
        return True
    except TypeError:
        return False
    except ValueError:
        return False


def is_unary_operator(token):
    return token in ["neg", "pos"]


def is_binary_operator(token):
    return token in ["+", "-", "*", "/", "^"]


def is_operator(token):
    return is_unary_operator(token) or is_binary_operator(token)


def is_opening_bracket(token: str):
    return token in ["(", "[", "{"]


def is_closing_bracket(token: str):
    return token in [")", "]", "}"]


def is_bracket(token: str):
    return is_opening_bracket(token) or is_closing_bracket(token)


def is_operand(token: str):
    return check_is_a_number(token) or token == "x"
