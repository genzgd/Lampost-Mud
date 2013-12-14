from lampost.context.resource import m_requires
from lampost.env.room import Room
from lampost.lpflavor.setup import GAME_SETTINGS
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate
from lampost.model.player import Player
from lampost.model.race import PlayerRace
from lampost.setup.scripts import build_default_displays, build_default_settings
from lampost.setup.settings import GAME_SETTINGS_DEFAULT, SERVER_SETTINGS_DEFAULT

m_requires('log', 'datastore', __name__)


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















