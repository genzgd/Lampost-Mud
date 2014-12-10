angular.module('lampost_remote', []).service('lpRemote', ['$timeout', '$http', '$q', '$log', 'lpEvent', 'lpDialog',
  function ($timeout, $http, $q, $log, lpEvent, lpDialog) {

    var sessionId = '';
    var connectEndpoint = '';
    var connected = false;
    var loadingTemplate;
    var waitCount = 0;
    var waitDialogId = null;
    var services = {};
    var resourceRoot = '../';
    var reconnectTemplate = '<div class="modal"><div class="modal-dialog"><div class="modal-content">' +
      '<div class="modal-header"> <h3>Reconnecting To Server</h3></div><div class="modal-body">' +
      '<p>Reconnecting in {{time}} seconds.</p></div><div class="modal-footer">' +
      '<button class="btn btn-primary" ng-click="reconnectNow()">Reconnect Now</button></div></div></div></div>';

    function serverRequest(resource, data) {
      return $http({method: 'POST',
        url: resourceRoot + resource,
        data: data || {},
        headers: sessionId ? {'X-Lampost-Session': sessionId} : null}).success(lpEvent.dispatchMap).error(linkFailure);
    }

    function resourceRequest(resource, data) {
      if (waitCount == 0) {
        waitDialogId = lpDialog.show({template: loadingTemplate, noEscape: true});
      }
      waitCount++;

      function checkWait() {
        waitCount--;
        if (waitCount == 0) {
          lpDialog.close(waitDialogId);
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
          if (status === 409 || status === 400) {
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
            lpDialog.showOk("Denied", "You do not have permission for that action");
          } else if (status) {
            lpDialog.showOk("Server Error: " + status, data);
          }
        });

      return deferred.promise;
    }

    function linkFailure(data, status) {
      if (!connected) {
        return;
      }
      if (status == 500) {
        lpEvent.dispatch('server_error');
        return;
      }
      connected = false;
      $log.log("Link stopped: " + status);
      $timeout(function () {
        if (!connected && !window.windowClosing) {
          lpDialog.show({template: reconnectTemplate, controller: ReconnectCtrl, noEscape: true});
        }
      }, 50);
    }

    function onLinkStatus(status) {
      connected = true;
      if (status == "good") {
        serverRequest('link');
      } else if (status == "session_not_found") {
        sessionId = '';
        connected = false;
        angular.forEach(services, function(service) {
          service.registered = false;
        });
        lpEvent.dispatch("logout", "invalid_session");
        serverRequest(connectEndpoint);
      } else if (status == "no_login") {
        lpEvent.dispatch("logout", "invalid_session");
      } else if (status == "cancel") {
        $log.log("Outstanding request cancelled");
      }
    }

    function onConnect(data) {
      connected = true;
      sessionId = data;
      angular.forEach(services, validateService);
      serverRequest('link');
    }

    function reconnect() {
      if (!sessionId) {
        serverRequest(endpoint);
      } else {
        serverRequest("link");
      }
    }

    function validateService(service) {
      if (!connected) {
        return;
      }
      if (service.refCount < 0) {
        $log.log("Error: Service " + service.serviceId + " has refCount " + service.refCount);
        service.refCount = 0;
      }
      if (service.refCount == 0 && service.registered && !service.inFlight) {
        service.inFlight = true;
        serverRequest('unregister', {service_id: service.serviceId}).then(function () {
          service.inFlight = false;
          service.registered = false;
          validateService(service);
        })
      } else if (service.refCount > 0 && !service.registered && !service.inFlight) {
        service.inFlight = true;
        serverRequest('register', {service_id: service.serviceId, data: service.data}).then(function () {
          service.inFlight = false;
          service.registered = true;
          validateService(service);
        })
      }
    }

    this.connect = function(endpoint, oldSessionId, data) {
      if (oldSessionId) {
        sessionId = oldSessionId;
      }
      connectEndpoint = endpoint;
      serverRequest(endpoint, data);
    };

    this.request = function (resource, args) {
      return $http.get('common/dialogs/loading.html').then(function (template) {
        loadingTemplate = template.data;
      }).then(function () {
        return resourceRequest(resource, args)
      });
    };

    this.log = function (logMessage) {
      rawRequest("remote_log", logMessage)
    };

    this.asyncRequest = function (resource, args) {
      return rawRequest(resource, args);
    };

    this.registerService = function (serviceId, data) {
      var service = services[serviceId];
      if (!service) {
        service = {refCount: 0, registered: false, serviceId: serviceId};
        services[serviceId] = service;
      }
      service.refCount++;
      service.data = data;
      validateService(service);
    };

    this.unregisterService = function (serviceId) {
      var service = services[serviceId];
      if (!service) {
        $log.error(serviceId + " unregistered without registration");
        return;
      }
      service.refCount--;
      validateService(service);
    };

    lpEvent.register("connect", onConnect);
    lpEvent.register("link_status", onLinkStatus);
    lpEvent.register("server_request", serverRequest);


    function ReconnectCtrl($scope, $timeout) {
      var tickPromise;
      var time = 16;
      lpEvent.register("link_status", function (link_status) {
        if (link_status == 'cancel') {
          return;
        }
        $scope.dismiss();
        $timeout.cancel(tickPromise);
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

    ReconnectCtrl.$inject = ['$scope', '$timeout'];

  }]);