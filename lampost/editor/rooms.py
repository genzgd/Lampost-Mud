from twisted.web.resource import Resource

from lampost.client.resources import request
from lampost.context.resource import m_requires
from lampost.datastore.exceptions import DataError
from lampost.env.movement import Direction
from lampost.env.room import Room, Exit
from lampost.model.mobile import MobileReset
from lampost.model.article import ArticleReset
from lampost.model.item import BaseItem

m_requires('datastore', 'cls_registry', 'perm', 'mud', __name__)


class RoomResource(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('list', RoomList())
        self.putChild('get', RoomGet())
        self.putChild('create', RoomCreate())
        self.putChild('delete', RoomDelete())
        self.putChild('update', RoomUpdate())
        self.putChild('visit', RoomVisit())
        self.putChild('dir_list', DirList())
        self.putChild('create_exit', CreateExit())
        self.putChild('delete_exit', DeleteExit())


class DirList(Resource):
    @request
    def render_POST(self, content, session):
        return [{'key':direction.key, 'name':direction.desc} for direction in Direction.ordered]


class RoomList(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        if not area:
            raise DataError("Missing Area")
        return [room_stub_dto(room) for room in area.rooms.values()]


class RoomGet(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.room_id, session)
        return room_dto(room)


class RoomCreate(Resource):
    @request
    def render_POST(self, content, session):
        area = mud.get_area(content.area_id)
        check_perm(session, area)
        room_dto = content.room
        room_id = content.area_id + ':' + str(room_dto['id'])
        room = cls_registry(Room)(room_id, room_dto['title'], room_dto['desc'])
        create_object(room)
        area.append_map('rooms', room)
        area.inc_next_room(room_dto['id'])
        save_object(area)
        return {'next_room_id': area.next_room_id, 'room': room_stub_dto(room)}


class RoomDelete(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.room_id, session)
        main_contents = save_contents(room)
        deleted_exits = []
        for my_exit in room.exits:
            other_room = my_exit.destination
            for other_exit in other_room.exits:
                if other_exit.destination == room:
                    other_contents = save_contents(other_room)
                    other_room.exits.remove(other_exit)
                    save_object(other_room, True)
                    restore_contents(other_room, other_contents)
                    deleted_exits.append(exit_dto(other_exit, other_room.dbo_id))
        delete_object(room)
        area.remove_map('rooms', room)
        save_object(area, True)
        for entity in main_contents:
            if entity.dbo_key_type == 'player':
                mud.start_player(entity)
            else:
                entity.detach()
        return deleted_exits


class RoomVisit(Resource):
    @request
    def render_POST(self, content, session):
        room = mud.find_room(content.room_id)
        if not Room:
            raise DataError("ROOM_MISSING")
        session.player.change_env(room)
        session.player.parse('look')


class RoomUpdate(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.id, session)
        contents = save_contents(room)
        room.title = content.title
        room.desc = content.desc
        room.extras = []
        for extra_json in content.extras:
            if extra_json.get('title', None):
                extra = BaseItem()
                hydrate_dbo(extra, extra_json)
                room.append_list('extras', extra)
        room.mobile_resets = []
        for mobile_json in content.mobiles:
            mobile_reset = MobileReset()
            hydrate_dbo(mobile_reset, mobile_json)
            room.append_list('mobile_resets', mobile_reset)
        room.article_resets = []
        for article_json in content.articles:
            article_reset = ArticleReset()
            hydrate_dbo(article_reset, article_json)
            room.append_list('article_reset', article_reset)
        save_object(room, True)
        restore_contents(room, contents)
        return room_dto(room)


class CreateExit(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.start_room, session)
        new_dir = Direction.ref_map[content.direction]
        rev_dir = new_dir.rev_dir
        other_id = content.dest_area + ':' + str(content.dest_id)
        if room.find_exit(new_dir):
            raise DataError("Room already has " + new_dir.key + " exit.")

        if content.is_new:
            if area.get_room(other_id):
                raise DataError("Room " + other_id + " already exists")
            other_room = cls_registry(Room)(other_id, content.dest_title, content.dest_title)
        else:
            other_area, other_room = get_room(other_id, session)
            if not content.one_way and other_room.find_exit(rev_dir):
                raise DataError("Room " + other_id + " already has a " + rev_dir.key + " exit.")

        contents = save_contents(room)
        if content.one_way:
            other_contents = None
        else:
            other_contents = save_contents(other_room)
        this_exit = cls_registry(Exit)(new_dir, other_room, room)
        room.append_list('exits', this_exit)
        save_object(room, True)
        result = {}
        if not content.one_way:
            other_exit = cls_registry(Exit)(rev_dir, room, other_room)
            other_room.append_list('exits', other_exit)
            result['other_exit'] = exit_dto(other_exit, other_id)
        if content.is_new:
            save_object(other_room)
            area.append_map('rooms', other_room)
            area.inc_next_room(content.dest_id)
            result['next_room_id'] = area.next_room_id
            result['new_room'] = room_stub_dto(other_room)
            save_object(area, True)
        elif not content.one_way:
            save_object(other_room, True)
        restore_contents(room, contents)
        if other_contents:
            restore_contents(other_room, other_contents)
        result['exit'] = exit_dto(this_exit, room.dbo_id)
        return result


class DeleteExit(Resource):
    @request
    def render_POST(self, content, session):
        area, room = get_room(content.start_room, session)
        direction = Direction.ref_map[content.dir]
        local_exit = room.find_exit(direction)
        if not local_exit:
            raise DataError('Exit does not exist')
        contents = save_contents(room)
        room.remove_list('exits', local_exit)
        save_object(room, True)
        restore_contents(room, contents)

        result = {'exit': exit_dto(local_exit, room.dbo_id)}
        if not content.both_sides:
            return result
        other_room = local_exit.destination
        other_exit = other_room.find_exit(direction.rev_dir)
        if not other_exit:
            return result
        other_room.remove_list('exits', other_exit)
        if not other_room.dbo_rev and not other_room.exits:
            other_room.dbo_rev = -1
            delete_object(other_room)
            area.remove_map('rooms', other_room)
            result['room_deleted'] = other_room.dbo_id
            save_object(area)
        else:
            result['other_exit'] = exit_dto(other_exit, other_room.dbo_id)
            save_object(other_room)
        return result


def get_room(room_id, session=None):
    area_id = room_id.split(":")[0]
    area = mud.get_area(area_id)
    if not area:
        raise DataError("AREA_MISSING")
    room = area.get_room(room_id)
    if not room:
        raise DataError("ROOM_MISSING")
    if session:
        check_perm(session, area)
    return area, room


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


def room_stub_dto(room):
    return {'id': room.dbo_id, 'title': room.title, 'exit_count': len(room.exits), 'item_count': len(room.article_resets),
            'mobile_count': len(room.mobile_resets), 'extra_count': len(room.extras)}


def exit_dto(room_exit, start_id=None):
    two_way = False
    if room_exit.destination.find_exit(room_exit.direction.rev_dir):
        two_way = True
    return {'start_id': start_id, 'dest_id': room_exit.destination.dbo_id, 'dest_title': room_exit.destination.title,
            'dest_desc': room_exit.destination.desc, 'dir': room_exit.dir_name, 'two_way': two_way}


def mobile_reset_dto(mobile_reset):
    dto = mobile_reset.dto_value
    mobile = mud.get_mobile(mobile_reset.mobile_id)
    if mobile:
        dto['desc'] = mobile.desc if mobile.desc else mobile.title
        dto['title'] = mobile.title
    else:
        dto['desc'] = '<MISSING>'
        dto['title'] = '<MISSING>'
    return dto


def article_reset_dto(article_reset):
    dto = article_reset.dto_value
    article = mud.get_article(article_reset.article_id)
    if article:
        dto['desc'] = article.desc if article.desc else article.title
        dto['title'] = article.title
    else:
        dto['desc'] = '<MISSING>'
        dto['title'] = '<MISSING>'
    return dto


def room_dto(room):
    return {'id': room.dbo_id, 'title': room.title, 'desc': room.desc, 'dbo_rev': room.dbo_rev, 'extras': [extra.dbo_dict for extra in room.extras],
            'exits': [exit_dto(room_exit) for room_exit in room.exits], 'mobiles': [mobile_reset_dto(mobile_reset) for mobile_reset in room.mobile_resets],
            'articles': [article_reset_dto(article_reset) for article_reset in room.article_resets]}
