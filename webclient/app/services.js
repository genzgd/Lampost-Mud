
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
    var reconnectTemplate = '<div class="modal"><div class="modal-dialog"><div class="modal-content">' +
            '<div class="modal-header"> <h3>Reconnecting To Server</h3></div><div class="modal-body">' +
            '<p>Reconnecting in {{time}} seconds.</p></div><div class="modal-footer">' +
            '<button class="btn btn-primary" ng-click="reconnectNow()">Reconnect Now</button></div></div></div></div>';

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
      lmBus.register("link_status", function (link_status) {
        if (link_status == 'cancel') {
            return;
        }
        $scope.dismiss();
        $timeout.cancel(tickPromise);
        lmBus.unregister("link_status");
      }, $scope, -500);

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