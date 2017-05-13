angular.module('lampost_mud', ['lampost_dir', 'lampost_dlg', 'lampost_util', 'lampost_remote', 'ngRoute', 'ngSanitize']);

angular.module('lampost_mud').config(['$routeProvider', '$locationProvider', function (
  $routeProvider, $locationProvider) {
  $routeProvider.
    when('/game', {templateUrl: 'mud/view/main.html'}).
    when('/settings', {templateUrl: 'mud/view/settings.html'}).
    otherwise({redirectTo: '/game'});
  $locationProvider.hashPrefix('!');
}]);


angular.module('lampost_mud').run(
  ['$rootScope', '$timeout', '$window', '$injector', 'lpEvent', 'lpRemote', 'lpStorage',
  function ($rootScope, $timeout, $window, $injector, lpEvent, lpRemote, lpStorage) {

    $window.name = "lpMudWindow" + new Date().getTime();

    $window.onbeforeunload = function () {
      window.windowClosing = true;
      lpEvent.dispatch("window_closing");
    };

    $rootScope.siteTitle = lampost_config.title;
    jQuery('title').text(lampost_config.title);

    var lastSession = lpStorage.lastSession();
    lpRemote.connect('app_connect', lastSession && {player_id: lastSession.playerId, session_id: lastSession.sessionId});
    $injector.get('lpData');
    $injector.get('lpDialog');
    $injector.get('lmComm');
  }]);

angular.module('lampost_mud').service('lmApp', ['$timeout', '$interval', 'lpEvent', 'lpData', 'lpDialog',
  function ($timeout, $interval, lpEvent, lpData, lpDialog) {

    lpEvent.register("user_login", function () {
      if (lpData.playerIds.length == 0) {
        lpDialog.show({templateUrl: 'mud/dialogs/new_character.html', controller: 'NewCharacterCtrl'});
      } else {
        lpDialog.show({templateUrl: 'mud/dialogs/select_character.html', controller: "SelectCharacterCtrl"});
      }
    });

    lpEvent.register("password_reset", function () {
      lpDialog.show({templateUrl: 'mud/dialogs/password_reset.html', controller: 'PasswordResetCtrl', noEscape: true});
    });

    lpEvent.register('server_error', function() {
      lpEvent.dispatch("display", {lines: [{text: "You hear a crash.  Something unfortunate seems to have happened in the back room.", display: 'combat'},
              {text:"Don't mind the smoke, I'm sure someone is investigating.", display: 'combat'}
             ]});
    });

    lpEvent.register("invalid_session", function() {
      lpDialog.removeAll();
      if (lpData.playerId) {
        lpDialog.showOk("Session Lost", "Your session has been disconnected.");
        lpEvent.dispatch("logout");
      }
    });

    lpEvent.register("other_location", function() {
      var playerName = lpData.playerName ? lpData.playerName : "Unknown";
      lpDialog.showOk("Logged Out", playerName + " logged in from another location.")
      lpEvent.dispatch("logout");
    });

    $interval(lpEvent.dispatch, 60 * 1000, 0, false, 'heartbeat');

  }]);


angular.module('lampost_mud').controller('NavCtrl',
  ['$rootScope', '$scope', '$location', '$log', 'lpEvent', 'lpRemote', 'lpData', 'lpUtil', 'lpDialog',
  function ($rootScope, $scope, $location, $log, lpEvent, lpRemote, lpData, lpUtil, lpDialog) {

    var baseLinks = [new Link("game", "Mud", "fa fa-tree", 0)];
    var settingsLink = new Link("settings", "Settings", "fa fa-sliders", 50);
    var editorLink = new Link('editor', 'Editor', 'fa fa-pencil', 100);
    var editorWindow = window.opener;

    $(window).on("resize", function () {
      $rootScope.$apply(resize);
    });

    function resize() {
      var navbar = jQuery('#lm-navbar');
      var navBarMargin = parseInt(navbar.css('marginBottom').replace('px', ''));
      var gameHeight = $(window).height() - navbar.height() - navBarMargin;
      $rootScope.gameHeight = {height: gameHeight.toString() + 'px'};
    }

    resize();

    function Link(name, label, icon, priority, href) {
      this.name = name;
      this.label = label;
      this.icon = icon;
      this.priority = priority;
      this.active = function () {
        return $location.path() == '/' + this.name;
      };
      this.class = function () {
        return this.active() ? "active" : "";
      };

    }

    function validatePath() {
      $scope.links = baseLinks.slice();
      if ($scope.loggedIn) {
        $scope.welcome = 'Welcome ' + lpData.playerName;
        $scope.links.push(settingsLink);
        if (lpData.immLevel) {
          $scope.links.push(editorLink);
        }
      } else {
        $scope.welcome = 'Please Log In';
        $location.path(baseLinks[0].name);
      }
    }

    $scope.changeLocation = function (link, event) {
      if (link === editorLink) {
        sessionStorage.removeItem('editSessionId');
        try {
          if (editorWindow && !editorWindow.closed) {
            editorWindow = window.open("", editorWindow.name);
          }
        }
        catch (e) {
          $log.log("Unable to reference editor window");
          editorWindow = null;
        }
        if (!editorWindow || editorWindow.closed) {
          editorWindow = window.open('editor.html', '_blank');
        }
        if (editorWindow) {
          try {
            editorWindow.focus();
          } catch (e) {
            $log.log("Error opening other window", e);
          }
        }
      } else {
        $location.path(link.name);
      }
    };

    $scope.logout = function () {
      lpRemote.send("action", {action: "quit"});
    };

    lpEvent.register("login", function () {
      $scope.loggedIn = true;
      validatePath();
    }, $scope);

    lpEvent.register('player_update', validatePath);

    lpEvent.register("logout", function () {
      $scope.loggedIn = false;
      validatePath();
    }, $scope, -500);

    validatePath();
  }]);


angular.module('lampost_mud').controller('GameCtrl', ['$scope', 'lmApp', 'lpEvent', 'lpData', 'lpDialog',
  function ($scope, lmApp, lpEvent, lpData, lpDialog) {

    update();

    lpEvent.register("login", function () {
      update();
    }, $scope);

    lpEvent.register("logout", update, $scope);



    function update() {
      if (lpData.playerId) {
        $scope.actionPane = "action";
      } else {
        $scope.actionPane = "login";
      }    }

  }]);


angular.module('lampost_mud').controller('LoginCtrl', ['$scope', 'lpDialog', 'lpEvent', 'lpRemote',
  function ($scope, lpDialog, lpEvent, lpRemote) {

    $scope.loginError = false;
    $scope.siteDescription = lampost_config.description;
    $scope.login = function () {
      lpRemote.send("player_login", {user_name: this.userId, password: this.password})
    };

    $scope.newAccountDialog = function () {
      lpDialog.show({templateUrl: "mud/dialogs/new_account.html", controller: "NewAccountCtrl"});
    };

    $scope.forgotName = function () {
      lpDialog.show({templateUrl: "mud/dialogs/forgot_name.html", controller: "ForgotNameCtrl"})
    };

    $scope.forgotPassword = function () {
      lpDialog.show({templateUrl: "mud/dialogs/forgot_password.html", controller: "ForgotPasswordCtrl"})
    };

    lpEvent.register("login_failure", function (loginFailure) {
      $scope.loginError = loginFailure
    }, $scope);

  }]);

angular.module('lampost_mud').controller('NewAccountCtrl', ['$scope', '$timeout', 'lpRemote', 'lpDialog', 'lpData',
  function ($scope, $timeout, lpRemote, lpDialog, lpData) {

    $scope.accountName = "";
    $scope.password = "";
    $scope.passwordCopy = "";
    $scope.email = "";
    $scope.dirty = function () {
      $scope.errorText = null;
    };

    $scope.createAccount = function () {
      if ($scope.password != $scope.passwordCopy) {
        $scope.errorText = "Passwords don't match.";
        return;
      }
      if ($scope.accountName.indexOf(" ") > -1) {
        $scope.errorText = "Spaces not permitted in account names";
        return;
      }
      lpRemote.request("settings/create_account", {account_name: $scope.accountName,
        password: $scope.password, email: $scope.email}).then(function (response) {
          lpData.userId = response.user_id;
          $scope.dismiss();
          $timeout(function () {
            lpDialog.show({templateUrl: "mud/dialogs/new_character.html", controller: "NewCharacterCtrl", noEscape: true});
          })
        }, function (error) {
          $scope.errorText = "Account name " + error.text + " is in use.";
        });
    }
  }]);

angular.module('lampost_mud').controller('ForgotNameCtrl', ['$scope', 'lpRemote', 'lpDialog', function ($scope, lpRemote, lpDialog) {
  $scope.showError = false;
  $scope.submitRequest = function () {
    lpRemote.request("settings/send_name", {info: $scope.info}).then(function () {
      $scope.dismiss();
      lpDialog.showOk("Email Sent", "An email has been sent to " + $scope.info + " with account information");
    }, function () {
      $scope.showError = true;
    })
  };
}]);

angular.module('lampost_mud').controller('ForgotPasswordCtrl', ['$scope', 'lpRemote', 'lpDialog', function ($scope, lpRemote, lpDialog) {
  $scope.submitRequest = function () {
    lpRemote.request("settings/temp_password", {info: $scope.info}).then(function () {
      $scope.dismiss();
      lpDialog.showOk("Password Sent", "An email has been set to the address on file for " + $scope.info +
        " with a temporary password.");
    }, function (error) {
      $scope.showError = error.text
    })
  };
}]);

angular.module('lampost_mud').controller('PasswordResetCtrl', ['$scope', 'lpRemote', function ($scope, lpRemote) {
  $scope.errorText = null;
  $scope.password = '';
  $scope.passwordCopy = '';
  $scope.submitRequest = function () {
    if ($scope.password != $scope.passwordCopy) {
      $scope.errorText = "Passwords do not match";
    } else {
      $scope.dismiss();
      lpRemote.request('settings/set_password', {password: $scope.password});
    }
  }
}]);

angular.module('lampost_mud').controller('ActionCtrl', ['$scope', '$timeout', 'lpEvent', 'lpRemote', 'lpData',
  function ($scope, $timeout, lpEvent, lpRemote, lpData) {
  var curAction;

  $scope.update = 0;
  $scope.display = lpData.display;

  function updateAction(action) {
    $scope.action = action;
    $timeout(function () {
      lpEvent.dispatch('user_activity')
    }, 150);
  }

  lpEvent.register("display_update", function () {
    $scope.update++;
  }, $scope);

  $scope.actionFocus = function() {
    lpEvent.dispatch('user_activity');
  };

  $scope.sendAction = function () {
    if ($scope.action) {
      lpRemote.send("action", {action: $scope.action});
      lpData.history.push($scope.action);
      lpData.historyIx = lpData.history.length;
      updateAction('');
    }
  };

  $scope.historyUp = function () {
    if (lpData.historyIx > 0) {
      if (lpData.historyIx == lpData.history.length) {
        curAction = this.action;
      }
      lpData.historyIx--;
      updateAction(lpData.history[lpData.historyIx]);
    }
  };

  $scope.historyDown = function () {
    if (lpData.historyIx < lpData.history.length) {
      lpData.historyIx++;
      if (lpData.historyIx == lpData.history.length) {
        updateAction(curAction);
      } else {
        updateAction(lpData.history[lpData.historyIx]);
      }
    }
  }
}]);
