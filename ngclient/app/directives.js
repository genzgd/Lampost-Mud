lampost.directive("enterKey", function() {
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            element.bind('keypress', function(event) {
                if (event.keyCode == 13) {
                    scope.$eval(attrs.enterKey);
                    event.preventDefault();
                    return false;
                }
            })
        }
    }
});

lampost.directive('scrollBottom', function() {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            scope.$watch(attrs.scrollBottom, function(newValue, oldValue) {
                element.scrollTop(element[0].scrollHeight);
            })
        }
    };
})

lampost.directive("prefFocus", ['$rootScope', '$timeout', function($rootScope, $timeout) {
    return {
        restrict: "ACE",
        link: function(scope, element) {
            scope.$on("refocus", forceFocus);

            var timer = $timeout(forceFocus, 0);

            function forceFocus() {
                $timeout.cancel(timer);
                element.focus();
            }

        }

    }
}]);