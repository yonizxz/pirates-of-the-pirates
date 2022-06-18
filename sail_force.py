import math


class Force:
    def __init__(self, size, angle):
        self._size = size
        self._angle = angle

    @property
    def size(self):
        return self._size

    @property
    def angle(self):
        return self._angle

    @classmethod
    def from_cartesian(cls, x, y):
        return cls(math.sqrt(x ** 2 + y ** 2), math.atan2(y, x))


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
