angular.module('lampost_editor').service('lpEditFilters', [function() {

  this.hasChild = function (filterType) {
    return function (items) {
      var result = [];
      angular.forEach(items, function (item) {
        if (item[filterType + "_list"].length) {
          result.push(item);
        }
      });
      return result;
    }
  }
}]);

angular.module('lampost_editor').filter('immTitle', ['lpUtil', 'lpEditor', function(lpUtil, lpEditor) {

    var map = {};
    angular.forEach(lpEditor.constants.imm_levels, function(level, title) {
      map[level] = lpUtil.capitalize(title);
    });

    return function(model) {
       return map[model.imm_level];
    }
}]);
