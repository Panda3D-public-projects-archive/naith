# -*- coding: utf-8 -*-
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



import posixpath
import time

from panda3d.core import *
from direct.showbase.ShowBase import ShowBase

from bin.shared import odeSpaceHier


class Level:
  """This loads a level - that is it loads a collection fo egg files and sticks them at the origin. These files will typically be very large. 4 files, all optional, are typically given - the rendered file, the collision file, the detail file (Visible instances of high res geometry.) and the entity file. (Lots of empties used by the programmer.)"""
  def __init__(self,manager,xml):
    self.reload(manager,xml)

  def reload(self,manager,xml):
    # Load from the xml the details needed to do the actual loading...
    
    # Get the path to load levels from...
    basePath = manager.get('paths').getConfig().find('levels').get('path')

    # Get the details for the renderable geometry...
    rendElem = xml.find('render')
    if rendElem!=None:
      self.rendPath = posixpath.join(basePath,rendElem.get('filename'))
      self.rendAmb = xml.find('ambient')!=None
    else:
      self.rendPath = None

    # Get the details for the collision geometry...
    colElem = xml.find('collide')
    if colElem!=None:
      self.colPath = posixpath.join(basePath,colElem.get('filename'))
      self.colSurface = colElem.get('surface','default')
    else:
      self.colPath = None

    # Get the details for the instancing information - the things...
    thingElem = xml.find('things')
    if thingElem!=None:
      self.thingPath = posixpath.join(basePath,thingElem.get('filename'))
    else:
      self.thingPath = None

    # We need access to the physics manager to do physics...
    physics = xml.find('physics')
    if physics!=None:
      odeName = physics.get('plugin','ode')
    else:
      odeName = 'ode'
    self.ode = manager.get(odeName)


  def postInit(self):
    for i in self.postReload():
      yield i

  def postReload(self):
    # The renderable geometry...
    self.rend = None
    if self.rendPath!=None:
      def rendCallback(model):
        self.rend = model
      loader.loadModel(self.rendPath, callback=rendCallback)
      while self.rend==None:
        time.sleep(0.05)
        yield
      
      # Let's hide it from the shadowcam for now.
      self.rend.hide(BitMask32.bit(3))
      if self.rendAmb:
        self.ambLight = AmbientLight('Ambient Light')
        self.ambLight.setColor(VBase4(1.0,1.0,1.0,1.0))
        self.ambLightNode = self.rend.attachNewNode(self.ambLight)
        self.rend.setLight(self.ambLightNode)
        yield

    # The collision geometry...
    self.colEgg = None
    if self.colPath!=None:
      def colCallback(model):
        self.colEgg = model
      loader.loadModel(self.colPath, callback=colCallback)
      while self.colEgg==None:
        time.sleep(0.05)
        yield

      surfaceType = self.ode.getSurface(self.colSurface)
      for r in odeSpaceHier.eggToOde(self.colEgg,surfaceType):
        yield
        self.col = r

      if (self.col==None):
        print( 'WARNING: Collision geometry contained nothing to collide against.')
      else:
        self.ode.getSpace().add(self.col)


    # The thing egg...
    self.things = None
    if self.thingPath!=None:
      def thingCallback(model):
        self.things = model
      loader.loadModel(self.thingPath, callback=thingCallback)
      while self.things==None:
        time.sleep(0.05)
        yield


  def start(self):
    if self.rend: self.rend.reparentTo(render)

  def stop(self):
    if self.rend: self.rend.detachNode()


  def getThings(self):
    return self.things

  def getByIsA(self,name):
    """Given a name this returns a list of all objects in the things structure that have the tag IsA with the given name as the data. Will return an empty list if none available."""
    if self.things == None: return []
    col = self.things.findAllMatches('**/=IsA='+name)
    return col

  def toggleVisible(self):
    if self.rend.isHidden():
      self.rend.show()
    else:
      self.rend.hide()

