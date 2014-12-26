angular.module('lampost_editor').filter('hasRooms', ['$filter', function($filter) {

    return function(items) {
        return $filter('filter')(items, function(value) {
            return value.room_list.length;
        });
    }
}]);

angular.module('lampost_editor').filter('immTitle', ['lpUtil', 'lpEditor', function(lpUtil, lpEditor) {

    var map = {};
    angular.forEach(lpEditor.constants.imm_titles, function(level, title) {
      map[level] = lpUtil.capitalize(title);
    })

    return function(model) {
       return map[model.imm_level];
    }
}]);