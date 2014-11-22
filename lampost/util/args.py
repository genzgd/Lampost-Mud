import argparse

parent_parser = argparse.ArgumentParser(add_help=False, )
parent_parser.add_argument('-l', '--log', help="default logging level", choices=['fatal', 'error', 'warn', 'info', 'debug'], default='info')
parent_parser.add_argument('-p', '--port', help="engine web server port", type=int, default=2500)

main_parser = argparse.ArgumentParser(parents=[parent_parser], formatter_class=argparse.ArgumentDefaultsHelpFormatter, description="lampost -- The Lampost Game Engine")
