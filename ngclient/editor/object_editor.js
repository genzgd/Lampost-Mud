angular.module('lampost_editor').controller('ObjectListCtrl', ['$scope', 'lmEditor', 'lmDialog', 'lmBus',
    function ($scope, lmEditor, lmDialog, lmBus) {

        $scope.type = $scope.editor.childType;
        $scope.areaId = $scope.editor.parent;
        $scope.ready = false;
        loadObjects();

        lmBus.register('area_updated', angular.noop, $scope);

        $scope.deleteObject = function(event, object) {
            event.preventDefault();
            event.stopPropagation();
            lmEditor.deleteObject($scope.type, object.dbo_id)
        };

        $scope.showNewDialog = function() {
            lmDialog.show({templateUrl:'editor/dialogs/new_' + $scope.type + '.html', controller:"NewObjectCtrl",
                locals:{type:$scope.type, areaId:$scope.areaId}});
        };

        function loadObjects() {
            lmEditor.loadObjects($scope.type, $scope.areaId).then(function(objects) {
                angular.forEach(objects, function(object) {
                    object.objectId = object.dbo_id.split(':')[1]
                });
                $scope.objects = objects;
                $scope.ready = true;
            }, function() {
                lmEditor.closeEditor($scope.editor)
            });
        }

    }]);

angular.module('lampost_editor').controller('NewObjectCtrl', ['$scope', 'lmRemote', 'lmEditor', 'type', 'areaId',
    function ($scope, lmRemote, lmEditor, type, areaId) {

        $scope.areaId = areaId;
        $scope.errorText = null;
        $scope.newObject = lmEditor.newObject(type);

        $scope.createObject = function () {
            lmRemote.request('editor/' + type + '/create', {area_id:areaId, object:$scope.newObject}).then(function (object) {
                lmEditor.objectAdded(type, object);
                $scope.dismiss();
            }, function (error) {
                $scope.errorText = error.text;
            })
        };

        $scope.dirty = function() {
            $scope.errorText = null;
        }
    }
]);

angular.module('lampost_editor').controller('ObjectEditorCtrl', ['$scope', 'lmBus', 'lmRemote', 'lmEditor', '$timeout',
    function ($scope, lmBus, lmRemote, lmEditor, $timeout) {

        var copy = {};
        var type = $scope.editor.type;
        $scope.objectDirty = false;
        $scope.dirty = function() {
            $scope.objectDirty = true;
            $scope.showResult = false;
        };
        $scope.objectId = $scope.editor.parent;

        updateData();

        $scope.updateObject = function() {
            updateAliases();
            lmRemote.request($scope.editor.url + "/update", {object_id:$scope.objectId, model:$scope.model}).then(function (model) {
              lmEditor.updateObject(type, model);
              $scope.objectDirty = false;
              $scope.model = model;
              $scope.editor.copyToModel($scope);
              appendAliases();
            })
        };

        $scope.deleteObject = function() {
            lmEditor.deleteObject(type, $scope.objectId);
        };

        $scope.revertObject = function() {
            $scope.model = copy;
            appendAliases();
        };

        $scope.addNewAlias = function() {
            $scope.editAliases.push({title:''});
            $timeout(function () {
                jQuery('.alias-row:last', '.' + $scope.editor.parentClass).focus();
            })
        };

        $scope.deleteAlias = function(index) {
            $scope.editAliases.splice(index, 1);
            $scope.dirty();
        };

        function updateData() {
            $scope.ready = false;
            lmRemote.request($scope.editor.url + "/get", {object_id:$scope.objectId}).then(function (model) {
                if (model.dbo_rev > $scope.editor.model_rev) {
                    $scope.model = model;
                    $scope.editor.copyToModel($scope);
                    $scope.editor.model_rev = model.dbo_rev;
                    lmEditor.updateObject(type, model);
                } else {
                    $scope.editor.copyFromModel($scope);
                }
                appendAliases();
                copy = jQuery.extend(true, {}, $scope.model);
                $scope.ready = true;
            });
        }

        function appendAliases() {
            $scope.editAliases = [];
            angular.forEach($scope.model.aliases, function(alias) {
                $scope.editAliases.push({title:alias});
            });
        }

        function updateAliases() {
            $scope.model.aliases = [];
            angular.forEach($scope.editAliases, function(alias) {
               if (alias.title) {
                   $scope.model.aliases.push(alias.title);
               }
            });
        }
    }]);
