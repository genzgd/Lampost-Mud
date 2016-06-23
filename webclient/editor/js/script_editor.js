angular.module('lampost_editor').controller('ScriptEditorCtrl', ['$scope', 'lpUtil', 'lpEvent', 'lpEditor',
  function ($scope, lpUtil, lpEvent, lpEditor) {

    var classMap, activeClass;
    classMap = lpEditor.constants['shadow_types'];

    $scope.updateShadowClass = function (forceUpdate) {
      if ($scope.model.builder != 'shadow') {
        return;
      }
      activeClass = classMap[$scope.model.metadata.cls_type];
      lpUtil.stringSort(activeClass, 'name');
      $scope.shadowFuncs = activeClass;

      if (forceUpdate || $scope.model.text == '') {
        $scope.updateArgs()
      }
    };

    $scope.updateArgs = function () {
      var activeShadow, i, lines, firstLine;
      var shadowMap = lpUtil.toMap(activeClass, 'name');
      activeShadow = shadowMap[$scope.model.metadata.cls_shadow];
      if (!activeShadow) {
        $scope.model.metadata.cls_shadow = $scope.shadowFuncs[0].name;
        activeShadow = shadowMap[$scope.model.metadata.cls_shadow];
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

    $scope.updateBuilder = function() {
      if ($scope.model.builder) {
        $scope.builderPanel = "editor/panels/" + $scope.model.builder + "_script.html";
        $scope.updateShadowClass(true);
      } else {
        $scope.builderPanel = null;
      }
    };

    $scope.noApprove = lpEditor.immLevel < lpEditor.constants.imm_levels.admin;

    lpEvent.register('editReady', function() {
      $scope.updatebuilder();
      $scope.updateShadowClass(false)
    }, $scope);

  }]);


angular.module('lampost_editor').controller('ScriptRefCtrl', ['$q', '$scope', 'lpRemote', 'lpEditFilters',
  'lpEditorTypes', 'lpEditor', function ($q, $scope, lpRemote, lpEditFilters, lpEditorTypes, lpEditor) {

    var classMap, classId, shadow;
    classId = $scope.model.class_id;
    classMap = lpEditor.constants['shadow_types'];

    $scope.scriptSelect = new lpEditorTypes.ChildSelect('script', 'script');
    $scope.scriptSelect.parentFilter = lpEditFilters.hasChild('script');
    $scope.scriptSelect.childFilter = function (scripts) {
      var valid = [];
      angular.forEach(scripts, function (script) {
        if (script.cls_type === classId || script.cls_type === 'any') {
          valid.push(script);
        }
      });
      return valid;
    };

    $scope.scriptSelect.childSelect = function (script) {
      if (!script || script.invalid) {
        shadow.script = null;
        shadow.func_name = null;
        return;
      }
      shadow.script = script.dbo_id;
      if (script.cls_shadow === 'any_func') {
        $scope.shadows =  classMap[classId];
        shadow.func_name = null;
      } else {
        $scope.shadows = classMap[classId].filter(function(s) {
          return s.name === script.cls_shadow;
        });
        shadow.func_name = script.cls_shadow;
      }
    };

    $scope.scriptSelect.parentSelect = function () {
      $scope.addObj.script = null;
    };

    function initialize() {
      if (lpEditor.addObj) {
        shadow = lpEditor.addObj;
      } else {
        shadow = {priority: 0, func_name: ''};
      }
      $scope.addObj = shadow;
    }

    $scope.validScript = function () {
      return shadow.func_name && shadow.script
    };

    $scope.addScriptRef = function () {
      $scope.model.script_refs.push(shadow);
      $scope.closeAdd();
    };

    $scope.deleteScriptRef = function () {
      $scope.model.script_refs.splice($scope.model.script_refs.indexOf(shadow), 1);
      $scope.closeAdd();
    };

    $scope.$on('addInit', initialize);

    initialize();

  }]);
