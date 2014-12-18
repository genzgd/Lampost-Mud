angular.module('lampost_editor').service('lpEditor', ['$q', 'lpUtil', 'lpRemote', 'lpDialog', 'lpCache', 'lpEvent',
  function ($q, lpUtil, lpRemote, lpDialog, lpCache, lpEvent) {

    var lpEditor = this;
    var contextMap = {};

    function EditContext(id, init) {
      angular.copy(init, this);
      this.id = id;
      this.url = this.url || id;
      this.label = this.label || lpUtil.capitalize(id);
      this.baseUrl = 'editor/' + this.url + '/';
      this.objLabel = this.objLabel || this.label;
      this.include = this.include || 'editor/view/' + id + '.html';
      this.extend = this.extend || angular.noop;
    }

    EditContext.prototype.newModel = function () {
      var model = angular.copy(this.newObj);
      model.can_write = true
      model.owner_id = lpEditor.playerId;
      this.extend(model);
      return model;
    };

    EditContext.prototype.preCreate = function (model) {
      model.dbo_id = model.dbo_id.toString().toLocaleLowerCase();
      if (model.dbo_id.indexOf(':') > -1) {
        return $q.reject("Colons not allowed in base ids");
      }
      if (model.dbo_id.indexOf(' ') > -1) {
        return $q.reject("No spaces allowed in ids");
      }

      if (this.parentType) {
        if (this.parent) {
          model.dbo_id = this.parent.dbo_id + ':' + model.dbo_id;
        } else {
          return $q.reject("No parent " + this.parentType + " set.")
        }
      }
      return $q.when();
    };

    this.init = function (data) {
      this.playerId = data.playerId;
      lpCache.clearAll();
      return lpRemote.request('editor/constants').then(function (constants) {
        lpEditor.constants = constants;
      });
    };

    this.initView = function() {
      var requests = [];
      angular.forEach(contextMap, function(context) {
        delete context.parent;
        if (!context.newObj) {
          requests.push(lpRemote.request('editor/' + context.url + '/metadata').then(function(data) {
            context.parentType = data.parent_type;
            context.newObj = data.new_object;
          }));
        }
        if (context.invalidate) {
          lpCache.invalidate(context.id);
        }
      });
      return $q.all(requests);
    }

    this.registerContext = function (contextId, context) {
      if (!contextMap[contextId]) {
        contextMap[contextId] = new EditContext(contextId, context);
      }
      return contextMap[contextId];
    };

    this.getContext = function (contextId) {
      return contextMap[contextId];
    };

    this.translateError = function (error) {
      if (error.id == 'ObjectExists') {
        return "The object id " + error.text + " already exists";
      }
      if (error.id == 'NonUnique') {
        return "The name " + error.text + "is already in use";
      }
      return error.text || error;
    };

    this.deleteModel = function (context, model, error) {
      lpRemote.request(context.baseUrl + 'test_delete', {dbo_id: model.dbo_id}).then(function (holders) {
        var extra = '';
        if (holders.length > 0) {
          extra = "<br/><br/>This object will be removed from:<br/><br/><div> " + holders.join(' ') + "</div>";
        }
        lpDialog.showConfirm("Delete " + context.objLabel,
            "Are you certain you want to delete " + context.objLabel + " " + model.dbo_id + "?" + extra,
          function () {
            lpRemote.request(context.baseUrl + 'delete', {dbo_id: model.dbo_id}).then(function () {
              lpCache.deleteModel(model);
            }, error);
          });
      });
    };

    this.display = function (model) {
      return model.name || model.title || (model.dbo_id || model.dbo_id === 0) && model.dbo_id.toString() || '-new-';
    };

    lpEvent.register('modelDelete', function(delModel) {
      angular.forEach(contextMap, function (context) {
        if (context.parent == delModel) {
          context.parent = null;
          lpEvent.dispatch('contextUpdate', context);
        }
      })
    });

    lpEvent.register('modelSelected', function (activeModel) {
      angular.forEach(contextMap, function (context) {
        if (context.parentType === activeModel.dbo_key_type) {
          context.parent = activeModel;
        }
      });
      lpEvent.dispatch('activeUpdated', activeModel);
    });


    /*  config: new lpEditContext({label: "Mud Config", url: "config"}),
     script: {label: "Script", url: "script"},
     display: {label: "Display", url: "display"},
     race: {label: "Races", objLabel: "Race", url: "race"},
     attack: {label: "Attacks", objLabel: "Attack", url: "skill"},
     defense: {label: "Defenses", objLabel: "Defense", url: "skill"},
     imports: {label: "Imports"} */


  }]);


angular.module('lampost_editor').controller('MainEditorCtrl',
  ['$scope', '$rootScope', '$q', '$timeout', 'lpEvent', 'lpRemote', 'lpDialog', 'lpCache', 'lpEditor',
  function ($scope, $rootScope, $q, $timeout, lpEvent, lpRemote, lpDialog, lpCache, lpEditor) {

    var activeModel = {};
    var originalModel = {};
    var cacheKeys = [];
    var context;
    var baseUrl;

    function display() {
      return lpEditor.display(activeModel);
    }

    function clearSeeds() {
      var cacheKey;
      while (cacheKey = cacheKeys.pop()) {
        lpCache.deref(cacheKey);
      }
    }

    function initScope() {
      lpEvent.dispatch('editStarting', originalModel);
      angular.copy(originalModel, activeModel);
      lpEditor.original = originalModel;
      lpEditor.context = context;
      $scope.isDirty = false;
      $scope.editorLabel = context.label;
      if (context.parent) {
        $scope.parentType = lpEditor.getContext(context.parentType).label + ':';
        $scope.parentLabel = lpEditor.display(context.parent);
      } else {
        $scope.parentType = null;
        $scope.parentLabel = 'MUD';
      }
      $scope.detailTemplate = context.include;
      $rootScope.activeEditor = activeModel.dbo_key_type;
      lpEvent.dispatch('editReady', activeModel);
    }

    function init(orig) {
      baseUrl = context.baseUrl;
      originalModel = orig;
      clearSeeds();
      $q.all(lpCache.seedCache(context.refs, originalModel, cacheKeys)).then(initScope);
    }

    function reset() {
      context = {label: 'Get Started'};
      init({});
    }

    function intercept(interceptor, args) {
      if (context[interceptor]) {
        return $q.when(context[interceptor](args));
      }
      return $q.when();
    }

    function dataError(error) {
      $scope.errors.dataError = lpEditor.translateError(error);
    }

    function saveModel() {
      return intercept('preUpdate', activeModel).then(function () {
        if ($scope.isNew) {
          var modelDto = angular.copy(activeModel);
          return context.preCreate(modelDto).then(function () {
            lpRemote.request(baseUrl + 'create', modelDto).then(onCreated, dataError);
          }, dataError);
        }
        return lpRemote.request(baseUrl + 'update', activeModel).then(onSaved, dataError);
      })
    }

    function onCreated(created) {
      $scope.isDirty = false;
      lpCache.insertModel(created);
      existingEdit(created);
    }

    function onSaved(updated) {
      $scope.isDirty = false;
      lpCache.updateModel(updated);
      return intercept('postUpdate', activeModel);
    }

    function checkUnsaved() {
      return lpDialog.showConfirm("Unsaved Changes", "You have unsaved changes to " + $scope.objLabel +
        ": " + display() + ".  Save changes now?", saveModel);
    }

    function onOverwrite() {
      if (!$scope.isDirty) {
        return $q.when();
      }
      var deferred = $q.defer();
      lpDialog.showAlert({title: "Unsaved Changes ",
        body: "You have unsaved changes to <b>" + display() +
          "</b>.  Save your changes, discard your changes, or continue editing <b>" + display() + "</b>?",
        buttons: [
          {label: "Save Changes", class: "btn-default", dismiss: true, click: function () {
            deferred.resolve(saveModel())
          }},
          {label: "Discard Changes", class: "btn-danger", dismiss: true, click: deferred.resolve},
          {label: "Continue Previous Edit", class: "btn-info", default: true, cancel: true}
        ],
        onCancel: deferred.reject}, true);
      return deferred.promise;
    }

    function existingEdit(model) {
      onOverwrite(model).then(function () {
        context = lpEditor.getContext(model.dbo_key_type);
        $scope.isNew = false;
        intercept('preEdit').then(function() {
          init(model);
          lpEvent.dispatch('modelSelected', originalModel);
        })
      });
    }

    lpEvent.register('modelUpdate', function (updatedModel, outside) {
      if (updatedModel !== originalModel) {
        return;
      }
      if ($scope.isDirty && outside) {
        lpDialog.showConfirm("Outside Edit", "Warning -- This object has been updated by another user.  " +
          "Do you want to load the new object and lose your changes?", function () {
          angular.copy(originalModel, activeModel);
        });
      } else {
        $scope.outsideEdit = outside;
        angular.copy(originalModel, activeModel);
      }
    }, $scope);

    lpEvent.register('modelDelete', function (delModel, outside) {
      if (activeModel.dbo_id === delModel.dbo_id) {
        if (outside) {
          lpDialog.showOk("Outside Delete", "This object has been deleted by another user.");
        }
        reset();
      }
    }, $scope);

    lpEvent.register('editorClosing', function (handlers) {
      if ($scope.isDirty) {
        handlers.push(checkUnsaved);
      }
    }, $scope);

    lpEvent.register('newEdit', function (type) {
      onOverwrite().then(function () {
        context = lpEditor.getContext(type);
        $scope.isNew = true;
        init(context.newModel());
      });
    }, $scope);

    lpEvent.register('startEdit', existingEdit);

    $scope.model = activeModel;
    $scope.saveModel = saveModel;

    $scope.$watch('model', function () {
      $scope.isDirty = !angular.equals(originalModel, activeModel);
    }, true);

    $scope.revertModel = function () {
      angular.copy(originalModel, activeModel);
      lpEvent.dispatch('editStarting', originalModel);
    };

    $scope.addNewAlias = function () {
      activeModel.aliases.push('');
      $timeout(function () {
        jQuery('.alias-row:last').focus();
      });
    };

    $scope.modelName = display;

    $scope.deleteAlias = function (index) {
      activeModel.aliases.splice(index, 1);
    };

    $scope.deleteModel = function (event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      if (!$scope.isNew) {
        lpEditor.deleteModel(context, originalModel, dataError);
      } else if ($scope.isDirty) {
        lpDialog.showConfirm("Delete " + context.objLabel,
            "Are you sure you want to abandon this new " + context.objLabel + "?", reset);
      } else {
        reset();
      }
    };

    $scope.$on('$destroy', clearSeeds);
    reset();
  }]);


angular.module('lampost_editor').controller('EditListCtrl',
  ['$scope', '$attrs', 'lpEvent', 'lpCache', 'lpEditor', 'lpEditorView',
  function ($scope, $attrs, lpEvent, lpCache, lpEditor, lpEditorView) {

    var type =  $attrs.listType || $attrs.lpEditList;
    var context = lpEditor.getContext(type);
    var activeModel;
    var listKey;

    $scope.type = type;
    $scope.editorLabel = context.label;
    $scope.addAllowed = function () {
      return (context.parent && context.parent.can_write) || !context.parentType;
    };

    function changeActive(active) {
      activeModel = active;
      lpEditorView.selectModel(type, active);
    }

    function updateList() {
      lpCache.deref(listKey);
      if (context.parentType) {
        if (context.parent) {
          listKey = type + ":" + context.parent.dbo_id;
        } else {
          activeModel = null;
          $scope.modelList = [];
          return;
        }
      } else {
        listKey = type;
      }
      lpCache.cache(listKey).then(function (objs) {
        $scope.modelList = objs;
        var selectedId = lpEditorView.selectedId(type);
        if (selectedId) {
          var selected = lpCache.cacheValue(listKey, selectedId);
          if (selected) {
            activeModel = selected;
            lpEvent.dispatch("modelSelected", activeModel);
            if (selectedId == lpEditorView.lastEdit(type)) {
               lpEvent.dispatch("startEdit", activeModel);
            }
          }
        }
      });
    }

    function dataError(error) {
      $scope.errors.dataError = lpEditor.translateError(error);
    }

    lpEvent.register("contextUpdate", function(updated) {
      if (context === updated) {
        updateList();
      }
    });

    lpEvent.register("activeUpdated", function (activated) {
      if (activated.dbo_key_type === type) {
        changeActive(activated);
      } else if (context.parent === activated) {
        updateList();
        changeActive(null);
      }

    });

    lpEvent.register("modelDelete", function(delModel) {
      if (activeModel == delModel) {
        changeActive(null);
      }
    })


    $scope.selectModel = function (model, event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      lpEvent.dispatch("startEdit", model);
    };

    $scope.rowClass = function (model) {
      return model === activeModel ? 'warning' : '';
    };

    $scope.activeModel = function () {
      return activeModel ? lpEditor.display(activeModel) : '-NOT SELECTED-';
    };

    $scope.refreshList = function () {
      lpCache.invalidate(listKey);
      updateList();
    }

    $scope.$on('$destroy', function() {
      lpCache.deref(listKey)}
    );

    updateList()

  }]);

angular.module('lampost_editor').controller('MudConfigCtrl', ['$q', '$rootScope', '$scope', 'lpRemote',
  'lmEditor', '$timeout', function ($q, $rootScope, $scope, lpRemote, lmEditor, $timeout) {

    var roomKey;
    var startConfig = null;
    lmEditor.prepare(this, $scope);

    $scope.isnumber = function (value) {
      return typeof(value) === 'number';
    };

    $q.all([
      lmEditor.cache('area').then(function (areas) {
        $scope.areaList = areas;
      }),
      lpRemote.request('editor/config/get_defaults').then(function (defaults) {
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
      lpRemote.request('editor/config/get').then(function (config) {
        startConfig = config;
        $scope.startAreaId = config.start_room.split(':')[0];
      })
    ]).then(function () {
      $scope.changeArea().then(function () {
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

    this.postUpdate = function (config) {
      $timeout(function () {
        $rootScope.siteTitle = config.title;
      });

      lampost_config.title = config.title;
      lampost_config.description = config.description;
    }

  }]);
