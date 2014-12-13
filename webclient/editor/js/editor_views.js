angular.module('lampost_editor').service('lpEditorView', ['$window', '$log', 'lpEvent', 'lpEditor',
  function($window, $log, lpEvent, lpEditor) {

    var mudWindow = $window.opener;
    var localData;
    var views = {};
    var viewState = {};

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
      mobile: {},
      article: {}
    };

    views.mud = {
      social: {}
    };

    views.player = {
      player: {invalidate: true}
    }

    this.lastView = function() {
        loadLocal();
        return localData.lastView;
    }

    this.prepareView = function(viewType) {
      loadLocal();
      localData.lastView = viewType;
      localData.viewStates = localData.viewStates || {};
      viewState = localData.viewStates[viewType] || {};
      viewState.models = viewState.models || {}
      viewState.openLists = viewState.openLists || {}
      localData.viewStates[viewType] = viewState;
      updateLocal();

      angular.forEach(views[viewType], function(contextDef, key) {
        lpEditor.registerContext(key, contextDef);
      });

      return lpEditor.initView();
    }

    this.toggleList = function(type, value) {
        if (value) {
            viewState.openLists[type] = true;
        } else {
            delete viewState.openLists[type];
        }
        updateLocal();
    }

    this.listState = function(type) {
        return viewState.openLists[type];
    }

    this.selectedId = function(type) {
        return viewState.models[type];
    }

    this.lastEdit = function(type) {
        return type == viewState.lastType ? viewState.lastEdit : undefined;
    }

    this.selectModel = function(type, value) {
      if (value && value.dbo_id) {
        viewState.models[type] = value.dbo_id;
        updateLocal();
      }
    }

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
    }

    lpEvent.register('editReady', function(model) {
      if (model.dbo_key_type && model.dbo_id) {
        viewState.lastEdit = model.dbo_id
        viewState.lastType = model.dbo_key_type;
      }
      updateLocal();
    });

  }]);

