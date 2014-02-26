def _area_load(type, obj_id, area=None):
    if obj_id.find(':') == -1:
        parent = area if area else _host.parent_id
        obj_id = '{}:{}'.format(obj_id, parent)
    return load_by_key(type, obj_id)


def room(room_id, area_id=None):
    return _area_load('room', room_id, area_id)



