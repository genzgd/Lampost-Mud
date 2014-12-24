angular.module('lampost_editor').factory('lpEditorTypes', ['lpUtil', function(lpUtil) {

  function rowLabel(row) {
    return row.name;
  }

  var sortFunc = lpUtil.stringSortFunc('name');

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
    this.unused.sort(this.sortFunc);
    this.newValue = this.unused[0];
  }


  function ValueMap(source_prop, name) {
    this.source_prop = source_prop;
    this.desc = this.name = name;
  }

  ValueMap.prototype.updateUnused = updateUnused;
  ValueMap.prototype.optionKey = 'dbo_id';
  ValueMap.prototype.default = 1;
  ValueMap.prototype.sortFunc = sortFunc;
  ValueMap.prototype.transform = function(key, value) {
      return this.rowMap[key] = {key: key, name: key, value: value};
    };
  ValueMap.prototype.rowLabel = rowLabel;
  ValueMap.prototype.setSource = function(model) {
      this.sourceMap = model[this.source_prop];
      this.rows = [];
      this.rowMap = {};
      for (var prop in this.sourceMap) {
        if (this.sourceMap.hasOwnProperty(prop)) {
          this.rows.push(this.transform(prop, this.sourceMap[prop]))
        }
      }
      this.rows.sort(this.sortFunc);
      this.updateUnused();
    };
  ValueMap.prototype.onChange = function(row) {
      this.sourceMap[row.key] = row.value;
    };
  ValueMap.prototype.insert = function() {
      var key = this.newValue[this.optionKey];
      this.sourceMap[key] = this.default;
      this.rows.push(this.transform(key, this.default));
      this.rows.sort(this.sortFunc);
      this.updateUnused();
    };
  ValueMap.prototype.remove = function(row, rowIx) {
      delete this.rowMap[row.key];
      this.rows.splice(rowIx, 1);
      delete this.sourceMap[row.key];
      this.updateUnused();
    };



  function ValueObjList(source_prop, name, keyProp, valueProp) {
    this.source_prop = source_prop;
    this.desc = this.name = name;
    this.keyProp = keyProp;
    this.valueProp = valueProp;
    this.sourceSort = lpUtil.stringSortFunc(keyProp);
  }

  ValueObjList.prototype.updateUnused = updateUnused;
  ValueObjList.prototype.optionKey = 'dbo_id';
  ValueObjList.prototype.default = 1;
  ValueObjList.prototype.rowLabel = rowLabel;
  ValueObjList.prototype.sortFunc = sortFunc;
  ValueObjList.prototype.transform = function(source) {
    var key = source[this.keyProp];
    return this.rowMap[key] = {key: key, name: source[this.keyProp], value: source[this.valueProp]};
  }
  ValueObjList.prototype.setSource = function(model) {
      this.sourceList = model[this.source_prop];
      this.sourceList.sort(this.sourceSort);
      this.rowMap = {};
      this.rows = [];
      for (var ix = 0; ix < this.sourceList.length; ix++) {
        this.rows.push(this.transform(this.sourceList[ix]));
      }
      this.rows.sort(this.sortFunc);
      this.updateUnused();
    }
  ValueObjList.prototype.onChange = function(row, rowIx) {
      this.sourceList[rowIx][this.valueProp] = row.value;
    }
  ValueObjList.prototype.insert = function() {
      var value = {};
      value[this.keyProp] = this.newValue[this.optionKey];
      value[this.valueProp] = this.default;
      this.sourceList.push(value);
      this.sourceList.sort(this.sourceSort);
      this.rows.push(this.transform(value));
      this.rows.sort(this.sortFunc);
      this.updateUnused();
    }
  ValueObjList.prototype.remove = function(row, rowIx) {
      delete this.rowMap[row.key];
      this.rows.splice(rowIx, 1);
      this.sourceList.splice(rowIx, 1);
      this.updateUnused();
    }

  return {
    ValueMap: ValueMap,
    ValueObjList: ValueObjList
  }

}]);