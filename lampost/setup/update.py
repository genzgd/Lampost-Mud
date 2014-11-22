from lampost.context.resource import m_requires
from lampost.env.room import Room
from lampost.model.area import Area
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate

m_requires(__name__, 'log', 'datastore', 'dispatcher', 'config_manager')


def convert_areas(source):
    for area_id in fetch_set_keys('areas'):
        source.display_line("Starting {}.".format(area_id))
        area_key = 'area:{}'.format(area_id)
        area_dict = load_raw(area_key)
        for coll_type, coll_class in [('rooms', Room), ('mobiles', MobileTemplate),
                                      ('articles', ArticleTemplate)]:
            if coll_type in area_dict:
                set_key = 'area_{}:{}'.format(coll_type, area_id)
                for obj_id in area_dict[coll_type]:
                    if object_exists(coll_class.dbo_key_type, obj_id):
                        add_set_key(set_key, obj_id)
                    else:
                        source.display_line("Missing object {}:{}".format(coll_type, obj_id))
                del area_dict[coll_type]
            save_raw(area_key, area_dict)
    return 'Convert Complete'


def add_display(source, display_key, display_desc, display_color):
    display_desc = str.title(display_desc.replace('_', ' '))
    config_manager.config.default_displays[display_key] = {'desc': display_desc, 'color': display_color}
    config_manager.save_config()


def test_memory(source, *_):

    for area_ix in range(1000):
        area_id = 'perf_test{}'.format(area_ix)
        old_area = load_object(Area, area_id)
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
        old_area = load_object(Area, area_id)
        if old_area:
            delete_object(old_area)


def add_game_setting(source, setting, value):
    config_manager.config.game_settings[setting] = value
    config_manager.save_config()

