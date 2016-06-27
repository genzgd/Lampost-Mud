angular.module('lampost_editor').factory('lpEditorTypes', ['lpUtil', function(lpUtil) {

 function updateUnused() {
    var ix;
    var option;
    if (!this.options) {
      return;
    }
    this.unused = [];
    for (ix = 0; ix < this.options.length; ix++) {
      option = this.options[ix];
      if (!this.rowMap[option[this.optionKey]]) {
        this.unused.push(option);
      }
    }
    this.optionSort(this.unused);
    this.newValue = this.unused[0];
  }

  var valProto = {
    updateUnused: updateUnused,
    rowSort:  lpUtil.fieldSortFunc('name'),
    optionKey: 'dbo_id',
    optionSort: lpUtil.fieldSortFunc('dbo_id'),
    default: 1,
    rowLabel: function(row) {
      return row.name;
    },
    setOptions: function(options, optionKey) {
      this.options = options;
      if (optionKey && optionKey != this.optionKey) {
        this.optionKey = optionKey;
        this.optionSort = lpUtil.fieldSortFunc(optionKey);
      }
      for (var ix = 0; ix < options.length; ix++) {
        var option = options[ix];
        option.name = option.name || option[this.optionKey];
      }
    }
  };


  function ValueMap(sourceProp, name) {
    this.sourceProp = sourceProp;
    this.desc = this.name = name;
  }

  angular.extend(ValueMap.prototype, valProto);
  ValueMap.prototype.transform = function(key, value) {
      return this.rowMap[key] = {key: key, name: key, value: value};
    };
  ValueMap.prototype.setSource = function(model) {
      this.sourceMap = model[this.sourceProp];
      this.rows = [];
      this.rowMap = {};
      for (var prop in this.sourceMap) {
        if (this.sourceMap.hasOwnProperty(prop)) {
          this.rows.push(this.transform(prop, this.sourceMap[prop]))
        }
      }
      this.rowSort(this.rows);
      this.updateUnused();
    };
  ValueMap.prototype.onChange = function(row) {
      this.sourceMap[row.key] = row.value;
    };
  ValueMap.prototype.insert = function() {
      var key = this.newValue[this.optionKey];
      this.sourceMap[key] = this.default;
      this.rows.push(this.transform(key, this.default));
      this.rowSort(this.rows);
      this.updateUnused();
    };
  ValueMap.prototype.remove = function(row, rowIx) {
      delete this.rowMap[row.key];
      this.rows.splice(rowIx, 1);
      delete this.sourceMap[row.key];
      this.updateUnused();
    };


  function ValueObjList(sourceProp, name, keyProp, valueProp) {
    this.sourceProp = sourceProp;
    this.desc = this.name = name;
    this.keyProp = keyProp;
    this.valueProp = valueProp;
    this.sourceSort = lpUtil.fieldSortFunc(keyProp);
  }

  angular.extend(ValueObjList.prototype, valProto);
  ValueObjList.prototype.transform = function(source) {
    var key = source[this.keyProp];
    return this.rowMap[key] = {key: key, name: source[this.keyProp], value: source[this.valueProp]};
  };

  ValueObjList.prototype.setSource = function(model) {
      this.sourceList = model[this.sourceProp];
      this.sourceSort(this.sourceList);
      this.rowMap = {};
      this.rows = [];
      for (var ix = 0; ix < this.sourceList.length; ix++) {
        this.rows.push(this.transform(this.sourceList[ix]));
      }
      this.rowSort(this.rows);
      this.updateUnused();
    };

  ValueObjList.prototype.onChange = function(row, rowIx) {
      this.sourceList[rowIx][this.valueProp] = row.value;
    };

  ValueObjList.prototype.insert = function() {
      var value = {};
      value[this.keyProp] = this.newValue[this.optionKey];
      value[this.valueProp] = this.default;
      this.sourceList.push(value);
      this.sourceSort(this.sourceList);
      this.rows.push(this.transform(value));
      this.rowSort(this.rows);
      this.updateUnused();
    };

  ValueObjList.prototype.remove = function(row, rowIx) {
      delete this.rowMap[row.key];
      this.rows.splice(rowIx, 1);
      this.sourceList.splice(rowIx, 1);
      this.updateUnused();
    };
    
    
  function OptionsList(sourceProp, name) {
    this.sourceProp = sourceProp;
    this.name = name;
  }

  angular.extend(OptionsList.prototype, valProto);
  OptionsList.prototype.rowSort = lpUtil.naturalSort;
  OptionsList.prototype.setSource = function(model) {
    this.rows = model[this.sourceProp];
    this.rowMap = {};
    for (var ix = 0; ix < this.rows.length; ix++) {
      var value = this.rows[ix];
      this.rowMap[value] = value;
    }
    this.rowSort(this.rows);
    this.updateUnused();
  };

  OptionsList.prototype.insert = function() {
    var value = this.newValue[this.optionKey];
    this.rows.push(value);
    this.rowMap[value] = value;
    this.rowSort(this.rows);
    this.updateUnused();
  };

  OptionsList.prototype.remove = function(row, rowIx) {
    delete this.rowMap[row];
    this.rows.splice(rowIx, 1);
    this.updateUnused();
  };


  function StringOptions(sourceProp, name, options) {
    this.sourceProp = sourceProp;
    this.name = name;
    this.options = options;

    this.setSource = function(model) {
      var ix;
      this.sourceList = model[sourceProp];
      this.selectedList = [];
      for (ix = 0; ix < options.length; ix++) {
        this.selectedList.push(this.sourceList.indexOf(options[ix] > -1));
      }
    };

    this.remove = function(rowIx) {
      this.selectedList[rowIx] = false;
      this.update();
    };

    this.insert = function(rowIx) {
      this.selectedList[rowIx] = false;
      this.update();
    };

    this.update = function() {
      var ix;
      this.sourceList.splice(0, this.sourceList.length);
      for (ix = 0; ix < this.options.length; ix++) {
        if (this.selectedList[ix]) {
          this.sourceList.push(this.options[ix]);
        }
      }
    }
  }


  function ChildSelect(sourceProp, type) {
    this.sourceProp = sourceProp;
    this.type = type;
  }
  ChildSelect.prototype.parentFilter = ChildSelect.prototype.childFilter = function(items) {
    return items;
  };
  ChildSelect.prototype.parentSelect = ChildSelect.prototype.childSelect = angular.noop;
  ChildSelect.prototype.setSource = function(model) {
    this.initial = true;
    this.model = model;
    this.value = model[this.sourceProp];
  };
  ChildSelect.prototype.setValue = function(value) {
    this.initial = false;
    this.model[this.sourceProp] = value;
  };

  return {
    ValueMap: ValueMap,
    ValueObjList: ValueObjList,
    OptionsList: OptionsList,
    ChildSelect: ChildSelect,
    StringOptions: StringOptions
  }

}]);