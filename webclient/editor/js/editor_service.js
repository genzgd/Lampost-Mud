angular.module('lampost_editor').service('lpEditor',
  ['$q', 'lpUtil', 'lpRemote', 'lpDialog', 'lpCache', 'lpEvent', 'contextDefs',
  function ($q, lpUtil, lpRemote, lpDialog, lpCache, lpEvent, contextDefs) {

    var lpEditor = this;
    var contextMap = {};

    function EditContext(id, init) {
      angular.copy(init, this);
      this.id = id;
      this.url = this.url || id;
      this.label = this.label || lpUtil.capitalize(id);
      this.plural = this.plural || this.label + 's';
      this.baseUrl = 'editor/' + this.url + '/';
      this.objLabel = this.objLabel || this.label;
      this.include = this.include || 'editor/view/' + id + '.html';
      this.extend = this.extend || angular.noop;
      this.preReqs = this.preReqs || {};
    }

    EditContext.prototype.newModel = function () {
      var model = angular.copy(this.newObj);
      model.can_write = true;
      model.owner_id = lpEditor.playerId;
      this.extend(model);
      return model;
    };

    EditContext.prototype.preCreate = function (model) {
      model.dbo_id = model.dbo_id.toString().toLocaleLowerCase();
      if (model.dbo_id.indexOf(':') > -1) {
        return $q.reject("Colons not allowed in base ids");
      }
      if (model.dbo_id.indexOf(' ') > -1) {
        return $q.reject("No spaces allowed in ids");
      }

      if (this.parentType) {
        if (this.parent) {
          model.dbo_id = this.parent.dbo_id + ':' + model.dbo_id;
        } else {
          return $q.reject("No parent " + this.parentType + " set.")
        }
      }
      return $q.when();
    };

    function contextInit(contextId) {
      var context = contextMap[contextId];
      if (context.metadata) {
        return $q.when();
      }

      return (lpRemote.request('editor/' + context.url + '/metadata').then(function(data) {
        context.parentType = data.parent_type;
        if (data.children_types && data.children_types.length) {
          context.childrenTypes = data.children_types;
        }
        context.newObj = data.new_object;
        context.perms = data.perms;
        context.metadata = true;
      }));
    }

    angular.forEach(contextDefs, function(context, contextId) {
      contextMap[contextId] = new EditContext(contextId, context);
    });

    this.init = function (data) {
      this.playerId = data.playerId;
      this.immLevel = data.imm_level;
      lpCache.clearAll();
      var promises = [];
      promises.push(lpRemote.request('editor/constants').then(function (constants) {
        lpEditor.constants = constants;
      }));
      promises.push(lpCache.cache('immortal').then(function(immortals) {
        lpEditor.immortals = immortals;
      }));
      return $q.all(promises);
    };

    this.initView = function(contexts) {
      var requests = [];
      angular.forEach(contexts, function(contextId) {
        requests.push(contextInit(contextId));
        angular.forEach(contextMap[contextId].preReqs.context, function(contextId) {
          requests.push(contextInit(contextId));
        });
        angular.forEach(contextMap[contextId].preReqs.cache, function(contextId) {
          requests.push(lpCache.cache(contextId));
        });
      });
      return $q.all(requests);
    };

    this.getContext = function (contextId) {
      return contextMap[contextId];
    };

    this.translateError = function (error) {
      if (error.id == 'ObjectExists') {
        return "The object id " + error.text + " already exists";
      }
      if (error.id == 'NonUnique') {
        return "The name " + error.text + "is already in use";
      }
      return error.text || error;
    };

    this.deleteModel = function (context, model, error) {
      lpRemote.request(context.baseUrl + 'test_delete', {dbo_id: model.dbo_id}).then(function (holders) {
        var extra = '';
        if (holders.length > 0) {
          extra = "<br/><br/>This object will be removed from:<br/><br/><div> " + holders.join(' ') + "</div>";
        }
        lpDialog.showConfirm("Delete " + context.objLabel,
            "Are you certain you want to delete " + context.objLabel + " " + model.dbo_id + "?" + extra).then(
          function () {
            lpRemote.request(context.baseUrl + 'delete_obj', {dbo_id: model.dbo_id}).then(function () {
              lpCache.deleteModel(model);
            }, error);
          });
      });
    };

    this.display = function (model) {
      return model.name || model.title || (model.dbo_id || model.dbo_id === 0) && model.dbo_id.toString() || '-new-';
    };

    lpEvent.register('modelDelete', function(delModel) {
      angular.forEach(contextMap, function (context) {
        if (context.parent == delModel) {
          context.parent = null;
          lpEvent.dispatch('contextUpdate', context);
        }
      })
    });

    lpEvent.register('modelSelected', function (activeModel, selectType) {
      angular.forEach(contextMap, function (context) {
        if (context.parentType === activeModel.dbo_key_type) {
          context.parent = activeModel;
        }
      });
      lpEvent.dispatch('activeUpdated', activeModel, selectType);
    });

    /*  config: new lpEditContext({label: "Mud Config", url: "config"}),
     display: {label: "Display", url: "display"},
     imports: {label: "Imports"} */

  }]);


angular.module('lampost_editor').factory('contextDefs', ['$q', function($q) {

  return {
    no_item: {metadata: true},
    area: {},
    room:  {
      nameProp: 'title',
      refs: [
        {type: 'room', path: 'exits.destination'},
        {type: 'mobile', path: 'mobile_resets.mobile'},
        {type: 'article', path: 'article_resets.article'},
        {type: 'script', path: 'shadow_refs.script'}
      ],
      extend: function(model) {
        model.dbo_id = this.parent.next_room_id;
      }
    },
    mobile: {
      preReqs: {cache: ['attack', 'defense']}
    },
    article: {
      preReqs: {cache: ['attack', 'defense']}
    },
    script: {
      nameProp: 'title'
    },
    social: {},
    race: {
      preReqs: {context: ['room'], cache:['attack', 'defense']}
    },
    attack: {
      preUpdate: function (attack) {
        if (attack.damage_type == 'weapon' && attack.weapon_type == 'unused') {
          return $q.reject("Damage type of weapon with 'Unused' weapon is invalid.");
        }
        return $q.when();
      }
    },
    defense: {
      preUpdate: function(defense) {
        if (!defense.auto_start && !defense.verb) {
          return $q.reject("Either a command or 'autoStart' is required.");
        }
        return $q.when();
      }
    },
    user: {nameProp: 'user_name'},
    player: {
      preReqs: {context: ['room']}
    }
  }
}]);
