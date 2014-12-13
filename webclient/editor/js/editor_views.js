angular.module('lampost_editor').service('lpEditorView', ['$window', '$log', 'lpEvent', 'lpEditor',
  function($window, $log, lpEvent, lpEditor) {

    var mudWindow = $window.opener;
    var localData;
    var views = {};
    var openViews = {};

    lpEvent.register('editReady', function(model) {
        localData.editId = model.dbo_id;
        localData.editType = model.dbo_key_type;
        updateLocal();
    });

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
      localData.viewState = localData.viewState || {};
      this.openViews = localData.viewState[viewType] || {};
      localData.viewState[viewType] = this.openViews;
      updateLocal();

      angular.forEach(views[viewType], function(context, key) {
        lpEditor.registerContext(key, context)
      });
      return lpEditor.initView();
    }

    this.toggleList = function(type, value) {
        if (value) {
            this.openViews[type] = true;
        } else {
            delete this.openViews[type];
        }
        updateLocal();
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
  }]);

