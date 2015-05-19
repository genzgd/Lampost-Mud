angular.module('lampost_editor').controller('ShadowScriptCtrl', ['$q', '$scope', 'lpRemote', 'lpEditor',
  function ($q, $scope, lpRemote, lpEditor) {

    var active;

    $scope.active = active = {};
    $scope.errors = {};
    $scope.modelShadows = lpEditor.context.shadows;

    $scope.newAdd = !lpEditor.addObj;
    if ($scope.newAdd) {
      $scope.shadowScript = {text: '', priority: 0};
      originalText = '';
    } else {
      $scope.shadowScript = angular.copy(lpEditor.addObj);
    }

    angular.forEach($scope.modelShadows, function(shadow) {
      if (shadow.name === $scope.shadowScript.name) {
        $scope.active.shadow = shadow;
      }
    });

    $scope.changeShadow = function() {
      var i, lines, firstLine;
      $scope.shadowScript.name = active.shadow.name;
      lines = $scope.shadowScript.text.split('\n');
      firstLine= 'def ' + $scope.shadowScript.name + '(';
      for (i = 0; i < active.shadow.args.length; i++) {
        var argName = active.shadow.args[i];
        firstLine += argName + ', ';
      }
      firstLine += '*args, **kwargs):';
      lines[0] = firstLine;
      $scope.shadowScript.text = lines.join('\n');
    };

    $scope.deleteScript = function() {
      var ix = $scope.model.shadows.indexOf(lpEditor.addObj);
      $scope.model.shadows.splice(ix, 1);
      $scope.closeAdd();
    };

    $scope.createScript = function() {
      lpRemote.request('editor/script/validate', $scope.shadowScript).then(function() {
          $scope.model.shadows.push($scope.shadowScript);
          $scope.closeAdd();
        });
    };

    $scope.updateScript = function() {
      angular.copy($scope.shadowScript, lpEditor.addObj);
      lpRemote.request('editor/script/validate', $scope.shadowScript).then(function() {
          angular.copy($scope.shadowScript, lpEditor.addObj);
          $scope.closeAdd();
        }, function(error) {
          $scope.errors.scriptError = error;
        }
      );
    };

  }]);
