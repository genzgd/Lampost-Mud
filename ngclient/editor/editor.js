angular.module('lampost_editor', ['lampost_svc', 'lampost_dir']);

angular.module('lampost_editor').run(['$timeout', 'lmUtil', 'lmEditor', 'lmRemote',
  function ($timeout, lmUtil, lmEditor, lmRemote) {

    var playerId = name.split('_')[1];
    var sessionId = localStorage.getItem('lm_session_' + playerId);
    if (!sessionId) {
      alert("No Editor Session Found");
      window.close();
    }

    lmRemote.childSession(sessionId);

  }]);


angular.module('lampost_editor').service('lmEditor', ['$q', 'lmBus', 'lmRemote', 'lmDialog', '$location', 'lmUtil',
  function ($q, lmBus, lmRemote) {

    var remoteCache = {
      allSkills: {url: 'skills/all'},
      area: {url: 'area/list'}
    };

    function idSort(values, field) {
      values.sort(function (a, b) {
        var aid = parseInt(a[field].split(':')[1]);
        var bid = parseInt(b[field].split(':')[1]);
        return aid - bid;
      })
    }

    this.cache = function (request) {
      if (!request) {
        return $q.when();
      }
      var key = typeof request === 'string' ? request : request.key;
      var entry = remoteCache[key];
      if (!entry) {
        entry = request;
        remoteCache[key] = entry;
        if (!entry.url) {
          entry.url = entry.key + '/list';
        }
      }
      if (entry.data) {
        return $q.when(entry.data);
      }
      return lmRemote.request('editor/' + entry.url).then(function (data) {
        entry.data = data;
        return $q.when(data);
      });
    };

    this.invalidate = function (key) {
      delete remoteCache[key].data;
    };

    this.visitRoom = function (roomId) {
      lmRemote.request('editor/room/visit', {room_id: roomId});
      window.open("", window.opener.name);
    };

    this.sanitize = function (text) {
      text = text.replace(/(\r\n|\n|\r)/gm, " ");
      return text.replace(/\s+/g, " ");
    };
  }]);


angular.module('lampost_editor').controller('EditorCtrl', ['$scope', 'lmEditor', 'lmBus', 'lmRemote',
  function ($scope, lmEditor, lmBus, lmRemote) {


    var playerId = name.split('_')[1];
    var editorList = jQuery.parseJSON(localStorage.getItem('lm_editors_' + playerId));
    if (!editorList) {
      alert("No Editor List Found");
      window.close();
    }

    $scope.editorMap = {
      config: {label: "Mud Config", url: "config"},
      players: {label: "Players", url: "player"},
      area: {label: "Areas", url: "area", create: 'fragment'},
      room: {label: "Room", url: "room", create: 'dialog'},
      mobile: {label: "Mobile", url: "mobile"},
      article: {label: "Article", url: "article"},
      socials: {label: "Socials", url: "socials"},
      display: {label: "Display", url: "display"},
      race: {label: "Races", url: "race"},
      attack: {label: "Attacks", url: "attack"},
      defense: {label: "Defenses", url: "defense"}
    };

    $scope.editorInclude = function (editor) {
      return editor.activated ? 'editor/view/' + editor.id + '.html' : undefined;
    };

    $scope.idOnly = function(dboId) {
      return dboId.split(':')[1];
    };

    $scope.click = function (editor) {
      editor.activated = true;
      $scope.lastEditor = $scope.currentEditor;
      $scope.currentEditor = editor;
    };

    $scope.editors = [];
    angular.forEach(editorList, function (key) {
      var editor = $scope.editorMap[key];
      if (editor) {
        editor.id = key;
        $scope.editors.push(editor);
      } else {
        lmRemote.log("Missing editor type: " + key);
      }
    });

    $scope.tabClass = function (editor) {
      return (editor == $scope.currentEditor ? "active " : " ") + editor.label_class;
    };

    lmEditor.cache({key: 'constants', url: 'constants'}).then(function (constants) {
      $scope.constants = constants;
      $scope.loaded = true;
      $scope.click($scope.editors[0]);
    });

  }]);


angular.module('lampost_editor').controller('MudConfigCtrl', ['$rootScope', '$scope', 'lmBus', 'lmRemote', 'lmEditor', '$timeout',
  function ($rootScope, $scope, lmBus, lmRemote, lmEditor, $timeout) {

    var configCopy;
    $scope.ready = false;
    $scope.areaList = [];
    angular.forEach(lmEditor.areaList, function (value) {
      $scope.areaList.push(value.id);
      $scope.areaList.sort();
    });
    if (lmEditor.currentEditor === $scope.editor) {
      loadConfig();
    }

    $scope.changeArea = function () {
      lmEditor.loadRooms($scope.startAreaId).then(function (rooms) {
        $scope.rooms = [];
        $scope.startRoom = null;
        angular.forEach(rooms, function (room) {
          var roomStub = {id: room.dbo_id, label: room.dbo_id.split(':')[1] + ': ' + room.title};
          $scope.rooms.push(roomStub);
          if (roomStub.dbo_id == $scope.config.start_room) {
            $scope.startRoom = roomStub;
          }
        });
        if (!$scope.startRoom) {
          $scope.startRoom = $scope.rooms[0];
        }
        $scope.ready = true;
      });
    };
    lmBus.register("editor_activated", function (editor) {
      if (editor == $scope.editor) {
        loadConfig();
      }
    });

    $scope.updateConfig = function () {
      $scope.config.start_room = $scope.startRoom.id;
      lmRemote.request($scope.editor.url + "/update", {config: $scope.config}).then(function (config) {
        prepare(config);
        lampost_config.title = config.title;
        lampost_config.description = config.description;
        $timeout(function () {
          $rootScope.siteTitle = config.title;
        });
        $('title').text(lampost_config.title);
      });
    };

    $scope.revertConfig = function () {
      $scope.config = configCopy;
      $scope.startAreaId = $scope.config.start_room.id.split(':')[0];
      $scope.changeArea();
    };

    function loadConfig() {
      lmRemote.request($scope.editor.url + "/get_defaults").then(function (defaults) {
        angular.forEach(defaults, function (subDefaults) {
          angular.forEach(subDefaults, function (value) {
            value.type = value.type || 'number';
            if (value.type === 'number') {
              if (value.min === undefined) {
                value.min = 1;
              }
              value.step = value.step || 1;
            }
          });
        });
        $scope.defaults = defaults;
        lmRemote.request($scope.editor.url + "/get").then(prepare);
      })
    }

    function prepare(config) {
      configCopy = angular.copy(config);
      $scope.config = config;
      $scope.startAreaId = config.start_room.split(':')[0];
      $scope.changeArea();
    }

  }]);
