angular.module('lampost_remote', []).service('lpRemote', ['$timeout', '$http', '$templateCache', '$q', '$log', 'lpEvent', 'lpDialog',
  function ($timeout, $http, $templateCache, $q, $log, lpEvent, lpDialog) {

    var current_req_id = 0;
    var req_map = {};
    var socket;
    var connectEndpoint = '';
    var connectOptions = {};
    var connected = false;
    var loadingTemplate;
    var waitCount = 0;
    var waitDialogId = null;
    var services = {};
    var resourceRoot = '/';
    var reconnectTemplate = '<div class="modal"><div class="modal-dialog"><div class="modal-content">' +
      '<div class="modal-header"> <h3>Reconnecting To Server</h3></div><div class="modal-body">' +
      '<p>Reconnecting in {{time}} seconds.</p></div><div class="modal-footer">' +
      '<button class="btn btn-primary" ng-click="reconnectNow()">Reconnect Now</button></div></div></div></div>';


    function request(path, data, withWait) {
      if (!connected) {
        $log.warn("Attempting request " + path + " before socket connected");
        return $q.reject({id: 'Error', text: 'Socket not connected'});
      }
      if (withWait && waitCount++ == 0) {
        waitDialogId = lpDialog.show({template: loadingTemplate, noEscape: true});
      }
      data = data || {};
      data.path = path;
      data.req_id = current_req_id++;

      var deferred = $q.defer();
      req_map[data.req_id] = {deferred: deferred, withWait: withWait};
      socket.send(JSON.stringify(data));
      return deferred.promise;
    }

    function send(path, data) {
      if (connected) {
        data = data || {};
        data.path = path;
        socket.send(JSON.stringify(data))
      } else {
        $log.warn("Attempt to send " + path + " before socket connected");
      }
    }

    function onMessage(message) {
      var response = JSON.parse(message.data);
      var req_id = response.req_id;
      if (req_id !== undefined) {
        var req_data = req_map[req_id];
        if (!req_data) {
          $log.error("Received response for missing req_id " + req_id);
          return;
        }
        delete req_map[req_id];
        if (req_data.withWait && --waitCount === 0) {
          lpDialog.close(waitDialogId);
          waitDialogId = null;
        }
        var deferred = req_data.deferred;
        switch (response.http_status) {
          case 0:
          case 200:
          case 204:
          case undefined:
          case null:
            deferred.resolve(response.data);
            break;
          case 401:
            lpDialog.showOk("Denied", "You do not have permission for that action");
            deferred.reject(response);
            break;
          case 400:
          case 409:
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
            break;
          default:
            lpDialog.showOk("Server Error: " + response.http_status, response.client_message);
            deferred.reject(response);
            break;
        }
      } else {
        lpEvent.dispatchMap(response);
      }
    }

    function onError(e) {
      $log.log("Web socket error" + e);
    }

    function onClose(e) {
      connected = false;
      $log.log("Web socket close" + e);
      $timeout(function () {
        if (!connected && !window.windowClosing) {
          lpDialog.show({template: reconnectTemplate, controller: ReconnectCtrl, noEscape: true});
        }
      }, 50);
    }

    lpEvent.register('connect', function(session_id) {
      connectOptions.session_id = session_id;
      angular.forEach(services, validateService);
    });

    function connect(endpoint, options) {
      connectEndpoint = endpoint;
      connectOptions = options || {};
      var socket_url = (window.location.protocol === "https:" ? "wss://" : "ws://") +
        window.location.host + resourceRoot + 'link';
      socket = new WebSocket(socket_url);
      socket.onclose = onClose;
      socket.onerror = onError;
      socket.onmessage = onMessage;
      socket.onopen = function() {
        connected = true;
        send(endpoint, connectOptions);
      };
    }

    function reconnect() {
      connect(connectEndpoint, connectOptions);
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
        request('unregister_service', {service_id: service.serviceId}).then(function () {
          service.inFlight = false;
          service.registered = false;
          validateService(service);
        })
      } else if (service.refCount > 0 && !service.registered && !service.inFlight) {
        service.inFlight = true;
        request('register_service', {service_id: service.serviceId, data: service.data}).then(function () {
          service.inFlight = false;
          service.registered = true;
          validateService(service);
        })
      }
    }

    this.request = function(path, args) {
      return $http.get('common/dialogs/loading.html', {cache: $templateCache}).then(function (template) {
        loadingTemplate = template.data;
      }).then(function () {
        return request(path, args, true)
      });
    };

    this.send = send;

    this.connect = connect;

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

    function ReconnectCtrl($scope, $timeout) {
      var tickPromise;
      var time = 16;
      lpEvent.register("connect", function () {
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
