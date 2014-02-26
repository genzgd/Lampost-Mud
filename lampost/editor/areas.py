from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.datastore.classes import get_dbo_class
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.base import EditResource
from lampost.editor.children import EditChildrenResource, find_parent
from lampost.env.movement import Direction
from lampost.env.room import Room
from lampost.model.area import Area
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate

m_requires('datastore', 'log', 'perm', 'dispatcher', 'edit_update_service', 'config_manager',  __name__)


class AreaResource(EditResource):

    def pre_delete(self, del_obj, session):
        if del_obj.dbo_id == config_manager.root_area:
            raise ActionError("Cannot delete root area.")
        for room in load_object_set(Room, 'area_rooms:{}'.format(del_obj.dbo_id)):
            room_clean_up(room, session, del_obj.dbo_id)


class RoomResource(EditChildrenResource):
    def __init__(self):
        EditChildrenResource.__init__(self, Room)
        self.putChild('visit', RoomVisit())
        self.putChild('create_exit', CreateExit())
        self.putChild('delete_exit', DeleteExit())

    def post_create(self, room, session):
        add_room(find_parent(room), session)

    def post_delete(self, room, session):
        room_clean_up(room, session)

    def post_update(self, room, session):
        room.reload()


class CreateExit(Resource):
    @request
    def render_POST(self, content, session):
        area, room = find_area_room(content.start_room, session)
        new_dir = Direction.ref_map[content.direction]
        if room.find_exit(new_dir):
            raise DataError("Room already has " + new_dir.dbo_id + " exit.")
        rev_dir = new_dir.rev_dir
        other_id = content.dest_id
        if content.is_new:
            other_room = create_object(Room, {'dbo_id': other_id, 'title': content.dest_title, 'dbo_rev': -1})
            publish_edit('create', other_room, session, True)
            add_room(area,  session)
        else:
            other_area, other_room = find_area_room(other_id, session)
            if not content.one_way and other_room.find_exit(rev_dir):
                raise DataError("Room " + other_id + " already has a " + rev_dir.obj_id + " exit.")
        this_exit = get_dbo_class('exit')()
        this_exit.direction = new_dir
        this_exit.destination = other_id
        room.exits.append(this_exit)
        save_object(room)
        publish_edit('update', room, session)
        if not content.one_way:
            other_exit = get_dbo_class('exit')()
            other_exit.direction = rev_dir
            other_exit.destination = room.dbo_id
            other_room.exits.append(other_exit)
            save_object(other_room)
            publish_edit('update', other_room, session, True)
        return this_exit.dto_value


class DeleteExit(Resource):
    @request
    def render_POST(self, content, session):
        area, room = find_area_room(content.start_room, session)
        direction = Direction.ref_map[content.dir]
        local_exit = room.find_exit(direction)
        if not local_exit:
            raise DataError('Exit does not exist')
        room.exits.remove(local_exit)
        save_object(room)

        if content.both_sides:
            other_room = local_exit.dest_room
            other_exit = other_room.find_exit(direction.rev_dir)
            if other_exit:
                other_room.exits.remove(other_exit)
                if other_room.dbo_rev or other_room.exits:
                    save_object(other_room)
                    publish_edit('update', other_room, session, True)
                else:
                    delete_object(other_room)
                    room_clean_up(room, session)
                    publish_edit('delete', other_room, session, True)


class RoomVisit(Resource):
    @request
    def render_POST(self, content, session):
        room = load_object(Room, content.room_id)
        if not room:
            raise DataError("ROOM_MISSING")
        room.reset()
        session.player.change_env(room)


def add_room(area, session):
    area.add_room()
    publish_edit('update', area, session, True)


def find_area_room(room_id, session=None):
    room = load_object(Room, room_id)
    if not room:
        raise DataError("ROOM_MISSING")
    area = find_parent(room)
    if session:
        check_perm(session, area)
    return area, room


def room_clean_up(room, session, area_delete=None):
    start_room = load_object(Room, config_manager.start_room)
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
                if other_exit.destination == room:
                    other_room.exits.remove(other_exit)
                    save_object(other_room, True)
                    publish_edit('update', other_room, session, True)
    room.clean_up()
