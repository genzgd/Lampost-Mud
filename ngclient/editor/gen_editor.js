angular.module('lampost_editor').controller('GenEditorCtrl', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog', 'lmUtil',
  function ($scope, lmRemote, lmEditor, lmDialog, lmUtil) {


    var newDialogId = null;
    var originalObject = null;
    var dialogScope = null;
    var baseUrl = $scope.editor.url + '/';

    $scope.ready = false;
    $scope.isDirty = false;
    $scope.objectExists = false;
    $scope.activeObject = null;
    $scope.newObject = null;
    $scope.copyFromId = null;
    $scope.objLabel = $scope.editor.id.charAt(0).toUpperCase() + $scope.editor.id.slice(1);
    loadObjects();

    function loadObjects() {
      lmRemote.request(baseUrl + 'list').then(function (objects) {
        $scope.objectList = objects;
        $scope.ready = true;
      })
    }

    function mainDelete(object) {
      lmRemote.request(baseUrl + 'delete', {dbo_id: object.dbo_id}).then(function () {
        if ($scope.activeObject = object) {
          $scope.activeObject = null;
        }
        for (var i = 0; i < $scope.objectList.length; i++) {
          if ($scope.objectList[i] == object) {
            $scope.objectList.splice(i, 1);
            break;
          }
        }
      });
    }

    $scope.dirty = function () {
      $scope.isDirty = true;
    };

    $scope.revertObject = function () {
      $scope.activeObject = jQuery.extend(true, originalObject, {});
      $scope.isDirty = false;
    };

    $scope.updateObject = function () {
      lmRemote.request(baseUrl + 'update', {dbo: $scope.activeObject}).then(
        function (updatedObject) {
          $scope.isDirty = false;
          for (var i = 0; i < $scope.objectList.length; i++) {
            if ($scope.objectList[i].dbo_id == updatedObject.dbo_id) {
              $scope.objectList[i] = updatedObject;
              break;
            }
          }
        }
      )
    };

    $scope.submitNewObject = function () {
      lmRemote.request(baseUrl + 'create', {dbo_id: $scope.newObject.dbo_id, dbo: $scope.newObject.dbo}).then(
        function (createdObject) {
          $scope.objectList.push(createdObject);
          lmUtil.stringSort($scope.objectList, 'dbo_id');
          lmDialog.close(newDialogId);
          $scope.editObject(createdObject);
        }, function () {
          dialogScope.objectExists = true;
        });
    };

    $scope.newObjectDialog = function () {
      $scope.newObject = {dbo_id: '', dbo: {}};
      var dialogName = $scope.editor.newDialog ? $scope.editor.id : 'generic';
      dialogScope = $scope.$new();
      newDialogId = lmDialog.show({templateUrl: 'editor/dialogs/new_' + dialogName + '.html', scope: dialogScope});
    };

    $scope.editObject = function (object) {
      originalObject = object;
      $scope.activeObject = jQuery.extend(true, {}, object);
    };

    $scope.deleteObject = function (event, object) {
      event.preventDefault();
      event.stopPropagation();
      lmDialog.showConfirm("Delete " + $scope.objLabel, "Are you certain you want to delete " + $scope.objLabel + " " + object.dbo_id + "?",
        function () {
          mainDelete(object);
        });
    };

    $scope.copyObject = function (event, object) {
      event.preventDefault();
      event.stopPropagation();
      $scope.copyFromId = object.dbo_id;
      $scope.newObject = {dbo_id: '', dbo: jQuery.extend(true, {}, object)};
      delete $scope.newObject.dbo['dbo_id'];
      dialogScope = $scope.$new();
      var dialogName = $scope.editor.copyDialog ? $scope.editor.id : 'generic';
      newDialogId = lmDialog.show({templateUrl: 'editor/dialogs/copy_' + dialogName + '.html', scope: dialogScope});
    };

    $scope.objectRowClass = function (object) {
      if ($scope.activeObject && $scope.activeObject.dbo_id == object.dbo_id) {
        return 'highlight';
      }
      return "";
    };

  }]);
