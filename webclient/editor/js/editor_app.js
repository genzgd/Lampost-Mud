angular.module('lampost_editor', ['lampost_dir', 'lampost_dlg', 'lampost_util', 'lampost_remote']);

angular.module('lampost_editor').run(['$timeout', '$rootScope', 'lmUtil', 'lmEditor', 'lmRemote', 'lmBus',
  function ($timeout, $rootScope, lmUtil, lmEditor, lmRemote, lmBus) {

    window.onbeforeunload = function () {
      var handlers = [];
      lmBus.dispatch('editorClosing', handlers);
      if (handlers.length) {
        return "You have changes to " + handlers.length + " item(s).  Changes will be lost if you leave this page.";
      }
      return undefined;
    };

    window.onunload = function () {
      window.windowClosing = true;
    };

    $rootScope.siteTitle = lampost_config.title;
    var immSession = localStorage.getItem('activeImm');
    if (immSession) {
      immSession = JSON.parse(immSession);
      lmRemote.connect('edit_connect', immSession.sessionId, immSession);
    } else {
      lmRemote.connect('edit_connect');
    }

  }]);

angular.module('lampost_editor').controller('EditorNavController', ['$scope', 'lmBus', function($scope, lmBus) {

  lmBus.register('editor_login', function(data) {

  });
}]);

angular.module('lampost_editor').controller('EditorAppController', ['$scope', function($scope) {

}]);