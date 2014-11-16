angular.module('lampost_svc', []);

angular.module('lampost_svc').service('lmLog', [function () {
  this.log = function (msg) {
    if (window.console) {
      window.console.log(msg);
    }
  }
}]);

angular.module('lampost_svc').service('lmBus', ['lmLog', function (lmLog) {
  var self = this;
  var registry = {};

  function applyCallback(callback, args, scope) {
    if (!scope || (scope.$root.$$phase === '$apply' || scope.$root.$$phase === '$digest')) {
      callback.apply(this, args);
    } else {
      scope.$apply(function () {
        callback.apply(scope, args)
      });
    }
  }

  function dispatchMap(eventMap) {
    for (var key in eventMap) {
      self.dispatch(key, eventMap[key]);
    }
  }

  this.register = function (event_type, callback, scope, priority) {
    if (!registry[event_type]) {
      registry[event_type] = [];
    }

    var registration = {event_type: event_type, callback: callback,priority: priority || 0};
    registry[event_type].push(registration);
    registry[event_type].sort(function (a, b) {
      return a.priority - b.priority
    });
    if (scope) {
      registration.scope = scope;
      if (!scope['lm_regs']) {
        scope.lm_regs = [];
        scope.$on('$destroy', function (event) {
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
      if (registrations[i] === registration) {
        registrations.splice(i, 1);
        found = true;
        break;
      }

    }

    if (!registrations.length) {
      delete registry[registration.event_type];
    }

    if (!found) {
      lmLog.log("Failed to unregister event " + registration.event_type + " " + registration.callback);
      return;
    }
    if (registration.scope) {
      var listeners = registration.scope.lm_regs;
      for (i = 0; i < listeners.length; i++) {
        if (listeners[i] === registration) {
          listeners.splice(i, 1);
          break;
        }
      }
      if (!listeners.length) {
        delete registration.scope.lm_regs;
      }
    }
  };

  this.dispatch = function () {
    var event_type = arguments[0];
    var i;
    var args = [];
    for (i = 1; i < arguments.length; i++) {
      args.push(arguments[i]);
    }
    var registrations = registry[event_type];
    if (registrations) {
      for (i = 0; i < registrations.length; i++) {
        applyCallback(registrations[i].callback, args, registrations[i].scope)
      }
    }
  };

  this.dispatchMap = function (eventMap) {
    if (Array.isArray(eventMap)) {
      angular.forEach(eventMap, dispatchMap);
    } else {
      dispatchMap(eventMap);
    }
  }
}]);


angular.module('lampost_svc').service('lmRemote', ['$timeout', '$http', '$q', 'lmLog', 'lmBus', 'lmDialog',
  function ($timeout, $http, $q, lmLog, lmBus, lmDialog) {

    var sessionId = '';
    var playerId = '';
    var connected = true;
    var loadingTemplate;
    var waitCount = 0;
    var waitDialogId = null;
    var services = {};
    var resourceRoot = '/';
    var reconnectTemplate = '<div class="modal fade hide">' +
      '<div class="modal-header"><h3>Reconnecting To Server</h3></div>' +
      '<div class="modal-body"><p>Reconnecting in {{time}} seconds.</p></div>' +
      '<div class="modal-footer"><button class="btn btn-primary" ng-click="reconnectNow()">Reconnect Now</button></div>' +
      '</div>';

    function serverRequest(resource, data) {
      return $http({method: 'POST',
        url: resourceRoot + resource,
        data: data || {},
        headers: {'X-Lampost-Session': sessionId}}).success(lmBus.dispatchMap).error(linkFailure);
    }

    function resourceRequest(resource, data) {
      if (waitCount == 0) {
        waitDialogId = lmDialog.show({template: loadingTemplate, noEscape: true});
      }
      waitCount++;

      function checkWait() {
        waitCount--;
        if (waitCount == 0) {
          lmDialog.close(waitDialogId);
          waitDialogId = null;
        }
      }

      return rawRequest(resource, data, checkWait);
    }

    function rawRequest(resource, data, checkWait) {
      var deferred = $q.defer();
      $http({method: 'POST', url: resourceRoot + resource, data: data || {}, headers: {'X-Lampost-Session': sessionId}})
        .success(function (data) {
          checkWait && checkWait();
          deferred.resolve(data);
        }).error(function (data, status) {
          checkWait && checkWait();
          if (status === 409) {
            var errorResult = {id: 'Error', raw: data, text: data};
            var colon_ix = data.indexOf(':');
            if (colon_ix > 0) {
              var space_ix = data.indexOf(' ');
              if (space_ix == -1 || colon_ix < space_ix) {
                errorResult.id = data.substring(0, colon_ix);
                errorResult.text = $.trim(data.substring(colon_ix + 1));
              }
            }
            deferred.reject(errorResult);
          } else if (status === 403) {
            lmDialog.showOk("Denied", "You do not have permission for that action");
          } else if (status) {
            lmDialog.showOk("Server Error: " + status, data);
          }
        });

      return deferred.promise;
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

    function linkFailure(data, status) {
      if (!connected) {
        return;
      }
      if (status >= 500) {
          lmBus.dispatch("display", {lines: [{text: "You hear a crash.  Something unfortunate seems to have happened in the back room.", display: 'combat'},
              {text:"Don't mind the smoke, I'm sure someone is investigating.", display: 'combat'}
             ]});
          return;
      }
      connected = false;
      lmLog.log("Link stopped: " + status);
      $timeout(function () {
        if (!connected && !window.windowClosing) {
          lmDialog.show({template: reconnectTemplate, controller: ReconnectCtrl, noEscape: true});
        }
      }, 100);
    }

    function onLinkStatus(status) {
      connected = true;
      if (status == "good") {
        link();
      } else if (status == "session_not_found") {
        sessionId = '';
        connected = false;
        for (var serviceId in services) {
          services[serviceId].registered = false;
        }
        lmBus.dispatch("logout", "invalid_session");
        serverRequest("connect");
      } else if (status == "no_login") {
        lmBus.dispatch("logout", "invalid_session");
      } else if (status == "cancel") {
        lmLog.log("Outstanding request cancelled");
      }
    }

    function onConnect(data) {
      connected = true;
      sessionId = data;
      for (var serviceId in services) {
        validateService(serviceId)
      }
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
      angular.forEach(activePlayers, function (checkId) {
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

    function validateService(serviceId) {
      if (!connected) {
        return;
      }
      var service = services[serviceId];
      if (service.refCount < 0) {
        lmLog.log("Error: Service " + serviceId + " has refCount " + service.refCount);
        service.refCount = 0;
      }
      if (service.refCount == 0 && service.registered && !service.inFlight) {
        service.inFlight = true;
        serverRequest('unregister', {service_id: serviceId}).then(function () {
          service.inFlight = false;
          service.registered = false;
          validateService(serviceId);
        })
      } else if (service.refCount > 0 && !service.registered && !service.inFlight) {
        service.inFlight = true;
        serverRequest('register', {service_id: serviceId, data: service.data}).then(function () {
          service.inFlight = false;
          service.registered = true;
          validateService(serviceId);
        })
      }
    }

    this.childSession = function (parentSession) {
      sessionId = parentSession;
    };

    this.request = function (resource, args) {
      return $http.get('dialogs/loading.html').then(function (template) {
        loadingTemplate = template.data;

      }).then(function () {
          return resourceRequest(resource, args)
        });
    };

    this.log = function(logMessage) {
      rawRequest("remote_log", logMessage)
    };

    this.asyncRequest = function (resource, args) {
      return rawRequest(resource, args);
    };

    this.registerService = function (serviceId, data) {
      if (!services[serviceId]) {
        services[serviceId] = {refCount: 0, registered: false};
      }
      services[serviceId].refCount++;
      services[serviceId].data = data;
      validateService(serviceId);
    };

    this.unregisterService = function (serviceId) {
      if (!services[serviceId]) {
        lmLog.error(serviceId + " unregistered without registration");
        return;
      }
      services[serviceId].refCount--;
      validateService(serviceId);
    };


    this.connect = function () {
      var data = {};
      if (!sessionId) {
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


    function ReconnectCtrl($scope, $timeout, lmDialog) {
      var tickPromise;
      var time = 16;
      lmBus.register("link_status", function () {
        $scope.dismiss();
        $timeout.cancel(tickPromise);
        lmDialog.forceEnable();
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

    ReconnectCtrl.$inject = ['$scope', '$timeout', 'lmDialog'];

  }]);


angular.module('lampost_svc').service('lmDialog', ['$rootScope', '$compile', '$controller', '$templateCache', '$timeout', '$http',
  function ($rootScope, $compile, $controller, $templateCache, $timeout, $http) {

    var dialogMap = {};
    var nextId = 0;
    var prevElement;
    var enabledElements;
    var enabledLinks;

    // Hack to avoid bootstrap multiple modal bug.  Allegedly fixed in Bootstrap 3
    jQuery().modal.Constructor.prototype.enforceFocus = angular.noop;

    function showDialog(args) {
      var dialogId = "lmDialog_" + nextId++;
      if (args.templateUrl) {
        $http.get(args.templateUrl, {cache: $templateCache}).then(
          function (response) {
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
      enabledLinks.each(function () {
        $(this).attr("data-oldhref", $(this).attr("href"));
        $(this).removeAttr("href");
      })
    }

    function enableUI() {
      enabledElements.removeAttr('disabled');
      enabledLinks.each(function () {
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
      dialogScope.dismiss = function () {
        element.modal("hide");
      };
      dialogMap[dialog.id] = dialog;

      var link = $compile(element.contents());
      if (args.controller) {
        var locals = args.locals || {};
        locals.$scope = dialogScope;
        locals.dialog = dialog;
        var controller = $controller(args.controller, locals);
        element.contents().data('$ngController', controller);
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
        $timeout(function () {
          dialog.scope.$destroy();
          dialog = null;
        });
      }

      element.on(jQuery.support.transition && 'hidden' || 'hide', function () {
        destroy();
      });
      element.on(jQuery.support.transition && 'shown' || 'show', function () {
        var focusElement = $('input:text:visible:first', element);
        if (!focusElement.length) {
          focusElement = $(".lmdialogfocus" + dialog.id + ":first");
        }
        focusElement.focus();
      });
      $timeout(function () {
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

    this.close = function (dialogId) {
      closeDialog(dialogId);
    };

    this.forceEnable = enableUI;

    this.removeAll = function () {
      for (var dialogId in dialogMap) {
        closeDialog(dialogId);
      }
    };

    this.showAlert = function(options, noEscape) {
      showDialog({templateUrl: 'dialogs/alert.html',
        scope: angular.extend($rootScope.$new(), options),
        controller: AlertCtrl, noEscape: noEscape});
    };

    this.showOk = function (title, body) {
      this.showAlert({title: title, body: body,
          buttons: [{label: 'OK', default: true, dismiss: true, class: "btn-primary"}]});
    };

    this.showConfirm = function (title, body, confirm, onCancel) {
      this.showAlert({title: title, body: body, onCancel: onCancel,
        buttons: [{label: 'Yes', dismiss: true, class: 'btn-danger', click: confirm},
        {label: "No", class: 'btn-primary', default: true, cancel: true}]
      }, true);
    };

    this.showPrompt = function (args) {
      var scope = $rootScope.$new();
      scope.submit = args.submit;
      scope.promptValue = "";
      scope.title = args.title;
      scope.prompt = args.prompt;
      scope.inputType = args.password ? "password" : "text";
      scope.onCancel = args.onCancel;
      scope.doSubmit = function () {
        scope.submit.call(scope, scope.promptValue);
        scope.dismiss();
      };
      showDialog({templateUrl: 'dialogs/prompt.html', scope: scope,
        noEscape: true});
    };

    function AlertCtrl($scope, dialog) {
      $scope.click = function (button) {
        button.click && button.click();
        button.cancel && $scope.cancel();
        button.dismiss && $scope.dismiss();
      };

      $scope.cancel = function() {
        $scope.onCancel && $scope.onCancel();
        $scope.dismiss();
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


angular.module('lampost_svc').service('lmUtil', [function () {
  this.stringSort = function (array, field) {
    array.sort(function (a, b) {
      var aField = a[field].toLowerCase();
      var bField = b[field].toLowerCase();
      return ((aField < bField) ? -1 : ((aField > bField) ? 1 : 0));
    });
  };

  this.intSort = function (array, field) {
    array.sort(function (a, b) {
      return a[field] - b[field];
    })
  };

  this.descIntSort = function (array, field) {
    array.sort(function (a, b) {
      return b[field] - a[field];
    })
  };

  this.urlVars = function () {
    var vars = {};
    var keyValuesPairs = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for (var i = 0; i < keyValuesPairs.length; i++) {
      var kvp = keyValuesPairs[i].split('=');
      vars[kvp[0]] = kvps[1];
    }
    return vars;
  };

  this.getScrollBarSizes = function () {
    var inner = $('<p></p>').css({
      'width': '100%',
      'height': '100%'
    });
    var outer = $('<div></div>').css({
      'position': 'absolute',
      'width': '100px',
      'height': '100px',
      'top': '0',
      'left': '0',
      'visibility': 'hidden',
      'overflow': 'hidden'
    }).append(inner);
    $(document.body).append(outer);
    var w1 = inner.width(), h1 = inner.height();
    outer.css('overflow', 'scroll');
    var w2 = inner.width(), h2 = inner.height();
    if (w1 == w2 && outer[0].clientWidth) {
      w2 = outer[0].clientWidth;
    }
    if (h1 == h2 && outer[0].clientHeight) {
      h2 = outer[0].clientHeight;
    }
    outer.detach();
    return [(w1 - w2), (h1 - h2)];
  };
}]);





