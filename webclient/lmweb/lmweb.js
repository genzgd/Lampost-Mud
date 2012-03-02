function LMWeb() {

	var self = this;
	var version = "0.038";
	var imports = {};
	var moduleMap = {};
	var nextModuleId = 0;
	
	this.loadImport = function(name, moduleRoot, moduleId) {
			lmdp.log("Importing " + name + " javascript");
			if (!imports[name]) {
				var importScript = $('<script src="comp/' + name + '.js" >//@ sourceURL=createOrder.js</script>');
				imports[name] = importScript;
				$("head").append(importScript);
			}
			if (moduleRoot) {
				var moduleClass = name.charAt(0).toUpperCase() + name.slice(1) + "LMModule";
				var module = new window[moduleClass](moduleRoot);
				module.moduleId = moduleId;
				module.root = moduleRoot;
				moduleMap[moduleId] = module;
			}
		};

	this.loadModule = function(name, root) {
			var moduleId = ++nextModuleId;	
			lmdp.log("Loading comp/" + name + ".html  root:" + root.attr("id"));
			root.load("comp/" + name + ".html?version=" + version, null, function(response, status, request) {
				if (status == "success") {
					self.loadImport(name, root, moduleId);
				}
				else {
					alert("Error importing " + name);
				}
			});
			return moduleId;
		};
	
	this.unloadModule = function (moduleId) {
			var module = moduleMap[moduleId];
			module.unload();
			delete moduleMap[moduleId];
		};

}


LMWeb.BaseModule = {
		register: function (type, callback, once) {
			if (!this.hasOwnProperty("regs")) {
				this.regs = [];
			}
			this.regs.push(lmdp.register(type, callback, once));
		},
		
		unload: function unload() {
			if (this.hasOwnProperty("regs")) {
				for (var i = 0; i < this.regs.length; i++) {
					lmdp.unregister(this.regs[i]);
				}
			}
			this.root.empty();
		}
	};


var lmweb = new LMWeb();