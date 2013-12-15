from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires, requires
from lampost.datastore.exceptions import DataError
from lampost.editor.base import EditResource
from lampost.env.movement import Direction
from lampost.env.room import Room, Exit
from lampost.model.area import Area
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate

m_requires('datastore', 'log', 'perm', 'dispatcher', 'cls_registry', 'edit_update_service',  __name__)


class AreaResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, Area)

    def on_delete(self, del_area, session):
        for room in del_area.rooms.itervalues():
            delete_room_exits(room, session, del_area.dbo_id)
        delete_object_set(Room, 'area_rooms:{}'.format(del_area.dbo_id))
        delete_object_set(MobileTemplate, 'area_mobiles:{}'.format(del_area.dbo_id))
        delete_object_set(ArticleTemplate, 'area_articles:{}'.format(del_area.dbo_id))


class AreaListResource(Resource):
    def __init__(self, list_class):
        Resource.__init__(self)
        self.list_class = list_class

    def getChild(self, area_id, request):
        return self.list_class(area_id)


class RoomResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, Room)
        self.putChild('list', AreaListResource(RoomListResource))
        self.putChild('visit', RoomVisit())
        self.putChild('create_exit', CreateExit())

    def pre_create(self, room_dto, session):
        area = room_area(room_dto)
        check_perm(session, area)

    def on_create(self, room, session):
        add_room(room_area(room), room, session)

    def pre_delete(self, room, session):
        check_perm(session, room_area(room))

    def on_delete(self, room, session):
        save_contents(room)
        delete_room_exits(room, session)
        try:
            room_area(room).rooms.pop(room.dbo_id)
        except KeyError:
            warn("Trying to remove room {} not found in area").format(room_dbo_id)


class RoomListResource(Resource):
    def __init__(self, area_id):
        Resource.__init__(self)
        self.area_id = area_id
        self.imm_level = 'admin'

    @request
    def render_POST(self):
        return [room.dto_value for room in load_object_set(Room, 'area_rooms:{}'.format(self.area_id))]


class CreateExit(Resource):
    @request
    def render_POST(self, content, session):
        area, room = find_area_room(content.start_room, session)
        new_dir = Direction.ref_map[content.direction]
        if room.find_exit(new_dir):
            raise DataError("Room already has " + new_dir.key + " exit.")
        rev_dir = new_dir.rev_dir
        other_id = content.dest_id
        if content.is_new:
            if load_object(Room, other_id):
                raise DataError("Room " + other_id + " already exists")
            other_room = cls_registry(Room)(other_id, content.dest_title, content.dest_title)
        else:
            other_area, other_room = find_area_room(other_id, session)
            if not content.one_way and other_room.find_exit(rev_dir):
                raise DataError("Room " + other_id + " already has a " + rev_dir.key + " exit.")
        contents = save_contents(room)
        this_exit = cls_registry(Exit)(new_dir, other_room, room)
        room.append_list('exits', this_exit)
        save_object(room)
        restore_contents(room, contents)
        publish_edit('update', room, session)
        if not content.one_way:
            other_contents = save_contents(other_room)
            other_exit = cls_registry(Exit)(rev_dir, room, other_room)
            other_room.append_list('exits', other_exit)
            restore_contents(other_room, other_contents)
            if not content.is_new:
                save_object(other_room, True)
                publish_edit('update', room, session, True)
        if content.is_new:
            save_object(other_room)
            publish_edit('create', other_room, session, True)
            add_room(area, other_room, session)
        return this_exit.dbo_dict


class RoomVisit(Resource):
    @request
    def render_POST(self, content, session):
        room = load_object(Room, content.room_id)
        if not room:
            raise DataError("ROOM_MISSING")
        session.player.change_env(room)
        session.player.parse('look')


def add_room(area, room, session):
    area.add_room(room)
    publish_edit('update', area.dto_value, session, True)


def find_area_room(room_id, session=None):
    room = load_object(Room, room_id)
    if not room:
        raise DataError("ROOM_MISSING")
    area = room_area(room)
    if session:
        check_perm(session, area)
    return area, room


def room_area(room):
    try:
        dbo_id = room.dbo_id
    except AttributeError:
        dbo_id = room['dbo_id']
    area = load_object(Area, dbo_id.split(':')[0])
    if not area:
        raise DataError("Area Missing")
    return area


def delete_room_exits(room, session, area_delete=None):
    for my_exit in room.exits:
        other_room = my_exit.destination
        if not other_room or other_room.area_id == area_delete:
            continue
        for other_exit in other_room.exits:
            if other_exit.destination == room:
                other_contents = save_contents(other_room)
                other_room.exits.remove(other_exit)
                save_object(other_room, True)
                restore_contents(other_room, other_contents)
                publish_edit('update', other_room, session, True)


def save_contents(start_room):
    safe_room = Room("safe_room", "A Temporary Safe Room")
    contents = []
    for entity in start_room.contents[:]:
        if hasattr(entity, 'change_env'):
            entity.change_env(safe_room)
            contents.append(entity)
    return contents


def restore_contents(room, contents):
    for entity in contents:
        entity.change_env(room)
