import math
import arcade
import numpy as np
import enum

from sail_force import lift_coef, drag_coef, Force

SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 750
BACKGROUND_COLOR = arcade.color.OCEAN_BOAT_BLUE


class HelpModes(enum.Enum):
    NO_HELP = 0
    WIND = 1
    ALL = 2


class Pirates(arcade.Window):
    def __init__(self, width, height):
        super().__init__(width, height)
        arcade.set_background_color(BACKGROUND_COLOR)
        self._sail_angle = 0
        self._sail_openness = 1
        self._keel_angle = math.pi
        self._boat_x = width / 2
        self._boat_y = height / 2
        self._sail_angle_delta = 0
        self._sail_openness_delta = 0
        self._keel_angle_delta = 0
        self._mast_length = 60
        self._keel_length = 35
        self._sail_move_speed = 3
        self._sail_open_speed = 0.35
        self._keel_move_speed = 3
        self._move_angle = 0
        self._move_speed = 0
        self._map_width = width * 2
        self._map_height = height * 2
        self._location_x = self._map_width / 2
        self._location_y = self._map_height / 2
        self._wave_margin = width / 10
        self._wave_x_coords = np.arange(0, self._map_width, self._wave_margin)
        self._wave_y_coords = np.arange(0, self._map_height, self._wave_margin)
        self._speed_x = 0
        self._speed_y = 0
        self._wind_angle = 0
        self._wind_speed = 50
        self._wind_arrow_length = 70
        self._help_mode = HelpModes.NO_HELP
        self._wind_drag = Force(0, 0)
        self._wind_lift = Force(0, 0)
        self._water_drag = Force(0, 0)
        self._water_lift = Force(0, 0)

    def setup(self):
        pass

    def on_draw(self):
        """ Render the screen. """
        arcade.start_render()
        self._draw_waves()
        self._draw_boat()
        self._draw_borders()
        self._draw_wind_arrow()
        self._draw_force_scaffolds()

    def _draw_force_scaffolds(self):
        if self._help_mode == HelpModes.WIND or self._help_mode == HelpModes.ALL:
            self._draw_arrow(self._boat_x, self._boat_y, self._wind_drag.size, self._wind_drag.angle,
                             arcade.color.BLACK, 5, "Wind drag")
            self._draw_arrow(self._boat_x, self._boat_y, self._wind_lift.size, self._wind_lift.angle,
                             arcade.color.PURPLE, 5, "Wind lift")
        if self._help_mode == HelpModes.ALL:
            self._draw_arrow(self._boat_x, self._boat_y, self._water_drag.size, self._water_drag.angle,
                             arcade.color.SILVER, 5, "Water drag")
            self._draw_arrow(self._boat_x, self._boat_y, self._water_lift.size, self._water_lift.angle,
                             arcade.color.YELLOW, 5, "Water lift")

    def _draw_boat(self):
        keel_end_x = self._boat_x + math.cos(self._keel_angle) * self._keel_length
        keel_end_y = self._boat_y + math.sin(self._keel_angle) * self._keel_length
        arcade.draw_line(self._boat_x, self._boat_y, keel_end_x, keel_end_y, arcade.color.DARK_BROWN, 10)
        arcade.draw_circle_filled(self._boat_x, self._boat_y, 20, arcade.color.NAVY_BLUE)
        mast_end_x = self._boat_x + math.cos(self._sail_angle) * self._mast_length
        mast_end_y = self._boat_y + math.sin(self._sail_angle) * self._mast_length
        arcade.draw_line(self._boat_x, self._boat_y, mast_end_x, mast_end_y, arcade.color.REDWOOD, 5)
        self._draw_sail()

    def _draw_sail(self):
        sail_length = self._mast_length * self._sail_openness
        mast_center_x = self._boat_x + math.cos(self._sail_angle) * sail_length / 2
        mast_center_y = self._boat_y + math.sin(self._sail_angle) * sail_length / 2
        angle_diff = self._wind_angle - self._sail_angle
        if angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        sail_curve_tilt = self._sail_angle
        if not (0 < angle_diff < math.pi):
            sail_curve_tilt += math.pi
        arcade.draw_arc_outline(mast_center_x, mast_center_y, sail_length, self._wind_drag.size / 7.5,
                                arcade.color.WHITE,
                                0, 180, 5, tilt_angle=math.degrees(sail_curve_tilt))

    def _draw_wind_arrow(self):
        center_x = self._wind_arrow_length * 2
        center_y = self.height - self._wind_arrow_length * 2
        arcade.draw_circle_outline(center_x, center_y, self._wind_arrow_length / 1.5, arcade.color.MEDIUM_TURQUOISE)
        self._draw_arrow(center_x, center_y, self._wind_arrow_length, self._wind_angle, arcade.color.METALLIC_SUNBURST, 5)

    @staticmethod
    def _draw_arrow(center_x, center_y, length, angle, color, width, text=""):
        arcade.draw_line(center_x + (length / 2) * math.cos(angle),
                         center_y + (length / 2) * math.sin(angle),
                         center_x - (length / 2) * math.cos(angle),
                         center_y - (length / 2) * math.sin(angle),
                         color, width)
        arcade.draw_triangle_filled(center_x + (length / 2) * math.cos(angle),
                                    center_y + (length / 2) * math.sin(angle),
                                    center_x + (length / 3) * math.cos(angle - math.pi / 8),
                                    center_y + (length / 3) * math.sin(angle - math.pi / 8),
                                    center_x + (length / 3) * math.cos(angle + math.pi / 8),
                                    center_y + (length / 3) * math.sin(angle + math.pi / 8),
                                    color)

        arcade.draw_text(text,
                         center_x + (length / 2) * math.cos(angle) + 3,
                         center_y + (length / 2) * math.sin(angle) + 3,
                         color)

    def _draw_waves(self):

        onscreen_waves_x = self._wave_x_coords[(self._location_x - (self.width / 2) < self._wave_x_coords) &
                                               (self._wave_x_coords < self._location_x + (self.width / 2))]
        onscreen_waves_y = self._wave_y_coords[(self._location_y - (self.height / 2) < self._wave_y_coords) &
                                               (self._wave_y_coords < self._location_y + (self.height / 2))]

        for x_coord in onscreen_waves_x:
            for y_coord in onscreen_waves_y:
                arcade.draw_circle_filled(x_coord - (self._location_x - (self.width / 2)),
                                          y_coord - (self._location_y - (self.height / 2)),
                                          5, arcade.color.WHITE_SMOKE)

    def _draw_borders(self):
        relative_x = self._map_width - self._location_x
        if relative_x < (self.width / 2):
            arcade.draw_xywh_rectangle_filled((self.width / 2) + relative_x, 0, (self.width / 2) - relative_x,
                                              self.height, arcade.color.DARK_BROWN)
        elif self._location_x < (self.width / 2):
            arcade.draw_xywh_rectangle_filled(0, 0, (self.width / 2) - self._location_x, self.height,
                                              arcade.color.DARK_BROWN)
        relative_y = self._map_height - self._location_y
        if relative_y < (self.height / 2):
            arcade.draw_xywh_rectangle_filled(0, (self.height / 2) + relative_y, self.width,
                                              (self.height / 2) - relative_y, arcade.color.DARK_BROWN)
        elif self._location_y < (self.height / 2):
            arcade.draw_xywh_rectangle_filled(0, 0, self.width, (self.height / 2) - self._location_y,
                                              arcade.color.DARK_BROWN)

    def update(self, delta_time):
        self._sail_angle += self._sail_angle_delta * delta_time
        if self._sail_angle > math.pi * 2:
            self._sail_angle -= math.pi * 2
        elif self._sail_angle < 0:
            self._sail_angle += math.pi * 2

        if 0 < self._sail_openness + self._sail_openness_delta * delta_time < 1:
            self._sail_openness += self._sail_openness_delta * delta_time

        self._keel_angle += self._keel_angle_delta * delta_time
        if self._keel_angle > math.pi * 2:
            self._keel_angle -= math.pi * 2
        elif self._keel_angle < 0:
            self._keel_angle += math.pi * 2

        self._speed_x, self._speed_y = self._calculate_speed()
        if 20 < self._location_x + self._speed_x < self._map_width - 20:
            self._location_x += self._speed_x * delta_time * 10
        if 20 < self._location_y + self._speed_y < self._map_height - 20:
            self._location_y += self._speed_y * delta_time * 10

    def _calculate_speed(self):
        apparent_wind_x = self._wind_speed * math.cos(self._wind_angle) - self._speed_x
        apparent_wind_y = self._wind_speed * math.sin(self._wind_angle) - self._speed_y
        apparent_wind_angle = math.atan2(apparent_wind_y, apparent_wind_x)
        apparent_wind_speed = math.sqrt(apparent_wind_x ** 2 + apparent_wind_y ** 2)
        wind_drag_x, wind_drag_y, wind_lift_x, wind_lift_y = self._get_lift_and_drag(apparent_wind_angle,
                                                                                     apparent_wind_speed,
                                                                                     self._sail_angle,
                                                                                     self._sail_openness)

        water_angle = math.atan2(-self._speed_y, -self._speed_x)
        water_speed = math.sqrt(self._speed_x ** 2 + self._speed_y ** 2)
        water_drag_x, water_drag_y, water_lift_x, water_lift_y = self._get_lift_and_drag(water_angle, water_speed, self._keel_angle)

        self._wind_drag = Force.from_cartesian(wind_drag_x, wind_drag_y)
        self._wind_lift = Force.from_cartesian(wind_lift_x, wind_lift_y)
        self._water_drag = Force.from_cartesian(water_drag_x, water_drag_y)
        self._water_lift = Force.from_cartesian(water_lift_x, water_lift_y)

        total_force_x = (wind_drag_x + wind_lift_x + water_drag_x + water_lift_x) / 100
        total_force_y = (wind_drag_y + wind_lift_y + water_drag_y + water_lift_y) / 100

        # Add friction
        total_force_x -= self._speed_x / 10
        total_force_y -= self._speed_y / 10

        return self._speed_x + total_force_x, self._speed_y + total_force_y

    def _get_lift_and_drag(self, resistance_angle, resistance_speed, wing_angle, gating=1):
        attack_angle = resistance_angle - wing_angle + math.pi
        if attack_angle > math.pi:
            attack_angle -= math.pi * 2
        elif attack_angle < -math.pi:
            attack_angle += math.pi * 2
        drag_x = (resistance_speed ** 2) * drag_coef(abs(attack_angle)) * math.cos(resistance_angle) * gating
        drag_y = (resistance_speed ** 2) * drag_coef(abs(attack_angle)) * math.sin(resistance_angle) * gating
        lift_x = (resistance_speed ** 2) * lift_coef(abs(attack_angle)) * \
                 math.cos(resistance_angle + math.copysign(math.pi / 2, attack_angle)) * gating
        lift_y = (resistance_speed ** 2) * lift_coef(abs(attack_angle)) * \
                 math.sin(resistance_angle + math.copysign(math.pi / 2, attack_angle)) * gating
        return [self._cap_to_wind_speed(i) for i in [drag_x, drag_y, lift_x, lift_y]]

    def _cap_to_wind_speed(self, speed):
        return math.copysign(min(abs(speed), abs(self._wind_speed * 10)), speed)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.RIGHT:
            self._sail_angle_delta = -self._sail_move_speed
        elif symbol == arcade.key.LEFT:
            self._sail_angle_delta = self._sail_move_speed
        elif symbol == arcade.key.UP:
            self._sail_openness_delta = self._sail_open_speed
        elif symbol == arcade.key.DOWN:
            self._sail_openness_delta = -self._sail_open_speed
        elif symbol == arcade.key.D:
            self._keel_angle_delta = -self._keel_move_speed
        elif symbol == arcade.key.A:
            self._keel_angle_delta = self._keel_move_speed
        elif symbol == arcade.key.SPACE:
            self._help_mode = HelpModes((self._help_mode.value + 1) % len(HelpModes))

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in [arcade.key.RIGHT, arcade.key.LEFT]:
            self._sail_angle_delta = 0
        elif symbol in [arcade.key.UP, arcade.key.DOWN]:
            self._sail_openness_delta = 0
        elif symbol in [arcade.key.A, arcade.key.D]:
            self._keel_angle_delta = 0


def main():
    game = Pirates(SCREEN_WIDTH, SCREEN_HEIGHT)
    game.setup()
    arcade.run()


if __name__ == "__main__":
    main()
