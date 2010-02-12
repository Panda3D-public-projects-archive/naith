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



import math

from pandac.PandaModules import *
from direct.showbase import DirectObject
import direct.directbase.DirectStart


class InitODE(DirectObject.DirectObject):
  """This creates the various ODE core objects, and exposes them to other plugins. Should be called ode."""
  def __init__(self,manager,xml):
    # Setup the physics world...
    erp = float(xml.find('param').get('erp',0.8))
    cfm = float(xml.find('param').get('cfm',1e-3))
    slip = float(xml.find('param').get('slip',0.0))
    dampen = float(xml.find('param').get('dampen',0.1))
    
    self.world = OdeWorld()
    self.world.setGravity(float(xml.find('gravity').get('x',0.0)), float(xml.find('gravity').get('y',0.0)), float(xml.find('gravity').get('z',-9.81)))
    self.world.setErp(erp)
    self.world.setCfm(cfm)
    self.world.setAutoDisableFlag(True)

    # Create a surface table - contains interactions between different surface types - loaded from config file...
    surElem = [x for x in xml.findall('surface')]
    self.world.initSurfaceTable(len(surElem))
    self.surFromName = dict()
    for a in xrange(len(surElem)):
      self.surFromName[surElem[a].get('name')] = a

      # Maths used below is obviously wrong - should probably work out something better.

      # Interaction with same surface...
      mu = float(surElem[a].get('mu'))
      bounce = float(surElem[a].get('bounce'))
      absorb = float(surElem[a].get('absorb'))
      self.world.setSurfaceEntry(a,a,mu,bounce,absorb,erp,cfm,slip,dampen)

      # Interaction with other surfaces...
      for b in xrange(a+1,len(surElem)):
        mu = float(surElem[a].get('mu')) * float(surElem[b].get('mu'))
        bounce = float(surElem[a].get('bounce')) * float(surElem[b].get('bounce'))
        absorb = float(surElem[a].get('absorb')) + float(surElem[b].get('absorb'))
        self.world.setSurfaceEntry(a,b,mu,bounce,absorb,erp,cfm,slip,dampen)

    # Create a space to manage collisions...
    self.space = OdeHashSpace()
    self.space.setAutoCollideWorld(self.world)

    # Setup a contact group to handle collision events...
    self.contactGroup = OdeJointGroup()
    self.space.setAutoCollideJointGroup(self.contactGroup)


    # Create the synch database - this is a database of NodePath and ODEBodys - each frame the NodePaths have their positions synched with the ODEBodys...
    self.synch = dict() # dict of tuples (node,body), indexed by an integer that is written to the NodePath as a integer using setPythonTag into 'ode_key'
    self.nextKey = 0

    # Create the extra function databases - pre- and post- functions for before and after each collision step...
    self.preCollide = dict() # id(func) -> func
    self.postCollide = dict()

    # Create the damping database - damps objects so that they slow down over time, which is very good for stability...
    self.damping = dict() # id(body) -> (body,amount)

    # Variables for the physics simulation to run on automatic - start and stop are used to enable/disable it however...
    self.timeRem = 0.0
    self.step = 1.0/50.0
    
    # Arrange variables for collision callback, enable the callbacks...
    self.collCB = dict() # OdeGeom to func(entry,flag), where flag is False if its in 1, true if its in 2.
    self.space.setCollisionEvent("collision")


  def reload(self,manager,xml):
    pass # No-op: This makes this module incorrect, but only because you can't change the configuration during runtime without unloading it first. Physics setup tends to remain constant however.


  def simulationTask(self,task):
    # Step the simulation and set the new positions - fixed time step...
    self.timeRem += globalClock.getDt()
    while self.timeRem>self.step:
      # Call the pre-collision functions...
      for ident,func in self.preCollide.iteritems():
        func()

      # Apply damping to all objects in damping db...
      for key,data in self.damping.iteritems():
        if data[0].isEnabled():
          vel = data[0].getLinearVel()
          vel *= -data[1]
          data[0].addForce(vel)
          rot = data[0].getAngularVel()
          rot *= -data[2]
          data[0].addTorque(rot)

      # A single step of collision detection...
      self.space.autoCollide() # Setup the contact joints
      self.world.quickStep(self.step)
      self.timeRem -= self.step
      self.contactGroup.empty() # Clear the contact joints

      # Call the post-collision functions...
      for ident,func in self.postCollide.iteritems():
        func()

    # Update all objects registered with this class to have their positions updated...
    for key, data in self.synch.items():
      node, body = data
      node.setPosQuat(render,body.getPosition(),Quat(body.getQuaternion()))

    return task.cont


  def onCollision(self,entry):
    geom1 = entry.getGeom1()
    geom2 = entry.getGeom2()

    for geom,func in self.collCB.iteritems():
      if geom==geom1:
        func(entry,False)
      if geom==geom2:
        func(entry,True)


  def start(self):
    self.task = taskMgr.add(self.simulationTask,'Physics Sim',sort=100)
    self.accept("collision",self.onCollision)

  def stop(self):
    taskMgr.remove(self.task)
    del self.task

    self.timeRem = 0.0
    self.ignoreAll()


  def getWorld(self):
    """Retuns the ODE world"""
    return self.world

  def getSpace(self):
    """Returns the ODE space used for automatic collisions."""
    return self.space

  def getSurface(self,name):
    """This returns the surface number given the surface name. If it doesn't exist it prints a warning and returns 0 instead of failing."""
    if self.surFromName.has_key(name):
      return self.surFromName[name]
    else:
      print 'Warning: Surface %s does not exist'%name
      return 0

  def getDt(self):
    return self.step

  def getRemTime(self):
    return self.timeRem


  def regBodySynch(self,node,body):
    """Given a NodePath and a Body this arranges that the NodePath tracks the Body."""
    if node.hasTag('ode_key'):
      key = node.getTag('ode_key')
    else:
      key = self.nextKey
      self.nextKey += 1
      node.setPythonTag('ode_key',key)

    self.synch[key] = (node,body)

  def unregBodySynch(self,node):
    """Removes a NodePath/Body pair from the synchronisation database, so the NodePath will stop automatically tracking the Body."""
    if node.hasTag('ode_key'):
      key = node.getTag('ode_key')
      if self.synch.has_key(key):
        del self.synch[key]

  def regPreFunc(self,name,func):
    """Registers a function under a unique name to be called before every step of the physics simulation - this is different from every frame, being entirly regular."""
    self.preCollide[name] = func

  def unregPreFunc(self,name):
    """Unregisters a function to be called every step, by name."""
    if self.preCollide.has_key(name):
      del self.preCollide[name]

  def regPostFunc(self,name,func):
    """Registers a function under a unique name to be called after every step of the physics simulation - this is different from every frame, being entirly regular."""
    self.postCollide[name] = func

  def unregPostFunc(self,name):
    """Unregisters a function to be called every step, by name."""
    if self.postCollide.has_key(name):
      del self.postCollide[name]

  def regCollisionCB(self,geom,func):
    """Registers a callback that will be called whenever the given geom collides. The function must take an OdeCollisionEntry followed by a flag, which will be False if geom1 is the given geom, True if its geom2."""
    self.collCB[geom] = func

  def unregCollisionCB(self,geom):
    """Unregisters the collision callback for a given geom."""
    if self.collCB.has_key(geom):
      del self.collCB[geom]

  def regDamping(self,body,linear,angular):
    """Given a body this applies a damping force, such that the velocity and rotation will be reduced in time. If the body is already registered this will update the current setting."""
    self.damping[str(body)] = (body,linear,angular)

  def unregDampingl(self,body):
    """Unregisters a body from damping."""
    key = str(body)
    if self.damping.has_key(key):
      del self.air_resist[key]
