import math


def drag_coef(angle):
    """
    :param angle: attack angle
    :return: drag coefficient
    """
    return 2 * (math.sin(angle) ** 4)


def lift_coef(angle):
    """
    :param angle: attack angle
    :return: lift coefficient
    """
    return 2 * math.sin(angle) * math.cos(angle)
