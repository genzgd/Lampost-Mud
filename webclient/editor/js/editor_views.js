angular.module('lampost_editor').service('lpEditorView',
  ['$window', '$q', '$filter', '$log', '$http', '$templateCache', 'lpEvent', 'lpCache', 'lpEditor','lpUtil', 'lpSkillService',
  function($window, $q,  $filter, $log, $http, $templateCache, lpEvent, lpCache, lpEditor, lpUtil, lpSkillService) {

    var mudWindow = $window.opener;
    var localData;
    var views = {};
    var viewLists = {};
    var viewState = {};
    var cols = {};
    var currentView;

    function ColDef(id, size, filter, options) {
      this.id = id;
      this.size = size;
      this.filter = (filter || 'model_prop').split(' ');
      angular.extend(this, options);
      if (!this.header) {
        if (this.id === 'dbo_id') {
          this.header = 'Id';
        } else {
          this.header = lpUtil.capitalize(this.id);
        }
      }
    }

    ColDef.prototype.hClass = ColDef.prototype.dClass = function() {
      return this.size ? 'col-md-' + this.size : '';
    };

    ColDef.prototype.data = function(model) {
      var result = model;
      for (var ix = 0; ix < this.filter.length; ix++) {
        result = $filter(this.filter[ix])(result, this.id);
      }
      return result;
    }

    function loadLocal() {
        localData = JSON.parse(localStorage.getItem(lpEditor.playerId + '*editData')) || {};
    }

    function updateLocal() {
        localStorage.setItem(lpEditor.playerId + '*editData', JSON.stringify(localData));
    }

    views.build = {
      area: {},
      room:  {
        refs: [
          {type: 'room', path: 'exits.destination'},
          {type: 'mobile', path: 'mobile_resets.mobile'},
          {type: 'article', path: 'article_resets.article'}
        ],
        extend: function(model) {
          model.dbo_id = this.parent.next_room_id;
        }
      },
      mobile: {
        preReqs: [lpSkillService.preLoad]
      },
      article: {
        preReqs: [lpSkillService.preLoad],
      }
    };

    viewLists.build = ['area', 'room', 'mobile', 'article'];
    cols.area = [new ColDef('dbo_id', 3), new ColDef('name', 5), new ColDef('owner_id', 4, 'model_prop cap',
     {header: 'Owner'})];
    cols.room = [new ColDef('dbo_id', 2, 'idOnly'), new ColDef('title', 10, 'model_prop cap')];
    cols.article = cols.mobile = [new ColDef('dbo_id', 3, 'idOnly'), new ColDef('title', 9, 'model_prop cap')];


    views.mud = {
      social: {},
      race: {
        preReqs: [lpSkillService.preLoad],
      },
      attack: {
        preUpdate: function (attack) {
          if (attack.damage_type == 'weapon' && attack.weapon_type == 'unused') {
            return $q.reject("Damage type of weapon with 'Unused' weapon is invalid.");
          }
          return $q.when();
        }
      },
      defense: {
        preUpdate: function(defense) {
          if (!defense.auto_start && !defense.verb) {
            return $q.reject("Either a command or 'autoStart' is required.");
          }
          return $q.when();
        }
      }
    };

    cols.social = [new ColDef('dbo_id', 4), new ColDef('aliases', 8, 'model_prop join')];
    cols.attack = cols.defense = [new ColDef('dbo_id', 5), new ColDef('verb', 7, null, {header: 'Command'})];
    cols.race = [new ColDef('dbo_id', 5), new ColDef('name', 7)];
    viewLists.mud = ['social', 'race', 'attack', 'defense'];

    views.player = {
      player: {invalidate: true}
    }
    cols.player = [new ColDef('dbo_id', 3, 'model_prop cap', {header: 'Name'})];
    viewLists.player = ['player'];

    this.lastView = function() {
        loadLocal();
        return localData.lastView;
    };

    this.cols = function(type) {
      return cols[type];
    };

    this.prepareView = function(viewType) {
      currentView = viewType;
      loadLocal();
      localData.lastView = viewType;
      localData.viewStates = localData.viewStates || {};
      viewState = localData.viewStates[viewType] || {};
      viewState.models = viewState.models || {}
      viewState.openLists = viewState.openLists || {}
      localData.viewStates[viewType] = viewState;
      this.viewState = viewState;
      updateLocal();

      angular.forEach(views[viewType], function(contextDef, key) {
        lpEditor.registerContext(key, contextDef);
      });

      lpEditor.initView().then(finalizeView);
    };

    function finalizeView() {
      lpEvent.dispatchLater("startViewLayout");
      var promises = [];
      promises.push($http.get('editor/view/edit_list.html', {cache: $templateCache}));
      promises.push($http.get('editor/view/editor_main.html', {cache: $templateCache}));
      angular.forEach(viewState.models, function(dbo_id, type) {
        promises.push(lpCache.seedCacheId(type + ':'+ dbo_id));
      })
      if (viewState.lastType) {
        promises.push(lpCache.seedCacheId(viewState.lastType + ':' + viewState.lastEdit));
        promises.push($http.get('editor/view/' + viewState.lastType + '.html', {cache: $templateCache}));
      }
      $q.all(promises).then(function() {
        angular.forEach(viewState.models, function(dbo_id, type) {
          var selectedModel = lpCache.cacheValue(type + ':' + dbo_id);
          if (selectedModel) {
            lpEvent.dispatchLater('modelSelected', selectedModel, 'load');
          }
        })
        if (viewState.lastType) {
          var editModel = lpCache.cacheValue(viewState.lastType + ':' + viewState.lastEdit);
          if (editModel) {
            lpEvent.dispatchLater('startEdit', editModel);
          }
        }
      });
    }


    this.toggleList = function(type, value) {
        if (value) {
            viewState.openLists[type] = true;
        } else {
            delete viewState.openLists[type];
        }
        updateLocal();
    };

    this.listState = function(type) {
        return viewState.openLists[type];
    };

    this.editLists = function() {
      return viewLists[currentView];
    }

    this.selectModel = function(type, value, selectType) {
      if (selectType === 'load') {
        return;
      }
      if (value && value.dbo_id) {
        viewState.models[type] = value.dbo_id;
      } else {
        delete viewState.models[type];
      }
      updateLocal();
    };

    this.mudWindow = function() {
      try {
        if (mudWindow && !mudWindow.closed) {
          window.open("", mudWindow.name);
        }
      } catch (e) {
        $log.log("Unable to reference mud window");
        mudWindow = null;
      }
      if (!mudWindow || mudWindow.closed) {
        mudWindow = window.open('lampost.html', '_blank');
      }
      if (mudWindow) {
        try {
          mudWindow.focus();
        } catch (e) {
          $log.log("Error opening other window", e);
        }
      }
    };


    lpEvent.register('editReady', function(model) {
      if (model.dbo_key_type && model.dbo_id) {
        viewState.lastEdit = model.dbo_id
        viewState.lastType = model.dbo_key_type;
        updateLocal();
      }

    });

  }]);


angular.module('lampost_editor').controller('EditLayoutCtrl', ['$scope', 'lpEvent', 'lpEditorView',
  function($scope, lpEvent, lpEditorView) {

  var viewState = {};

  $scope.listPaneClass = function() {
    return 'col-md-' + (viewState.listPaneSize === undefined ? '3' : viewState.listPaneSize);
  }

  $scope.editPaneClass = function() {
    return 'col-md-' + (viewState.editPaneSize === undefined ? '9' : viewState.editPaneSize);
  }

  lpEvent.register('startViewLayout', function() {
    $scope.editLists = lpEditorView.editLists();
    viewState = lpEditorView.viewState;
    }, $scope);
}]);