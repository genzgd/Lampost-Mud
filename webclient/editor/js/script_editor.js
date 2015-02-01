angular.module('lampost_editor').controller('ShadowScriptCtrl', ['$q', '$scope', 'lpEditor',
  function ($q, $scope, lpEditor) {


    $scope.modelShadows = lpEditor.context.shadows;
    $scope.modelShadow = null;

    $scope.newAdd = !lpEditor.addObj;
    if ($scope.newAdd) {
      $scope.shadowScript = {text: '', priority: 0};
    } else {
      $scope.shadowScript = angular.copy(lpEditor.addObj);
    }

    angular.forEach($scope.modelShadows, function(shadow) {
      if (shadow.name === $scope.shadowScript.name) {
        $scope.modelShadow = shadow;
      }
    });

    $scope.changeShadow = function() {
      var i;
      $scope.shadowScript.name = $scope.modelShadow.name;
      var textlines = $scope.shadowScript.text.split('\n');
      var firstLine= 'def ' + $scope.shadowScript.name + '(';
      for (i = 0; i < $scope.modelShadow.args.length; i++) {
        var argName = $scope.modelShadow.args[i];
        firstLine += argName + ', ';

      }
      firstLine += '*args, **kwargs):';
      if (textlines.length) {
        textlines[0] = firstLine;
        $scope.shadowScript.text = textlines.join('\n');
      } else {
        $scope.shadowSript.text = firstLine;
      }
    };

    $scope.createScripte = function() {
      model.shadows.push($scope.shadowScript);
      $scope.closeAdd();
    }
  }]);
