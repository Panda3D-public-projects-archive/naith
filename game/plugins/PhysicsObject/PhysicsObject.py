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


class PhysicsObject:
  """Provides a simple physics object capability - replaces all of a specific IsA in a scene with a specific mesh and specific physics capabilities. Initialises such objects with simulation off, so they won't move until they itnteract with the player or an AI somehow - needed to restrict computation but means such objects must be positioned very accuratly in the level.
  It can also contain a bunch of <instance> tags, that way you can specify positions yourself instead of doing it in the world model."""
  def __init__(self,manager,xml):
    self.reload(manager,xml)
    self.node = render.attachNewNode('PhysicsObjects')
    self.node.hide()

    self.things = [] # Tuple of (mesh,body,collider)

  def reload(self,manager,xml):
    self.manager = manager
    self.xml = xml

  def destroy(self):
    for mesh,body,collider in self.things:
      if mesh:
        mesh.removeNode()
      if body:
        body.destroy()
      collider.destroy()

    self.node.removeNode()


  def postInit(self):
    for i in self.postReload():
      yield i

  def postReload(self):
    # We need to delete any old objects from before this reload...
    for mesh,body,collider in self.things:
      if mesh:
        mesh.removeNode()
      if body:
        body.destroy()
      collider.destroy()
      yield
    self.things = []
    yield
    
    # Mesh path, physics plugin and physics type...
    basePath = self.manager.get('paths').getConfig().find('objects').get('path')
    
    phys = self.xml.find('physics')
    odeName = phys.get('plugin','ode')
    self.ode = self.manager.get(odeName)

    pType = phys.get('type').lower()

    # Find all instances of the object to obtain...
    toMake = []
    for isa in self.xml.findall('isa'):
      level = self.manager.get(isa.get('source'))
      toMake += level.getByIsA(isa.get('name'))
      yield

    for inst in self.xml.findall('instance'):
      # Find <instance> tags that can be used to create instances of the physics object.
      make = NodePath('physicsObject')
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
        if pType=='mesh':
          # Need some way of calculating/obtaining an inertial tensor - currently using a box centered on the object with the dimensions of the collision meshes bounding axis aligned box...
          colMesh = loader.loadModel(os.path.join(basePath,phys.get('filename')))

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
        col = OdeTriMeshGeom(self.ode.getSpace(), OdeTriMeshData(colMesh,True))
      elif pType=='plane':
        col = OdePlaneGeom(self.ode.getSpace(), float(phys.get('a')), float(phys.get('b')), float(phys.get('c')), -float(phys.get('d')))

      # Weirdness! We can't move a Plane, so we'll have to bake the transform onto the plane equation.
      # We can do that easily thanks to panda's Plane class.
      if pType=='plane': # This needs moving elsewhere - a plane is a static object and should never have been added to this plugin - it needs to be done using a 'static' plugin.
        # Remember that the D is inverted in ODE compared to Panda.
        plane = Plane(col.getParams())
        plane.setW(-plane.getW())
        plane.xform(make.getNetTransform().getMat())
        plane.setW(-plane.getW())
        col.setParams(plane)
      else:
        col.setPosition(make.getPos(render))
        col.setQuaternion(make.getQuat(render))

      surface = phys.get('surface')
      self.ode.getSpace().setSurfaceType(col,self.ode.getSurface(surface))

      if self.xml.find('mesh')!=None:
        # Move it to the correct location/orientation...
        model.setPosQuat(make.getPos(render),make.getQuat(render))

        # Create the mass object for the physics...
        body = OdeBody(self.ode.getWorld())
        col.setBody(body)
        mass = OdeMass()
        if pType=='sphere':
          mass.setSphereTotal(float(phys.get('mass')), float(phys.get('radius')))
        elif pType=='box':
          mass.setBoxTotal(float(phys.get('mass')), float(phys.get('lx')), float(phys.get('ly')), float(phys.get('lz')))
        elif pType=='cylinder':
          mass.setCylinderTotal(float(phys.get('mass')), 3, float(phys.get('radius')), float(phys.get('height')))
        elif pType=='capsule':
          mass.setCapsuleTotal(float(phys.get('mass')), 3, float(phys.get('radius')), float(phys.get('height')))
        elif pType=='mesh':
          low, high = colMesh.getTightBounds()
          mass.setBoxTotal(float(phys.get('mass')), high[0]-low[0], high[1]-low[1], high[2]-low[2])
        else:
          raise Exception('Unrecognised physics type')

        body.setMass(mass)
        body.setPosition(make.getPos(render))
        body.setQuaternion(make.getQuat(render))
        body.disable() # To save computation until the player actually interacts with 'em. And stop that annoying jitter.
        damp = self.xml.find('damping')
        if damp!=None:
          self.ode.regDamping(body,float(damp.get('linear')),float(damp.get('angular')))

        # Tie everything together, arrange for damping...
        self.ode.regBodySynch(model,body)
        self.things.append((model,body,col))
      else:
        self.things.append((None,None,col))

      yield


  def start(self):
    self.node.show()

  def stop(self):
    self.node.hide()