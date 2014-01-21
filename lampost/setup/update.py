from lampost.context.resource import m_requires
from lampost.datastore.exceptions import ObjectExistsError
from lampost.env.feature import FeatureTemplate
from lampost.env.room import Room
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate

m_requires('log', 'datastore', 'cls_registry',  __name__)


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


def add_feature(source, feature_name):
    if cls_registry(feature_name):
        try:
            create_object(FeatureTemplate, {'dbo_id': feature_name, 'instance_class_id': feature_name})
        except ObjectExistsError:
            return "Feature template already exists"
        return "{} created.".format(feature_name)
    else:
        return "No appropriate feature class found"


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
















