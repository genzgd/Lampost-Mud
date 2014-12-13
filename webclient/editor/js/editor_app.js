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
    $rootScope.join = function (values, del) {
      return values.join(del || ' ');
    };
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

    $rootScope.newEditor = function (editorId, event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      lpEvent.dispatch('newEdit', editorId);
    }

  }]);

angular.module('lampost_editor').controller('EditorNavController',
  ['$q', '$log', '$window', '$rootScope', '$scope', 'lpEvent', 'lpEditor', 'lpEditorView',
  function ($q, $log, $window, $rootScope,  $scope, lpEvent, lpEditor, lpEditorView) {

    var sessionId;
    var mudWindow = $window.opener;

    var editNav = [
      {id: 'build', label: 'Areas', icon: 'fa-share-alt'},
      {id: 'mud', label: 'Shared', icon: 'fa-shield'},
      {id: 'config', label: 'Admin', icon: 'fa-wrench'},
      {id: 'player', label: 'Players', icon: 'fa-user'}
    ];

    var activeNav = '';

    lpEvent.register('connect', function (data) {
      sessionId = data;
      $rootScope.appState = 'connected';
      $scope.welcome = 'Please log in.';
    });

    lpEvent.register('editor_login', function (data) {
      activeNav = '';
      $rootScope.appState = 'loggedIn';
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
        if ($scope.links.length) {
          $scope.changeNav($scope.links[0].id);
        }
      });

    });

    lpEvent.register('editor_logout', function () {
      sessionStorage.removeItem('editSessionId');
      $rootScope.appState = 'connected';
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
        activeNav = newNav;
        for (var i = 0; i < $scope.links.length; i++) {
          var link = $scope.links[i];
          if (link.id === activeNav) {
            link.active = 'active';
          } else {
            link.active = '';
          }
        }
        lpEditorView.prepareView(activeNav).then(function () {
          $rootScope.mainTemplate = 'editor/view/' + activeNav + '_view.html';
        })
      });
    };

    $scope.mudWindow = function(event) {
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