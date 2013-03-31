angular.module('lampost_editor').controller('DisplayEditorController', ['$scope', 'lmRemote', 'lmBus', function ($scope, lmRemote, lmBus) {

    lmBus.register("editor_activated", function (editor) {
        if (editor == $scope.editor) {
            loadDisplays();
        }
    });

    $scope.updateDisplays = function() {
        lmRemote.request($scope.editor.url + '/update', {displays: $scope.displays}, true);
    };

    function loadDisplays() {
        $scope.ready = false;
        lmRemote.request($scope.editor.url + '/list').then(function (displays) {
            $scope.displays = displays;
            $scope.ready = true;
        })
    }
}]);
