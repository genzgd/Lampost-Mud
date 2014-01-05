from twisted.web.resource import Resource
from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.editor.base import EditResource
from lampost.env.movement import Direction
from lampost.env.room import Room, Exit
from lampost.model.area import Area
from lampost.model.article import ArticleTemplate
from lampost.model.mobile import MobileTemplate

m_requires('datastore', 'log', 'perm', 'dispatcher', 'cls_registry', 'edit_update_service',  __name__)


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
        add_room(parent_area(room), room, session)
        add_resets(room)

    def pre_update(self, room, session):
        check_perm(session, parent_area(room))
        room.update_contents = save_contents(room)
        clear_resets(room)

    def post_update(self, room, session):
        restore_contents(room, room.update_contents)
        add_resets(room)
        del room.update_contents

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
            add_room(area, other_room, session)
        else:
            other_area, other_room = find_area_room(other_id, session)
            if not content.one_way and other_room.find_exit(rev_dir):
                raise DataError("Room " + other_id + " already has a " + rev_dir.key + " exit.")
        contents = save_contents(room)
        this_exit = cls_registry(Exit)(new_dir, other_room)
        room.exits.append(this_exit)
        save_object(room)
        restore_contents(room, contents)
        publish_edit('update', room, session)
        if not content.one_way:
            other_contents = save_contents(other_room)
            other_exit = cls_registry(Exit)(rev_dir, room)
            other_room.exits.append(other_exit)
            restore_contents(other_room, other_contents)
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
        contents = save_contents(room)
        room.exits.remove(local_exit)
        save_object(room)
        restore_contents(room, contents)

        if content.both_sides:
            other_room = local_exit.destination
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
        session.player.change_env(room)
        room.reset()
        session.player.parse('look')


def add_room(area, room, session):
    area.add_room(room)
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
    save_contents(room)
    for my_exit in room.exits:
        other_room = my_exit.destination
        if other_room and other_room.area_id != area_delete:
            for other_exit in other_room.exits:
                if other_exit.destination == room:
                    other_contents = save_contents(other_room)
                    other_room.exits.remove(other_exit)
                    save_object(other_room, True)
                    restore_contents(other_room, other_contents)
                    publish_edit('update', other_room, session, True)
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
