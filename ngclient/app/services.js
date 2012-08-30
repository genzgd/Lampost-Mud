angular.module('lampost_svc', []);

angular.module('lampost_svc').service('lmLog', [function() {
    this.log  = function(msg) {
        if (window.console) {
            window.console.log(msg);
        }
    }
}]);

angular.module('lampost_svc').service('lmRemote', ['$rootScope', '$http', '$timeout', 'lmLog', 'lmDialog',
    function($rootScope, $http, $timeout, lmLog, lmDialog) {

        var sessionId = 0;
        var connected = true;
        var reconnectTemplate = '<div class="modal fade hide">' +
            '<div class="modal-header"><h3>Reconnecting To Server</h3></div>' +
            '<div class="modal-body"><p>Reconnecting in {{time}} seconds.</p></div>' +
            '<div class="modal-footer"><button class="btn btn-primary" ng-click="reconnectNow()">Reconnect Now</button></div>' +
            '</div>';

        function linkRequest(method, data) {
            data = data ? data : {};
            data.session_id = sessionId;
            $http({method: 'POST', url: '/' + method, data:data}).
                success(serverResult).
                error(function (data, status) {
                    linkFailure(status);
                });
        }

        function link() {
            linkRequest("link");
        }

        function linkFailure(status) {
            if (connected) {
                connected = false;
                lmLog.log("Link stopped: " + status);
                $timeout(function() {
                    if (!connected && !$rootScope.windowClosing) {
                        lmDialog.show({template: reconnectTemplate, controller: ReconnectController, noEscape:true});
                    }
                }, 100);
            }
        }

        //noinspection JSUnusedLocalSymbols
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

        //noinspection JSUnusedLocalSymbols
        function onConnect(event, data) {
            sessionId = data;
            link();
        }

        //noinspection JSUnusedLocalSymbols
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

        this.request = function (method, args) {
            linkRequest(method, args);
        };

        $rootScope.$on("connect", onConnect);
        $rootScope.$on("link_status", onLinkStatus);
        $rootScope.$on("server_request", onServerRequest);


        function ReconnectController($scope, $timeout) {

            var tickPromise;
            var time = 16;

            //noinspection JSUnusedLocalSymbols
            $scope.$on("link_status", function(event) {
                $scope.dismiss();
                $timeout.cancel(tickPromise);
            });

            $scope.reconnectNow = function () {
                time = 1;
                $timeout.cancel(tickPromise);
                tickDown();
            };

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


angular.module('lampost_svc').service('lmDialog', ['$rootScope', '$compile', '$controller', '$templateCache',
    '$timeout',  '$http', function($rootScope, $compile, $controller, $templateCache,
                                   $timeout, $http) {
        var dialogMap = {};
        var nextId = 0;
        var self = this;
        var prevElement;
        var enabledElements;
        var enabledLinks;

        function showDialog(args) {
            if (args.templateUrl) {
                $http.get(args.templateUrl, {cache: $templateCache}).then(
                    function(response) {
                        args.template = response.data;
                        showDialogTemplate(args);
                    });
            } else {
                showDialogTemplate(args);
            }
        }

        function disableUI() {
            prevElement = $(document.activeElement);
            enabledElements = $('button:enabled, selector:enabled, input:enabled, textarea:enabled');
            enabledLinks = $('a[href]');
            enabledElements.attr('disabled', true);
            enabledLinks.each(function() {
                $(this).attr("data-oldhref", $(this).attr("href"));
                $(this).removeAttr("href");
            })
        }

        function enableUI() {
            enabledElements.removeAttr('disabled');
            enabledLinks.each(function() {
                $(this).attr("href", $(this).attr("data-oldhref"));
                $(this).removeAttr("data-oldhref");
            });
            $timeout(function () {
                if (prevElement.closest('html').length) {
                    prevElement.focus();
                } else {
                    $rootScope.$broadcast("refocus");
                }
            }, 0);
        }

        function showDialogTemplate(args) {
            var element = angular.element(args.template);
            var dialog = {};
            var dialogScope = args.scope || $rootScope.$new(true);
            if ($.isEmptyObject(dialogMap)) {
                disableUI();
            }

            dialog.id = "lmDialog_" + nextId++;
            dialog.element = element;
            dialog.scope = dialogScope;
            dialogScope.dismiss = function() {
                element.modal("hide");
            };

            var link = $compile(element.contents());
            if (args.controller) {
                var locals = args.locals || {};
                locals.$scope = dialogScope;
                locals.dialog = dialog;
                var controller = $controller(args.controller, locals);
                element.contents().data('$ngControllerController', controller);
            }
            dialogMap[dialog.id] = dialog;
            link(dialogScope);
            element.on(jQuery.support.transition && 'hidden' || 'hide', function() {
                if (!dialogMap[dialog.id]) {
                    return;
                }
                dialog.scope.finalize && dialog.scope.finalize();
                delete dialogMap[dialog.id];
                dialog.element.remove();
                if ($.isEmptyObject(dialogMap)) {
                    enableUI();
                }
                $timeout(function() {
                    dialog.scope.$destroy();
                    dialog = null;
                });
            });
            element.on(jQuery.support.transition && 'shown' || 'shown', function () {
                var focusElement = $('input:text:visible:first', element);
                if (!focusElement.length) {
                    focusElement = $(".lmdialogfocus" + dialog.id + ":first");
                }
                focusElement.focus();
            });
            $timeout(function() {
                var modalOptions = {show: true, keyboard: !args.noEscape,
                    backdrop: args.noBackdrop ? false : (args.noEscape ? "static" : true)};
                element.modal(modalOptions);
            });
            return dialog.id;
        }

        function closeDialog(dialogId) {
            var dialog = dialogMap[dialogId];
            if (dialog) {
                dialog.element.modal("hide");
            }
        }

        //noinspection JSUnusedLocalSymbols
        function onShowDialog(event, args) {
            if (args.dialog_type == 1) {
                self.showOk(args.dialog_title, args.dialog_msg);
            } else if (args.dialog_type == 0) {
                self.showConfirm(args.dialog_title, args.dialog_msg);
            }
        }

        this.show = function (args) {
            showDialog(args);
        };

        this.removeAll = function () {
            for (var dialogId in dialogMap) {
                closeDialog(dialogId);
            }
        };

        this.showOk = function (title, msg) {
            var scope = $rootScope.$new();
            scope.buttons = [
                {label:'OK', default:true, dismiss:true, class:"btn-primary"}
            ];
            scope.title = title;
            scope.body = msg;
            showDialog({templateUrl:'dialogs/alert.html', scope:scope,
                controller:AlertController});
        };

        this.showConfirm = function (title, msg) {
            var scope = $rootScope.$new();
            var yesButton = {label:"Yes", dismiss:true, click:function () {
                $rootScope.$broadcast("server_request", "dialog", {response:"yes"});
            }};
            var noButton = {label:"No", dismiss:true, click:function () {
                $rootScope.$broadcast("server_request", "dialog", {response:"no"});
            },
                class:"btn-primary", default:true};
            scope.buttons = [yesButton, noButton];
            scope.title = title;
            scope.body = msg;

            showDialog({templateUrl:'dialogs/alert.html', scope:scope,
                controller:AlertController, noEscape:true});
        };

        $rootScope.$on("show_dialog", onShowDialog);

        function AlertController($scope, dialog) {
            $scope.click = function (button) {
                button.click && button.click();
                button.dismiss && $scope.dismiss();
            };

            for (var i = 0; i < $scope.buttons.length; i++) {
                var button = $scope.buttons[i];
                if (button.default) {
                    var focusClass = " lmdialogfocus" + dialog.id;
                    button.class = button.class && button.class + focusClass || focusClass;
                }
            }
        }

    }]);





