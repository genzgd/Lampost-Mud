angular.module('lampost', ['lampost_dir', 'lampost_svc']);

angular.module('lampost').config(['$routeProvider', '$locationProvider', function (
    $routeProvider, $locationProvider) {
    $routeProvider.
        when('/game', {templateUrl:'view/main.html'}).
        when('/settings', {templateUrl:'view/settings.html'}).
        otherwise({redirectTo:'/game'});
    $locationProvider.hashPrefix('!');
}]);


// Using here so they get instantiated.
//noinspection JSUnusedLocalSymbols
angular.module('lampost').run(['$rootScope', 'lmBus', 'lmRemote', 'lmData', 'lmDialog',
    function ($rootScope, lmBus, lmRemote, lmData, lmDialog) {
        window.onbeforeunload = function () {
            if (lmData.editorWindow && !lmData.editorWindow.closed) {
                return "Closing or reloading this window will close the editor.  Continue?";
            }
            return null;
        };

        window.onunload = function() {
            if (lmData.editorWindow && !lmData.editorWindow.closed) {
                lmData.editorWindow.close();
            }
            lmBus.dispatch("window_closing");
            window.windowClosing = true;
        };

        $rootScope.siteTitle = lampost_config.title;
        $('title').text(lampost_config.title);

        lmRemote.connect();
        window.name = "lampost_main_" + new Date().getTime();

        lmBus.register("user_login", function() {
            if (lmData.playerIds.length == 0) {
                lmDialog.show({templateUrl:"dialogs/new_character.html", controller:"NewCharacterController"});
            } else {
                lmDialog.show({templateUrl:"dialogs/select_character.html", controller:"SelectCharacterController"});
            }
        });
    }]);


angular.module('lampost').controller('NavController', ['$rootScope', '$scope', '$location', 'lmBus', 'lmData', 'lmUtil', 'lmDialog',
    function ($rootScope, $scope, $location, lmBus, lmData, lmUtil, lmDialog) {

        $(window).on("resize", function () {
            $rootScope.$apply(resize);
        });

        function resize() {
            var navbar = jQuery('#lm-navbar');
            var navBarMargin = parseInt(navbar.css('marginBottom').replace('px', ''));
            var gameHeight = $(window).height() - navbar.height() - navBarMargin;
            $rootScope.gameHeight = {height:gameHeight.toString() + 'px'};
         }

        resize();

        function Link(name, label, icon, priority) {
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
            this.iconClass = function () {
                return this.icon + " icon-white" + (this.active() ? "" : " icon-gray");
            };
        }

        var baseLinks = [new Link("game", "Mud", "icon-leaf", 0)];
        var settingsLink = new Link("settings", "Settings", "icon-user", 50);

        function validatePath() {
            $scope.welcome = 'Please Log In';
            $scope.loggedIn = false;
            $scope.links = baseLinks.slice();
            for (var i = 0; i < $scope.links.length; i++) {
                if ($scope.links[i].active()) {
                    return;
                }
            }
            $location.path(baseLinks[0].name);
        }

        $scope.changeLocation = function (name) {
            $location.path(name);
        };

        $scope.logout = function() {
            lmBus.dispatch("server_request", "action", {action:"quit"});
        };

        validatePath();
        lmBus.register("login", function () {
            $scope.links.push(settingsLink);
            $scope.welcome = 'Welcome ' + lmData.playerName;
            $scope.loggedIn = true;
        }, $scope);

        lmBus.register("logout", function(reason) {
            if (reason == "other_location") {
                var playerName = lmData.playerName ? lmData.playerName : "Unknown";
                lmDialog.showOk("Logged Out", playerName + " logged in from another location.");
            }
            validatePath();
        }, $scope, -500);
    }]);


angular.module('lampost').controller('GameController', ['$scope', 'lmBus', 'lmData', 'lmDialog',
    function ($scope, lmBus, lmData, lmDialog) {

        $scope.toolbar = [];
        update();

        lmBus.register("login", function() {
            update();

        }, $scope);

        lmBus.register("logout", function (reason) {
            if (reason == "invalid_session") {
                lmDialog.removeAll();
                lmDialog.showOk("Session Lost", "Your session has been disconnected.");
            }
            if (lmData.editorWindow && !lmData.editorWindow.closed) {
                lmData.editorWindow.close();
                delete lmData.editorWindow;
            }
            update();
        }, $scope);

        function launchEditor(roomId) {
            if (lmData.editorWindow && lmData.editorWindow.closed) {
                delete lmData.editorWindow;
            }
            if (lmData.editorWindow) {
                lmData.editorWindow.focus();
            } else {
                if (roomId) {
                    localStorage.setItem("editor_room_id", roomId);
                }
                var editorWidth = 800;
                var editorHeight = 600;
                if (window.screen) {
                    editorWidth = window.screen.availWidth * .8;
                    editorHeight = window.screen.availHeight * .8;
                }

                lmData.editorWindow = open('editor.html', 'editor_' + lmData.playerId, 'width=' + editorWidth + ',height=' + editorHeight);
            }
        }

        function update() {
            $scope.toolbar = [];
            if (lmData.playerId) {
                $scope.actionPane = "action";
                if (lmData.editors.length) {
                    $scope.toolbar.push({label: 'Editor', click: launchEditor});
                    lmBus.register("start_room_edit", function(roomId) {
                        if (!lmData.editorWindow || lmData.editorWindow.closed) {
                            launchEditor(roomId);
                        } else {
                            lmData.editorWindow.editLampostRoom(roomId);
                            window.open("",lmData.editorWindow.name);
                        }
                    });
                }
            } else {
                $scope.actionPane = "login";
            }

    }

    }]);


angular.module('lampost').controller('LoginController', ['$scope',  'lmDialog', 'lmBus',
    function ($scope, lmDialog, lmBus) {

    $scope.loginError = false;
    $scope.siteDescription = lampost_config.description;
    $scope.login = function () {
        lmBus.dispatch("server_request", "login", {user_id:this.userId,
            password:this.password})
    };

    $scope.newAccountDialog = function() {
        lmDialog.show({templateUrl:"dialogs/new_account.html", controller:"NewAccountController"});
    };

    lmBus.register("login_failure", function() {
        $scope.loginError = true},
        $scope);

}]);

angular.module('lampost').controller('NewAccountController', ['$scope', '$timeout', 'lmRemote', 'lmDialog', 'lmData',
    function($scope, $timeout, lmRemote, lmDialog, lmData) {

    $scope.accountName = "";
    $scope.password = "";
    $scope.passwordCopy = "";
    $scope.email = "";
    $scope.dirty = function() {
        $scope.errorText = null;
    };

    $scope.createAccount = function() {
        if ($scope.password != $scope.passwordCopy) {
            $scope.errorText = "Passwords don't match.";
            return;
        }
        if ($scope.accountName.indexOf(" ") > -1) {
            $scope.errorText = "Spaces not permitted in account names";
            return;
        }
        lmRemote.request("settings/create_account", {account_name:$scope.accountName,
              password:$scope.password,  email:$scope.email}).then(function(response) {
                lmData.userId = response.user_id;
                $scope.dismiss();
                $timeout(function() {
                    lmDialog.show({templateUrl:"dialogs/new_character.html", controller:"NewCharacterController"});
                })
            }, function(error) {
                if (error.status == 409) {
                    $scope.errorText = error.data;
                }
            });
    }
}]);

angular.module('lampost').controller('ActionController', ['$scope', 'lmBus', 'lmData', function ($scope, lmBus, lmData) {
    var curAction;
    $scope.update = 0;
    $scope.action = "";
    $scope.display = lmData.display;
    lmBus.register("display_update", function () {
        $scope.display = lmData.display;
        $scope.update++;
    }, $scope);
    $scope.sendAction = function () {
        if ($scope.action) {
            lmBus.dispatch("server_request", "action", {action:$scope.action});
            lmData.history.push($scope.action);
            lmData.historyIx = lmData.history.length;
            $scope.action = "";
        }
    };
    $scope.historyUp = function () {
        if (lmData.historyIx > 0) {
            if (lmData.historyIx == lmData.history.length) {
                curAction = this.action;
            }
            lmData.historyIx--;
            this.action = lmData.history[lmData.historyIx];
        }
    };
    $scope.historyDown = function () {
        if (lmData.historyIx < lmData.history.length) {
            lmData.historyIx++;
            if (lmData.historyIx == lmData.history.length) {
                this.action = curAction;
            } else {
                this.action = lmData.history[lmData.historyIx];
            }
        }
    }
}]);
