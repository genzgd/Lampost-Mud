 angular.module('lampost_editor').controller('EditStoreCtrl', ['$scope', '$filter', function($scope, $filter) {

  var noCurrency = {dbo_id: ':--None--'};
  var noItems = {dbo_id: ':--No Items--'};

  var store_edit = {};
  $scope.store_edit = store_edit;
  store_edit.store = $scope.activeFeature;
  store_edit.currencyParent = store_edit.store.currency ? store_edit.store.currency.split(":")[0] : undefined;
  store_edit.newPerm = noItems.dbo_id;

  $scope.setCurrencyList = function(objects) {
    store_edit.currencyList = $filter('filter')(objects, {divisible: true});
    store_edit.currencyList.unshift(noCurrency);

    for (var ix = 0; ix < store_edit.currencyList.length; ix++) {
      if (store_edit.store.currency == store_edit.currencyList[ix].dbo_id) {
        store_edit.newCurrency = store_edit.store.currency;
        return;
      }
    }
    store_edit.newCurrency = noCurrency.dbo_id;
    store_edit.store.currency = null;
  };


  $scope.setPermList = function (objects) {
    store_edit.permList = $filter('filter')(objects, {divisible: false});
    if (store_edit.permList.length === 0) {
      store_edit.permList = [noItems];
    }
    store_edit.newPerm = store_edit.permList[0].dbo_id;
  };

  $scope.updateCurrency = function() {
    if (store_edit.newCurrency == noCurrency.dbo_id) {
      store_edit.store.currency = null;
    } else {
      store_edit.store.currency = store_edit.newCurrency;
    }
  };

  $scope.addPerm = function() {
    store_edit.store.perm_inven.push(store_edit.newPerm);
  };

  $scope.permExists = function() {
    return store_edit.newPerm === noItems.dbo_id || store_edit.store.perm_inven.indexOf(store_edit.newPerm) > -1;
  };

  $scope.removePerm = function(perm) {
    var ix = store_edit.store.perm_inven.indexOf(perm);
    if (ix > -1) {
      store_edit.store.perm_inven.splice(ix, 1);
    }
  };

}]);


angular.module('lampost_editor').controller('EditEntranceCtrl', ['$scope', 'lpEditFilters', 'lpEditor',
  function($scope, lpEditFilters, lpEditor) {

    $scope.ent_dirs = angular.copy(lpEditor.constants.directions);
    $scope.ent_dirs.unshift({key: 'unused', name: "Use Command"});
    $scope.parentFilter = lpEditFilters.hasChild('room');

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
      if (!$scope.entrance.title && !$scope.entrance.desc) {
        $scope.lastError = "Title and description required.";
        return;
      }
      if ($scope.entrance.direction == 'unused') {
        $scope.entrance.direction = null;
      }
      if ($scope.newAdd) {
        $scope.model.features.push($scope.entrance);
      } else {
        angular.copy($scope.entrance, $scope.activeFeature);
      }
      $scope.closeAdd();
    };

    $scope.$on('addInit', initialize);

    initialize();



}]);
