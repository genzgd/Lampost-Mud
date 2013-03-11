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
                if (registration.scope && !registration.scope.$$phase) {
                    registration.scope.$apply(registration.callback.apply(registration.scope, args));
                } else {
                    registration.callback.apply(this, args);
                }
            }
        }
    };

    this.dispatchMap = function(eventMap) {
        for (var key in eventMap) {
            self.dispatch(key, eventMap[key]);
        }
    }
}]);



angular.module('lampost_svc').service('lmRemote', ['$timeout', '$http', 'lmLog', 'lmBus', 'lmDialog',
    function($timeout, $http, lmLog, lmBus, lmDialog) {

    var sessionId = '';
    var playerId = '';
    var connected = true;
    var loadingTemplate;
    var waitCount = 0;
    var waitDialogId = null;
    var reconnectTemplate = '<div class="modal fade hide">' +
        '<div class="modal-header"><h3>Reconnecting To Server</h3></div>' +
        '<div class="modal-body"><p>Reconnecting in {{time}} seconds.</p></div>' +
        '<div class="modal-footer"><button class="btn btn-primary" ng-click="reconnectNow()">Reconnect Now</button></div>' +
        '</div>';

    function serverRequest(resource, data) {

        $.ajax({
            type: 'POST',
            dataType: 'json',
            url: '/' + resource,
            data: JSON.stringify(data || {}),
            headers: {'X-Lampost-Session': sessionId},
            success: lmBus.dispatchMap,
            error: function (jqXHR, status) {
                linkFailure(status)}
        });
    }

    function resourceRequest(resource, data, showWait) {
        if (showWait) {
            if (waitCount == 0) {
                waitDialogId = lmDialog.show({template:loadingTemplate, noEscape:true});
            }
            waitCount++;
        }

        function checkWait() {
            if (showWait) {
                waitCount--;
                if (waitCount == 0) {
                    lmDialog.close(waitDialogId);
                    waitDialogId = null;
                }
            }
        }

        return $http({method: 'POST', url: '/' + resource, data: data || {}, headers: {'X-Lampost-Session': sessionId}}).
            error(function(data, status) {
                checkWait();
                if (status == 403) {
                    lmDialog.showOk("Denied", "You do not have permission for that action");
                } else if (status != 409) {
                    lmDialog.showOk("Server Error: " + status, data);
                }
            }).then(function(result) {
                checkWait();
                return result.data;
            });

    }

    function link() {
        if (playerId) {
            localStorage.setItem('lm_timestamp_' + playerId, new Date().getTime().toString());
        }
        serverRequest("link");
    }

    function onWindowClosing() {
        if (playerId) {
            localStorage.setItem('lm_disconnect_player', playerId);
        }
    }

    function linkFailure(status) {
        if (!connected) {
            return;
        }
        connected = false;
        lmLog.log("Link stopped: " + status);
        setTimeout(function() {
            if (!connected && !window.windowClosing) {
                lmDialog.show({template: reconnectTemplate, controller: ReconnectController, noEscape:true});
            }
        }, 100);
    }

    function onLinkStatus(status) {
        connected = true;
        if (status == "good") {
            link();
        } else if (status == "session_not_found") {
            lmBus.dispatch("logout", "invalid_session");
            sessionId = '';
            serverRequest("connect");
        } else if (status == "no_login") {
            lmBus.dispatch("logout", "invalid_session");
        } else {
            lmDialog.showOk("Unknown Server Error", status);
        }
    }

    function onConnect(data) {
        sessionId = data;
        link();
    }

    function onLogin(data) {
        if (data.name) {
            playerId = data.name.toLowerCase();
            storePlayer();
        }
    }

    function storePlayer() {
        var activePlayers = activePlayerList();
        if (activePlayers.indexOf(playerId) == -1) {
            activePlayers.push(playerId);
            localStorage.setItem('lm_active_players', activePlayers.join('**'));
        }
        localStorage.setItem('lm_session_' + playerId, sessionId);
        localStorage.setItem('lm_timestamp_' + playerId, new Date().getTime().toString());
    }

    function activePlayerList() {
        var activePlayers = localStorage.getItem('lm_active_players');
        if (!activePlayers) {
            return [];
        }
        return activePlayers.split('**');
    }

    function deletePlayerData(activePlayers, deleteId) {
        var ix = activePlayers.indexOf(deleteId);
        if (ix == -1) {
            return;
        }
        activePlayers.splice(ix, 1);
        localStorage.setItem('lm_active_players', activePlayers.join('**'));
        localStorage.removeItem('lm_session_' + deleteId);
        localStorage.removeItem('lm_timestamp_' + deleteId);
    }

    function findSession() {
        var activePlayers = activePlayerList();
        // Anything older than a minute should not be reconnected, so we clear
        // the active players list in localStorage
        var staleTimestamp = new Date().getTime() - 60 * 1000;
        var activeTimestamp = new Date().getTime() - 10 * 1000;
        var lastPlayerId;
        var lastTimestamp = 0;
        angular.forEach(activePlayers, function(checkId) {
            var timestamp = Number(localStorage.getItem('lm_timestamp_' + checkId));
            if (timestamp < staleTimestamp) {
                deletePlayerData(activePlayers, checkId);
            } else if (timestamp > lastTimestamp && timestamp < activeTimestamp) {
                lastPlayerId = checkId;
                lastTimestamp = timestamp;
            }
        });

        var disconnectPlayer = localStorage.getItem('lm_disconnect_player');
        if (disconnectPlayer && activePlayers.indexOf(disconnectPlayer) > -1) {
            lastPlayerId = disconnectPlayer;
            localStorage.removeItem('lm_disconnect_player');
        }

        if (lastPlayerId) {
            var lastSession = localStorage.getItem('lm_session_' + lastPlayerId);
            if (lastSession) {
                playerId = lastPlayerId;
                sessionId = lastSession;
            }
        }
    }

    function onLogout() {
        deletePlayerData(activePlayerList(), playerId);
        playerId = '';

    }

    function reconnect() {
        if (!sessionId) {
            serverRequest("connect");
        } else {
            link();
        }
    }

    this.childSession = function(parentSession) {
        sessionId = parentSession;
    };

    this.request = function(resource, args, showWait) {
        return $http.get('dialogs/loading.html').then(function(template) {
            loadingTemplate = template.data;

        }).then(function() {
                return resourceRequest(resource, args, showWait)
            });
    };

    this.connect = function() {
        var data = {};
        if (!sessionId ) {
            findSession();
            if (sessionId) {
                data.player_id = playerId;
            }
        }
        serverRequest("connect", data);
    };

    lmBus.register("connect", onConnect);
    lmBus.register("link_status", onLinkStatus);
    lmBus.register("server_request", serverRequest);
    lmBus.register("login", onLogin);
    lmBus.register("logout", onLogout);
    lmBus.register("window_closing", onWindowClosing);


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


angular.module('lampost_svc').service('lmDialog', ['$rootScope', '$compile', '$controller', '$templateCache', '$timeout',  '$http',
    function($rootScope, $compile, $controller, $templateCache, $timeout, $http) {

    var dialogMap = {};
    var nextId = 0;
    var prevElement;
    var enabledElements;
    var enabledLinks;

    function showDialog(args) {
        var dialogId = "lmDialog_" + nextId++;
        if (args.templateUrl) {
            $http.get(args.templateUrl, {cache: $templateCache}).then(
                function(response) {
                    args.template = response.data;
                    showDialogTemplate(args, dialogId);
                });
        } else {
            showDialogTemplate(args, dialogId);
        }
        return dialogId;
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

    function showDialogTemplate(args, dialogId) {
        var element = angular.element(args.template);
        var dialog = {};
        var dialogScope = args.scope || $rootScope.$new(true);
        if ($.isEmptyObject(dialogMap)) {
            disableUI();
        }

        dialog.id = dialogId;
        dialog.element = element;
        dialog.scope = dialogScope;
        dialog.valid = true;
        dialogScope.dismiss = function() {
            element.modal("hide");
        };
        dialogMap[dialog.id] = dialog;

        var link = $compile(element.contents());
        if (args.controller) {
            var locals = args.locals || {};
            locals.$scope = dialogScope;
            locals.dialog = dialog;
            var controller = $controller(args.controller, locals);
            element.contents().data('$ngControllerController', controller);
        }

        link(dialogScope);
        function destroy() {
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
        }

        element.on(jQuery.support.transition && 'hidden' || 'hide', function() {
           destroy();
        });
        element.on(jQuery.support.transition && 'shown' || 'shown', function () {
            var focusElement = $('input:text:visible:first', element);
            if (!focusElement.length) {
                focusElement = $(".lmdialogfocus" + dialog.id + ":first");
            }
            focusElement.focus();
        });
        $timeout(function() {
            if (!dialog.valid) {
                destroy();
                return;
            }
            var modalOptions = {show: true, keyboard: !args.noEscape,
                backdrop: args.noBackdrop ? false : (args.noEscape ? "static" : true)};
            element.modal(modalOptions);
        });
    }

    function closeDialog(dialogId) {
        var dialog = dialogMap[dialogId];
        if (dialog) {
            dialog.valid = false;
            dialog.element.modal("hide");
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

    this.showPrompt = function(args) {
        var scope = $rootScope.$new();
        scope.submit = args.submit;
        scope.promptValue = "";
        scope.title = args.title;
        scope.prompt = args.prompt;
        scope.inputType = args.password ? "password" : "text";
        scope.doSubmit = function() {
            scope.submit.call(scope, scope.promptValue);
            scope.dismiss();
        };
        showDialog({templateUrl:'dialogs/prompt.html', scope:scope,
            noEscape:true});

    };

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

    this.urlVars = function() {
        var vars = {};
        var keyValuesPairs = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
        for(var i = 0; i < keyValuesPairs.length; i++)
        {
            var kvp = keyValuesPairs[i].split('=');
            vars[kvp[0]] = kvps[1];
        }
        return vars;
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





