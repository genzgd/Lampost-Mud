angular.module('lampost_editor', ['lampost_dir', 'lampost_dlg', 'lampost_util', 'lampost_remote', 'ngSanitize']);

angular.module('lampost_editor').run(['$window', '$rootScope', 'lpRemote', 'lpEvent', 'lpUtil',
  function ($window, $rootScope, lpRemote, lpEvent, lpUtil) {

    $window.name = 'lpEditor' + new Date().getTime();

    $window.onbeforeunload = function () {
      var handlers = [];
      lpEvent.dispatchSync('editorClosing', handlers);
      if (handlers.length) {
        return "You have changes to " + handlers.length + " item(s).  Changes will be lost if you leave this page.";
      }
      $window.windowClosing = true;
      lpEvent.dispatch("window_closing");
      return undefined;
    };

    $window.onunload = function () {
      $window.windowClosing = true;
    };

    $rootScope.idOnly = function (model) {
      return model && model.dbo_id && model.dbo_id.split(':')[1];
    };
    $rootScope.cap = lpUtil.capitalize;

    $rootScope.errors = {};
    $rootScope.siteTitle = lampost_config.title;
    $rootScope.appState = 'connecting';
    var previousSession = sessionStorage.getItem('editSessionId');
    if (previousSession) {
      lpRemote.connect('editor/edit_connect', previousSession);
    } else {
      var gameSession = localStorage.getItem('activeImm');
      if (gameSession) {
        gameSession = JSON.parse(gameSession);
        lpRemote.connect('editor/edit_connect', null, gameSession);
      } else {
        lpRemote.connect('editor/edit_connect');
      }
    }

  }]);

angular.module('lampost_editor').controller('EditorNavController',
  ['$q', '$rootScope', '$scope', 'lpEvent', 'lpUtil', 'lpEditor', 'lpEditorLayout',
  function ($q, $rootScope,  $scope, lpEvent, lpUtil, lpEditor, lpEditorLayout) {

    var sessionId;
    var editNav = [
      {id: 'build', label: 'Areas', icon: 'fa-share-alt', mode: 'edit'},
      {id: 'mud', label: 'Global', icon: 'fa-globe', mode: 'edit'},
      {id: 'player', label: 'Players', icon: 'fa-user', mode: 'edit'},
      //{id: 'config', label: 'Config', icon: 'fa-gears', mode: 'edit'},
      {id: 'admin', label: 'Admin', icon: 'fa-wrench', mode: 'admin'}
    ];

    var activeNav;

    lpEvent.register('connect', function (data) {
      sessionId = data;
    });

    lpEvent.register('connect_only', function() {
      $rootScope.appState = 'connected';
      $rootScope.mainTemplate = null;
      $scope.welcome = 'Please log in.';
    });

    lpEvent.register('editor_login', function (data) {
      activeNav = undefined;
      $rootScope.playerName = data.playerName;
      sessionStorage.setItem('editSessionId', sessionId);
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

      lpEditor.init(data).then(function () {
        $rootScope.constants = lpEditor.constants;
        $rootScope.immortals = lpEditor.immortals;
        var access = [];
        angular.forEach(lpEditor.constants.imm_titles, function(value, key) {
          if (value > 0) {
            access.push({name: lpUtil.capitalize(key), value: value});
          }
        });
        lpUtil.descIntSort(access, 'value');
        access.unshift({name: 'Default', value: 0});
        $rootScope.accessLevels = access;

        var lastView = lpEditorLayout.lastView();
        for (var ix = 0; ix < $scope.links.length; ix++) {
          var link = $scope.links[ix];
          if (link.id === lastView ) {
            $scope.changeNav(link);
            return;
          }
        }
        $scope.changeNav($scope.links[0]);
      });

    });

    lpEvent.register('editor_logout', function () {
      sessionStorage.removeItem('editSessionId');

      $rootScope.appState = 'connected';
      $rootScope.mainTemplate = null;
      $scope.welcome = 'Please Log In';
      $scope.links = [];
    }, $scope);

    $scope.editorLogout = function () {
      lpEvent.dispatch('server_request', 'editor/edit_logout');
    }

    $scope.changeNav = function (newNav) {
      if (newNav == activeNav) {
        return;
      }

      var handlers = [];
      lpEvent.dispatch('editorClosing', handlers);
      $q.all(handlers).then(function () {
        $rootScope.appState = newNav.mode;
        activeNav = newNav;
        for (var i = 0; i < $scope.links.length; i++) {
          var link = $scope.links[i];
          if (link.id === activeNav.id) {
            link.active = 'active';
          } else {
            link.active = '';
          }
        }
        lpEditorLayout.prepareView(activeNav.id);
      });
    };

    $scope.mudWindow = lpEditorLayout.mudWindow;

  }]);


angular.module('lampost_editor').controller('EditLoginController', ['$scope', 'lpEvent',
  function ($scope, lpEvent) {

    $scope.login = {};

    $scope.editorLogin = function () {
      lpEvent.dispatch('server_request', 'editor/edit_login', $scope.login);
    };

    lpEvent.register('login_failure', function (failure) {
      $scope.loginError = failure;
    }, $scope);

  }]);