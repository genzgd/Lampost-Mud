lampost.service('lmRemote', ['$rootScope', '$http', '$timeout', 'lmLog', 'lmDialog',
    function($rootScope, $http, $timeout, lmLog, lmDialog) {

    var sessionId = 0;
    var connected = true;
    var windowClosed = false;
    var reconnectTemplate = '<div class="modal fade hide">' +
        '<div class="modal-header"><h3>Reconnecting To Server</h3></div>' +
        '<div class="modal-body"><p>Reconnecting in {{time}} seconds.</p></div>' +
        '<div class="modal-footer"><button class="btn btn-primary" ng-click="reconnectNow()">Reconnect Now</button></div>' +
        '</div>';

    function linkRequest(method, data) {
        if (data === undefined) {
            data = {};
        }
        data.session_id = sessionId;
        $http({method: 'POST', url: '/' + method, data:data}).
            success(serverResult).
            error(function(data, status, headers, config) {
                linkFailure(status);
            });
    }

    function link(data) {
        linkRequest("link");
    }

    function linkFailure(status) {
        if (connected) {
            connected = false;
            lmLog.log("Link stopped: " + status);
            $timeout(function() {
                if (!connected && !windowClosed) {
                    lmDialog.show({template: reconnectTemplate, controller: ReconnectController, noEscape:true});
                }
            }, 100);
        }
    }

    function onLinkStatus(event, status) {
        connected = true;
        if (status == "good") {
            link();
        } else if (status == "no_session") {
            $rootScope.$broadcast("logout", "invalid_session");
            sessionId = 0;
            linkRequest("connect");
        } else if (status == "no_login") {
            $rootScope.$broadcast("logout", "invalid_session");
        }
    }

    function serverResult(eventMap) {
        for (var key in eventMap) {
            $rootScope.$broadcast(key, eventMap[key]);
        }
    }

    function onConnect(event, data) {
        sessionId = data;
        link();
    }

    function onServerRequest(event, method, data) {
        linkRequest(method, data);
    }

    function reconnect() {
        if (sessionId == 0) {
            linkRequest("connect");
        } else {
            link();
        }
    }

    this.request = function(method, args) {
        linkRequest(method, args);
    }

    $rootScope.$on("connect", onConnect);
    $rootScope.$on("link_status", onLinkStatus);
    $rootScope.$on("server_request", onServerRequest);

    $(window).unload(function() {
        windowClosed = true;
    });

    function ReconnectController($scope, dialog, $timeout) {

        var tickPromise;
        var time = 16;

        $scope.$on("link_status", function(event) {
            $scope.dismiss();
            $timeout.cancel(tickPromise);
        });

        $scope.reconnectNow = function () {
            time = 1;
            $timeout.cancel(tickPromise);
            tickDown();
        }

        tickDown();
        function tickDown() {
            time--;
            if (time == 0) {
                time = 15;
                reconnect();
            }
            $scope.time = time;
            tickPromise = $timeout(tickDown, 1000);
        }
    }
}]);



