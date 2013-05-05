angular.module('lampost_editor').controller('SocialsEditorCtrl', ['$scope', 'lmRemote', 'lmEditor', 'lmDialog', 'lmBus',
    function ($scope, lmRemote, lmEditor, lmDialog, lmBus) {

        lmBus.register("editor_activated", function(editor) {
            if (editor == $scope.editor) {
                loadSocials();
            }
        });

        var oldMap;
        var originalId;

        $scope.social = {};
        $scope.social_valid = false;
        $scope.displayMode = 'edit';
        $scope.source = 'Player';
        $scope.target = 'Target';
        $scope.sourceSelf = false;

        $scope.editSocial = function(social_id) {
            if (mapDiff()) {
                lmDialog.showConfirm("Social Edited", "Changes to this social will be lost.  Continue anyway?",
                    function() {
                        startEdit(social_id);
                    })
            } else {
                startEdit(social_id);
            }
        };

        $scope.copySocial = function(event, social_ix) {
            event.preventDefault();
            event.stopPropagation();
            originalId = $scope.socials[social_ix];
            lmDialog.showPrompt({title:"Copy Social", prompt:"New Social", submit:submitCopy});
        };



        $scope.socialRowClass = function(social) {
            if ($scope.social_valid && social == $scope.social.social_id) {
                return "highlight";
            }
            return "";
        };

        $scope.previewSocial = function() {
            lmRemote.request($scope.editor.url + '/preview', {target:$scope.target, self_source:$scope.sourceSelf,
                source:$scope.source, b_map:$scope.social.b_map})
                .then( function(preview) {
                   $scope.preview = preview;
                    $scope.displayMode = 'view';
                });
        };

        $scope.showNewSocialDialog = function() {
            lmDialog.show({templateUrl:'editor/dialogs/new_social.html', controller:"NewSocialCtrl",
                locals:{updateFunc:newSocial}});
        };

        $scope.deleteSocial = function(event, social_ix) {
            event.preventDefault();
            event.stopPropagation();
            var delSocial = $scope.socials[social_ix];
            lmDialog.showConfirm("Delete Social", "Are you sure you want to delete " + delSocial + "?", function() {
                lmRemote.request($scope.editor.url + '/delete', {social_id:delSocial}, true).then(function() {
                    $scope.socials.splice(social_ix, 1);
                    if ($scope.social && delSocial == $scope.social.social_id) {
                        $scope.social = null;
                        $scope.social_valid = false;
                    }
                })
            });
            return false;
        };

        $scope.revertSocial = function() {
            $scope.social.b_map = oldMap;
        };

        $scope.saveSocial = function() {
            lmRemote.request('editor/socials/update', $scope.social).then( function() {
                $scope.social_valid = false;
            });
        };

        function submitCopy(copy_id) {
            lmRemote.request($scope.editor.url + "/copy", {original_id:originalId, copy_id:copy_id}).
                then(function(new_social) {
                    $scope.socials.push(copy_id);
                    $scope.socials.sort();
                    if (!$scope.social_valid || !mapDiff()) {
                        new_social.social_id = copy_id;
                        editSocial(new_social);
                    }
                });
        }

        function startEdit(social_id) {
            lmRemote.request($scope.editor.url + '/get', {social_id:social_id}, true).then(function (social) {
                if (social) {
                    social.social_id = social_id;
                    editSocial(social);
                }
                else {
                    alert("Social does not exist");
                }
            })
        }

        function mapDiff() {
            if (!$scope.social_valid) {
                return false;
            }
            var matched = true;
            angular.forEach($scope.constants.broadcast_types, function(broadcast_type) {
                var id = broadcast_type.id;

                if (!$scope.social.b_map[id] && !oldMap[id]) {
                    return;
                }
                if ($scope.social.b_map[id] == oldMap[id]) {
                    return;
                }
                matched = false;
            });
            return !matched;
        }

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
            oldMap = jQuery.extend(true, {}, social.b_map);
            $scope.social = social;
            $scope.social_valid = true;
            if ($scope.displayMode == 'view') {
                $scope.previewSocial();
            }
        }


    }]);

angular.module('lampost_editor').controller('NewSocialCtrl', ['$scope', 'lmRemote', 'updateFunc',
    function($scope, lmRemote, updateFunc) {

        $scope.social = {social_id:"", b_map:{}};

        $scope.changeSocial = function() {
            $scope.social.social_id = $scope.social.social_id.replace(' ', '');
            $scope.social.social_id = $scope.social.social_id.toLocaleLowerCase();
            $scope.social.b_map.s = 'You ' + $scope.social.social_id + '.';
            $scope.socialExists = false;
        };

        $scope.createSocial = function () {
            lmRemote.request('editor/socials/valid', {social_id:$scope.social.social_id}).then( function() {
                lmRemote.request('editor/socials/update', $scope.social).then( function() {
                    $scope.dismiss();
                    updateFunc($scope.social);
                })
                }, function() {
                    $scope.socialExists = true;
                })
        };



    }]);
