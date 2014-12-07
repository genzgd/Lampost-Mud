angular.module('lampost_editor').service('lpEditorStorage', ['$window', 'lpEvent', function($window, lpEvent) {

  var sessionId;

  lpEvent.register('connect', function(data) {
    sessionId = data;
  });

  lpEvent.register('editor_login', function(data) {
    sessionStorage.setItem('editSessionId', sessionId);
    $window.name = 'lpEditor*' + data.playerId
    localStorage.setItem($window.name, 'active')
  })

  lpEvent.register('editor_logout', function() {
    sessionStorage.removeItem('editSessionId');
    localStorage.removeItem($window.name)
  })

  lpEvent.register('window_closing', function() {
    if ($window.name) {
      localStorage.removeItem($window.name)
    }
  })

}])