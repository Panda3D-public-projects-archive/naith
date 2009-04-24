# Copyright Tom SF hHaines
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



import os.path
from pandac.PandaModules import *
import direct.directbase.DirectStart


class Level:
  """This loads a level - that is it loads a collection fo egg files and sticks them at the origin. These files will typically be very large. 4 files, all optional, are typically given - the rendered file, the collision file, the detail file (Visible instances of high res geometry.) and the entity file. (Lots of empties used by the programmer.)"""
  def __init__(self,manager,xml):
    # Get the path to load levels from...
    basePath = manager.get('paths').getConfig().find('levels').get('path')

    # Calculate the renderable path, load the egg...
    rendElem = xml.find('render')
    if rendElem!=None:
      rendPath = os.path.join(basePath,rendElem.get('filename'))
      self.rend = loader.loadModel(rendPath)

      self.ambLight = AmbientLight('Ambient Light')
      self.ambLight.setColor(VBase4(1.0,1.0,1.0,1.0))
      self.ambLightNode = self.rend.attachNewNode(self.ambLight)
      self.rend.setLight(self.ambLightNode)
    else:
      self.rend = None

    # Calculate the collision egg, load the egg, turn it into an ode mesh...
    colElem = xml.find('collide')
    if colElem!=None:
      colPath = os.path.join(basePath,colElem.get('filename'))
      self.colEgg = loader.loadModel(colPath)
      self.colEgg.flattenStrong() # This is silly - removes all the advantage of octrees - need to write code to do this properlly by constructing the hierachy using ODE spaces. ###################################################################
      
      ode = manager.get('ode')
      mesh = OdeTriMeshData(self.colEgg,True)
      self.col = OdeTriMeshGeom(ode.getSpace(),mesh)
      ode.getSpace().setSurfaceType(self.col,ode.getSurface('default'))
    else:
      self.colEgg = None

    # Get the things mesh - this is usually a load of empties used to create objects...
    thingElem = xml.find('things')
    if thingElem!=None:
      thingPath = os.path.join(basePath,thingElem.get('filename'))
      self.things = loader.loadModel(thingPath)
    else:
      self.things = None


  def start(self):
    if self.rend: self.rend.reparentTo(render)

  def stop(self):
    if self.rend: self.rend.clearParent()

  def getThings(self):
    return self.things

  def getByIsA(self,name):
    """Given a name this returns a list of all objects in the things structure that have the tag IsA with the given name as the data. Will return an empty list if none available."""
    if self.things == None: return []
    col = self.things.findAllMatches('**/=IsA='+name)
    ret = []
    for i in xrange(col.size()):
      ret.append(col[i])
    return ret

