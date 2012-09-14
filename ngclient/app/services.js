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

    this.register = function(event_type, callback, scope, priority) {
        if (!registry[event_type]) {
            registry[event_type] = [];
        }

        var registration = {event_type: event_type,  callback: callback,
            priority: priority ? priority : 0};
        registry[event_type].push(registration);
        registry[event_type].sort(function(a, b) {return a.priority - b.priority});
        if (scope) {
            registration.scope = scope;
            if (!scope['lm_regs']) {
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
            if (!registrations.length) {
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
            if (!listeners.length) {
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


angular.module('lampost_svc').service('lmCookies', [function() {

    var self = this;

    this.readCookie = function(cookieName) {
        var cookieString = document.cookie;
        if (!cookieString) {
            return '';
        }
        var cookies = cookieString.split('; ');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i];
            var ix = cookie.indexOf('=');
            if (cookie.substring(0, ix) == cookieName) {
                return cookie.substring(ix + 1);
            }
        }
        return '';
    };

    this.writeCookie = function(cookieName, value, expireSeconds) {
        var expireDate = new Date(new Date().getTime() + expireSeconds * 1000);
        document.cookie = cookieName + '=' + value.toString() + '; ' + expireDate.toGMTString();
    };

    this.deleteCookie = function(cookieName) {
        self.writeCookie(cookieName, 'delete', -1);
    };
}]);

angular.module('lampost_svc').service('lmRemote', ['$timeout', '$http', 'lmLog', 'lmBus', 'lmDialog', 'lmCookies',
    function($timeout, $http, lmLog, lmBus, lmDialog, lmCookies) {

    var sessionId = '';
    var playerId = '';
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

    function resourceRequest(resource, data, showWait) {
        data = data ? data : {};
        data.session_id = sessionId;
        if (showWait) {
            var dialogId = lmDialog.show({templateUrl:'dialogs/loading.html', noEscape:true});
        }
        return $http({method: 'POST', url: '/' + resource, data:data}).
            error(function(data, status) {
                dialogId && lmDialog.close(dialogId);
                if (status == 403) {
                    lmDialog.showOk("Denied", "You do not have permission for that action");
                } else if (status != 410) {
                    lmDialog.showOk("Server Error: " + status, data);
                }
            }).then(function(result) {
                dialogId && lmDialog.close(dialogId);
                var data = result.data;
                $timeout(function() {
                    serverResult(data)}, 0);
                return data.hasOwnProperty('response') ? data.response : data;
            });

    }

    function link() {
        if (playerId) {
            lmCookies.writeCookie('lampost_session', sessionId + '&&' + playerId, 60);
        }
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
        } else if (status == "no_session_id") {
            lmBus.dispatch("logout", "invalid_session");
            sessionId = 0;
            linkRequest("connect");
        } else if (status == "no_login") {
            lmBus.dispatch("logout", "invalid_session");
        } else {
            lmDialog.showOk("Unknown Server Error", status);
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

    function onLogin(data) {
        playerId = data.name.toLowerCase();
    }

    function onLogout() {
        playerId = '';
        lmCookies.deleteCookie('lampost_session');
    }

    function reconnect() {
        if (sessionId == 0) {
            linkRequest("connect");
        } else {
            link();
        }
    }

    this.request = function(resource, args, showWait) {
        return resourceRequest(resource, args, showWait);
    };

    this.connect = function() {
        var data = {};
        if (!sessionId ) {
            var cookie = lmCookies.readCookie('lampost_session').split('&&');
            if (cookie.length == 2) {
                sessionId = cookie[0];
                data.player_id = cookie[1];
            }
        }
        linkRequest("connect", data);
    };

    lmBus.register("connect", onConnect);
    lmBus.register("link_status", onLinkStatus);
    lmBus.register("server_request", onServerRequest);
    lmBus.register("login", onLogin);
    lmBus.register("logout", onLogout);


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
    ReconnectController.$inject = ['$scope', '$timeout'];

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
        return showDialog(args);
    };

    this.close = function(dialogId) {
        closeDialog(dialogId);
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

    this.showConfirm = function (title, msg, confirm) {
        var scope = $rootScope.$new();
        var yesButton = {label:"Yes", dismiss:true, class:"btn-danger", click:confirm};
        var noButton = {label:"No", dismiss:true, class:"btn-primary", default:true};
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

angular.module('lampost_svc').service('lmUtil', [function() {
    this.stringSort = function(array, field) {
        array.sort(function (a, b){
            var aField = a[field].toLowerCase();
            var bField = b[field].toLowerCase();
            return ((aField < bField) ? -1 : ((aField > bField) ? 1 : 0));
        });
    };

    this.intSort = function(array, field) {
        array.sort(function(a, b) {
            return a[field] - b[field];
        })
    };

    this.getScrollBarSizes = function() {
        var inner = $('<p></p>').css({
            'width':'100%',
            'height':'100%'
        });
        var outer = $('<div></div>').css({
            'position':'absolute',
            'width':'100px',
            'height':'100px',
            'top':'0',
            'left':'0',
            'visibility':'hidden',
            'overflow':'hidden'
        }).append(inner);
        $(document.body).append(outer);
        var w1 = inner.width(), h1 = inner.height();
        outer.css('overflow','scroll');
        var w2 = inner.width(), h2 = inner.height();
        if (w1 == w2 && outer[0].clientWidth) {
            w2 = outer[0].clientWidth;
        }
        if (h1 == h2 && outer[0].clientHeight) {
            h2 = outer[0].clientHeight;
        }
        outer.detach();
        return [(w1 - w2),(h1 - h2)];
    };
}]);





