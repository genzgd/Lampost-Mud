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
    var previousSession = sessionStorage.getItem('editSessionId');
    if (previousSession) {
      lmRemote.connect('editor/edit_connect', previousSession);
    } else {
      var gameSession = localStorage.getItem('activeImm');
      if (gameSession) {
        gameSession = JSON.parse(gameSession);
        lmRemote.connect('editor/edit_connect', null, gameSession);
      } else {
        lmRemote.connect('editor/edit_connect');
      }
    }

  }]);

angular.module('lampost_editor').controller('EditorNavController', ['$rootScope', '$scope', 'lmBus',
  function($rootScope, $scope, lmBus) {

  lmBus.register('editor_login', function(data) {
    $rootScope.loggedIn = true;
    $rootScope.playerName = data.playerName;
  });
}]);

angular.module('lampost_editor').controller('EditorAppController', ['$scope', function($scope) {

}]);