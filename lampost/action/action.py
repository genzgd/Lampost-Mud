from lampost.context.resource import requires

@requires('dispatcher', 'datastore')
class Action(object):
    imm_level = 0
    mud = None
    prep = None
    
    def __init__(self, verbs, msg_class=None):
        self.verbs = set()
        try:
            self.add_verb(verbs)
        except AttributeError:
            for verb in verbs:
                self.add_verb(verb)
        if msg_class:
            self.msg_class = "rec_{0}".format(msg_class)
                
    def add_verb(self, verb):
        self.verbs.add(tuple(verb.split(" ")))
        
    def execute(self, target_method, **kwargs):
        if target_method:
            return target_method(**kwargs)

            
class HelpAction(Action):
    def __init__(self):
        Action.__init__(self, "help")
        
    def execute(self, source, args, **ignored):
        action_set = source.actions.get(args)
        if not action_set:
            return "No matching command found"
        if len(action_set) > 1:
            return "Multiple matching commands"
        action = iter(action_set).next()
        return getattr(action, "help_text", "No help available.")
