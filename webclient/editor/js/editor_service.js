angular.module('lampost_editor').service('lpEditor', ['lmUtil', 'lmRemote', 'lmDialog', 'lpCache',
  function (lmUtil, lmRemote, lmDialog, lpCache) {

    function EditContext(id, init) {
      this.id = id;
      angular.copy(init, this);
      this.url = this.url || id;
      this.label = this.label || lmUtil.capitalize(id);
      this.baseUrl = 'editor/' + this.url + '/';
      this.objLabel = this.objLabel || this.label;
    }

    var contextMap = {};

    this.init = function() {
      return lpCache('constants').then(function (constants) {
        this.constants = constants;
      });
    };

    this.registerContext = function (contextId, context) {
      contextMap[contextId] = new EditContext(context);
    };

    this.getContext = function (contextId) {
      return contextMap[contextId];
    };

    this.registerContext('none', {label: 'No Object Selected'});
    this.registerContext('room');
    this.registerContext('area');

    this.deleteModel = function (dbo_id, error) {
       var context = contextMap[dbo_id.split(':')[0]];
       lmRemote.request(context.baseUrl + 'test_delete', {dbo_id: dbo_id}).then(function (holders) {
          var extra = '';
          if (holders.length > 0) {
            extra = "<br/><br/>This object will be removed from:<br/><br/><div> " + holders.join(' ') + "</div>";
          }
          lmDialog.showConfirm("Delete " + context.objLabel,
              "Are you certain you want to delete " + context.objLabel + " " + dbo_id + "?" + extra,
            function () {
              lmRemote.request(context.baseUrl + 'delete', {dbo_id: model.dbo_id}).then(function () {
                deleteModel(model);
              }, error);
            });
        });
    };


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


angular.module('lampost_editor').controller('mainEditorController', ['$q', '$scope', 'lmBus', 'lmRemote', 'lmDialog', 'lpCache', 'lpEditor',
  function ($q, $scope, lmBus, lmRemote, lmDialog, lpCache, lpEditor) {

    var activeModel = {};
    var originalModel;
    var context;
    var baseUrl;
    var parentId;

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

    function init(type) {
      context = lpEditor.getContext(type);
      baseUrl = context.baseUrl;
      parentId = context.parentId;
      $scope.isDirty = false;
      $scope.editorLabel = context.label;
    }

    function reset(type) {
      init(type);
      originalModel = null;
      angular.copy({}, activeModel);
    }

    function intercept(interceptor, args) {
      if (context[interceptor]) {
        return $q.when(context[interceptor](args));
      }
      return $q.when();
    }

    function dataError(error) {
      $scope.dataError = error.text;
    }

    function saveModel() {
      return intercept('preUpdate', activeModel).then(function () {
        if (originalModel) {
          return lmRemote.request(baseUrl + 'update', activeModel).then(onSaved, dataError);
        }
        return lmRemote.request(baseUrl + 'create', activeModel).then(onCreated, dataError);
      })
    }

    function onCreated(created) {
      lpCache.insertModel(created);
      originalModel = created;
      angular.copy(originalModel, activeModel);
    }

    function onSaved(updated) {
      editScope.isDirty = false;
      lpCache.updateModel(updated);
      return intercept('postUpdate', activeModel);
    }

    function checkUnsaved() {
      return lmDialog.showConfirm("Unsaved Changes", "You have unsaved changes to " + $scope.objLabel +
        ": " + $scope.model.dbo_id + ".  Save changes now?", saveModel);
    }

    function onOverwrite() {
      var deferred = $q.defer();
      lmDialog.showAlert({title: "Unsaved Changes ",
        body: "You have unsaved changes to <b>" + display(activeModel) +
          "</b>.  Save your changes, discard your changes, or continue editing <b>" + display($scope.model) + "</b>?",
        buttons: [
          {label: "Save Changes", class: "btn-default", dismiss: true, click: function () {
            deferred.resolve(saveModel())
          }},
          {label: "Discard Changes", class: "btn-danger", dismiss: true, click: deferred.resolve},
          {label: "Continue Previous Edit", class: "btn-info", default: true, cancel: true}
        ]}, true);
      return deferred.promise;
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
      if (activeModel.dbo_id == delModel.dbo_id) {
        if (outside) {
          lmDialog.showOk("Outside Delete", "This object has been deleted by another user.");
        }
        reset('none');
      }
    }, $scope);

    lmBus.register('editorClosing', function (handlers) {
      if ($scope.isDirty) {
        handlers.push(checkUnsaved);
      }
    }, $scope);

    lmBus.register('newEdit', function (type) {

      function startNew() {
        reset(type);
        $scope.saveLabel = "Create";
        intercept('create', activeModel);
      }

      if ($scope.isDirty) {
        onOverwrite().then(startNew);
      } else {
        startNew();
      }
    }, $scope);

    $scope.constants = lpEditor.constants;
    $scope.model = activeModel;
    $scope.saveModel = saveModel;

    $scope.$watch('model', function (model) {
      if (model) {
        scope.isDirty = originalModel && !angular.equals(originalModel, activeModel);
      } else {
        scope.isDirty = false;
      }
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

    $scope.deleteAlias = function (index) {
      activeModel.aliases.splice(index, 1);
    };

    $scope.deleteModel = function (event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      if (originalModel) {
        lpEditor.deleteModel(originalModel.dbo_id, dataError);
      } else {
        reset('none');
      }
    };

    reset('none');
  }
]);


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
