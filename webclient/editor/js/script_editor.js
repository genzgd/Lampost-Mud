angular.module('lampost_editor').controller('ShadowScriptCtrl', ['$q', '$scope', 'lpRemote', 'lpEditor',
  function ($q, $scope, lpRemote, lpEditor) {


    var validText, originalText;

    $scope.modelShadows = lpEditor.context.shadows;
    $scope.modelShadow = null;
    $scope.scriptChanged = false;

    $scope.newAdd = !lpEditor.addObj;
    if ($scope.newAdd) {
      $scope.shadowScript = {text: '', priority: 0};
      originalText = '';
    } else {
      $scope.shadowScript = lpEditor.addObj;
      originalText = validText = $scope.shadowScript.text;
    }
    $scope.scriptText = $scope.shadowScript.text;

    angular.forEach($scope.modelShadows, function(shadow) {
      if (shadow.name === $scope.shadowScript.name) {
        $scope.modelShadow = shadow;
      }
    });

    $scope.changeShadow = function() {
      var i, lines, firstLine;
      $scope.shadowScript.name = $scope.modelShadow.name;
      lines = $scope.scriptText.split('\n');
      firstLine= 'def ' + $scope.shadowScript.name + '(';
      for (i = 0; i < $scope.modelShadow.args.length; i++) {
        var argName = $scope.modelShadow.args[i];
        firstLine += argName + ', ';
      }
      firstLine += '*args, **kwargs):';
      if (lines.length) {
        lines[0] = firstLine;
        $scope.scriptText = lines.join('\n');
      } else {
        $scope.scriptText = firstLine;
      }
    };

    $scope.deleteScript = function() {
      var ix = $scope.model.shadows.indexOf(lpEditor.addObj);
      $scope.model.shadows.splice(ix, 1);
      $scope.closeAdd();
    };

    $scope.createScript = function() {
      $scope.model.shadows.push($scope.shadowScript);
      $scope.closeAdd();
    };

    $scope.updateScript = function() {
      lpEditor.addObj.text = $scope.scriptText;
      originalText = $scope.scriptText;
    };

    $scope.checkValid = function() {
      $scope.scriptValid = validText && validText === $scope.scriptText;
      $scope.scriptChanged = $scope.scriptText !== originalText;
    };

    $scope.validateScript = function() {
      lpRemote.request('editor/script/validate', {name: $scope.shadowScript.name, text: $scoe.scriptText}).then(function() {
        validText = $scope.scriptText;
        $scope.checkValid();
      }, function(error) {
        $scope.scriptError = error;
      })
    }

  }]);
