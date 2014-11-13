from lampost.context.resource import m_requires, register

m_requires(__name__, 'log')


def select_json():
    try:
        ujson = __import__('ujson')
        register('json_decode', ujson.decode)
        register('json_encode', UJsonEncoder(ujson.encode).encode)
        info("Selected ujson JSON library")
    except ImportError:
        json = __import__('json')
        register('json_decode', json.JSONDecoder().decode)
        register('json_encode', json.JSONEncoder().encode)
        info("Defaulted to standard JSON library")


class UJsonEncoder():
    def __init__(self, ujson_encode):
        self.ujson_encode = ujson_encode

    def encode(self, obj):
        return self.ujson_encode(obj, encode_html_chars=True, ensure_ascii=False)
