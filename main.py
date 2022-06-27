import math
import random
import time

import arcade
import numpy as np
import enum

from onscreen_text import OnscreenText
from sail_force import lift_coef, drag_coef, Force
from stage import Stage, BoatInitParams

SCREEN_WIDTH = 1300
SCREEN_HEIGHT = 750
BACKGROUND_COLOR = arcade.color.OCEAN_BOAT_BLUE


class HelpModes(enum.Enum):
    NO_HELP = 0
    WIND = 1
    ALL = 2


class Pirates(arcade.Window):
    def __init__(self, width, height, stages):
        super().__init__(width, height)
        arcade.set_background_color(BACKGROUND_COLOR)
        self._stages = stages
        self._stage = stages[0]
        self._stage_index = 0
        self._is_started = False
        self._is_finished = False
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
        self._location_x = 0
        self._location_y = 0
        self._wave_margin = width / 10
        self._wave_x_coords = []
        self._wave_y_coords = []
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
        self._litters = []
        self._last_spawn_time = 0
        self._reach_distance = 30
        self._last_collect_time = 0
        self._collect_message_display_time = 1
        self._score = 0

    def on_draw(self):
        """ Render the screen. """
        arcade.start_render()
        if not self._is_started:
            if self._is_finished:
                self._draw_end_screen()
            else:
                self._draw_intro_screen()
            return

        self._draw_waves()
        self._draw_litter()
        self._draw_boat()
        self._draw_borders()
        self._draw_wind_arrow()
        self._draw_force_scaffolds()
        self._draw_messages()
        self._draw_score()
        self._draw_onscreen_texts()

    def _draw_onscreen_texts(self):
        for text in self._stage.stage_texts:
            if self._is_location_in_screen_visibility(text.location_x, text.location_y):
                arcade.draw_text(text.text,
                                 text.location_x - (self._location_x - (self.width / 2)),
                                 text.location_y - (self._location_y - (self.height / 2)),
                                 font_size=text.size, **text.kwargs)

    def _is_location_in_screen_visibility(self, location_x, location_y):
        return (self._location_x - (self.width / 2) < location_x < self._location_x + (self.width / 2) and
                self._location_y - (self.height / 2) < location_y < self._location_y + (self.height / 2))

    def _draw_intro_screen(self):
        arcade.draw_text(self._stage.intro_text, self.width * 2 / 5, self.height / 2, width=self.width / 2, font_size=20, multiline=True)

    def _draw_end_screen(self):
        arcade.draw_text(heb("זה הכל, תודה ששיחקתם!"), self.width * 2 / 5, self.height / 2, width=self.width / 2, font_size=20, multiline=True)

    def _draw_score(self):
        arcade.draw_text(" {}".format(self._score), 300, self.height - 100)

    def _draw_messages(self):
        if time.time() - self._last_collect_time < self._collect_message_display_time:
            arcade.draw_text(" +100", self._boat_x * 1.05, self._boat_y * 1.05, arcade.color.GREEN, bold=True)

    def _draw_litter(self):
        for litter in self._litters:
            if self._is_location_in_screen_visibility(litter[0], litter[1]):
                arcade.draw_circle_filled(litter[0] - (self._location_x - (self.width / 2)),
                                          litter[1] - (self._location_y - (self.height / 2)),
                                          8, arcade.color.BULGARIAN_ROSE)

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
        if self._stage.has_keel:
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
        relative_x = self._stage.map_width - self._location_x
        if relative_x < (self.width / 2):
            arcade.draw_xywh_rectangle_filled((self.width / 2) + relative_x, 0, (self.width / 2) - relative_x,
                                              self.height, arcade.color.DARK_BROWN)
        if self._location_x < (self.width / 2):
            arcade.draw_xywh_rectangle_filled(0, 0, (self.width / 2) - self._location_x, self.height,
                                              arcade.color.DARK_BROWN)
        relative_y = self._stage.map_height - self._location_y
        if relative_y < (self.height / 2):
            arcade.draw_xywh_rectangle_filled(0, (self.height / 2) + relative_y, self.width,
                                              (self.height / 2) - relative_y, arcade.color.DARK_BROWN)
        if self._location_y < (self.height / 2):
            arcade.draw_xywh_rectangle_filled(0, 0, self.width, (self.height / 2) - self._location_y,
                                              arcade.color.DARK_BROWN)

    def update(self, delta_time):
        if not self._is_started:
            return
        elif self._stage.end_condition(self):
            self._end_stage()
            return

        self._sail_angle = self._cap_angle(self._sail_angle + self._sail_angle_delta * delta_time)
        self._sail_openness = np.clip(self._sail_openness + self._sail_openness_delta * delta_time, 0, 1)
        if self._stage.has_keel:
            self._keel_angle = self._cap_angle(self._keel_angle + self._keel_angle_delta * delta_time)

        self._speed_x, self._speed_y = self._calculate_speed()
        self._location_x = np.clip(self._location_x + self._speed_x * delta_time * 10, 20, self._stage.map_width - 20)
        self._location_y = np.clip(self._location_y + self._speed_y * delta_time * 10, 20, self._stage.map_height - 20)

        if self._stage.has_litter:
            self._spawn_litter()
            self._litter_interaction()

    def _litter_interaction(self):
        for litter in self._litters:
            if math.dist(litter, (self._location_x, self._location_y)) < self._reach_distance:
                self._litters.remove(litter)
                self._last_collect_time = time.time()
                self._score += 100

    def _spawn_litter(self):
        if time.time() - self._last_spawn_time > self._stage.litter_spawn_rate:
            litter = (random.random() * self._stage.map_width, random.random() * self._stage.map_height)
            self._litters.append(litter)
            self._last_spawn_time = time.time()

    @staticmethod
    def _cap_angle(angle):
        if angle > math.pi * 2:
            angle -= math.pi * 2
        elif angle < 0:
            angle += math.pi * 2
        return angle

    def _calculate_speed(self):
        apparent_wind_x = self._wind_speed * math.cos(self._wind_angle) - self._speed_x
        apparent_wind_y = self._wind_speed * math.sin(self._wind_angle) - self._speed_y
        apparent_wind_angle = math.atan2(apparent_wind_y, apparent_wind_x)
        apparent_wind_speed = math.sqrt(apparent_wind_x ** 2 + apparent_wind_y ** 2)
        wind_drag_x, wind_drag_y, wind_lift_x, wind_lift_y = self._get_lift_and_drag(apparent_wind_angle,
                                                                                     apparent_wind_speed,
                                                                                     self._sail_angle,
                                                                                     self._sail_openness ** 2)

        water_angle = math.atan2(-self._speed_y, -self._speed_x)
        water_speed = math.sqrt(self._speed_x ** 2 + self._speed_y ** 2)
        if self._stage.has_keel:
            water_drag_x, water_drag_y, water_lift_x, water_lift_y = self._get_lift_and_drag(water_angle, water_speed, self._keel_angle)
        else:
            water_drag_x, water_drag_y, water_lift_x, water_lift_y = [0, 0, 0, 0]

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
        if not self._is_started and not self._is_finished:
            if symbol == arcade.key.SPACE:
                self._start_stage()
            return

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
        elif symbol == arcade.key.H:
            self._help_mode = HelpModes((self._help_mode.value + 1) % len(HelpModes))

    def _start_stage(self):
        self._location_x = self._stage.boat_init_params.location_x
        self._location_y = self._stage.boat_init_params.location_y
        self._sail_angle = self._stage.boat_init_params.sail_angel
        self._sail_openness = self._stage.boat_init_params.sail_openness
        self._wave_x_coords = np.arange(0, self._stage.map_width, self._wave_margin)
        self._wave_y_coords = np.arange(0, self._stage.map_height, self._wave_margin)
        self._litters = []
        self._last_spawn_time = 0
        self._last_collect_time = 0
        self._score = 0
        self._is_started = True

    def _end_stage(self):
        self._is_started = False
        self._stage_index += 1
        if self._stage_index < len(self._stages):
            self._stage = self._stages[self._stage_index]
        else:
            self._is_finished = True

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol in [arcade.key.RIGHT, arcade.key.LEFT]:
            self._sail_angle_delta = 0
        elif symbol in [arcade.key.UP, arcade.key.DOWN]:
            self._sail_openness_delta = 0
        elif symbol in [arcade.key.A, arcade.key.D]:
            self._keel_angle_delta = 0

    def is_at_the_end_of_horizontal_stage(self):
        return self._location_x > self._stage.map_width * 9 / 10

    def is_at_the_end_of_vertical_stage(self):
        return self._location_y > self._stage.map_height * 9 / 10

    def is_at_the_start_of_horizontal_stage(self):
        return self._location_x < self._stage.map_width / 10

    def is_score_enough(self):
        return self._score >= 1000


def main():
    stage1_texts = [
        OnscreenText(heb("השתמשו בחצים ימינה ושמאלה כדי להזיז את המפרש"), -SCREEN_WIDTH / 10, SCREEN_HEIGHT * 2.3 / 4, 20),
        OnscreenText(heb("יופי! המשיכו הלאה!"), SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2.3 / 4, 20),
    ]
    stage1 = Stage(SCREEN_WIDTH * 4, SCREEN_HEIGHT / 2, BoatInitParams(SCREEN_WIDTH / 10, SCREEN_HEIGHT / 4), False,
                    False, heb("ברוכים הבאים למשחק!", "במשחק זה תלמדו להשיט סירת מפרש", "לחצו רווח כדי להתחיל"), stage1_texts,
                    Pirates.is_at_the_end_of_horizontal_stage)
    stage2_texts = [
        OnscreenText(heb("השתמשו בחצים למעלה ולמטה כדי לפתוח/לסגור את המפרש"), -SCREEN_WIDTH / 10, SCREEN_HEIGHT * 2.3 / 4, 20),
    ]
    stage2 = Stage(SCREEN_WIDTH * 3, SCREEN_HEIGHT / 2, BoatInitParams(SCREEN_WIDTH / 10, SCREEN_HEIGHT / 4, 0, math.pi / 2),
                   False, False, heb("כל הכבוד!", "לחצו רווח כדי להמשיך לשלב הבא"), stage2_texts,
                   Pirates.is_at_the_end_of_horizontal_stage)
    stage3_texts = [
        OnscreenText(heb("לחצו על A ו-D כדי להזיז את הסנפיר"), -SCREEN_WIDTH / 10, SCREEN_HEIGHT * 2.3 / 4, 20),
        OnscreenText(heb("נסו לאסוף את הליכלוך!"), SCREEN_WIDTH * 1.5, SCREEN_HEIGHT * 2.3 / 4, 20),
    ]
    stage3 = Stage(SCREEN_WIDTH * 6, SCREEN_HEIGHT / 2, BoatInitParams(SCREEN_WIDTH / 10, SCREEN_HEIGHT / 4), True,
                   True, heb("אחלה!", "עכשיו נכיר חלק נוסף של הסירה: הסנפיר"), stage3_texts,
                   Pirates.is_at_the_end_of_horizontal_stage, 1.5)
    stage4_texts = [
        OnscreenText(heb("נסו לזוז למעלה!",
                     "מקמו את הסנפיר למטה, ",
                     # Since the text is reversed, we write 54 so it'll be written as 45
                     "ושימו את המפרש בזווית של 54 מעלות עם הרוח"),
                     0, -SCREEN_HEIGHT / 8, 20, multiline=True, width=SCREEN_WIDTH / 2),
        OnscreenText(heb("אתם על זה!"), SCREEN_WIDTH * 4 / 10, SCREEN_HEIGHT * 1.5, 20),
    ]
    stage4 = Stage(SCREEN_WIDTH / 3, SCREEN_HEIGHT * 3, BoatInitParams(SCREEN_WIDTH / 6, SCREEN_HEIGHT / 10), True,
                   False, heb("לזוז בכוון הרוח זה קל", "עכשיו ננסה לזוז במאונך לרוח"), stage4_texts,
                   Pirates.is_at_the_end_of_vertical_stage)
    stage5_texts = [
        OnscreenText(heb("מקמו את הסנפיר למטה, ",
                         # Since the text is reversed, we write 54 so it'll be written as 45
                         "ושימו את המפרש בזווית של 54 מעלות עם הרוח"),
                     0, -SCREEN_HEIGHT / 8, 20, multiline=True, width=SCREEN_WIDTH / 2),
        OnscreenText(heb("השתמשו בסנפיר כדי לכוון"), SCREEN_WIDTH * 4 / 10, SCREEN_HEIGHT * 1.5, 20),
    ]
    stage5 = Stage(SCREEN_WIDTH / 3, SCREEN_HEIGHT * 6, BoatInitParams(SCREEN_WIDTH / 6, SCREEN_HEIGHT / 10), True,
                   True, heb("יפה מאוד!", "עכשיו נסו לאסוף לכלוך תוך כדי"), stage5_texts,
                   Pirates.is_at_the_end_of_vertical_stage, 1.5)
    stage6_texts = [
        OnscreenText(heb("נסו לעלות לרוח!",
                         "תוך כדי שאתם זזים למעלה כמו שלמדתם,",
                         "הזיזו את הסנפיר מעט ימינה"),
                     SCREEN_WIDTH * 2, 0, 20, multiline=True, width=SCREEN_WIDTH / 2),
        OnscreenText(heb("נסו לעלות לרוח!",
                         "תוך כדי שאתם זזים למטה כמו שלמדתם,",
                         "הזיזו את הסנפיר מעט שמאלה"),
                     SCREEN_WIDTH * 2, SCREEN_HEIGHT, 20, multiline=True, width=SCREEN_WIDTH / 2),
        OnscreenText(heb("לא להתייאש, אתם כמעט שם!"), SCREEN_WIDTH, SCREEN_HEIGHT / 2, 20, color=arcade.color.BLACK)
    ]
    stage6 = Stage(SCREEN_WIDTH * 2, SCREEN_HEIGHT, BoatInitParams(SCREEN_WIDTH * 1.9, SCREEN_HEIGHT / 10), True,
                   False, heb("מעולה!", "עכשיו ננסה לזוז כנגד הרוח"), stage6_texts,
                   Pirates.is_at_the_start_of_horizontal_stage)
    stage7 = Stage(SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2, BoatInitParams(SCREEN_WIDTH, SCREEN_HEIGHT), True,
                   True, heb("מדהים! אתם מלחים של ממש עכשיו", "בשלב הבא נסו לאסוף כמה שיותר לכלוך"), [],
                   Pirates.is_score_enough, 7)
    game = Pirates(SCREEN_WIDTH, SCREEN_HEIGHT, [stage1, stage2, stage3, stage4, stage5, stage6, stage7])
    arcade.run()


def heb(*texts):
    return "\n".join("".join(reversed(text)) for text in texts)


if __name__ == "__main__":
    main()
