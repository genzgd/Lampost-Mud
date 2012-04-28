'''
Created on Apr 14, 2012

@author: Geoff
'''
class TemplateException(Exception):
    pass

class Template(object):
    class_map = {}
    template_fields = []
    instance_count = 0
    world_max = 1000000
    
    def config_instance(self, instance):
        pass

    def get_class(self):
        clazz = self.class_map.get(self.instance_class)
        if clazz:
            return clazz
        split_path = self.instance_class.split(".")
        module_name = ".".join(split_path[:-1])
        class_name = split_path[-1]
        module = __import__(module_name, globals(), locals(), [class_name])
        clazz = getattr(module, class_name)
        self.class_map[self.instance_class] = clazz
        return clazz 
    
    def create_instance(self):
        if self.instance_count >= self.world_max:
            raise TemplateException
        instance = self.get_class()(self.dbo_id)
        for field in self.template_fields:
            setattr(instance, field, getattr(self, field, "None"))
        instance.on_loaded()
        instance.template = self
        self.instance_count = self.instance_count + 1
        self.config_instance(instance)
        return instance
        
    def delete_instance(self, instance):
        self.instance_count = self.instance_count - 1
        
