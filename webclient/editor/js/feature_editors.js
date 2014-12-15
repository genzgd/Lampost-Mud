angular.module('lampost_editor').controller('EditStoreCtrl', ['$scope', '$filter', function($scope, $filter) {

  var noCurrency = {dbo_id: ':--None--'};
  var noItems = {dbo_id: '--No Items--', invalid: true};

  $scope.store = $scope.activeFeature;
  $scope.currencyParent = $scope.store.currency ? $scope.store.currency.split(":")[0] : undefined;
  $scope.newPerm = {};

  $scope.setCurrencyList = function(objects) {
    $scope.currencyList = $filter('filter')(objects, {divisible: true});
    $scope.currencyList.unshift(noCurrency);

    for (var ix = 0; ix < $scope.currencyList.length; ix++) {
      if ($scope.store.currency == $scope.currencyList[ix].dbo_id) {
        $scope.newCurrency = $scope.store.currency;
        return;
      }
    }
    $scope.newCurrency = noCurrency.dbo_id;
    $scope.store.currency = null;
  };


  $scope.setPermList = function (objects) {
    $scope.permList = $filter('filter')(objects, {divisible: false});
    if ($scope.permList.length === 0) {
      $scope.permList = [noItems];
    }
    $scope.newPerm = $scope.permList[0].dbo_id;
  }

  $scope.updateCurrency = function() {
    if ($scope.newCurrency == noCurrency.dbo_id) {
      $scope.store.currency = null;
    } else {
      $scope.store.currency = $scope.newCurrency;
    }
  };

  $scope.addPerm = function() {
    $scope.store.perm_inven.push($scope.newPerm);
  };

  $scope.permExists = function() {
    return $scope.newPerm.invalid || $scope.store.perm_inven.indexOf($scope.newPerm) > -1;
  };

  $scope.removePerm = function(perm) {
    var ix = $scope.store.perm_inven.indexOf(perm);
    if (ix > -1) {
      $scope.store.perm_inven.splice(ix, 1);
    }
  };

}]);


angular.module('lampost_editor').controller('EditEntranceCtrl', ['$scope', 'lpEditor',
  function($scope, lpEditor) {

    $scope.ent_dirs = angular.copy(lpEditor.constants.directions);
    $scope.ent_dirs.unshift({key: 'unused', name: "Use Command"});
    $scope.parentFilter = 'hasRooms';


    function initialize() {
       $scope.entrance = angular.copy($scope.activeFeature);
       $scope.newAdd = !!lpEditor.addObj;
       if (!$scope.entrance.direction) {
        $scope.entrance.direction = 'unused';
       }
    }

    $scope.listChange = function(children) {
      $scope.childList = children;
      $scope.entrance.destination = children[0].dbo_id;
      $scope.destRoom = children[0];
    };

    $scope.checkVerb = function() {
      if ($scope.entrance.verb) {
        $scope.entrance.direction = 'unused';
      }
    };

    $scope.checkDirection = function () {
      if ($scope.entrance.direction != 'unused') {
        $scope.entrance.verb = null;
      }
    };

    $scope.updateRoom = function() {
      $scope.entrance.destination = $scope.destRoom.dbo_id;
    };

    $scope.updateEntrance = function() {
      if ($scope.entrance.direction == 'unused') {
        $scope.entrance.direction = null;
      }
      if ($scope.isAdd) {
        $scope.model.features.push($scope.entrance);
      } else {
        angular.copy($scope.entrance, $scope.activeFeature);
      }
      $scope.closeAdd();
    };

    $scope.$on('addInit', initialize);

    initialize();



}]);
