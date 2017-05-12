from lampost.di.config import ConfigVal
from lampost.di.resource import Injected, module_inject
from lampost.db.registry import get_dbo_class
from lampost.db.exceptions import DataError
from lampost.editor.editor import Editor, ChildrenEditor

from lampmud.env.movement import Direction

log = Injected('log')
db = Injected('datastore')
perm = Injected('perm')
ev = Injected('dispatcher')
edit_update = Injected('edit_update_service')
module_inject(__name__)


root_area_id = ConfigVal('root_area_id')
default_start_room = ConfigVal('default_start_room')


class AreaEditor(Editor):
    def __init__(self):
        super().__init__('area')

    def _pre_create(self, obj_def, *_):
        if db.object_exists('player', obj_def['dbo_id']):
            raise DataError("Area name should not match any player name.")

    def _pre_delete(self, del_obj, session):
        if del_obj.dbo_id == root_area_id:
            raise DataError("Cannot delete root area.")
        for room in db.load_object_set('room', 'area_rooms:{}'.format(del_obj.dbo_id)):
            room_clean_up(room, session, del_obj.dbo_id)


class RoomEditor(ChildrenEditor):
    def __init__(self):
        super().__init__('room')

    @staticmethod
    def visit(player, room_id,  **_):
        if not player.session:
            raise DataError("You are not logged in")
        room = db.load_object(room_id, 'room')
        if not room:
            raise DataError("ROOM_MISSING")
        room.reload()
        player.change_env(room)

    @staticmethod
    def create_exit(session, player, start_room, direction, dest_id, is_new, one_way, dest_title=None, **_):
        area, room = find_area_room(start_room, player)
        if room.find_exit(direction):
            raise DataError("Room already has " + direction + " exit.")
        rev_dir = Direction.ref_map[direction].rev_key
        other_id = dest_id
        if is_new:
            other_room = db.create_object('room', {'dbo_id': other_id, 'title': dest_title}, False)
            edit_update.publish_edit('create', other_room, session, True)
            update_next_room_id(area, session)
        else:
            other_area, other_room = find_area_room(other_id, player)
            if not one_way and other_room.find_exit(rev_dir):
                raise DataError("Room " + other_id + " already has a " + rev_dir + " exit.")
        this_exit = get_dbo_class('exit')()
        this_exit.dbo_owner = room
        this_exit.direction = direction
        this_exit.destination = other_room
        this_exit.on_loaded()
        room.exits.append(this_exit)
        db.save_object(room)
        edit_update.publish_edit('update', room, session)
        if not one_way:
            other_exit = get_dbo_class('exit')()
            other_exit.dbo_owner = room
            other_exit.direction = rev_dir
            other_exit.destination = room
            other_exit.on_loaded()
            other_room.exits.append(other_exit)
            db.save_object(other_room)
            edit_update.publish_edit('update', other_room, session, True)
        return this_exit.dto_value

    @staticmethod
    def delete_exit(session, player, start_room, direction, both_sides, **_):
        area, room = find_area_room(start_room, player)
        local_exit = room.find_exit(dir)
        if not local_exit:
            raise DataError('Exit does not exist')
        room.exits.remove(local_exit)
        db.save_object(room)

        if both_sides:
            other_room = local_exit.destination
            other_exit = other_room.find_exit(Direction.ref_map[direction].rev_key)
            if other_exit:
                other_room.exits.remove(other_exit)
                if other_room.dbo_ts or other_room.exits:
                    db.save_object(other_room)
                    edit_update.publish_edit('update', other_room, session, True)
                else:
                    db.delete_object(other_room)
                    room_clean_up(room, session)
                    edit_update.publish_edit('delete', other_room, session, True)

    def _post_create(self, room, session):
        update_next_room_id(room.parent_dbo, session)

    def _post_delete(self, room, session):
        room_clean_up(room, session)

    def _post_update(self, room, *_):
        room.reload()


def update_next_room_id(area, session):
    next_id = 0
    sorted_ids = area.dbo_child_keys('room')
    for dbo_id in sorted_ids:
        room_id = int(dbo_id.split(':')[1])
        if room_id == next_id:
            next_id += 1
        else:
            break
    area.next_room_id = next_id
    db.save_object(area)
    edit_update.publish_edit('update', area, session, True)


def find_area_room(room_id, player):
    room = db.load_object(room_id, 'room')
    if not room:
        raise DataError("ROOM_MISSING")
    area = room.parent_dbo
    perm.check_perm(player, area)
    return area, room


def room_clean_up(room, session, area_delete=None):
    start_room = db.load_object(default_start_room.value, 'room')
    for denizen in getattr(room, 'denizens', ()):
        if hasattr(denizen, 'is_player'):
            denizen.display_line('You were in a room that was destroyed by some unknown force')
            denizen.change_env(start_room)
    room.detach()
    for my_exit in room.exits:
        other_room = my_exit.destination
        if other_room and other_room.parent_id != area_delete:
            for other_exit in other_room.exits:
                if not other_exit.destination or other_exit.destination == room:
                    other_room.exits.remove(other_exit)
                    db.save_object(other_room, True)
                    edit_update.publish_edit('update', other_room, session, True)
    update_next_room_id(room.parent_dbo, session)

