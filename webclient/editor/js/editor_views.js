angular.module('lampost_editor').service('lpEditorView', ['lpEditor', function(lpEditor) {

    this.build = {
      area: {},
      room:  {
        refs: [
          {type: 'room', path: 'exits.destination'},
          {type: 'mobile', path: 'mobile_resets.mobile_id'},
          {type: 'article', path: 'article_resets.article_id'}
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
  }]);

