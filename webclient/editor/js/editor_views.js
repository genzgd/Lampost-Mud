angular.module('lampost_editor').controller('BuildViewCtrl', ['lpEditor', function (lpEditor) {

    lpEditor.reset();

    lpEditor.registerContext('area');

    lpEditor.registerContext('room', {
      refs: [
        {type: 'room', path: 'exits.destination'},
        {type: 'mobile', path: 'mobile_resets.mobile_id'},
        {type: 'article', path: 'article_resets.article_id'}
      ],
      extend: function(model) {
        model.dbo_id = this.parent.next_room_id;
      }
    });

    lpEditor.registerContext('mobile');
    lpEditor.registerContext('article', {
      preEdit: function(model) {
      }
    });

    lpEditor.initView();

  }]);


angular.module('lampost_editor').controller('MudViewCtrl', ['lpEditor', function (lpEditor) {

    lpEditor.reset();

    lpEditor.registerContext('social');

    lpEditor.initView();

  }]);
