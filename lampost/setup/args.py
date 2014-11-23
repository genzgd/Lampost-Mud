import argparse

parent_parser = argparse.ArgumentParser(add_help=False)

game_group = parent_parser.add_argument_group(title="Lampost Engine Configuration")
game_group.add_argument('-fl', '--flavor', help="engine flavor module", default='lpflavor')
game_group.add_argument('-cid', '--config_id', help="database configuration id", default='lampost')

log_group = parent_parser.add_argument_group(title="Logging Configuration")
log_group.add_argument('-l', '--log', help="default logging level", default='info', dest='log_level')
log_group.add_argument('-lf', '--log_file', help="log output file", default=None)

db_group = parent_parser.add_argument_group(title="Redis Database Configuration")
db_group.add_argument('-db_host', help="database server host name", default='localhost')
db_group.add_argument('-db_port', help="database server port", type=int, default=6379)
db_group.add_argument('-db_num', help="Redis database number", type=int, default=0)
db_group.add_argument('-db_pw', help="Redis database password", default=None)


main_parser = argparse.ArgumentParser(parents=[parent_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                      description="lampost -- The Lampost Game Engine  https://github.com/genzgd/Lampost-Mud")
web_group = main_parser.add_argument_group(title="Web Server Configuration")
web_group.add_argument('-p', '--port', help="web server port", type=int, default=2500)
web_group.add_argument('-si', help="web server network interface", default='127.0.0.1', metavar="NW_INT", dest="server_interface")


create_parser = argparse.ArgumentParser(parents=[parent_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                      description="create_lp_db -- Creation utility for the Lampost Game Engine https://github.com/genzgd/Lampost-Mud")

create_parser.add_argument('-flush', help="Flush (remove all keys) form existing Redis database", const=True, default=False, action='store_const')
create_parser.add_argument('-ra', '--root_area', help="root area name", default='immortal')

imm_group = create_parser.add_argument_group(title="Immortal User Configuration")
imm_group.add_argument('-ia', '--imm_account', help="root account name", default='root')
imm_group.add_argument('-im', '--imm_name', help="name of the root account primary primary", required=True)
imm_group.add_argument('-ipw', '--imm_password', help="root account password", default='lampost')


