from lampost.context.resource import m_requires
from lampost.editor.admin import admin_op
from lampost.env.room import Room
from lampost.model.area import Area
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate
from lampost.model.player import Player

m_requires(__name__, 'log', 'datastore', 'dispatcher', 'config_manager')


@admin_op
def assign_race(race_id):
    race = load_object(race_id, 'race')
    updates = 0
    if not race:
        return "Invalid race specified"
    for player in load_object_set(Player):
        if not player.race:
            info("Assigning race {} to {}", race_id, player.name)
            player.race = race
            save_object(player)
            updates += 1
    return "{} players updated.".format(updates)

def add_display(source, display_key, display_desc, display_color):
    display_desc = str.title(display_desc.replace('_', ' '))
    config_manager.config.default_displays[display_key] = {'desc': display_desc, 'color': display_color}
    config_manager.save_config()


def test_memory(source, *_):

    for area_ix in range(1000):
        area_id = 'perf_test{}'.format(area_ix)
        old_area = load_object(area_id, Area)
        if old_area:
            delete_object(old_area)
        area_dbo = {'dbo_id': area_id}
        create_object(Area, area_dbo)
        for dbo_id in range(100):
            room = {'dbo_id': '{}:{}'.format(area_id, dbo_id), 'desc': area_id * 40, 'title': area_id * 2}
            create_object(Room, room)


def clean_perf(source, *_):
    for area_ix in range(1000):
        area_id = 'perf_test{}'.format(area_ix)
        old_area = load_object(area_id, Area)
        if old_area:
            delete_object(old_area)


def add_game_setting(source, setting, value):
    config_manager.config.game_settings[setting] = value
    config_manager.save_config()

