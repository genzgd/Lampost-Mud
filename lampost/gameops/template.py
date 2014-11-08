from lampost.datastore.classes import set_dbo_class, get_dbo_class
from lampost.context.resource import m_requires
from lampost.datastore.auto import TemplateField
from lampost.datastore.dbo import DBOField, RootDBO, RootDBOMeta

m_requires('log', 'datastore', __name__)


class TemplateMeta(RootDBOMeta):
    def __init__(cls, class_name, bases, new_attrs):
        super().__init__(class_name, bases, new_attrs)
        try:
            template_id = cls.template_id
            cls.class_id = '{}_inst'.format(template_id)
            set_dbo_class(cls.class_id, cls)
        except AttributeError:
            template_id = None
            for base in bases:
                template_id = getattr(base, 'template_id', None)
                if template_id:
                    break

        if template_id:
            template_cls = get_dbo_class(template_id)
            template_cls.add_dbo_fields({name: dbo_field for name, dbo_field in cls.dbo_fields.items() if isinstance(dbo_field, TemplateField)})
            template_cls.instance_cls = cls
        elif __debug__:
            print('debug: {} has no template_id'.format(class_name))


class Template(RootDBO):
    dbo_rev = DBOField(0)

    def create_instance(self, owner=None):
        instance = self.instance_cls()
        instance.template = self
        instance.template_id = self.dbo_id
        self.config_instance(instance, owner)
        return instance

    def config_instance(self, instance, owner):
        pass


class TemplateInstance(RootDBO, metaclass=TemplateMeta):
    @classmethod
    def load_ref(cls, dbo_repr, owner=None):
        if hasattr(cls, 'template_id'):
            try:
                template = load_by_key(cls.template_id, dbo_repr['template_id'])
                instance = template.create_instance(owner)
            except KeyError:
                warn("Missing template_id loading template {}".format(dbo_repr))
                return None
            except AttributeError:
                warn("Missing database template loading template {}".format(dbo_repr))
                return None
        else:
            instance = cls()
        instance.hydrate(dbo_repr)
        try:
            instance.on_created()
        except AttributeError:
            pass
        return instance

    @property
    def save_value(self):
        return self.metafields(super().save_value, ['template_id'])
