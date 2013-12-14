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
    window.opener.jQuery('body').trigger('editor_opened');

    window.onunload = function () {
      window.opener.jQuery('body').trigger('editor_closing');
    };

    window.editUpdate = lmEditor.editUpdate;

  }]);


angular.module('lampost_editor').service('lmEditor', ['$q', 'lmBus', 'lmRemote', 'lmDialog', 'lmUtil',
  function ($q, lmBus, lmRemote, lmDialog, lmUtil) {

    var self = this;
    var cacheHeap = [];
    var cacheHeapSize = 24;
    var remoteCache = {};

    function cacheKey(model) {
       var cacheKey = (model.dbo_key_type + ':' + model.dbo_id).split(":");
       return cacheKey.slice(0, cacheKey.length - 1).join(':');
    }

    function cacheSort(entry) {
      if (entry.idSort) {
        idSort(entry.data, 'dbo_id')
      } else if (jQuery.isArray(entry.data)) {
        lmUtil.stringSort(entry.data, 'dbo_id')
      }
    }

    function idSort(values, field) {
      values.sort(function (a, b) {
        var aid = parseInt(a[field].split(':')[1]);
        var bid = parseInt(b[field].split(':')[1]);
        return aid - bid;
      })
    }

    function updateModel(model, outside) {
      var entry = remoteCache[cacheKey(model)];
      if (entry) {
        var cacheModel = entry.map[model.dbo_id];
        if (cacheModel) {
          angular.copy(model, cacheModel);
          lmBus.dispatch('modelUpdate', cacheModel, outside);
        }
      }
    }

    function insertModel(model, outside) {
      var entry = remoteCache[cacheKey(model)];
      if (entry && !entry.promise) {
        if (entry.map[model.dbo_id]) {
          updateModel(model, outside);
        } else {
          entry.data.push(model);
          cacheSort(entry);
          entry.map[model.dbo_id] = model;
          lmBus.dispatch('modelCreate', entry.data, model, outside);
        }
      }
    }

    function deleteModel(model, outside) {
      var entry = remoteCache[cacheKey(model)];
      if (entry && !entry.promise) {
        var cacheModel = entry.map[model.dbo_id];
        if (cacheModel) {
          entry.data.splice(entry.data.indexOf(cacheModel), 1);
          delete entry.map[model.dbo_id];
          lmBus.dispatch('modelDelete', entry.data, model, outside);
        }
      }
    }

    this.deref = function (key) {
      if (!key) {
        return;
      }
      var entry = remoteCache[key];
      entry.ref--;
      if (entry.ref === 0) {
        cacheHeap.unshift(key);
        for (var i = cacheHeap.length; i >= cacheHeapSize; i--) {
          var oldEntry = remoteCache[cacheHeap.pop()];
          delete oldEntry.map;
          delete oldEntry.data;
        }
      }
    };

    this.cacheEntry = function (entry) {
      if (typeof entry === 'string') {
        entry = {key: entry};
      }
      if (!remoteCache[entry.key]) {
        entry.ref = 0;
        remoteCache[entry.key] = entry;
        if (!entry.url) {
          entry.url = entry.key + '/list';
        }
      }
    };

    this.cache = function (key) {
      var entry = remoteCache[key];
      if (entry.data) {
        if (entry.ref === 0) {
          cacheHeap.splice(cacheHeap.indexOf(key), 1);
        }
        entry.ref++;
        return $q.when(entry.data);
      }

      if (entry.promise) {
        entry.ref++;
        return entry.promise;
      }
      entry.promise = lmRemote.request('editor/' + entry.url).then(function (data) {
        delete entry.promise;
        entry.ref++;
        entry.data = data;
        entry.map = {};
        for (var i = 0; i < data.length; i++) {
          entry.map[data[i].dbo_id] = data[i];
        }
        cacheSort(entry);
        return $q.when(data);
      });
      return entry.promise;
    };

    this.editUpdate = function (event) {
      switch (event.edit_type) {
        case 'update':
          updateModel(event.model, true);
          break;
        case 'create':
          insertModel(event.model, true);
          break;
        case 'delete':
          deleteModel(event.model, true);
          break;
      }
    };


    this.visitRoom = function (roomId) {
      lmRemote.request('editor/room/visit', {room_id: roomId});
      window.open("", window.opener.name);
    };

    this.sanitize = function (text) {
      text = text.replace(/(\r\n|\n|\r)/gm, " ");
      return text.replace(/\s+/g, " ");
    };

    this.prepare = function (controller, $scope) {

      var newDialogId = null;
      var originalObject = null;
      var editor = $scope.editor;
      var baseUrl = 'editor/' + editor.url + '/';

      $scope.objectExists = false;
      $scope.newModel = null;
      $scope.copyFromId = null;
      $scope.objLabel = editor.id.charAt(0).toUpperCase() + editor.id.slice(1);

      $scope.$watch('model', function () {
        $scope.isDirty = !angular.equals(originalObject, $scope.model);
      }, true);

      lmBus.register('modelUpdate', function(updatedModel, outside) {
        if (updatedModel !== originalObject) {
          return;
        }
        if ($scope.isDirty && outside) {
          lmDialog.showConfirm("Outside Edit", "Warning -- This object has been updated by another user.  " +
            "Do you want to load the new object and lose your changes?", function() {
              $scope.model = angular.copy(originalObject);
            });
        } else {
          $scope.outsideEdit = outside;
          $scope.model = angular.copy(originalObject);
        }
      }, $scope);

      lmBus.register('modelCreate', function(modelList, model, outside) {
        if (modelList !== $scope.modelList) {
          return;
        }
        $scope.outsideAdd = outside;
      }, $scope);

      lmBus.register('modelDelete', function(modelList, model, outside) {
        if (modelDeleted(model, outside)) {
          return;
        }
        if (modelList === $scope.modelList && outside) {
          $scope.outsideDelete = outside;
        }
      }, $scope);

      function intercept(interceptor, args) {
        if (controller[interceptor]) {
          return $q.when(controller[interceptor](args));
        }
        return $q.when();
      }

      function modelDeleted(delModel, outside) {
        if ($scope.model && $scope.model.dbo_id == delModel.dbo_id) {
          if (outside) {
            lmDialog.showOk("Outside Delete", "This object has been deleted by another user.");
          }
          $scope.outsideEdit = false;
          $scope.model = null;
          intercept('postDelete', object);
          return true;
        }
        return false;
      }

      function mainDelete(object) {
        intercept('preDelete').then(function () {
          lmRemote.request(baseUrl + 'delete', {dbo_id: object.dbo_id}).then(function () {
            deleteModel(object);
            modelDeleted(object);
          });
        })
      }

      function onLoaded() {
        intercept('onLoaded').then(function () {
          $scope.ready = true;
        })
      }

      function prepareList(listKey) {
        self.cache(listKey).then(function (listData) {
          $scope.modelList = listData;
          onLoaded();
        });
      }

      $scope.revertObject = function () {
        $scope.model = angular.copy(originalObject);
        $scope.$broadcast('updateModel');
      };

      $scope.updateObject = function () {
        intercept('preUpdate').then(function () {
          lmRemote.request(baseUrl + 'update', $scope.model).then(
            function (updatedObject) {
              $scope.isDirty = false;
              updateModel(updatedObject);
              intercept('postUpdate', $scope.model);
            }
          )
        })
      };

      $scope.submitNewObject = function () {
        intercept('preCreate', $scope.newModel).then(function () {
          lmRemote.request(baseUrl + 'create', $scope.newModel).then(
            function (createdObject) {
              insertModel(createdObject);
              lmDialog.close(newDialogId);
              intercept('postCreate', createdObject).then(function () {
                $scope.editObject(createdObject);
              });
            }, function () {
              $scope.newExists = true;
            });
        })
      };

      $scope.newObjectDialog = function () {
        $scope.newModel = {};
        intercept('newDialog', $scope.newModel).then(function () {
          var dialogName = editor.create === 'dialog' ? editor.id : 'generic';
          newDialogId = lmDialog.show({templateUrl: 'editor/dialogs/new_' + dialogName + '.html', scope: $scope.$new()});
        });
      };

      $scope.newModelInclude = function () {
        return editor.create === 'fragment' ? 'editor/fragments/new_' + editor.id + '.html' : null;
      };

      $scope.editObject = function (object) {
        originalObject = object;
        $scope.outsideEdit = false;
        $scope.model = angular.copy(originalObject);
        intercept('startEdit', $scope.model).then(function () {
          $scope.$broadcast('updateModel');
        });
      };

      $scope.deleteObject = function (event, object) {
        event.preventDefault();
        event.stopPropagation();
        lmDialog.showConfirm("Delete " + $scope.objLabel, "Are you certain you want to delete " + $scope.objLabel + " " + object.dbo_id + "?",
          function () {
            mainDelete(object);
          });
      };

      $scope.copyObject = function (event, object) {
        event.preventDefault();
        event.stopPropagation();
        $scope.copyFromId = object.dbo_id;
        $scope.newModel = angular.copy(object);
        delete $scope.newModel.dbo_id;
        var dialogName = editor.copyDialog ? editor.id : 'generic';
        newDialogId = lmDialog.show({templateUrl: 'editor/dialogs/copy_' + dialogName + '.html', scope: $scope.$new()});
      };

      $scope.objectRowClass = function (object) {
        return ($scope.model && $scope.model.dbo_id == object.dbo_id) ? 'highlight' : '';
      };

      return {prepareList: prepareList};
    }
  }
]);


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

    $scope.idOnly = function (dboId) {
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

    lmEditor.cacheEntry({key: 'constants', url: 'constants'});
    lmEditor.cache('constants').then(function (constants) {
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
