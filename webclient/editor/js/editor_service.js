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
      this.registerContext('no_item', {metadata: true});
      lpCache.clearAll();
      return lpRemote.request('editor/constants').then(function (constants) {
        lpEditor.constants = constants;
      });
    };

    this.initView = function() {
      var requests = [];
      angular.forEach(contextMap, function(context) {
        angular.forEach(context.preReqs, function(preReq) {
          requests.push(preReq());
        });
        if (!context.metadata) {
          requests.push(lpRemote.request('editor/' + context.url + '/metadata').then(function(data) {
            context.parentType = data.parent_type;
            if (data.children_types && data.children_types.length) {
              context.childrenTypes = data.children_types;
            }
            context.newObj = data.new_object;
            context.perms = data.perms;
            context.metadata = true;
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
            "Are you certain you want to delete " + context.objLabel + " " + model.dbo_id + "?" + extra).then(
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

    lpEvent.register('modelSelected', function (activeModel, selectType) {
      angular.forEach(contextMap, function (context) {
        if (context.parentType === activeModel.dbo_key_type) {
          context.parent = activeModel;
        }
      });
      lpEvent.dispatch('activeUpdated', activeModel, selectType);
    });

    /*  config: new lpEditContext({label: "Mud Config", url: "config"}),
     script: {label: "Script", url: "script"},
     display: {label: "Display", url: "display"},
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
      if ($scope.detailTemplate != context.include) {
        // Let everything load before sending out any events.  The initScope method should be called
        // again once the correct content is available
        $scope.detailTemplate = context.include;
        return;
      }
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

      $rootScope.activeEditor = activeModel.dbo_key_type;
      lpEvent.dispatch('editReady', activeModel);
    }

    $scope.$on('$includeContentLoaded', function(event, included) {
        if (included === $scope.detailTemplate) {
          initScope();
        }
      });

    function init(orig) {
      baseUrl = context.baseUrl;
      originalModel = orig;
      clearSeeds();
      $q.all(lpCache.seedCache(context.refs, originalModel, cacheKeys)).then(initScope);
    }

    function reset() {
      context = lpEditor.getContext('no_item');
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
      }, dataError);
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
          "Do you want to load the new object and lose your changes?").then(function () {
          angular.copy(originalModel, activeModel);
        });
      } else {
        $scope.outsideEdit = outside;
        angular.copy(originalModel, activeModel);
        lpEvent.dispatch('editReady', activeModel);
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
        handlers.push(onOverwrite());
      }
    }, $scope);

    lpEvent.register('childUpdate', angular.noop, $scope);

    lpEvent.register('newEdit', function (type) {
      onOverwrite().then(function () {
        context = lpEditor.getContext(type);
        $scope.isNew = true;
        init(context.newModel());
      });
    }, $scope);

    lpEvent.register('startEdit', existingEdit, $scope);

    $scope.model = activeModel;
    $scope.saveModel = saveModel;

    $scope.$watch('model', function () {
      $scope.isDirty = !angular.equals(originalModel, activeModel);
    }, true);

    $scope.revertModel = function () {
      angular.copy(originalModel, activeModel);
      lpEvent.dispatch('editStarting', originalModel);
      lpEvent.dispatch('editReady', activeModel)
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
            "Are you sure you want to abandon this new " + context.objLabel + "?").then(reset);
      } else {
        reset();
      }
    };

    $scope.$on('$destroy', clearSeeds);
    reset();
  }]);


angular.module('lampost_editor').controller('EditListCtrl',
  ['$scope', '$timeout', '$attrs', 'lpEvent', 'lpCache', 'lpEditor', 'lpEditorView',
  function ($scope, $timeout, $attrs, lpEvent, lpCache, lpEditor, lpEditorView) {

    var type;
    var context;
    var activeModel;
    var listKey;

    this.initType = function(listType) {
      type = listType;
      context = lpEditor.getContext(type);
      $scope.colDefs = lpEditorView.cols(type);
      $scope.type = type;
      updateList();
    }

    $scope.addAllowed = function () {
      return ((context.parent && context.parent.can_write) || !context.parentType) && context.perms.add;
    };

    $scope.refreshAllowed = function() {
      return context.perms.refresh;
    };

    $scope.doRefresh = function(event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      lpCache.invalidate(listKey);
      updateList();
    };

    function changeActive(active, selectType) {
      activeModel = active;
      lpEditorView.selectModel(type, active, selectType);
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
      });
    }

    function dataError(error) {
      $scope.errors.dataError = lpEditor.translateError(error);
    }

    lpEvent.register("contextUpdate", function(updated) {
      if (context === updated) {
        updateList();
      }
    }, $scope);

    lpEvent.register("activeUpdated", function (activated, selectType) {
      if (activated.dbo_key_type === type) {
        changeActive(activated);
      } else if (context.parent === activated) {
        updateList();
        changeActive(null, selectType);
      } else if (!context.childrenTypes) {
        changeActive(null, selectType);
      }

    }, $scope);

    lpEvent.register("modelDelete", function(delModel) {
      if (activeModel == delModel) {
        changeActive(null);
      }
    }, $scope);

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

    $scope.editorLabel = function() {
      return context.parentType ? (context.plural || context.label + 's') : context.label;
    }

    $scope.editorTitle = function () {
      if (context.parentType) {
        return $scope.modelList && $scope.modelList.length;
      }
      return activeModel ? lpEditor.display(activeModel) : $scope.modelList && $scope.modelList.length;
    };

    $scope.refreshList = function () {
      lpCache.invalidate(listKey);
      updateList();
    }

    $scope.$on('$destroy', function() {
      lpCache.deref(listKey)}
    );

  }]);