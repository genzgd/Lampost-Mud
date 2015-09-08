angular.module('lampost_editor').controller('ScriptEditorCtrl', ['$scope', 'lpEditor',
  function ($scope, lpEditor) {

    var shadowClass;


    $scope.updateShadow = function() {
      var activeShadow, i, lines, firstLine, name;
      activeShadow = lpEditor.constants[model.cls_type][model.cls_shadow];
      lines = $scope.model.text.split('\n');
      if (model.cls_type === 'any') {
        name = model.cls_shadow == 'any' ? 'any_func' : model.cls_shadow;
      } else {
        name = model.cls_shadow;
      }
      firstLine = 'def ' + name + '(';
      for (i = 0; i < activeShadow.args.length; i++) {
        var argName = activeShadow.args[i];
        firstLine += argName + ', ';
      }
      firstLine += '*args, **kwargs):';
      lines[0] = firstLine;
      $scope.model.text = lines.join('\n');
    };

    loadShadows();
    {

    }

  }]);

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

    angular.forEach($scope.modelShadows, function (shadow) {
      if (shadow.name === $scope.shadowScript.name) {
        $scope.active.shadow = shadow;
      }
    });


    $scope.deleteScript = function () {
      var ix = $scope.model.shadows.indexOf(lpEditor.addObj);
      $scope.model.shadows.splice(ix, 1);
      $scope.closeAdd();
    };

    $scope.createScript = function () {
      lpRemote.request('editor/script/validate', $scope.shadowScript).then(function () {
        $scope.model.shadows.push($scope.shadowScript);
        $scope.closeAdd();
      });
    };

    $scope.updateScript = function () {
      angular.copy($scope.shadowScript, lpEditor.addObj);
      lpRemote.request('editor/script/validate', $scope.shadowScript).then(function () {
          angular.copy($scope.shadowScript, lpEditor.addObj);
          $scope.closeAdd();
        }, function (error) {
          $scope.errors.scriptError = error;
        }
      );
    };

  }]);
