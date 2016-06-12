angular.module('lampost_editor').controller('ScriptEditorCtrl', ['$scope', 'lpUtil', 'lpEvent', 'lpEditor',
  function ($scope, lpUtil, lpEvent, lpEditor) {

    var classMap, activeClass;
    classMap = lpEditor.constants['shadow_types'];

    $scope.updateShadowClass = function () {
      activeClass = classMap[$scope.model.cls_type];
      if (!activeClass) {
        activeClass = classMap['any'];
      }
      lpUtil.stringSort(activeClass, 'name');
      $scope.shadowFuncs = activeClass;

      if (!$scope.model.args || $scope.model.cls_type !== 'any') {
        $scope.updateArgs();
      }
    };

    $scope.updateArgs = function() {
      var activeShadow, i, lines, firstLine;
      var shadowMap = lpUtil.toMap(activeClass, 'name');
      activeShadow = shadowMap[$scope.model.cls_shadow];
      if (!activeShadow) {
        $scope.model.cls_shadow = $scope.shadowFuncs[0].name;
        activeShadow = shadowMap[$scope.model.cls_shadow];
      }
      lines = $scope.model.text.split('\n');
      firstLine = 'def ' + activeShadow.name + '(';
      for (i = 0; i < activeShadow.args.length; i++) {
        var argName = activeShadow.args[i];
        firstLine += argName + ', ';
      }
      firstLine += '*args, **kwargs):';
      lines[0] = firstLine;
      $scope.model.text = lines.join('\n');
    };

    $scope.noApprove = lpEditor.immLevel < lpEditor.constants.imm_levels.admin;

    lpEvent.register('editReady', $scope.updateShadowClass, $scope);

  }]);

angular.module('lampost_editor').controller('ScriptRefCtrl', ['$q', '$scope', 'lpRemote', 'lpEditorTypes', 'lpEditor',
  function ($q, $scope, lpRemote, lpEditorTypes, lpEditor) {

    $scope.addObj = {};
    $scope.scriptSelect = new lpEditorTypes.ChildSelect('script', 'script');

    function initialize() {
        if (lpEditor.addObj) {
          $scope.addObj = lpEditor.addObj;
          $scope.newAdd = false;
        } else {
          $scope.addObj = {priority: 0, func_name: ''};
          $scope.newAdd = true;
        }
    }

    $scope.validScript = function() {
      return $scope.addObj.func_name && $scope.addObj.script
    };
    $scope.$on('addInit', initialize);

    initialize();

  }]);
