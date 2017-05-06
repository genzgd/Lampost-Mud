from lampost.di.resource import Injected, module_inject
from lampost.editor.admin import admin_op

log = Injected('log')
db = Injected('datastore')
ev = Injected('dispatcher')
module_inject(__name__)


@admin_op
def assign_race(race_id):
    race = db.load_object(race_id, 'race')
    updates = 0
    if not race:
        return "Invalid race specified"
    for player in db.load_object_set('player'):
        if not player.race:
            log.info("Assigning race {} to {}", race_id, player.name)
            player.race = race
            db.save_object(player)
            updates += 1
    return "{} players updated.".format(updates)


def test_memory(*_):
    for area_ix in range(1000):
        area_id = 'perf_test{}'.format(area_ix)
        old_area = db.load_object(area_id, 'area')
        if old_area:
            db.delete_object(old_area)
        area_dbo = {'dbo_id': area_id}
        db.create_object('area', area_dbo)
        for dbo_id in range(100):
            room = {'dbo_id': '{}:{}'.format(area_id, dbo_id), 'desc': area_id * 40, 'title': area_id * 2}
            db.create_object('room', room)


def clean_perf(*_):
    for area_ix in range(1000):
        area_id = 'perf_test{}'.format(area_ix)
        old_area = db.load_object(area_id, 'area')
        if old_area:
            db.delete_object(old_area)

