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
import direct.directbase.DirectStart


class PhysicsObject:
  """Provides a simple physics object capability - replaces all of a specific IsA in a scene with a specific mesh and specific physics capabilities. Initialises such objects with simulation off, so they won't move until they itneract with the player or an AI somehow - needed to restrict computation but means such objects must be positioned very accuratly in the level."""
  def __init__(self,manager,xml):
    basePath = manager.get('paths').getConfig().find('objects').get('path')
    ode = manager.get('ode')
    self.things = [] # Tuple of (mesh/body/collider)
    
    # Find all instances of the object to obtain...
    level = manager.get(xml.find('isa').get('source'))
    toMake = level.getByIsA(xml.find('isa').get('name'))
    for make in toMake:
      # Load the mesh, parent to render...
      filename = os.path.join(basePath,xml.find('mesh').get('filename'))
      model = loader.loadModel(filename)
      model.reparentTo(render)
      model.setShaderAuto()

      # Move it to the correct location/orientation...
      model.setPosQuat(make.getPos(render),make.getQuat(render))
      
      # Create the mass object for the physics...
      body = OdeBody(ode.getWorld())
      mass = OdeMass()
      phys = xml.find('physics')
      pType = phys.get('type')
      if pType=='sphere':
        mass.setSphereTotal(float(phys.get('mass')), float(phys.get('radius')))
      elif pType=='box':
        mass.setBoxTotal(float(phys.get('mass')), float(phys.get('lx')), float(phys.get('ly')), float(phys.get('lz')))
      elif pType=='cylinder':
        mass.setCylinderTotal(float(phys.get('mass')), 3, float(phys.get('radius')), float(phys.get('height')))
      elif pType=='capsule':
        mass.setCapsuleTotal(float(phys.get('mass')), 3, float(phys.get('radius')), float(phys.get('height')))
      elif pType=='mesh':
        # Need some way of calculating/obtaining an inertial tensor - currently using a box centered on the object with the dimensions of the collision meshes bounding axis aligned box...
        colMesh = loader.loadModel(os.path.join(basePath,phys.get('filename')))
        low, high = colMesh.getTightBounds()
        mass.setBoxTotal(float(phys.get('mass')), high[0]-low[0], high[1]-low[1], high[2]-low[2])
      else:
        raise Exception('Unrecognised physics type')
      
      body.setMass(mass)
      body.setPosition(make.getPos(render))
      body.setQuaternion(make.getQuat(render))
      body.disable() # To save computation until the player actually interacts with 'em. And stop that annoying jitter.

      # Create the collision object...
      if pType=='sphere':
        col = OdeSphereGeom(ode.getSpace(), float(phys.get('radius')))
      elif pType=='box':
        col = OdeBoxGeom(ode.getSpace(), float(phys.get('lx')), float(phys.get('ly')), float(phys.get('lz')))
      elif pType=='cylinder':
        col = OdeCylinderGeom(ode.getSpace(), float(phys.get('radius')), float(phys.get('height')))
      elif pType=='capsule':
        col = OdeCappedCylinderGeom(ode.getSpace(), float(phys.get('radius')), float(phys.get('height')))
      elif pType=='mesh':
        col = OdeTriMeshGeom(ode.getSpace(), OdeTriMeshData(colMesh,True))

      col.setBody(body)
      surface = phys.get('surface')
      ode.getSpace().setSurfaceType(col,ode.getSurface(surface))

      # Tie everything together, arrange for damping...
      ode.regBodySynch(model,body)
      self.things.append((model,body,col))

      damp = xml.find('damping')
      if damp!=None:
        ode.regDamping(body,float(damp.get('linear')),float(damp.get('angular')))