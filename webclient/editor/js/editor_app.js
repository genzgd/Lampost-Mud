angular.module('lampost_editor', ['lampost_dir', 'lampost_dlg', 'lampost_util', 'lampost_remote', 'ngSanitize']);

angular.module('lampost_editor').run(['$rootScope', 'lmRemote', 'lmBus',
  function ($rootScope, lmRemote, lmBus) {

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

  var editNav = [{id: 'build', label: 'Build', icon: 'fa-cubes'}, {id: 'mud', label: 'Mud', icon: 'fa-shield'},
    {id: 'config', label:'Admin', icon: 'fa-wrench'}, {id: 'players', label: 'Players', icon: 'fa-user'}];

  var activeNav = '';

  $scope.changeNav = function(newNav) {
    if (newNav == activeNav) {
      return;
    }
    activeNav = newNav;
    for (var i = 0; i < $scope.links.length; i++) {
      var link = $scope.links[i];
      if (link.id === activeNav) {
        link.active = 'active';
      } else {
        link.active = '';
      }
    }
    lmBus.dispatch('editorChanging');
    $rootScope.mainTemplate = 'editor/view/' + activeNav + '_view.html';
  };

  lmBus.register('connect', function() {
    $rootScope.appState = 'connected';
    $scope.welcome = 'Please log in.';
  });

  lmBus.register('editor_login', function(data) {
    activeNav = '';
    $rootScope.appState = 'loggedIn';
    $rootScope.playerName = data.playerName;
    $scope.welcome = "Immortal " + data.playerName;
    $scope.links = [];
    for (var i = 0; i < editNav.length; i++) {
      var nav = editNav[i];
      if (data.edit_perms.indexOf(nav.id) > -1) {
        var link = angular.copy(nav);
        link.active = '';
        $scope.links.push(link);
      }
    }
    if ($scope.links.length) {
      $scope.changeNav($scope.links[0].id);
    }

  });

  lmBus.register('editor_logout', function() {
    $rootScope.appState = 'connected';
    $scope.welcome = 'Please Log In';
    $scope.links = [];
  });

  $scope.editorLogout = function() {
    lmBus.dispatch('server_request', 'editor/edit_logout');
  }
}]);

angular.module('lampost_editor').controller('EditLoginController', ['$scope', 'lmBus',
  function($scope, lmBus) {

    $scope.login = {};

    $scope.editorLogin = function() {
      lmBus.dispatch('server_request', 'editor/edit_login', $scope.login);
    };

    lmBus.register('login_failure', function(failure) {
      $scope.loginError = failure;
    }, $scope);

}]);