angular.module('lampost_editor').service('lpEditorView', ['$window', '$log', 'lpEditor',
  function($window, $log, lpEditor) {

    var mudWindow = $window.opener;

    this.build = {
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

    this.mud = {
      social: {}
    };

    this.player = {
      player: {invalidate: true}
    }

    this.prepareView = function(viewType) {
      angular.forEach(this[viewType], function(context, key) {
        lpEditor.registerContext(key, context)
      });
      return lpEditor.initView();
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

