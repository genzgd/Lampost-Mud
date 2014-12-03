angular.module('lampost_editor').controller('BuildViewCtrl', ['$scope', 'lpEvent', 'lpEditor',
  function ($scope, lpEvent, lpEditor) {

    var editArea = null;

    lpEditor.reset();

    lpEditor.registerContext('area', {
      extend: function (model) {
        model.next_room_id = 0;
      }
    });

    lpEditor.registerContext('room', {
      parentType: 'area',
      extend: function (model) {
        angular.extend(model, {dbo_id: this.parent.next_room_id, exits: [], mobile_resets: [],
          article_resets: [], extras: [], features: []});
      },
      refs: [
        {type: 'room', path: 'exits.destination'}
      ]
    });

    lpEditor.registerContext('mobile', {
      parentType: 'area',
      extend: function (model) {
        model.level = 1;
        model.affinity = 'neutral';
      }
    });

    $scope.activeArea = function () {
      return editArea ? editArea.name : '-NOT SET-';
    };


    $scope.newEditor = function (editorId, event) {
      if (event) {
        event.preventDefault();
        event.stopPropagation();
      }
      lpEvent.dispatch('newEdit', editorId);
    }


  }]);