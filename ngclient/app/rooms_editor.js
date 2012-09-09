angular.module('lampost_edit').controller('RoomsEditorController', ['$scope', 'lmRemote', 'lmDialog', 'lmArrays', 'lmEditor',
    function ($scope, lmRemote, lmDialog, lmArrays, lmEditor) {

        $scope.areaId = $scope.editor.parent;
        $scope.model = $scope.editor.model;
        $scope.ready = false;
        var listPromise = lmRemote.request($scope.editor.url + "/list", {area_id:$scope.editor.parent}).then(function (rooms) {
            $scope.model.rooms = rooms;
            $scope.rooms = rooms;
            $scope.rooms_copy = jQuery.extend(true, [], rooms);
            $scope.ready = true;
        });
        $scope.editRoom = function() {

        }

    }]);