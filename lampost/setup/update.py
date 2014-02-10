from lampost.context.resource import m_requires
from lampost.env.room import Room
from lampost.lpflavor.combat import AttackTemplate, DefenseTemplate
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate

m_requires('log', 'datastore', 'config_manager', __name__)


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
    display_desc = unicode.title(display_desc.replace('_', ' '))
    config_manager.config.default_displays[display_key] = {'desc': display_desc, 'color': display_color}
    config_manager.save_config()


def fix_subclasses(source):

    for dbo_key in fetch_set_keys('skills'):
        raw_key = '{}:{}'.format('skill', dbo_key)
        class_raw = load_raw(raw_key)
        try:
            class_id = class_raw['class_id']
            class_raw['sub_class_id'] = class_id
            del class_raw['class_id']
            save_raw(raw_key, class_raw)
        except KeyError:
            warn('No class id found in {}'.format(raw_key))


def convert_directions(source):
    for area_id in fetch_set_keys('areas'):
        for room_id in fetch_set_keys('area_rooms:{}'.format(area_id)):
            room_key = 'room:{}'.format(room_id)
            room_raw = load_raw(room_key)
            for exit_dto in room_raw.get('exits', []):
                dir_key = exit_dto['dir_name']
                exit_dto['direction'] = dir_key
                del exit_dto['dir_name']
            print room_raw
            save_raw(room_key, room_raw)
