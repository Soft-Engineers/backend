import random
import string

_name_id = 0
# Obtain a unique name for testing
def generate_unique_testing_name():
    global _name_id
    name = "TName" + str(_name_id)
    _name_id += 1
    return name

# Random string with only lower
def get_random_string_lower(length):
    lower = string.ascii_lowercase
    result_str = "".join(random.choice(lower) for i in range(length))
    return result_str


# random string with only upper
def get_random_string_upper(length):
    upper = string.ascii_uppercase
    result_str = "".join(random.choice(upper) for i in range(length))
    return result_str


# Random string with only num
def get_random_string_num(length):
    num = string.digits
    result_str = "".join(random.choice(num) for i in range(length))
    return result_str

