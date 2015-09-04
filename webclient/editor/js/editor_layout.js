angular.module('lampost_editor').service('lpEditorLayout',
  ['$window', '$q', '$filter', '$log', '$http', '$templateCache', 'lpEvent', 'lpCache', 'lpEditor', 'lpUtil', 'lpSkillService',
    function ($window, $q, $filter, $log, $http, $templateCache, lpEvent, lpCache, lpEditor, lpUtil, lpSkillService) {

      var mudWindow = $window.opener;
      var localData;
      var localVersion = 1;
      var viewLists = {};
      var viewDefaults = {};
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
            this.header = lpUtil.capitalize(this.id.replace('_', ' '));
          }
        }
      }

      ColDef.prototype.hClass = ColDef.prototype.dClass = function () {
        return this.size ? 'col-md-' + this.size : '';
      };

      ColDef.prototype.data = function (model) {
        var result = model;
        for (var ix = 0; ix < this.filter.length; ix++) {
          result = $filter(this.filter[ix])(result, this.id);
        }
        return result;
      };

      function loadLocal() {
        localData = JSON.parse(localStorage.getItem(lpEditor.playerId + '*editData')) || {};
        if (localData.version != localVersion) {
          localData = {version: localVersion};
        }
      }

      function updateLocal() {
        localStorage.setItem(lpEditor.playerId + '*editData', JSON.stringify(localData));
      }

      viewLists.build = ['area', 'room', 'mobile', 'article', 'script'];
      cols.area = [new ColDef('dbo_id', 3), new ColDef('name', 5), new ColDef('owner_id', 4, 'model_prop cap',
        {header: 'Owner'})];
      cols.room = [new ColDef('dbo_id', 2, 'idOnly'), new ColDef('title', 10, 'model_prop cap')];
      cols.article = cols.mobile = [new ColDef('dbo_id', 3, 'idOnly'), new ColDef('title', 9, 'model_prop cap')];
      cols.script = [new ColDef('dbo_id', 2, 'idOnly'), new ColDef('title', 7, 'model_prop cap'), new ColDef('obj_type', 3)];
      viewDefaults.build = {paneSizes: [3, 9, 0]};

      viewLists.mud = ['social', 'race', 'attack', 'defense'];
      cols.social = [new ColDef('dbo_id', 12)];
      cols.attack = cols.defense = [new ColDef('dbo_id', 5), new ColDef('verb', 7, null, {header: 'Command'})];
      cols.race = [new ColDef('dbo_id', 5), new ColDef('name', 7)];
      viewDefaults.mud = {paneSizes: [2, 10, 0]};

      viewLists.player = ['player', 'user'];
      cols.user = [new ColDef('dbo_id', 1), new ColDef('user_name', 4, null, {header: 'Name'}), new ColDef('imm_level', 3, 'immTitle'), new ColDef('email', 4)];
      cols.player = [new ColDef('dbo_id', 4, 'model_prop cap', {header: 'Name'}), new ColDef('last_login', 5,
        null, {
          data: function (model) {
            return (model.logged_in == 'Yes' ? '*' : '') + $filter('date')(model.last_login * 1000, 'short')
          }
        }),
        new ColDef('imm_level', 3, 'immTitle')];
      viewDefaults.player = {paneSizes: [5, 7, 0]};

      this.lastView = function () {
        loadLocal();
        return localData.lastView;
      };

      this.cols = function (type) {
        return cols[type];
      };

      this.prepareView = function (viewType) {
        currentView = viewType;
        loadLocal();
        localData.lastView = viewType;
        localData.viewStates = localData.viewStates || {};
        viewState = localData.viewStates[viewType] || {};
        viewState.models = viewState.models || {};
        viewState.openLists = viewState.openLists || {};
        viewState.settings = viewState.settings || viewDefaults[viewType];
        localData.viewStates[viewType] = viewState;
        this.viewState = viewState;
        updateLocal();

        lpEditor.initView(viewLists[viewType]).then(finalizeView);
      };

      function finalizeView() {
        var promises = [];
        lpEvent.dispatchLater("startViewLayout");
        promises.push($http.get('editor/view/edit_list.html', {cache: $templateCache}));
        promises.push($http.get('editor/view/editor_main.html', {cache: $templateCache}));
        angular.forEach(viewState.models, function (dbo_id, type) {
          promises.push(lpCache.seedCacheId(type + ':' + dbo_id));
        });
        if (viewState.lastType) {
          promises.push(lpCache.seedCacheId(viewState.lastType + ':' + viewState.lastEdit));
          promises.push($http.get('editor/view/' + viewState.lastType + '.html', {cache: $templateCache}));
        }
        $q.all(promises).then(function () {
          var editModel, selectedModel;
          editModel = selectedModel = null;
          angular.forEach(viewState.models, function (dbo_id, type) {
            selectedModel = lpCache.cachedValue(type + ':' + dbo_id);
            if (selectedModel) {
              lpEvent.dispatchLater('modelSelected', selectedModel, 'load');
            }
          });
          if (viewState.lastType) {
            editModel = lpCache.cachedValue(viewState.lastType + ':' + viewState.lastEdit);
          }
          lpEvent.dispatchLater('startEdit', editModel || selectedModel || {dbo_key_type: 'no_item'});
        });
      }

      this.toggleList = function (type, value) {
        if (value) {
          viewState.openLists[type] = true;
        } else {
          delete viewState.openLists[type];
        }
        updateLocal();
      };

      this.listState = function (type) {
        return viewState.openLists[type];
      };

      this.editLists = function () {
        return viewLists[currentView];
      };

      this.selectModel = function (type, value, selectType) {
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

      this.mudWindow = function () {
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

      this.update = updateLocal;

      lpEvent.register('editReady', function (model) {
        if (model.dbo_key_type && model.dbo_id) {
          viewState.lastEdit = model.dbo_id;
          viewState.lastType = model.dbo_key_type;
          updateLocal();
        }

      });

    }]);


angular.module('lampost_editor').controller('EditLayoutCtrl', ['$scope', 'lpEvent', 'lpEditorLayout',
  function ($scope, lpEvent, lpEditorLayout) {

    var settings = {paneSizes: []};

    $scope.paneClass = function (pane) {
      return settings.paneSizes[pane] ? 'col-md-' + settings.paneSizes[pane] : 'hidden';
    };

    $scope.swapCheats = function () {
      settings.showCheats = !settings.showCheats;
      lpEditorLayout.update();
    };

    $scope.cheatSheets = ["editor/view/social_cheat.html"];

    $scope.changeSize = function (pane, other, size) {

      var newSize = settings.paneSizes[pane] + size;
      var otherSize = settings.paneSizes[other] - size;
      var availSize = newSize + otherSize;

      if (newSize < 2 && size < 0) {
        newSize = 0;
        otherSize = availSize;
      } else if (newSize < 2 && size > 0) {
        newSize = 2;
        otherSize = availSize - 2;
      } else if (otherSize < 2 && size > 0) {
        newSize = availSize;
        otherSize = 0;
      } else if (otherSize < 2 && size < 0) {
        otherSize = 2;
        newSize = availSize - 2;
      }
      settings.paneSizes[pane] = newSize;
      settings.paneSizes[other] = otherSize;

      lpEditorLayout.update();
    };

    lpEvent.register('startViewLayout', function () {
      $scope.editLists = lpEditorLayout.editLists();
      settings = lpEditorLayout.viewState.settings;
      $scope.settings = settings;
    }, $scope);
  }]);
