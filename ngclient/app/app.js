angular.module('lampost', ['lampost_dir', 'lampost_svc', 'lampost_edit']);

angular.module('lampost').config(['$routeProvider', '$locationProvider', function (
    $routeProvider, $locationProvider) {
    $routeProvider.
        when('/game', {templateUrl:'view/main.html', controller:'GameController'}).
        when('/editor', {templateUrl:'view/editor.html'}).
        when('/settings', {templateUrl:'view/settings.html'}).
        otherwise({redirectTo:'/game'});
    $locationProvider.hashPrefix('!');
}]);


// Using here so they get instantiated.
//noinspection JSUnusedLocalSymbols
angular.module('lampost').run(['$rootScope', 'lmBus', 'lmRemote', 'lmData', 'lmDialog', 'lmEditor',
    function ($rootScope, lmBus, lmRemote, lmData, lmDialog, lmEditor) {
        window.onbeforeunload = function () {
            window.windowClosing = true;
        };

        $rootScope.siteTitle = lampost_config.title;
        $('title').text(lampost_config.title);

        lmRemote.connect();
    }]);


angular.module('lampost').controller('NavController', ['$rootScope', '$scope', '$location', 'lmBus', 'lmData',
    function ($rootScope, $scope, $location, lmBus, lmData) {

        $(window).on("resize", function () {
            $rootScope.$apply(resize);
        });

        function resize() {
            var newHeight = $(window).height() - $('#lm-navbar').height() - 18;
            $rootScope.gameHeight = {height:newHeight.toString() + "px"};
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

        var editorLink = new Link("editor", "Editor", "icon-wrench", 100);

        function validatePath() {
            $scope.welcome = 'Please Log In';
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

        validatePath();
        lmBus.register("login", function () {
            if (lmData.player.editors.length) {
                $scope.links.push(editorLink);
            }
            $scope.links.push(settingsLink);
            $scope.welcome = 'Welcome ' + lmData.player.name;
        }, $scope);

        lmBus.register("logout", validatePath, $scope);
    }]);


angular.module('lampost').controller('GameController', ['$scope', 'lmBus', 'lmData', 'lmDialog',
    function ($scope, lmBus, lmData, lmDialog) {

        update();

        lmBus.register("login", update, $scope);
        lmBus.register("logout", function (reason) {
            if (reason == "invalid_session") {
                lmDialog.showOk("Session Lost", "Your session has been disconnected.");
            }
            update();
        }, $scope);

        function update() {
            $scope.actionPane = lmData.player ? "action" : "login";
        }
    }]);


angular.module('lampost').controller('LoginController', ['$scope', 'lmRemote', function ($scope, lmRemote) {
    $scope.loginError = false;
    $scope.siteDescription = lampost_config.description;
    $scope.login = function () {
        lmRemote.request("login", {user_id:this.userId,
            password:this.password}).then(loginError);

    };

    function loginError(response) {
        if (response == "not_found") {
            $scope.loginError = true;
        }
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
        if (this.action) {
            lmBus.dispatch("server_request", "action", {action:this.action});
            lmData.history.push(this.action);
            lmData.historyIx = lmData.history.length;
            this.action = "";
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
