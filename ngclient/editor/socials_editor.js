angular.module('lampost_editor').controller('SocialsEditorController', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog', 'lmBus',
    function ($scope, lmRemote, lmEditor, lmDialog, lmBus) {

        $scope.social = {};
        $scope.social_valid = false;

        $scope.editSocials = function(social_id) {
            LmRemote.request($scope.editor.url + '/get', {social_id:social_id}, true).then(function (social) {
                if (social) {
                    editSocial(social);
                }
                else {
                    alert("Social does not exist");
                }
            })
        };

        $scope.showNewSocialDialog = function() {
            lmDialog.show({templateUrl:'editor/dialogs/new_social.html', controller:"NewSocialController",
                locals:{updateFunc:newSocial}});
        };

        lmBus.register("editor_activated", function(editor) {
            if (editor == $scope.editor) {
                loadSocials();
            }
        });

        function loadSocials() {
            $scope.ready = false;
            lmRemote.request($scope.editor.url + '/list', null, true).then(function(socials) {
                $scope.socials = socials;
                $scope.socials.sort();
                $scope.ready = true;
            });
        }

        function newSocial(social) {
            $scope.socials.push(social.social_id);
            $scope.socials.sort();
            editSocial(social);
        }

        function editSocial(social) {
            $scope.social = social;
            $scope.social_valid = true;
        }


    }]);

angular.module('lampost_editor').controller('NewSocialController', ['$scope', 'lmRemote', 'updateFunc',
    function($scope, lmRemote, updateFunc) {

        $scope.social = {social_id:"", map:{}};

        $scope.changeSocial = function() {
            $scope.social.social_id = $scope.social.social_id.replace(' ', '');
            $scope.social.social_id = $scope.social.social_id.toLocaleLowerCase();
            $scope.social.map.s = 'You ' + $scope.social.social_id + '.';
            $scope.socialExists = false;
        };

        $scope.createSocial = function () {
            lmRemote.request('editor/socials/valid', {social_id:$scope.social.social_id}, true).then(function() {
                lmRemote.request($scope.editor.url + "/update", $scope.social).then( function() {
                    $scope.dismiss();
                    updateFunc(social);
                })
            }, function() {
                $scope.socialExists = true;
            })
        }


    }]);