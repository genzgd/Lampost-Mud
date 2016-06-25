angular.module('lampost_editor').controller('ScriptEditorCtrl', ['$scope', 'lpUtil', 'lpEvent', 'lpEditor',
  function ($scope, lpUtil, lpEvent, lpEditor) {

    var classMap, classList, activeClass;
    classMap = lpEditor.constants['shadow_types'];
    classList = lpUtil.toArray(classMap, 'name');
    lpUtil.stringSort(classList, 'name');

    $scope.updateShadowClass = function (forceUpdate) {
      if ($scope.model.builder != 'shadow') {
        return;
      }
      activeClass = classMap[$scope.model.metadata.cls_type];
      if (!activeClass) {
        activeClass = classList[0];
        $scope.model.metadata.cls_type = activeClass.name;
      }
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
      $scope.updateBuilder();
      $scope.updateShadowClass(false)
    }, $scope);

  }]);


angular.module('lampost_editor').controller('ScriptRefCtrl', ['$q', '$scope', 'lpRemote', 'lpEditFilters',
  'lpEditorTypes', 'lpEditor', function ($q, $scope, lpRemote, lpEditFilters, lpEditorTypes, lpEditor) {

    var classMap, classId, scriptRef;
    classId = $scope.model.class_id;
    classMap = lpEditor.constants['shadow_types'];

    $scope.scriptSelect = new lpEditorTypes.ChildSelect('script', 'script');
    $scope.scriptSelect.parentFilter = lpEditFilters.hasChild('script');
    $scope.scriptSelect.childFilter = function (scripts) {
      var valid = [];
      angular.forEach(scripts, function (script) {
        if (script.builder !== 'shadow') {
          valid.push(script);
        }
        if (script.metadata.cls_type === classId) {
          valid.push(script);
        }
      });
      return valid;
    };

    $scope.scriptSelect.childSelect = function (script) {
      if (!script || script.invalid) {
        scriptRef.script = null;
        scriptRef.func_name = null;
        return;
      }
      scriptRef.script = script.dbo_id;
      $scope.refShadow = null;
      if (script.builder === 'shadow') {
        $scope.refShadow = script;
        $scope.shadows = classMap[classId].filter(function (s) {
          return s.name === script.metadata.cls_shadow;
        });
        scriptRef.func_name = script.metadata.cls_shadow;
        scriptRef.build_args.priority = scriptRef.build_args.priority || 0;
      }
    };

    $scope.scriptSelect.parentSelect = function () {
      $scope.addObj.script = null;
    };

    function initialize() {
      if (lpEditor.addObj) {
        scriptRef = lpEditor.addObj;
      } else {
        scriptRef = {func_name: '', build_args: {}};
      }
      $scope.addObj = scriptRef;
    }

    $scope.validScript = function () {
      return scriptRef.func_name && scriptRef.script
    };

    $scope.addScriptRef = function () {
      $scope.model.script_refs.push(scriptRef);
      $scope.closeAdd();
    };

    $scope.deleteScriptRef = function () {
      $scope.model.script_refs.splice($scope.model.script_refs.indexOf(scriptRef), 1);
      $scope.closeAdd();
    };

    $scope.$on('addInit', initialize);

    initialize();

  }]);
