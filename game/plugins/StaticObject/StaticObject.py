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


import os.path
from pandac.PandaModules import *


class StaticObject:
  """Replaces all of a specific IsA in a scene with a specific mesh, including collision detection. It can also contain a bunch of <instance> tags, that way you can specify positions yourself instead of doing it in the world model."""
  def __init__(self,manager,xml):
    self.reload(manager,xml)
    self.node = render.attachNewNode('StaticObjects')
    self.node.hide()

    self.things = [] # Tuple of (mesh,collider)

  def reload(self,manager,xml):
    self.manager = manager
    self.xml = xml

  def destroy(self):
    for mesh,collider in self.things:
      if mesh:
        mesh.removeNode()
      if collider:
        collider.destroy()

    self.node.removeNode()


  def postInit(self):
    for i in self.postReload():
      yield i

  def postReload(self):
    # We need to delete any old objects from before this reload...
    for mesh,collider in self.things:
      if mesh:
        mesh.removeNode()
      if collider:
        collider.destroy()
      yield
    self.things = []
    yield
    
    # Mesh path, physics plugin and physics type...
    basePath = self.manager.get('paths').getConfig().find('objects').get('path')
    
    phys = self.xml.find('physics')
    if phys!=None:
      odeName = phys.get('plugin','ode')
      self.ode = self.manager.get(odeName)
      pType = phys.get('type').lower()
    else:
      pType = None

    # Find all instances of the object to create...
    toMake = []
    for isa in self.xml.findall('isa'):
      level = self.manager.get(isa.get('source'))
      toMake += level.getByIsA(isa.get('name'))
      yield

    for inst in self.xml.findall('instance'):
      # Find <instance> tags that can be used to create instances of the physics object.
      make = NodePath('staticObject')
      make.setPos(  float(inst.get('x', '0')), float(inst.get('y', '0')), float(inst.get('z', '0')))
      make.setHpr(  float(inst.get('h', '0')), float(inst.get('p', '0')), float(inst.get('r', '0')))
      make.setScale(float(inst.get('sx','1')), float(inst.get('sy','1')), float(inst.get('sz','1')))
      toMake.append(make)
      yield

    # Make all of the relevant instances...
    for make in toMake:
      if self.xml.find('mesh') != None:
        # Load the mesh, parent to render...
        filename = os.path.join(basePath,self.xml.find('mesh').get('filename'))
        model = loader.loadModel(filename)
        model.reparentTo(self.node)
        model.setShaderAuto()
      else:
        model = None

      # Create the collision object...
      if pType=='sphere':
        col = OdeSphereGeom(self.ode.getSpace(), float(phys.get('radius')))
      elif pType=='box':
        col = OdeBoxGeom(self.ode.getSpace(), float(phys.get('lx')), float(phys.get('ly')), float(phys.get('lz')))
      elif pType=='cylinder':
        col = OdeCylinderGeom(self.ode.getSpace(), float(phys.get('radius')), float(phys.get('height')))
      elif pType=='capsule':
        col = OdeCappedCylinderGeom(self.ode.getSpace(), float(phys.get('radius')), float(phys.get('height')))
      elif pType=='mesh':
        colMesh = loader.loadModel(os.path.join(basePath,phys.get('filename')))
        colTri = OdeTriMeshData(colMesh,True)
        col = OdeTriMeshGeom(self.ode.getSpace(),colTri)
      elif pType=='plane':
        col = OdePlaneGeom(self.ode.getSpace(), 0.0,0.0,1.0,0.0)
      else:
        col = None

      # Weirdness! We can't move a Plane, so we'll have to bake the transform onto the plane equation.
      # We can do that easily thanks to panda's Plane class.
      if pType=='plane':
        # Remember that the D is inverted in ODE compared to Panda.
        plane = Plane(col.getParams())
        plane.setW(-plane.getW())
        plane.xform(make.getNetTransform().getMat())
        plane.setW(-plane.getW())
        col.setParams(plane)
      elif col!=None:
        col.setPosition(make.getPos(render))
        col.setQuaternion(make.getQuat(render))

      if col!=None:
        surface = phys.get('surface')
        self.ode.getSpace().setSurfaceType(col,self.ode.getSurface(surface))

      if self.xml.find('mesh')!=None:
        model.setPosQuat(make.getPos(render),make.getQuat(render))
      self.things.append((model,col))

      yield


  def start(self):
    self.node.show()

  def stop(self):
    self.node.hide()
