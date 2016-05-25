import argparse

parent_parser = argparse.ArgumentParser(add_help=False)

config_group = parent_parser.add_argument_group(title="Lampost Engine Configuration")
config_group.add_argument('-cid', '--config_id', help="database configuration id", default='lampost')
config_group.add_argument('-a', '--app_id', help="application module", default='lampost.lpmud')

log_group = parent_parser.add_argument_group(title="Logging Configuration")
log_group.add_argument('-l', '--log', help="default logging level", default='info', dest='log_level')
log_group.add_argument('-lf', '--log_file', help="log output file", default=None)
log_group.add_argument('-lm', '--log_mode', help="log file open mode", default='w')

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

config_group.add_argument('-cd', '--config_dir', help="yaml configuration directory", default='conf')


create_parser = argparse.ArgumentParser(parents=[parent_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                      description="lampost_setup -- Creation utility for the Lampost Game Engine https://github.com/genzgd/Lampost-Mud")

create_parser.add_argument('-flush', help="Flush (remove all keys) form existing Redis database", const=True, default=False, action='store_const')

imm_group = create_parser.add_argument_group(title="Immortal User Configuration")
imm_group.add_argument('-ia', '--imm_account', help="root account name", default='root')
imm_group.add_argument('-im', '--imm_name', help="name of the root account primary primary", required=True)
imm_group.add_argument('-ipw', '--imm_password', help="root account password", default='lampost')


tools_parser = argparse.ArgumentParser(parents=[parent_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                       description="lampost_tools -- Some command line tools for lampost")
tools_parser.add_argument('op', metavar="OPERATION", help="Tools operation")




