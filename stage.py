import math


class BoatInitParams:
    def __init__(self, location_x, location_y, sail_openness=1, sail_angel=0, keel_angel=math.pi):
        self.location_x = location_x
        self.location_y = location_y
        self.sail_openness = sail_openness
        self.sail_angel = sail_angel
        self.keel_angel = keel_angel


class Stage:
    def __init__(self, map_width, map_height, boat_init_params, has_keel, has_litter, intro_text, stage_texts,
                 end_condition, litter_spawn_rate=10):
        self.map_width = map_width
        self.map_height = map_height
        self.boat_init_params = boat_init_params
        self.has_keel = has_keel
        self.has_litter = has_litter
        self.intro_text = intro_text
        self.stage_texts = stage_texts
        self.end_condition = end_condition
        self.litter_spawn_rate = litter_spawn_rate
