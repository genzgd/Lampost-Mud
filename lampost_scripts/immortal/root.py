def _area_load(load_type, obj_id, area=None):
    if obj_id.find(':') == -1:
        parent = area if area else _host.parent_id
        obj_id = '{}:{}'.format(parent, obj_id)
    return load_by_key(load_type, obj_id)


def room(room_id, area_id=None):
    return _area_load('room', str(room_id), area_id)

#Le Comment