# Development Suspended

This project is no longer updated.  The active version of Lampost is now on Gitlab:

[lampost_lib](https://gitlab.com/avezel/lampost_lib)
[lampost_mud](https://gitlab.com/avezel/lampost_mud)
[lampost_ui](https://gitlab.com/avezel/lampost-ui)

These "current" versions do not have full support for the angular.js client.  Instead they use a React.js/mobx based client.
My development efforts are now focused on building a non-MUD game using the Lampost framework, so there will not be a React.js MUD
client/editor in the near future.  Accordingly if you need a MUD UI you are limited to using these Github versions of the code, or
of course, I would welcome someone else expanding the lampost_ui project to include full MUD support.

As always, please contact me at <geoffrey@avezel.com> with any questions or ideas.


## Lampost

Lampost is a multi-user virtual world building platform inspired by the thriving community of multi-user dungeons (MUDs) of the 1990s.
 

### Quickstart

* Install Python 3.4+
* Install redis-py 2.10.3+, Tornado 4.5+ and PyYAML 3.10+ (for configuration) using pip
* Install Redis 2.4+ 
* Start Redis with the redis-server script
* Clone this Github repository
* Run lampost_setup --imm_name YOUR_SUPERUSER_PLAYER_NAME
* Run lampost.py
* Point your browser at <http://localhost:2500>

### Lampost Components

#### Application Server

The Lampost application server manages user/player sessions, client communication (via Web Sockets), and
the game engine via asynchronous, event driven atomic operations.
  
#### Web Client

The Lampost web client is an [angular.js](https://angularjs.org) single page application.  It provides a clean UI to the
Lampost Game Engine, as well as underlying support for Lampost sessions and client services.

#### Game Editor

The Lampost editor is a full featured administrative web client, also built on angular.js.  The editor allows building
traditional MUD environments in minutes, with real time creation of items, mobiles, rooms, areas (both shared and instanced)
and user scripts.
   
   
### Feature Highlights

#### Seamless Persistence

Lampost game objects are persisted in back end data storage.  Adding, subclassing, and combining persistent objects is all
but invisible to the developer.  Say goodbye to table definitions, xml configuration, lifecycle management, and all of the 
other annoying overhead of most persistence frameworks.  

Lampost by default uses Redis, but support for other key/value stores requires modifying only a single Lampost class.  
  
#### Intelligent Parsing

Lampost includes a sophisticated command parser designed around actions in a virtual world.  The parser is context aware,
tailoring available actions and targets to the player, their abilities, their possessions, and their environment.
The context aware algorithm results in extremely fast parsing performance.

#### User Scripts

Lampost has experimental support for user supplied scripts, allowing users to dynamically attach Python code to in-game objects
to dramatically expand the ability to customize the game experience without modifying source code.

#### Websocket API

Lampost has a full featured JSON/Websocket API for creating, modifying, and deleting in game objects.  This API supports the
Lampost editor.

  
### Requirements

The Lampost application server requires Python 3.4 or later.  Lampost has been run successfully on Linux, Windows, and OS X (CPython),
and smoke tested on [Pypy3 2.4.0](http://pypy.org) (Ubuntu).   

The Lampost web server is built on the [Tornado](http://www.tornadoweb.org) web server.  Lampost has been tested on Tornado 4.0.2.   

Lampost uses [Redis](http://redis.io) as its primary, high performance key/value datastore.  Lampost is currently compatible with
Redis 2.4 and later versions.  Lampost requires the awesome [redis-py](https://github.com/andymccurdy/redis-py) library for
Redis connectivity.

Finally Lampost requires PyYAML 3.x for initial configuration.


### License

Lampost is covered by the MIT license, a copy of which is included in this source tree.
