angular.module('lampost_editor').filter('hasRooms', ['$filter', function($filter) {

    return function(items) {
        return $filter('filter')(items, function(value) {
            return value.room_list.length;
        });
    }
}]);