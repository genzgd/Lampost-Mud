angular.module('lampost_editor', ['lampost_dir', 'lampost_dlg', 'lampost_util', 'lampost_remote']);

angular.module('lampost_editor').run(['$timeout', '$rootScope', 'lmUtil', 'lmEditor', 'lmRemote', 'lmBus',
  function ($timeout, $rootScope, lmUtil, lmEditor, lmRemote, lmBus) {

    window.onbeforeunload = function () {
      var handlers = [];
      lmBus.dispatch('editorClosing', handlers);
      if (handlers.length) {
        return "You have changes to " + handlers.length + " item(s).  Changes will be lost if you leave this page.";
      }
      window.windowClosing = true;
      return undefined;
    };

    window.onunload = function () {
      window.windowClosing = true;
    };

    $rootScope.siteTitle = lampost_config.title;
    $rootScope.appState = 'connecting';
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

  lmBus.register('connect', function() {
    $rootScope.appState = 'connected';
    $scope.welcome = 'Please log in.';
  });

  lmBus.register('editor_login', function(data) {
    $rootScope.appState = 'loggedIn';
    $rootScope.playerName = data.playerName;
    $scope.welcome = "Immortal " + data.playerName;
  });

  lmBus.register('editor_logout', function() {
    $rootScope.appState = 'connected';
    $scope.welcome = 'Please Log In';
  });

  $scope.editorLogout = function() {
    lmBus.dispatch('server_request', 'editor/edit_logout');
  }
}]);

angular.module('lampost_editor').controller('EditorAppController', ['$scope', 'lmBus',
  function($scope, lmBus) {

    $scope.login = {};
    $scope.loginError = true;

    $scope.editorLogin = function() {
      lmBus.dispatch('server_request', 'editor/edit_login', $scope.login);
    };

    lmBus.register('login_failure', function(failure) {
      $scope.loginError =true;
    }, $scope);

    lmBus.register('editor_login', function() {
      $scope.login = {};
    });

}]);