angular.module('lampost_editor').factory('lpEditorTypes', ['lpUtil', function(lpUtil) {

  function rowLabel(row) {
    return row.name;
  }

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

    this.newValue = this.unused[0];
  }


  function ValueMap(source_prop, name) {
    this.rowMap = {};
    this.source_prop = source_prop;
    this.desc = this.name = name;
  }

  ValueMap.prototype.updateUnused = updateUnused;
  ValueMap.prototype.optionKey = 'dbo_id';
  ValueMap.prototype.default = 1;
  ValueMap.prototype.transform = function(key, value) {
      return this.rowMap[key] = {key: key, name: key, value: value};
    };
  ValueMap.prototype.rowLabel = rowLabel;
  ValueMap.prototype.setSource = function(model) {
      this.sourceMap = model[this.source_prop];
      this.rows = [];
      for (var prop in this.sourceMap) {
        if (this.sourceMap.hasOwnProperty(prop)) {
          this.rows.push(this.transform(prop, this.sourceMap[prop]))
        }
      }
      this.updateUnused();
    };
  ValueMap.prototype.onChange = function(row) {
      this.sourceMap[row.key] = row.value;
    };



  function ValueObjList(source_prop, name, key_prop, value_prop) {
    this.rowMap = {};
    this.source_prop = source_prop;
    this.desc = this.name = name;
    this.key_prop = key_prop;
    this.value_prop = value_prop;
  }

  ValueObjList.prototype.updateUnused = updateUnused;
  ValueObjList.prototype.optionKey = 'dbo_id';
  ValueObjList.prototype.default = 1;
  ValueObjList.prototype.rowLabel = rowLabel;
  ValueObjList.prototype.transform = function(source) {
    var key = source[this.key_prop];
    return this.rowMap[key] = {key: key, name: source[this.key_prop], value: source[this.value_prop]};
  }
  ValueObjList.prototype.setSource = function(model) {
      this.sourceList = model[this.source_prop];
      this.rows = [];
      for (var ix = 0; ix < this.sourceList.length; ix++) {
        this.rows.push(this.transform(this.sourceList[ix]));
      }
      this.updateUnused();
    }
  ValueObjList.prototype.onChange = function(row, rowIx) {
      this.sourceList[rowIx][value_prop] = row.value;
    }
  ValueObjList.prototype.insert = function() {
      var value = {};
      value[this.key_prop] = this.newValue[this.optionKey];
      value[this.value_prop] = this.default;
      this.sourceList.push(value);
      this.rows.push(this.transform(value));
      this.updateUnused();
    }
  ValueObjList.prototype.delete = function(row, rowIx) {
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