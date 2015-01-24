def smell(self, source, **_):
    source.display_line("You smell bacon.")

smell = item_action(verbs='smell')(smell_func)
