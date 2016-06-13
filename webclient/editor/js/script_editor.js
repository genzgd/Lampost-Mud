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


angular.module('lampost_editor').controller('ScriptRefCtrl', ['$q', '$scope', 'lpRemote', 'lpEditFilters',
  'lpEditorTypes', 'lpEditor', function ($q, $scope, lpRemote, lpEditFilters, lpEditorTypes, lpEditor) {

    var classMap, parentFilter, childFilter, classId;
    classId = $scope.model.class_id;
    classMap = lpEditor.constants['shadow_types'];

    $scope.scriptSelect = new lpEditorTypes.ChildSelect('script', 'script');
    $scope.scriptSelect.parentFilter = lpEditFilters.hasChild('script');
    $scope.scriptSelect.childFilter = function(scripts) {
      var valid = [];
      angular.forEach(scripts, function(script) {
        if (script.cls_type === classId || script.cls_type === 'any') {
          valid.push(script);
        }
      });
      return valid;
    };

    $scope.scriptSelect.childSelect = function(script) {
      if (!script || script.invalid) {
        $scope.addObj.script = null;
        $scope.addObj.func_name = null;
        return;
      }
      $scope.addObj.script = script.dbo_id;
      if (script.cls_shadow === 'any_func') {
        $scope.shadows = classMap[classId];
        $scope.addObj.func_name = null;
      } else {
        $scope.shadows = classMap[classId][script.cls_shadow];
        $scope.addObj.func_name = script.cls_shadow;
      }
    };

    $scope.scriptSelect.parentSelect = function() {
      $scope.addObj.script = null;
    };

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

    $scope.addScriptRef = function() {
      $scope.model.shadow_refs.push($scope.addObj);
      $scope.closeAdd();
    };

    $scope.$on('addInit', initialize);

    initialize();

  }]);
