angular.module('lampost_editor').controller('MainEditorCtrl',
  ['$scope', '$rootScope', '$q', '$timeout', 'lpEvent', 'lpRemote', 'lpDialog', 'lpCache', 'lpEditor',
  function ($scope, $rootScope, $q, $timeout, lpEvent, lpRemote, lpDialog, lpCache, lpEditor) {

    var activeModel = {};
    var originalModel = {};
    var origAccess = {};
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

    function initActive() {
      angular.copy(originalModel, activeModel);
      origAccess.read = originalModel.read_access;
      origAccess.write = originalModel.write_access;
    }

    function initScope() {
      if ($scope.detailTemplate != context.include) {
        // Let everything load before sending out any events.  The initScope method should be called
        // again once the correct content is available
        $scope.detailTemplate = context.include;
        return;
      }
      lpEvent.dispatch('editStarting', originalModel);
      initActive();
      lpEditor.original = originalModel;
      lpEditor.context = context;
      $scope.isNew = !originalModel.dbo_id;
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
        if (included === $scope.detailTemplate && included === context.include) {
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
        if (!originalModel.dbo_id) {
          var modelDto = angular.copy(activeModel);
          return context.newDto(modelDto).then(function () {
            lpRemote.request(baseUrl + 'create', {obj_def: modelDto}).then(onCreated, dataError);
          }, dataError);
        }
        return lpRemote.request(baseUrl + 'update', {obj_def: activeModel}).then(onSaved, dataError);
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

    function discard() {
      angular.copy(originalModel, activeModel);
      $scope.$isDirty = false;
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
          {label: "Discard Changes", class: "btn-danger", dismiss: true, click: function() {
            deferred.resolve(discard())
          }},
          {label: "Continue Previous Edit", class: "btn-info", default: true, cancel: true}
        ],
        onCancel: deferred.reject}, true);
      return deferred.promise;
    }

    function existingEdit(model) {
      onOverwrite(model).then(function () {
        context = lpEditor.getContext(model.dbo_key_type);
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
        init(context.newModel());
      });
    }, $scope);

    lpEvent.register('startEdit', existingEdit, $scope);

    $scope.model = activeModel;
    $scope.saveModel = saveModel;

    $scope.checkAccess = function(type) {
      var error;
      var key = type + '_access';
      if (activeModel[key] > lpEditor.immLevel) {
        error = "Access should not be higher than your level.";
      } else if ($scope.model.read_access > $scope.model.write_access) {
        error = "Read access should not be higher than write access."
      } else if ($scope.model.write_access > $scope.model.imm_level) {
        error = "Write access should not be higher than owner level"
      }
      $scope.errors[key] = error;
      if (error) {
        activeModel[key] = origAccess[type];
      } else {
        origAccess[type] = activeModel[key];
      }
    };

    $scope.$watch('model', function () {
      $scope.isDirty = !angular.equals(originalModel, activeModel);
    }, true);

    $scope.revertModel = function () {
      initActive();
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
      if (originalModel.dbo_id) {
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
  ['$scope', '$timeout', '$attrs', 'lpEvent', 'lpCache', 'lpEditor', 'lpEditorLayout',
  function ($scope, $timeout, $attrs, lpEvent, lpCache, lpEditor, lpEditorLayout) {

    var type;
    var context;
    var activeModel;
    var listKey;

    this.initType = function(listType) {
      type = listType;
      context = lpEditor.getContext(type);
      $scope.colDefs = lpEditorLayout.cols(type);
      $scope.type = type;
      updateList();
    };

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
      lpCache.refresh(listKey);
      updateList();
    };

    function changeActive(active, selectType) {
      activeModel = active;
      lpEditorLayout.selectModel(type, active, selectType);
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
      return activeModel ? context.label : context.plural;
    };

    $scope.editorTitle = function () {
      if (activeModel) {
        return context.nameProp ? activeModel[context.nameProp] : lpEditor.display(activeModel);
      }
      if (context.parentType) {
        return $scope.modelList && $scope.modelList.length;
      }
      return $scope.modelList && $scope.modelList.length;
    };

    $scope.$on('$destroy', function() {
      lpCache.deref(listKey)}
    );

  }]);
