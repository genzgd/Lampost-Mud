angular.module('lampost_editor').service('lpCache', ['$q', 'lpEvent', 'lpRemote', 'lpUtil',
  function ($q, lpEvent, lpRemote, lpUtil) {

    var lpCache = this;
    var cacheHeap = [];
    var cacheHeapSize = 32;
    var remoteCache = {};

    var cacheSorts = {
      room: numericIdSort
    };

    function cacheEntry(key) {
      var keyParts = key.split(':');
      var keyType = keyParts[0];
      var url = keyType + '/list' + (keyParts[1] ? '/' + keyParts[1] : '');
      var entry = {ref: 0, sort: cacheSorts[keyType] || idSort, url: url};
      remoteCache[key] = entry;
      return entry;
    }

    function cacheKey(model) {
      var cacheKey = (model.dbo_key_type + ':' + model.dbo_id).split(":");
      return cacheKey.slice(0, cacheKey.length - 1).join(':');
    }

    function idSort(values) {
      lpUtil.stringSort(values, 'dbo_id')
    }

    function numericIdSort(values) {
      values.sort(function (a, b) {
        var aid = parseInt(a.dbo_id.split(':')[1]);
        var bid = parseInt(b.dbo_id.split(':')[1]);
        return aid - bid;
      })
    }

    function deleteEntry(key) {
      var heapIx = cacheHeap.indexOf(key);
      if (heapIx > -1) {
        cacheHeap.splice(heapIx, 1);
      }
      delete remoteCache[key];
    }

    function parentList(model) {
      if (model.dbo_parent_type) {
        entry = remoteCache[model.dbo_parent_type];
        if (entry && !entry.promise) {
          var parent = entry.map[model.dbo_id.split(':')[0]];
          if (parent) {
            return parent[model.dbo_key_type + '_list'];
          }
        }
      }
    }

    lpEvent.register('edit_update', function (event) {
      var outside = !event.local;
      switch (event.edit_type) {
        case 'update':
          lpCache.updateModel(event.model, outside);
          break;
        case 'create':
          lpCache.insertModel(event.model, outside);
          break;
        case 'delete':
          lpCache.deleteModel(event.model, outside);
          break;
      }
    });

    this.clearAll = function() {
      cacheHeap = [];
      remoteCache = {};
      lpEvent.dispatch('cacheCleared');
    };

    this.invalidate = function (key) {
      deleteEntry(key)
    };

    this.cacheValue = function (dbo_id) {
      var parts = dbo_id.split(':');
      var size = parts.length;
      var list_key = parts.slice(0, size - 1).join(':');
      var item_key = parts.slice(1, size).join(':');
      if (remoteCache[list_key]) {
        return remoteCache[list_key].map[item_key];
      }
    };

    this.deref = function (key) {
      if (!key) {
        return;
      }
      var entry = remoteCache[key];
      if (!entry) {
        return;
      }
      entry.ref--;
      if (entry.ref === 0) {
        cacheHeap.unshift(key);
        for (var i = cacheHeap.length; i >= cacheHeapSize; i--) {
          var oldEntry = remoteCache[cacheHeap.pop()];
          delete oldEntry.map;
          delete oldEntry.data;
        }
      }
    };

    this.updateModel = function (model, outside) {
      var entry = remoteCache[cacheKey(model)];
      if (entry) {
        var cacheModel = entry.map[model.dbo_id];
        if (cacheModel) {
          angular.copy(model, cacheModel);
          lpEvent.dispatch('modelUpdate', cacheModel, outside);
        }
      }
    };

    this.insertModel = function (model, outside) {
      var entry = remoteCache[cacheKey(model)];
      if (entry && !entry.promise) {
        if (entry.map[model.dbo_id]) {
          updateModel(model, outside);
        } else {
          entry.data.push(model);
          entry.sort(entry.data);
          entry.map[model.dbo_id] = model;
          lpEvent.dispatch('modelCreate', model, outside);
        }
      }
      var plist = parentList(model);
      if (plist) {
        plist.push(model.dbo_id);
        plist.sort();
        lpEvent.dispatch('childListUpdate', model.dbo_parent_type, model.dbo_key_type);
      }
    };

    this.deleteModel = function (model, outside) {
      var ix;
      var entry = remoteCache[cacheKey(model)];
      if (entry && !entry.promise) {
        var cacheModel = entry.map[model.dbo_id];
        if (cacheModel) {
          entry.data.splice(entry.data.indexOf(cacheModel), 1);
          delete entry.map[model.dbo_id];
          lpEvent.dispatch('modelDelete', model, outside);
        }
      }

      angular.forEach(model.dbo_children_types, function (cType) {
        var childList = model[cType + "_list"];
        for (ix = 0; ix < childList.length; ix++) {
          var key = childList[ix];
          var childModels = remoteCache[key];
          if (childModels) {
            for (var ic = 0; ic < childModels.length; ic++) {
              lpEvent.dispatch('modelDelete', childModels[ic], outside);
            }
          }
          deleteEntry[key];
        }
      });

      var plist = parentList(model);
      if (plist) {
        ix = plist.indexOf(model.dbo_id);
        if (ix > -1) {
          plist.splice(ix, 1);
          lpEvent.dispatch('childListUpdate', model.dbo_parent_type, model.dbo_key_type);
        }
      }
    };

    this.cache = function (key) {
      var entry = remoteCache[key] || cacheEntry(key);
      if (entry.data) {
        if (entry.ref === 0) {
          cacheHeap.splice(cacheHeap.indexOf(key), 1);
        }
        entry.ref++;
        return $q.when(entry.data);
      }

      if (entry.promise) {
        entry.ref++;
        return entry.promise;
      }
      entry.promise = lpRemote.request('editor/' + entry.url).then(function (data) {
        delete entry.promise;
        entry.ref++;
        entry.data = data;
        entry.map = {};
        for (var i = 0; i < data.length; i++) {
          entry.map[data[i].dbo_id] = data[i];
        }
        entry.sort(entry.data);
        return $q.when(entry.data);
      });
      return entry.promise;
    };

    this.seedCacheId = function(dboId, promises) {

      var parts = dboId.split(':');
      var size = parts.length;
      if (size == 2) {
        return lpCache.cache(parts[0]);
      }
      return lpCache.cache(parts[0] + ':' + parts[1]);
    }

    this.seedCache = function (refs, baseModel, cacheKeys) {

      var promises = [];

      function childRefs(refType, refPath, model) {
        var ix;
        var pieces = refPath.split('.');
        var children = model[pieces[0]];
        if (!children) {
          return;
        }
        children = [].concat(children);
        if (pieces.length === 1) {
          for (ix = 0; ix < children.length; ix++) {
             var childKey = refType + ':' + children[ix].split(":")[0];
             if (cacheKeys.indexOf(childKey) == -1) {
              cacheKeys.push(childKey);
              promises.push(lpCache.cache(childKey));
            }
          }
        } else {
          refPath = pieces.slice(1).join('.');
          for (ix = 0; ix < children.length; ix++) {
            childRefs(refType, refPath, children[ix]);
          }
        }
      }

      angular.forEach(refs, function(ref) {
        if (ref.path) {
          childRefs(ref.type, ref.path, baseModel);
        } else {
          promises.push(lpCache(cache(ref.type)));
        }
      });

      return promises;
    }

  }]);