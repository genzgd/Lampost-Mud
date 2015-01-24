from lampost.datastore.classes import get_dbo_class
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.editor import Editor, ChildrenEditor
from lampost.env.movement import Direction
from lampost.env.room import Room
from lampost.model.area import Area

m_requires(__name__, 'datastore', 'log', 'perm', 'dispatcher', 'edit_update_service')

m_configured(__name__, 'root_area_id', 'default_start_room')


class AreaEditor(Editor):
    def initialize(self):
        super().initialize(Area)

    def _pre_create(self):
        if object_exists('player', self.raw['dbo_id']):
            raise DataError("Area name should not match any player name.")

    def _pre_delete(self, del_obj):
        if del_obj.dbo_id == root_area_id:
            raise DataError("Cannot delete root area.")
        for room in load_object_set(Room, 'area_rooms:{}'.format(del_obj.dbo_id)):
            room_clean_up(room, self.session, del_obj.dbo_id)


class RoomEditor(ChildrenEditor):
    def initialize(self):
        super().initialize(Room)

    def visit(self):
        if not self.session.player.session:
            raise DataError("You are not logged in")
        room = load_object(self.raw['room_id'], Room)
        if not room:
            raise DataError("ROOM_MISSING")
        room.reload()
        self.session.player.change_env(room)

    def create_exit(self):
        content = self._content()
        area, room = find_area_room(content.start_room, self.player)
        new_dir = content.direction
        if room.find_exit(content.direction):
            raise DataError("Room already has " + new_dir + " exit.")
        rev_dir = Direction.ref_map[new_dir].rev_key
        other_id = content.dest_id
        if content.is_new:
            other_room = create_object(Room, {'dbo_id': other_id, 'title': content.dest_title, 'dbo_rev': -1})
            publish_edit('create', other_room, self.session, True)
            update_next_room_id(area, self.session)
        else:
            other_area, other_room = find_area_room(other_id, self.player)
            if not content.one_way and other_room.find_exit(rev_dir):
                raise DataError("Room " + other_id + " already has a " + rev_dir + " exit.")
        this_exit = get_dbo_class('exit')()
        this_exit.direction = new_dir
        this_exit.destination = other_id
        this_exit.on_loaded()
        room.exits.append(this_exit)
        save_object(room)
        publish_edit('update', room, self.session)
        if not content.one_way:
            other_exit = get_dbo_class('exit')()
            other_exit.direction = rev_dir
            other_exit.destination = room.dbo_id
            other_exit.on_loaded()
            other_room.exits.append(other_exit)
            save_object(other_room)
            publish_edit('update', other_room, self.session, True)
        return this_exit.dto_value

    def delete_exit(self):
        content = self._content()
        area, room = find_area_room(content.start_room, self.player)
        local_exit = room.find_exit(content.dir)
        if not local_exit:
            raise DataError('Exit does not exist')
        room.exits.remove(local_exit)
        save_object(room)

        if content.both_sides:
            other_room = local_exit.dest_room
            other_exit = other_room.find_exit(Direction.ref_map[content.dir].rev_key)
            if other_exit:
                other_room.exits.remove(other_exit)
                if other_room.dbo_rev or other_room.exits:
                    save_object(other_room)
                    publish_edit('update', other_room, self.session, True)
                else:
                    delete_object(other_room)
                    room_clean_up(room, self.session)
                    publish_edit('delete', other_room, self.session, True)


    def _post_create(self, room):
        update_next_room_id(room.parent_dbo, self.session)

    def _post_delete(self, room):
        room_clean_up(room, self.session)

    def _post_update(self, room):
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
    save_object(area)
    publish_edit('update', area, session, True)


def find_area_room(room_id, player):
    room = load_object(room_id, Room)
    if not room:
        raise DataError("ROOM_MISSING")
    area = room.parent_dbo
    check_perm(player, area)
    return area, room


def room_clean_up(room, session, area_delete=None):
    start_room = load_object(default_start_room, Room)
    if not start_room:
        start_room = safe_room
    for denizen in room.denizens:
        if hasattr(denizen, 'is_player'):
            denizen.display_line('You were in a room that was destroyed by some unknown force')
            denizen.change_env(start_room)
    for my_exit in room.exits:
        other_room = my_exit.dest_room
        if other_room and other_room.parent_id != area_delete:
            for other_exit in other_room.exits:
                if other_exit.destination == room.dbo_id:
                    other_room.exits.remove(other_exit)
                    save_object(other_room, True)
                    publish_edit('update', other_room, session, True)
    room.clean_up()
    update_next_room_id(room.parent_dbo, session)
