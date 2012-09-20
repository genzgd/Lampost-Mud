angular.module('lampost_edit').controller('MobilesEditorController', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog', 'lmBus',
    function ($scope, lmRemote, lmEditor, lmDialog, lmBus) {

        $scope.areaId = $scope.editor.parent;
        $scope.ready = false;
        loadMobiles();

        lmBus.register('mobile_updated', function() {}, $scope);

        $scope.deleteMobile = function(event, mobile) {
            event.preventDefault();
            event.stopPropagation();
            lmEditor.deleteMobile(mobile.dbo_id)
        };

        $scope.showNewDialog = function() {
            lmDialog.show({templateUrl:"dialogs/new_mobile.html", controller:"NewMobileController",
                locals:{parentScope:$scope}});
        };

        $scope.mobileCreated = function(mobile) {
            lmEditor.mobileAdded(mobile);
        };

        $scope.editMobile = function(mobile) {
            lmEditor.addEditor('mobile', mobile.dbo_id);
        };

        function loadMobiles() {
            lmEditor.loadMobiles($scope.areaId).then(function(mobiles) {
                $scope.mobiles = mobiles;
                $scope.ready = true;
            }, function() {
                lmEditor.closeEditor($scope.editor)
            });
        }

    }]);

angular.module('lampost_edit').controller('NewMobileController', ['$scope', 'lmRemote', 'parentScope',
    function ($scope, lmRemote, parentScope) {

        $scope.areaId = parentScope.areaId;
        $scope.errorText = null;
        $scope.newMobile = {id:'', title:'', desc:'', level:1};

        $scope.createMobile = function () {
            lmRemote.request('editor/mobile/create', {area_id:$scope.areaId, mobile:$scope.newMobile}).then(function (mobile) {
                parentScope.mobileCreated(mobile);
                $scope.dismiss();
            }, function (error) {
                if (error.status == 410) {
                    $scope.errorText = error.data;
                }
            })
        };

        $scope.dirty = function() {
            $scope.errorText = null;
        }
    }
]);

angular.module('lampost_edit').controller('MobileEditorController', ['$scope', 'lmBus', 'lmRemote', 'lmEditor', '$timeout',
    function ($scope, lmBus, lmRemote, lmEditor, $timeout) {

        var mobileCopy = {};
        $scope.mobileDirty = false;
        $scope.dirty = function() {
            $scope.mobileDirty = true;
            $scope.showResult = false;
        };
        $scope.mobileId = $scope.editor.parent;


        updateData();

        $scope.updateMobile = function() {
            updateAliases();
            lmRemote.request($scope.editor.url + "/update", {mobile_id:$scope.mobileId, mobile:$scope.mobile}).then(function (mobile) {
              lmEditor.updateMobile(mobile);
              $scope.mobileDirty = false;
              $scope.mobile = mobile;
              $scope.editor.copyToModel($scope);
              appendAliases();
            })
        };

        $scope.deleteMobile = function() {
            lmEditor.deleteMobile($scope.mobileId);
        };

        $scope.revertMobile = function() {
            $scope.mobile = mobileCopy;
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
            lmRemote.request($scope.editor.url + "/get", {mobile_id:$scope.mobileId}).then(function (mobile) {
                if (mobile.dbo_rev > $scope.editor.model_rev) {
                    $scope.mobile = mobile;
                    $scope.editor.copyToModel($scope);
                    $scope.editor.model_rev = mobile.dbo_rev;
                    lmEditor.updateMobile(mobile);
                } else {
                    $scope.editor.copyFromModel($scope);
                }
                appendAliases();
                mobileCopy = jQuery.extend(true, {}, $scope.mobile);
                $scope.ready = true;
            });
        }

        function appendAliases() {
            $scope.editAliases = [];
            angular.forEach($scope.mobile.aliases, function(alias) {
                $scope.editAliases.push({title:alias});
            });
        }

        function updateAliases() {
            $scope.mobile.aliases = [];
            angular.forEach($scope.editAliases, function(alias) {
               if (alias.title) {
                   $scope.mobile.aliases.push(alias.title);
               }
            });
        }
    }]);
