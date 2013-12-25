angular.module('lampost_editor', ['lampost_svc', 'lampost_dir']);

angular.module('lampost_editor').run(['$timeout', 'lmUtil', 'lmEditor', 'lmRemote', 'lmBus',
  function ($timeout, lmUtil, lmEditor, lmRemote, lmBus) {

    var playerId = name.split('_')[1];
    var sessionId = localStorage.getItem('lm_session_' + playerId);
    if (!sessionId) {
      alert("No Editor Session Found");
      window.close();
    }

    lmRemote.childSession(sessionId);
    window.opener.jQuery('body').trigger('editor_opened');

    window.onbeforeunload = function () {
      var handlers = [];
      lmBus.dispatch('editorClosing', handlers);
      if (handlers.length) {
        return "You have changes to " + handlers.length + " item(s).  Changes will be lost if you leave this page.";
      }
      return undefined;
    };

    window.onunload = function () {
      window.opener.jQuery('body').trigger('editor_closing');
    };

    window.editUpdate = lmEditor.editUpdate;

  }]);


angular.module('lampost_editor').service('lmEditor', ['$q', '$timeout', 'lmBus', 'lmRemote', 'lmDialog', 'lmUtil',
  function ($q, $timeout, lmBus, lmRemote, lmDialog, lmUtil) {

    var self = this;
    var cacheHeap = [];
    var cacheHeapSize = 32;
    var remoteCache = {};

    var cacheSorts = {
      'room': numericIdSort
    };

    remoteCache.constants = {ref: 0, url: 'constants', sort: angular.noop};

    function cacheEntry(key) {
      var keyParts = key.split(':');
      var keyType = keyParts[0];
      var url = keyType + '/list' + (keyParts[1] ? '/' + keyParts[1] : '');
      var entry = {ref: 0, sort: cacheSorts[keyType] || idSort, url: url};
      remoteCache[key] = entry;
      return entry;
    }

    function cacheKey(model) {
      var cacheKey = (model.dbo_key_type + ':' + model.dbo_id).split(":");
      return cacheKey.slice(0, cacheKey.length - 1).join(':');
    }

    function idSort(values) {
      lmUtil.stringSort(values, 'dbo_id')
    }

    function numericIdSort(values) {
      values.sort(function (a, b) {
        var aid = parseInt(a.dbo_id.split(':')[1]);
        var bid = parseInt(b.dbo_id.split(':')[1]);
        return aid - bid;
      })
    }

    function updateModel(model, outside) {
      var entry = remoteCache[cacheKey(model)];
      if (entry) {
        var cacheModel = entry.map[model.dbo_id];
        if (cacheModel) {
          angular.copy(model, cacheModel);
          $scope.$broadcast('updateModel');
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
          entry.sort(entry.data);
          entry.map[model.dbo_id] = model;
          lmBus.dispatch('modelCreate', entry.data, model, outside);
        }
      }
    }

    function deleteEntry(key) {
      var heapIx = cacheHeap.indexOf(key);
      if (heapIx > -1) {
        cacheHeap.splice(headIx, 1);
      }
      delete remoteCache[key];
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
      var deleted = [];
      angular.forEach(remoteCache, function (entry, key) {
        var keyParts = key.split(':');
        if (keyParts[1] === model.dbo_id) {
          deleted.push(key);
        }
      });
      angular.forEach(deleted, function (key) {
        deleteEntry(key);
      });
    }

    function display(model) {
      var display;
      if (model.name) {
        display = model.name;
      } else if (model.title) {
        display = model.title;
      }
      if (display) {
        display += ' (' + model.dbo_id + ')';
      } else {
        display = model.dbo_id;
      }
      return display;
    }

    this.invalidate = function(key) {
      deleteEntry(key)
    };

    this.cacheValue = function (key, dbo_id) {
      return remoteCache[key].map[dbo_id];
    };

    this.deref = function (key) {
      if (!key) {
        return;
      }
      var entry = remoteCache[key];
      if (!entry) {
        return;
      }
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

    this.cache = function (key) {
      var entry = remoteCache[key] || cacheEntry(key);
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
        entry.sort(entry.data);
        return $q.when(entry.data);
      });
      return entry.promise;
    };

    this.editUpdate = function (event) {
      var outside = !event.local;
      switch (event.edit_type) {
        case 'update':
          updateModel(event.model, outside);
          break;
        case 'create':
          insertModel(event.model, outside);
          break;
        case 'delete':
          deleteModel(event.model, outside);
          break;
      }
    };

    this.visitRoom = function (roomId) {
      lmRemote.request('editor/room/visit', {room_id: roomId});
      window.open("", window.opener.name);
    };

    this.prepare = function (controller, $scope) {

      var newDialogId = null;
      var originalModel = null;
      var editor = $scope.editor;
      var nextModel = null;
      var baseUrl = 'editor/' + editor.url + '/';

      editor.newEdit = newEdit;

      $scope.newModel = null;
      $scope.copyFromId = null;
      $scope.objLabel = editor.objLabel || editor.label;

      $scope.$watch('model', function (model) {
        if (model) {
          $scope.isDirty = originalModel && !angular.equals(originalModel, model);
        } else {
          $scope.isDirty = false;
        }
      }, true);

      lmBus.register('modelUpdate', function (updatedModel, outside) {
        if (updatedModel !== originalModel) {
          return;
        }
        if ($scope.isDirty && outside) {
          lmDialog.showConfirm("Outside Edit", "Warning -- This object has been updated by another user.  " +
            "Do you want to load the new object and lose your changes?", function () {
            $scope.model = angular.copy(originalModel);
          });
        } else {
          $scope.outsideEdit = outside;
          $scope.model = angular.copy(originalModel);
        }
      }, $scope);

      lmBus.register('editorChange', function (previousEditor) {
        if (previousEditor === $scope.editor && $scope.isDirty) {
          unsavedChanges();
        }
      }, $scope);

      lmBus.register('editorClosing', function (handlers) {
        if ($scope.isDirty) {
          handlers.push(this);
          unsavedChanges();
        }
      }, $scope);

      lmBus.register('modelCreate', function (modelList, model, outside) {
        if (modelList !== $scope.modelList) {
          return;
        }
        $scope.outsideAdd = outside;
      }, $scope);

      lmBus.register('modelDelete', function (modelList, model, outside) {
        if (modelDeleted(model, outside)) {
          return;
        }
        if (modelList === $scope.modelList && outside) {
          $scope.outsideDelete = outside;
        }
      }, $scope);

      function unsavedChanges() {
        lmDialog.showConfirm("Unsaved Changes", "You have unsaved changes to " + $scope.objLabel +
          ": " + $scope.model.dbo_id + ".  Save changes now?", function () {
          $scope.nextEdit = null;
          $scope.updateModel();
        })
      }

      function intercept(interceptor, args) {
        if (controller[interceptor]) {
          return $q.when(controller[interceptor](args));
        }
        return $q.when();
      }

      function dataError(error) {
        $scope.dataError = error.text;
      }

      function modelDeleted(delModel, outside) {
        if ($scope.model && $scope.model.dbo_id == delModel.dbo_id) {
          if (outside) {
            lmDialog.showOk("Outside Delete", "This object has been deleted by another user.");
          }
          $scope.outsideEdit = false;
          $scope.model = null;
          intercept('postDelete', delModel);
          return true;
        }
        return false;
      }

      function mainDelete(model) {
        intercept('preDelete').then(function () {
          lmRemote.request(baseUrl + 'delete', {dbo_id: model.dbo_id}).then(function () {
            deleteModel(model);
            modelDeleted(model);
          }, dataError);
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

      function newEdit(newModel) {
        if (!newModel) {
          return;
        }
        if ($scope.model && $scope.model.dbo_id !== newModel.dbo_id && $scope.isDirty) {
          nextModel = newModel;
          lmDialog.showAlert({title: "Unsaved Changes ",
            body: "You are about to edit <b>" + display(newModel) + "</b>.  You have unsaved changes to <b>" +
              display($scope.model) + "</b>.  Save your changes, discard your changes, or continue editing <b>" +
              display($scope.model) + "</b>?",
            buttons: [
              {label: "Save Changes", class: "btn-default", dismiss: true, click: $scope.updateModel},
              {label: "Discard Changes", class: "btn-danger", dismiss: true, click: nextEdit},
              {label: "Continue Previous Edit", class: "btn-info", default: true, cancel: true}
            ],
            onCancel: function () {
              nextModel = null;
            }}, true);
        } else {
          $scope.editModel(newModel);
        }
      }

      function nextEdit() {
        if (nextModel) {
          $scope.ready = false;
          $scope.model = null;
          newEdit(nextModel);
          nextModel = null;
        }
      }

      $scope.revertModel = function () {
        $scope.model = angular.copy(originalModel);
        $scope.$broadcast('updateModel');
      };

      $scope.updateModel = function () {
        intercept('preUpdate').then(function () {
          lmRemote.request(baseUrl + 'update', $scope.model).then(
            function (updatedObject) {
              $scope.isDirty = false;
              updateModel(updatedObject);
              intercept('postUpdate', $scope.model).then(nextEdit);
            }, dataError)
        })
      };

      $scope.submitNewModel = function () {
        intercept('preCreate', $scope.newModel).then(function () {
          lmRemote.request(baseUrl + 'create', $scope.newModel).then(
            function (createdObject) {
              insertModel(createdObject);
              lmDialog.close(newDialogId);
              intercept('postCreate', createdObject).then(function () {
                $scope.editModel(createdObject);
              });
            }, function () {
              $scope.dialog.newExists = true;
            });
        })
      };

      $scope.newModelDialog = function () {
        $scope.newModel = {};
        $scope.dialog = {};
        intercept('newDialog', $scope.newModel).then(function () {
          var dialogName = editor.create === 'dialog' ? editor.id : 'generic';
          newDialogId = lmDialog.show({templateUrl: 'editor/dialogs/new_' + dialogName + '.html', scope: $scope.$new()});
        });
      };

      $scope.newModelInclude = function () {
        return editor.create === 'fragment' ? 'editor/fragments/new_' + editor.id + '.html' : null;
      };

      $scope.editModel = function (object) {
        originalModel = object;
        $scope.outsideEdit = false;
        var model = angular.copy(originalModel);
        intercept('startEdit', model).then(function () {
          $scope.model = model;
          $scope.ready = true;
          $scope.$broadcast('updateModel');
        });
      };

      $scope.deleteModel = function (event, model) {
        if (event) {
          event.preventDefault();
          event.stopPropagation();
        }
        model = model || $scope.model;
        intercept('delConfirm', model).then(function () {
          lmDialog.showConfirm("Delete " + $scope.objLabel,
            "Are you certain you want to delete " + $scope.objLabel + " " + model.dbo_id + "?",
            function () {
              mainDelete(model);
            });
        });
      };

      $scope.copyObject = function (event, object) {
        event.preventDefault();
        event.stopPropagation();
        $scope.copyFromId = object.dbo_id;
        $scope.newModel = angular.copy(object);
        delete $scope.newModel.dbo_id;
        $scope.dialog = {};
        var dialogName = editor.copyDialog ? editor.id : 'generic';
        newDialogId = lmDialog.show({templateUrl: 'editor/dialogs/copy_' + dialogName + '.html', scope: $scope.$new()});
      };

      $scope.addNewAlias = function () {
        $scope.model.aliases.push('');
        $timeout(function () {
          jQuery('.alias-row:last').focus();
        });
      };

      $scope.deleteAlias = function (index) {
        $scope.model.aliases.splice(index, 1);
      };

      $scope.modelRowClass = function (object) {
        return ($scope.model && $scope.model.dbo_id == object.dbo_id) ? 'highlight' : '';
      };

      return {
        prepareList: prepareList,
        mainDelete: mainDelete, originalModel: function () {
          return originalModel;
        }};
    }
  }
]);


angular.module('lampost_editor').controller('EditorCtrl', ['$scope', 'lmEditor', 'lmRemote', 'lmBus',
  function ($scope, lmEditor, lmRemote, lmBus) {

    var playerId = name.split('_')[1];
    var editorList = jQuery.parseJSON(localStorage.getItem('lm_editors_' + playerId));
    if (!editorList) {
      alert("No Editor List Found");
      window.close();
    }

    $scope.editorMap = {
      config: {label: "Mud Config", url: "config"},
      players: {label: "Players", objLabel: 'Player', url: "player"},
      area: {label: "Areas", objLabel: "Area", url: "area", create: 'fragment'},
      room: {label: "Room", url: "room", create: 'dialog'},
      mobile: {label: "Mobile", url: "mobile"},
      article: {label: "Article", url: "article"},
      social: {label: "Socials", objLabel: "Social", url: "social", create: 'dialog'},
      display: {label: "Display", url: "display"},
      race: {label: "Races", objLabel: "Race", url: "race"},
      attack: {label: "Attacks", objLabel: "Attack", url: "attack"},
      defense: {label: "Defenses", objLabel: "Defense", url: "defense"}
    };

    $scope.editorInclude = function (editor) {
      return editor.activated ? 'editor/view/' + editor.id + '.html' : undefined;
    };

    $scope.idOnly = function (model) {
      return model.dbo_id.split(':')[1];
    };

    $scope.cap = function (name) {
      return name.substring(0, 1).toLocaleUpperCase() + name.substring(1);
    };

    $scope.click = function (editor) {
      if (editor === $scope.currentEditor) {
        return;
      }
      lmBus.dispatch('editorChange', $scope.currentEditor);
      editor.activated = true;
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

    $scope.startEditor = function (editType, editModel) {
      var editor = $scope.editorMap[editType];
      editor.editModel = editModel;
      $scope.click(editor);
      editor.newEdit && editor.newEdit(editModel);
    };

    lmEditor.cache('constants').then(function (constants) {
      $scope.constants = constants;
      $scope.loaded = true;
      $scope.click($scope.editors[0]);
    });

  }]);


angular.module('lampost_editor').controller('MudConfigCtrl', ['$q', '$rootScope', '$scope', 'lmRemote',
  'lmEditor', '$timeout', function ($q, $rootScope, $scope, lmRemote, lmEditor, $timeout) {

    var roomKey;
    var startConfig = null;
    lmEditor.prepare(this, $scope);

    $q.all([
      lmEditor.cache('area').then(function(areas) {
        $scope.areaList = areas;
        }),
      lmRemote.request('editor/config/get_defaults').then(function (defaults) {
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
      }),
      lmRemote.request('editor/config/get').then(function(config) {
        startConfig = config;
        $scope.startAreaId = config.start_room.split(':')[0];
      })
      ]).then(function() {
        $scope.changeArea().then(function() {
           $scope.editor.newEdit(startConfig);
        });
      });

    $scope.changeArea = function () {
      lmEditor.deref(roomKey);
      roomKey = 'room:' + $scope.startAreaId;
      return lmEditor.cache(roomKey).then(function (rooms) {
         $scope.rooms = rooms;
      });
    };

    this.postUpdate = function(config) {
      $timeout(function () {
          $rootScope.siteTitle = config.title;
        });

      lampost_config.title = config.title;
      lampost_config.description = config.description;
      $('title').text(lampost_config.title);
    }

  }]);
