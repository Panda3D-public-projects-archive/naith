# Copyright Tom SF Haines
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.



import sys
import xml.etree.ElementTree as et
import imp
import types

import direct.directbase.DirectStart


class Manager:
  """The simple plugin system - this is documented in the docs directory."""
  
  def __init__(self):
    # Basic configuratrion variables...
    self.pluginDir = 'plugins/'
    self.configDir = 'config/'
    self.loadingInvFrameRate = 1.0/20.0
    
    # The plugin database - dictionary of modules...
    self.plugin = dict()

    # Add 'shared' to the path so shared code can be loaded by the various plugins...
    sys.path.append('bin/shared')
    
    
    # Create the instance database - a list in creation order of (obj,name) where name can be None for nameless objects, plus a dictionary to get at the objects by name...
    self.objList = []
    self.named = dict()

    # The above, but only used during transitions...
    self.oldObjList = None
    self.oldNamed = None

    # For pandaStep...
    self.lastTime = 0.0
  
  def transition(self,config):
    """Transitions from the current configuration to a new configuration, makes a point to keep letting Panda draw whilst it is doing so, so any special loading screen plugin can do its stuff. Maintains some variables in this class so such a plugin can also display a loading bar."""
    
    # Step 1 - call stop on all current objects- do this immediatly as we can't have some running whilst others are not...
    for obj in self.objList:
      stop = getattr(obj[0],'stop',None)
      if isinstance(stop,types.MethodType):
        stop()

    # Declare the task that is going to make the transition - done this way to keep rendering whilst we make the transition, for a loading screen etc. This is a generator for conveniance...
    def transTask(task):
      # Step 2 - move the database to 'old', make a new one...
      self.oldObjList = self.objList
      self.oldNamed = self.named
      self.objList = []
      self.named = dict()
      yield task.cont

      # Step 3 - load and iterate the config file and add in each instance...
      elem = et.parse(self.configDir+config+'.xml')
      yield task.cont
      for obj in elem.findall('obj'):
        for blah in self.addObj(obj):
          yield task.cont

      # Step 4 - destroy the old database - call destroy methods when it exists...
      for obj in self.oldObjList:
        inst = obj[0]
        name = obj[1]
        if (not self.oldNamed.has_key(name)) or self.oldNamed[name]!=True:
          # It needs to die - we let the reference count being zeroed do the actual deletion but it might have a slow death, so we use the destroy method/generator to make it happen during the progress bar ratehr than blocking the gc at some random point...
          destroy = getattr(inst,'destroy',None)
          if isinstance(destroy,types.MethodType):
            ret = destroy()
            yield task.cont
            if isinstance(ret,types.GeneratorType):
              for blah in ret:
                yield task.cont

      self.oldObjList = None
      self.oldNamed = None
      yield task.cont

      # Step 5 - call start on all current objects - done in a single step to avoid problems, so no yields...
      for obj in self.objList:
        start = getattr(obj[0],'start',None)
        if isinstance(start,types.MethodType):
          start()

    # Create a task to do the dirty work...
    taskMgr.add(transTask,'Transition')


  def end(self):
    """Ends the program neatly - closes down all the plugins before calling sys.exit(). Effectivly a partial transition, though without the framerate maintenance."""

    # Stop all the plugins...
    for obj in self.objList:
      stop = getattr(obj[0],'stop',None)
      if isinstance(stop,types.MethodType):
        stop()

    # Destroy the database...
    for obj in self.objList:
      inst = obj[0]
      name = obj[1]
      destroy = getattr(inst,'destroy',None)
      if isinstance(destroy,types.MethodType):
        ret = destroy()
        if isinstance(ret,types.GeneratorType):
          for blah in ret:
            pass

    # Die...
    sys.exit()


  def addObj(self,element):
    """Given a xml.etree Element of type obj this does the necesary - can only be called during a transition, exposed like this for the Include class. Note that it is a generator."""
    
    # Step 1 - get the details of the plugin we will be making...
    plugin = element.get('type')
    name = element.get('name')

    # Step 2 - get the plugin - load it if it is not already loaded...
    if not self.plugin.has_key(plugin):
      print 'Loading plugin', plugin
      fp, path, desc = imp.find_module(plugin,[self.pluginDir+plugin+'/'])
      try:
        self.plugin[plugin] = imp.load_module(plugin,fp,path,desc)
      finally:
        if fp:
          fp.close()
      print 'Loaded', plugin
      yield None

    # Step 3a - check if there is an old object that can be repurposed, otherwise create a new object...
    done = False
    if self.oldNamed.has_key(name) and isinstance(self.oldNamed[name], getattr(self.plugin[plugin],plugin)) and getattr(self.oldNamed[name],'reload',None)!=None:
      print 'Reusing', plugin
      inst = self.oldNamed[name]
      self.oldNamed[name] = True # So we know its been re-used for during the deletion phase.
      inst.reload(self,element)
      yield None
      print 'Reused',plugin
      if getattr(inst,'postReload',None)!=None:
        for blah in inst.postReload():
          yield None
        print 'post reload',plugin
    else:
      print 'Making', plugin
      inst = getattr(self.plugin[plugin],plugin)(self,element)
      yield None
      print 'Made', plugin
      if getattr(inst,'postInit',None)!=None:
        for blah in inst.postInit():
          yield None
        print 'post init',plugin

    # Step 3b - Stick it in the object database...
    self.objList.append((inst,name))
    if name!=None:
      self.named[name] = inst

    # One last yield, just to keep things going...
    yield None

  def get(self,name):
    """Returns the plugin instance associated with the given name, or None if it doesn't exist."""
    if self.named.has_key(name):
      return self.named[name]
    else:
      return None

  def getPercentage(self):
    """During a transition this will return [0,1] indicating percentage done - for a loading plugin to use. Calling at other times will return 1.0 This is not yet implimented, as it needs to get very clever to compensate for variable loading times and includes."""
    return 1.0
