angular.module('lampost_mud').service('lpStorage', ['lmBus', function (lmBus) {

  var playerId;
  var sessionId;
  var sessions;
  var sessionKey = 'playerSessions';
  var lastKey = 'lastPlayer';

  function readSessions() {
    var value = localStorage.getItem(sessionKey);
    sessions = value ? JSON.parse(value) : {};
  }

  function writeSessions() {
    localStorage.setItem(sessionKey, JSON.stringify(sessions));
    if (playerId) {
      sessionStorage.setItem(lastKey, JSON.stringify({playerId: playerId, sessionId: sessionId,
        timestamp: new Date().getTime()}));
    } else {
      sessionStorage.removeItem(lastKey);
    }
  }

  function invalidateTimestamp() {
    readSessions();
    if (sessions.hasOwnProperty(playerId)) {
      delete sessions[playerId];
      writeSessions();
    }
    playerId = null;
  }

  function updateTimestamp() {
    readSessions();
    sessions[playerId] = {playerId: playerId, sessionId: sessionId, timestamp: new Date().getTime()};
    writeSessions();
  }

  this.lastSession = function () {
    readSessions();
    var staleTimestamp = new Date().getTime() - 60 * 1000;
    var lastSession;
    for (playerId in sessions) {
      if (sessions.hasOwnProperty(playerId)) {
        var session = sessions[playerId];
        if (session.timestamp < staleTimestamp) {
          delete sessions[playerId];
        } else if (!lastSession || session.timestamp > lastSession.timestamp) {
          lastSession = session;
        }
      }
    }
    var lastValue = sessionStorage.getItem(lastKey);
    if (lastValue) {
      lastSession = JSON.parse(lastValue);
    }
    writeSessions();
    return lastSession;
  };

  lmBus.register('connect', function (data) {
    sessionId = data;
  });

  lmBus.register("link_status", function (status) {
    if (playerId && status === 'good') {
      updateTimestamp();
    }
  });

  lmBus.register("login", function (data) {
    playerId = data.name.toLowerCase();
    updateTimestamp();
  });

  lmBus.register("logout", invalidateTimestamp);

  lmBus.register("window_closing", function () {
    if (playerId) {
      updateTimestamp();
    }
  });

}]);