from lampost.db.dbo import ChildDBO
from lampost.gameops.script import UserScript


class MudScript(UserScript, ChildDBO):
    dbo_key_type = 'script'
    dbo_parent_type = 'area'
