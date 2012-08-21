lampost.service('lmDialog', ['$rootScope', '$compile', '$controller', '$templateCache',
    '$timeout',  '$http', 'lmLog', function($rootScope, $compile, $controller, $templateCache,
                                            $timeout, $http, lmLog) {

    var dialogMap = {};
    var nextId = 0;

    function showDialog(params) {
        var element = angular.element(params.template);
        var dialog = {};
        var dialogScope = $rootScope.$new();
        jQuery('body').append(element);
        dialog.id = "lmDialog_" + nextId++;
        dialog.element = element;
        dialog.scope = dialogScope;

        var link = $compile(element.contents());

        if (params.controller) {
            var locals = {};
            locals.$scope = dialogScope;
            locals.dialog = dialog;
            var controller = $controller(params.controller, locals);
            element.contents().data('$ngControllerController', controller);
        }
        dialogMap[dialog.id] = dialog;
        link(dialogScope);
        dialogScope.$apply();
        element.on(jQuery.support.transition && 'hidden' || 'hide', destroy);
        var modalOptions = {show: true, keyboard: params.noEscape ? false : true,
            backdrop: params.noBackdrop ? false : (params.noEscape ? "static" : true)};
        element.modal(modalOptions);
        element.attr("id",  dialog.id);
        return dialog.id;
    }

    function destroy(event) {
        var dialogId = event.currentTarget.id
        var dialog = dialogMap[dialogId];
        if (dialog) {
            delete dialogMap[dialogId];
            $timeout(function() {
                dialog.element.remove();
                dialog.scope.$destroy();
            })
        }
    }

    this.show = function(params) {
        if (params.templateUrl) {
            $http.get(params.templateUrl, {cache: $templateCache}).then(
                function(response) {
                    params.template = response.data;
                    showDialog(params);
                });
        } else {
            showDialog(params);
        }
    }

    this.close= function(dialog) {
        var dialog = dialogMap[dialog.id];
        if (dialog) {
            dialog.element.modal("hide");
        }
    }

}]);
