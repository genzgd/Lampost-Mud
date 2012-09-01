angular.module('lampost_svc', []);

angular.module('lampost_svc').service('lmLog', [function() {
    this.log  = function(msg) {
        if (window.console) {
            window.console.log(msg);
        }
    }
}]);

angular.module('lampost_svc').service('lmBus', ['lmLog', function(lmLog) {
    var self = this;
    var registry = {};

    this.register = function(event_type, callback, scope) {
        if (!registry[event_type]) {
            registry[event_type] = [];
        }

        var registration = {event_type: event_type,  callback: callback};
        registry[event_type].push(registration);
        if (scope) {
            registration.scope = scope;
            if (!scope['lm_regs'])
            {
                scope.lm_regs = [];
                scope.$on('$destroy', function(event) {
                    var copy = event.currentScope.lm_regs.slice();
                    for (var i = 0; i < copy.length; i++) {
                        self.unregister(copy[i]);
                    }
                });
            }
            scope.lm_regs.push(registration);
        }
        return registration;
    };

    this.unregister = function (registration) {
        var registrations = registry[registration.event_type];
        if (!registrations) {
            lmLog.log("Unregistering event for " + event_type + " that was never registered");
            return;
        }
        var found = false;
        var i;
        for (i = 0; i < registrations.length; i++) {
            if (registrations[i] == registration) {
                registrations.splice(i, 1);
                found = true;
                break;
            }
            if (!registrations) {
                delete registry[registration.event_type];
            }
        }
        if (!found) {
            lmLog.log("Failed to unregister event " + registration.event_type + " " + registration.callback);
            return;
        }
        if (registration.scope) {
            var listeners = registration.scope.lm_regs;
            for (i = 0; i < listeners.length; i++) {
                if (listeners[i] == registration) {
                    listeners.splice(i, 1);
                    break;
                }
            }
            if (!listeners) {
                delete registration.scope.lm_regs;
            }
        }
    };

    this.dispatch = function() {
        var event_type = arguments[0];
        var i;
        var args = [];
        for (i = 1; i < arguments.length; i++) {
            args.push(arguments[i]);
        }
        var registrations = registry[event_type];
        if (registrations) {
            for (i = 0; i < registrations.length; i++) {
                var registration = registrations[i];
                if (registration.scope) {
                    registration.scope.$apply(registration.callback.apply(registration.scope, args));
                } else {
                    registration.callback.apply(this, args);
                }
            }
        }
    };
}]);


angular.module('lampost_svc').service('lmRemote', ['$timeout', '$http', 'lmLog', 'lmBus', 'lmDialog',
    function($timeout, $http, lmLog, lmBus, lmDialog) {

        var sessionId = 0;
        var connected = true;
        var reconnectTemplate = '<div class="modal fade hide">' +
            '<div class="modal-header"><h3>Reconnecting To Server</h3></div>' +
            '<div class="modal-body"><p>Reconnecting in {{time}} seconds.</p></div>' +
            '<div class="modal-footer"><button class="btn btn-primary" ng-click="reconnectNow()">Reconnect Now</button></div>' +
            '</div>';

        function linkRequest(resource, data) {
            data = data ? data : {};
            data.session_id = sessionId;
            $.ajax({
                type: 'POST',
                dataType: 'json',
                url: '/' + resource,
                data: JSON.stringify(data),
                success: serverResult,
                error: function (jqXHR, status) {
                    linkFailure(status)}
            });
        }

        function resourceRequest(resource, data) {
            data = data ? data : {};
            data.session_id = sessionId;
            return $http({method: 'POST', url: '/' + resource, data:data}).
                error(function(data, status) {
                    linkFailure(status);
                }).then(function(result) {
                    var data = result.data;
                    serverResult(data);
                    return data.hasOwnProperty('response') ? data.response : data;
                });

        }

        function link() {
            linkRequest("link");
        }

        function linkFailure(status) {
            if (connected) {
                connected = false;
                lmLog.log("Link stopped: " + status);
                setTimeout(function() {
                    if (!connected && !window.windowClosing) {
                        lmDialog.show({template: reconnectTemplate, controller: ReconnectController, noEscape:true});
                    }
                }, 100);
            }
        }

        function onLinkStatus(status) {
            connected = true;
            if (status == "good") {
                link();
            } else if (status == "no_session") {
                lmBus.dispatch("logout", "invalid_session");
                sessionId = 0;
                linkRequest("connect");
            } else if (status == "no_login") {
                lmBus.dispatch("logout", "invalid_session");
            }
        }

        function serverResult(eventMap) {
            for (var key in eventMap) {
                lmBus.dispatch(key, eventMap[key]);
            }
        }

        function onConnect(data) {
            sessionId = data;
            link();
        }

        function onServerRequest(resource, data) {
            linkRequest(resource, data);
        }

        function reconnect() {
            if (sessionId == 0) {
                linkRequest("connect");
            } else {
                link();
            }
        }

        this.request = function(resource, args) {
            return resourceRequest(resource, args);
        };

        lmBus.register("connect", onConnect);
        lmBus.register("link_status", onLinkStatus);
        lmBus.register("server_request", onServerRequest);


        function ReconnectController($scope, $timeout) {
            var tickPromise;
            var time = 16;
            lmBus.register("link_status", function() {
                $scope.dismiss();
                $timeout.cancel(tickPromise);
            }, $scope);

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
        ReconnectController.$inject = ['$scope, $timeout'];

    }]);


angular.module('lampost_svc').service('lmDialog', ['$rootScope', '$compile', '$controller', '$templateCache',
    '$timeout',  '$http', 'lmBus', function($rootScope, $compile, $controller, $templateCache,
                                   $timeout, $http, lmBus) {
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

        function onShowDialog(args) {
            if (args.dialog_type == 1) {
                $rootScope.$apply(
                    self.showOk(args.dialog_title, args.dialog_msg));
            } else if (args.dialog_type == 0) {
                $rootScope.$apply(
                    self.showConfirm(args.dialog_title, args.dialog_msg));
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
                lmBus.dispatch("server_request", "dialog", {response:"yes"});
            }};
            var noButton = {label:"No", dismiss:true, click:function () {
                lmBus.dispatch("server_request", "dialog", {response:"no"});
            },
                class:"btn-primary", default:true};
            scope.buttons = [yesButton, noButton];
            scope.title = title;
            scope.body = msg;

            showDialog({templateUrl:'dialogs/alert.html', scope:scope,
                controller:AlertController, noEscape:true});
        };

        lmBus.register("show_dialog", onShowDialog);

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





