angular.module('lampost_editor').service('lpEditor', ['$q', 'lmUtil', 'lmRemote', 'lmDialog', 'lpCache', 'lmBus',
  function ($q, lmUtil, lmRemote, lmDialog, lpCache, lmBus) {

    var lpEditor = this;
    var contextMap = {};

    function EditContext(id, init) {
      this.id = id;
      angular.copy(init, this);
      this.url = this.url || id;
      this.label = this.label || lmUtil.capitalize(id);
      this.baseUrl = 'editor/' + this.url + '/';
      this.objLabel = this.objLabel || this.label;
      this.include = this.include || 'editor/view/' + id + '.html';
      this.extend = this.extend || angular.noop;
    }

    EditContext.prototype.newModel = function () {
      var model = {can_write: true, owner_id: lpEditor.playerId};
      this.extend(model);
      return model;
    };

    EditContext.prototype.preCreate = function (model) {
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
      return lpCache.cache('constants').then(function (constants) {
        lpEditor.constants = constants;
      });
    };

    this.registerContext = function (contextId, context) {
      contextMap[contextId] = new EditContext(contextId, context);
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
      lmRemote.request(context.baseUrl + 'test_delete', {dbo_id: model.dbo_id}).then(function (holders) {
        var extra = '';
        if (holders.length > 0) {
          extra = "<br/><br/>This object will be removed from:<br/><br/><div> " + holders.join(' ') + "</div>";
        }
        lmDialog.showConfirm("Delete " + context.objLabel,
            "Are you certain you want to delete " + context.objLabel + " " + model.dbo_id + "?" + extra,
          function () {
            lmRemote.request(context.baseUrl + 'delete', {dbo_id: model.dbo_id}).then(function () {
              lpCache.deleteModel(model);
            }, error);
          });
      });
    };

    this.display = function (model) {
      return model.name || model.title || model.dbo_id || '-new-';
    };

    lmBus.register('modelSelected', function (activeModel) {
      angular.forEach(contextMap, function (context) {
        if (context.parentType === activeModel.dbo_key_type) {
          context.parent = activeModel;
        }
      });
      lmBus.dispatch('activeUpdated', activeModel);
    });


    /*  config: new lpEditContext({label: "Mud Config", url: "config"}),
     players: {label: "Players", objLabel: 'Player', url: "player"},
     area: new lpEditContext({label: "Areas", objLabel: "Area", url: "area"}),
     room: {label: "Room", url: "room", create: 'dialog'},
     mobile: {label: "Mobile", url: "mobile", create: "dialog"},
     article: {label: "Article", url: "article", create: "dialog"},
     script: {label: "Script", url: "script"},
     social: {label: "Socials", objLabel: "Social", url: "social", create: 'dialog'},
     display: {label: "Display", url: "display"},
     race: {label: "Races", objLabel: "Race", url: "race"},
     attack: {label: "Attacks", objLabel: "Attack", url: "skill"},
     defense: {label: "Defenses", objLabel: "Defense", url: "skill"},
     imports: {label: "Imports"} */


  }]);


angular.module('lampost_editor').controller('MainEditorCtrl', ['$q', '$scope', 'lmBus', 'lmRemote', 'lmDialog', 'lpCache', 'lpEditor',
  function ($q, $scope, lmBus, lmRemote, lmDialog, lpCache, lpEditor) {

    var activeModel = {};
    var originalModel = {};
    var cacheKeys = [];
    var context;
    var baseUrl;

    lpEditor.registerContext('none', {label: 'Get Started'});

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
      lmBus.dispatch('editStarting', originalModel);
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
    }

    function init(orig) {
      baseUrl = context.baseUrl;
      originalModel = orig;
      clearSeeds();
      $q.all(lpCache.seedCache(context.refs, originalModel, cacheKeys)).then(initScope);
    }

    function reset() {
      context = lpEditor.getContext('none');
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
          return context.preCreate(activeModel).then(function () {
            lmRemote.request(baseUrl + 'create', activeModel).then(onCreated, dataError);
          }, dataError);
        }
        return lmRemote.request(baseUrl + 'update', activeModel).then(onSaved, dataError);
      })
    }

    function onCreated(created) {
      $scope.isDirty = false;
      lpCache.insertModel(created);
      lmBus.dispatch('modelSelected', created);
    }

    function onSaved(updated) {
      $scope.isDirty = false;
      lpCache.updateModel(updated);
      return intercept('postUpdate', activeModel);
    }

    function checkUnsaved() {
      return lmDialog.showConfirm("Unsaved Changes", "You have unsaved changes to " + $scope.objLabel +
        ": " + display() + ".  Save changes now?", saveModel);
    }

    function onOverwrite() {
      if (!$scope.isDirty) {
        return $q.when();
      }
      var deferred = $q.defer();
      lmDialog.showAlert({title: "Unsaved Changes ",
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
        init(model);
      })
    }

    lmBus.register('modelUpdate', function (updatedModel, outside) {
      if (updatedModel !== originalModel) {
        return;
      }
      if ($scope.isDirty && outside) {
        lmDialog.showConfirm("Outside Edit", "Warning -- This object has been updated by another user.  " +
          "Do you want to load the new object and lose your changes?", function () {
          angular.copy(originalModel, activeModel);
        });
      } else {
        $scope.outsideEdit = outside;
        angular.copy(originalModel, activeModel);
      }
    }, $scope);

    lmBus.register('modelDelete', function (modelList, delModel, outside) {
      if (activeModel.dbo_id === delModel.dbo_id) {
        if (outside) {
          lmDialog.showOk("Outside Delete", "This object has been deleted by another user.");
        }
        reset();
      }
    }, $scope);

    lmBus.register('editorClosing', function (handlers) {
      if ($scope.isDirty) {
        handlers.push(checkUnsaved);
      }
    }, $scope);

    lmBus.register('newEdit', function (type) {
      onOverwrite().then(function () {
        context = lpEditor.getContext(type);
        $scope.isNew = true;
        init(context.newModel());
      });
    }, $scope);

    lmBus.register('modelSelected', existingEdit);

    $scope.constants = lpEditor.constants;
    $scope.model = activeModel;
    $scope.saveModel = saveModel;

    $scope.$watch('model', function () {
      $scope.isDirty = !angular.equals(originalModel, activeModel);
    }, true);

    $scope.revertModel = function () {
      angular.copy(originalModel, activeModel);
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
      if (originalModel.dbo_id) {
        lpEditor.deleteModel(context, originalModel, dataError);
      } else {
        lmDialog.confirm("Delete " + context.objLabel,
            "Are you sure you want to abandon this new " + context.objLabel + "?").then(reset);
      }
    };

    $scope.$on('$destroy', clearSeeds);
    reset();
  }]);


angular.module('lampost_editor').controller('EditListCtrl', ['$scope', '$attrs', 'lmBus', 'lpCache', 'lpEditor',
  function ($scope, $attrs, lmBus, lpCache, lpEditor) {

    var type = $attrs.listType;
    var context = lpEditor.getContext(type);
    var activeModel;
    var listKey;

    $scope.type = type;
    $scope.editorLabel = context.label;
    $scope.addAllowed = function () {
      return (context.parent && context.parent.can_write) || !context.parentType;
    };

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
      })
    }

    function dataError(error) {
      $scope.errors.dataError = lpEditor.translateError(error);
    }

    lmBus.register("activeUpdated", function (activated) {
      if (activated.dbo_key_type === type) {
        activeModel = activated;
      } else if (context.parent === activated) {
        updateList();
        activeModel = null;
      }
    });

    $scope.deleteModel = function (model, event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      lpEditor.deleteModel(context, model, dataError);
    };

    $scope.selectModel = function (model, event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      lmBus.dispatch("modelSelected", model);
    };

    $scope.rowClass = function (model) {
      return model === activeModel ? 'warning' : '';
    };

    $scope.activeModel = function () {
      return activeModel ? lpEditor.display(activeModel) : '-NOT SELECTED-';
    };

    updateList()

  }]);

angular.module('lampost_editor').controller('MudConfigCtrl', ['$q', '$rootScope', '$scope', 'lmRemote',
  'lmEditor', '$timeout', function ($q, $rootScope, $scope, lmRemote, lmEditor, $timeout) {

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
      lmRemote.request('editor/config/get').then(function (config) {
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
