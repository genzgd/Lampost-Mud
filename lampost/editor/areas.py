from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.datastore.classes import get_dbo_class
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.base import EditResource
from lampost.env.movement import Direction
from lampost.env.room import Room
from lampost.model.area import Area
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate

m_requires('datastore', 'log', 'perm', 'dispatcher', 'edit_update_service', 'config_manager',  __name__)


class AreaResource(EditResource):

    def post_delete(self, del_area, session):
        for room in del_area.rooms.itervalues():
            room_clean_up(room, session, del_area.dbo_id)
        delete_object_set(Room, 'area_rooms:{}'.format(del_area.dbo_id))
        delete_object_set(MobileTemplate, 'area_mobiles:{}'.format(del_area.dbo_id))
        delete_object_set(ArticleTemplate, 'area_articles:{}'.format(del_area.dbo_id))


class AreaListResource(Resource):
    def __init__(self, obj_class):
        Resource.__init__(self)
        self.obj_class = obj_class

    def getChild(self, area_id, request):
        return AreaListLeaf(self.obj_class, area_id)


class AreaListLeaf(Resource):
    def __init__(self, obj_class, area_id):
        Resource.__init__(self)
        self.obj_class = obj_class
        self.area_id = area_id
        self.imm_level = 'admin'

    @request
    def render_POST(self):
        set_key = 'area_{}s:{}'.format(self.obj_class.dbo_key_type, self.area_id)
        return [obj.dto_value for obj in load_object_set(self.obj_class, set_key)]


class RoomResource(EditResource):
    def __init__(self):
        EditResource.__init__(self, Room)
        self.putChild('list', AreaListResource(Room))
        self.putChild('visit', RoomVisit())
        self.putChild('create_exit', CreateExit())
        self.putChild('delete_exit', DeleteExit())

    def pre_create(self, room_dto, session):
        area = parent_area(room_dto)
        check_perm(session, area)

    def post_create(self, room, session):
        add_room(parent_area(room), session)
        add_resets(room)

    def pre_update(self, room, new_dto, session):
        check_perm(session, parent_area(room))
        clear_resets(room)

    def post_update(self, room, session):
        add_resets(room)

    def pre_delete(self, room, session):
        check_perm(session, parent_area(room))

    def post_delete(self, room, session):
        room_clean_up(room, session)
        clear_resets(room)


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
            other_room = create_object(Room, {'dbo_id': other_id, 'title': content.dest_title, 'dbo_rev': -1})
            publish_edit('create', other_room, session, True)
            add_room(area,  session)
        else:
            other_area, other_room = find_area_room(other_id, session)
            if not content.one_way and other_room.find_exit(rev_dir):
                raise DataError("Room " + other_id + " already has a " + rev_dir.key + " exit.")
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
    area = parent_area(room)
    if session:
        check_perm(session, area)
    return area, room


def parent_area(child):
    try:
        dbo_id = child.dbo_id
    except AttributeError:
        dbo_id = child['dbo_id']
    area = load_object(Area, dbo_id.split(':')[0])
    if not area:
        raise DataError("Area Missing")
    return area


def room_clean_up(room, session, area_delete=None):
    for my_exit in room.exits:
        other_room = my_exit.dest_room
        if other_room and other_room.area_id != area_delete:
            for other_exit in other_room.exits:
                if other_exit.destination == room:
                    other_room.exits.remove(other_exit)
                    save_object(other_room, True)
                    publish_edit('update', other_room, session, True)
    for denizen in room.denizens:
        if hasattr(denizen, 'is_player'):
            denizen.display_line('You were in a room that was destroyed by some unknown force')
            safe_room = load_object(Room, config_manager.start_room)
            if not safe_room:
                safe_room = Room('temp:safe')
                safe_room.title = "Safe Room"
                safe_room.desc = "A temporary safe room when room deleted"
            denizen.change_env(safe_room)
        else:
            denizen.die()
    for thing in [thing for thing in room.contents if hasattr(thing, 'detach')]:
        thing.detach()
    if not area_delete:
        try:
            parent_area(room).rooms.pop(room.dbo_id)
        except KeyError:
            warn("Trying to remove room {} not found in area".format(room.dbo_id))


def add_resets(room):
    for mobile_reset in room.mobile_resets:
        add_set_key(mobile_reset.reset_key, room.dbo_id)
    for article_reset in room.article_resets:
        add_set_key(article_reset.reset_key, room.dbo_id)


def clear_resets(room):
    for mobile_reset in room.mobile_resets:
        delete_set_key(mobile_reset.reset_key, room.dbo_id)
    for article_reset in room.article_resets:
        delete_set_key(article_reset.reset_key, room.dbo_id)
