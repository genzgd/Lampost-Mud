angular.module('lampost_editor').service('lpCache', ['$q', '$log', 'lpEvent', 'lpRemote', 'lpUtil',
  function ($q, $log, lpEvent, lpRemote, lpUtil) {

    var lpCache = this;
    var cacheHeap = [];
    var cacheHeapSize = 32;
    var remoteCache = {};

    var cacheSorts = {
      room: numericIdSort,
      user: lpUtil.fieldCmpSort('dbo_id', lpUtil.naturalCmp),
      immortal: lpUtil.fieldCmpSort('dbo_id', lpUtil.naturalCmp)
    };

    function cacheEntry(key) {
      var keyParts, keyType, path, entry;
      keyParts = key.split(':');
      keyType = keyParts[0];
      path = keyType + (keyParts[1] ? '/child_list' : '/list');
      entry = {ref: 0,
        sort: cacheSorts[keyType] || idSort,
        path: path,
        params: keyParts[1] ? {parent_id: keyParts[1]} : {}};
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

    function modelInsert(entry, model, outside) {
      var cacheModel;
      if (cacheModel = entry.map[model.dbo_id]) {
        modelUpdate(model, cacheModel, outside);
      } else {
        entry.data.push(model);
        entry.map[model.dbo_id] = model;
        lpEvent.dispatch('modelCreate', model, outside);
      }
    }

    function modelUpdate(model, cacheModel, outside) {
       angular.copy(model, cacheModel);
       lpEvent.dispatch('modelUpdate', cacheModel, outside);
    }

    function modelDelete(entry, model, outside) {
      var cacheModel;
      if (cacheModel = entry.map[model.dbo_id]) {
        entry.data.splice(entry.data.indexOf(cacheModel), 1);
        delete entry.map[model.dbo_id];
        lpEvent.dispatch('modelDelete', model, outside);
      }
    }

    function parentList(model) {
      var entry;
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

    function deleteChildren(model, outside) {
      angular.forEach(model.dbo_children_types, function (cType) {
        var ix, childList, entry, listKey;
        listKey = cType + ':' + model.dbo_id;
        entry = remoteCache[listKey];
        if (entry && entry.data) {
          childList = entry.data.slice();
          for (ix = 0; ix < childList.length; ix++) {
            lpEvent.dispatch('modelDelete', childList[ix], outside);
          }
          deleteEntry(listKey);
        }
      });
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

    this.cachedValue = function (dbo_key) {
      var parts, size, list_key, item_key;
      parts = dbo_key.split(':');
      size = parts.length;
      list_key = parts.slice(0, size - 1).join(':');
      item_key = parts.slice(1, size).join(':');
      if (remoteCache[list_key]) {
        return remoteCache[list_key].map[item_key];
      }
    };

    this.cachedList = function(key) {
      var entry = remoteCache[key];
      if (entry && entry.data) {
        return entry.data;
      }
      $log.warn('Expected key ' + key + ' not in cache.');
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
      var entry, cacheModel;
      entry = remoteCache[cacheKey(model)];
      if (entry) {
        if (cacheModel = entry.map[model.dbo_id]) {
          modelUpdate(model, cacheModel, outside);
        }
      }
    };

    this.insertModel = function (model, outside) {
      var entry, plist;
      entry = remoteCache[cacheKey(model)];
      if (entry && !entry.promise) {
        modelInsert(entry, model, outside);
        entry.sort(entry.data);
      }
      plist = parentList(model);
      if (plist) {
        plist.push(model.dbo_id);
        plist.sort();
        lpEvent.dispatch('childListUpdate', model.dbo_parent_type, model.dbo_key_type);
      }
    };

    this.deleteModel = function (model, outside) {
      var entry, plist;
      entry = remoteCache[cacheKey(model)];
      if (entry && !entry.promise) {
        modelDelete(entry, model, outside);
      }
      deleteChildren(model, outside);
      if (plist = parentList(model)) {
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
      entry.promise = lpRemote.request('editor/' + entry.path, entry.params).then(function (data) {
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

    this.refresh = function(key) {
      var entry = remoteCache[key];
      if (!entry || entry.promise) {
        return lpCache.cache(key);
      }
      entry.promise = lpRemote.request('editor/' + entry.path, entry.params).then(function(data) {
        delete entry.promise;
        var model, dataKeys, delModels, ix;
        dataKeys = {};
        delModels = [];
        for (ix = 0; ix < data.length; ix++) {
          model = data[ix];
          modelInsert(entry, model);
          dataKeys[model.dbo_id] = model;
        }
        for (ix = 0; ix < entry.data.length; ix++) {
          model = entry.data[ix];
          if (!dataKeys.hasOwnProperty(model.dbo_id)) {
            delModels.push(model);
          }
        }
        for (ix = 0; ix < delModels.length; ix++) {
          modelDelete(entry, delModels[ix], true);
        }
      });
    };

    this.seedCacheId = function(dboId) {
      var parts = dboId.split(':');
      var size = parts.length;
      if (size == 2) {
        return lpCache.cache(parts[0]);
      }
      return lpCache.cache(parts[0] + ':' + parts[1]);
    };

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
