angular.module('lampost_dlg', []).service('lpDialog', ['$q', '$rootScope', '$compile', '$controller', '$templateCache', '$timeout', '$http',
  function ($q, $rootScope, $compile, $controller, $templateCache, $timeout, $http) {

    var dialogMap = {};
    var nextId = 0;
    var prevElement;
    var enabledElements;
    var enabledLinks;

    function showDialog(args) {
      var dialogId = "lpDialog_" + nextId++;
      if (args.templateUrl) {
        $http.get(args.templateUrl, {cache: $templateCache}).then(
          function (response) {
            args.template = response.data;
            showDialogTemplate(args, dialogId);
          });
      } else {
        showDialogTemplate(args, dialogId);
      }
      return dialogId;
    }

    function disableUI() {
      prevElement = $(document.activeElement);
      enabledElements = $('button:enabled, selector:enabled, input:enabled, textarea:enabled');
      enabledLinks = $('a[href]');
      enabledElements.attr('disabled', true);
      enabledLinks.each(function () {
        $(this).attr("data-oldhref", $(this).attr("href"));
        $(this).removeAttr("href");
      })
    }

    function enableUI() {
      enabledElements.filter(':not([_lp_disabled])').removeAttr('disabled');
      enabledLinks.each(function () {
        $(this).attr("href", $(this).attr("data-oldhref"));
        $(this).removeAttr("data-oldhref");
      });
      $timeout(function () {
        if (prevElement.closest('html').length) {
          prevElement.focus();
        } else {
          $rootScope.$broadcast("refocus");
        }
      }, 0);
    }

    function showDialogTemplate(args, dialogId) {
      var element = angular.element(args.template);
      var dialog = {};
      var dialogScope = args.scope || $rootScope.$new(true);
      if ($.isEmptyObject(dialogMap)) {
        disableUI();
      }

      dialog.id = dialogId;
      dialog.element = element;
      dialog.scope = dialogScope;
      dialog.valid = true;
      dialogScope.dismiss = function () {
        element.modal("hide");
      };
      dialogMap[dialog.id] = dialog;

      var link = $compile(element.contents());
      if (args.controller) {
        var locals = args.locals || {};
        locals.$scope = dialogScope;
        locals.dialog = dialog;
        var controller = $controller(args.controller, locals);
        element.contents().data('$ngController', controller);
      }

      link(dialogScope);
      function destroy() {
        if (!dialogMap[dialog.id]) {
          return;
        }
        dialog.scope.finalize && dialog.scope.finalize();
        delete dialogMap[dialog.id];
        dialog.element.remove();
        if ($.isEmptyObject(dialogMap)) {
          enableUI();
        }
        $timeout(function () {
          dialog.scope.$destroy();
          dialog = null;
        });
      }

      element.on('hidden.bs.modal', function () {
        destroy();
      });
      element.on('shown.bs.modal', function () {
        var focusElement = $('input:text:visible:first', element);
        if (!focusElement.length) {
          focusElement = $(".lmdialogfocus" + dialog.id + ":first");
        }
        focusElement.focus();
      });
      $timeout(function () {
        if (!dialog.valid) {
          destroy();
          return;
        }
        var modalOptions = {show: true, keyboard: !args.noEscape,
          backdrop: args.noBackdrop ? false : (args.noEscape ? "static" : true)};
        element.modal(modalOptions);
      }, 20);
    }

    function closeDialog(dialogId) {
      var dialog = dialogMap[dialogId];
      if (dialog) {
        dialog.valid = false;
        dialog.element.modal("hide");
      }
    }

    this.show = function (args) {
      return showDialog(args);
    };

    this.close = function (dialogId) {
      closeDialog(dialogId);
    };

    this.removeAll = function () {
      for (var dialogId in dialogMap) {
        closeDialog(dialogId);
      }
    };

    this.showAlert = function(options, noEscape) {
      showDialog({templateUrl: 'common/dialogs/alert.html',
        scope: angular.extend($rootScope.$new(), options),
        controller: AlertCtrl, noEscape: noEscape});
    };

    this.showOk = function (title, body) {
      this.showAlert({title: title, body: body,
          buttons: [{label: 'OK', default: true, dismiss: true, class: "btn-primary"}]});
    };

    this.showConfirm = function (title, body) {
      var deferred = $q.defer();
      this.showAlert({title: title, body: body, onCancel: deferred.reject,
        buttons: [{label: 'Yes', dismiss: true, class: 'btn-danger', click: deferred.resolve},
        {label: "No", class: 'btn-primary', default: true, cancel: true}]
      }, true);
      return deferred.promise;
    };

    this.showPrompt = function (args) {
      var scope = $rootScope.$new();
      scope.submit = args.submit;
      scope.promptValue = "";
      scope.title = args.title;
      scope.prompt = args.prompt;
      scope.inputType = args.password ? "password" : "text";
      scope.onCancel = args.onCancel;
      scope.doSubmit = function () {
        scope.submit.call(scope, scope.promptValue);
        scope.dismiss();
      };
      showDialog({templateUrl: 'common/dialogs/prompt.html', scope: scope,
        noEscape: true});
    };

    function AlertCtrl($scope, dialog) {
      $scope.click = function (button) {
        button.click && button.click();
        button.cancel && $scope.cancel();
        button.dismiss && $scope.dismiss();
      };

      $scope.cancel = function() {
        $scope.onCancel && $scope.onCancel();
        $scope.dismiss();
      };

      for (var i = 0; i < $scope.buttons.length; i++) {
        var button = $scope.buttons[i];
        if (button.default) {
          var focusClass = " lmdialogfocus" + dialog.id;
          button.class = button.class && button.class + focusClass || focusClass;
        }
      }
    }

  }]);
