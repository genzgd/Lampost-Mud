angular.module('lampost_editor', ['lampost_svc', 'lampost_dir', 'ngSanitize']);

angular.module('lampost_editor').run(['$timeout', 'lmUtil', 'lmEditor', 'lmRemote', 'lmBus',
  function ($timeout, lmUtil, lmEditor, lmRemote, lmBus) {

    window.onbeforeunload = function () {
      var handlers = [];
      lmBus.dispatch('editorClosing', handlers);
      if (handlers.length) {
        return "You have changes to " + handlers.length + " item(s).  Changes will be lost if you leave this page.";
      }
      return undefined;
    };

    window.onunload = function () {
      window.windowClosing = true;
    };

  }]);

angular.module('lampost_editor').controller('EditorAppController', ['$scope', function($scope) {

}]);