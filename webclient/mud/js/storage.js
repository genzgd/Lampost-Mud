angular.module('lampost_mud').service('lpStorage', ['$window', 'lpEvent', function ($window, lpEvent) {

  var playerId;
  var sessionId;
  var sessions;
  var sessionKey = 'playerSessions';
  var lastKey = 'lastPlayer';
  var immKey = 'activeImm';
  var immSession;

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

  function onLogout() {
    readSessions();
    if (sessions.hasOwnProperty(playerId)) {
      delete sessions[playerId];
    }
    playerId = null;
    writeSessions();
    if (immSession) {
      localStorage.removeItem(immKey);
      immSession = null;
    }
  }

  function updateTimestamp() {
    readSessions();
    if (playerId) {
      sessions[playerId] = {playerId: playerId, sessionId: sessionId, timestamp: new Date().getTime()};
    }
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

  lpEvent.register('connect', function (data) {
    sessionId = data;
  });

  lpEvent.register("heartbeat", updateTimestamp);

  lpEvent.register("login", function (data) {
    playerId = data.name.toLowerCase();
    if (data.imm_level) {
      immSession = {user_id: data.user_id, app_session_id: sessionId};
      localStorage.setItem(immKey, JSON.stringify(immSession));
    }
    updateTimestamp();
  });

  lpEvent.register("logout", onLogout);

  lpEvent.register("window_closing", function () {
    if (playerId) {
      updateTimestamp();
    }
  });

}]);
