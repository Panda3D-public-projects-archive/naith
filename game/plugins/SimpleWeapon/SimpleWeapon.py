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
import random
import math

import ray_cast
import csp

from direct.actor.Actor import Actor
from direct.interval.IntervalGlobal import *
from direct.interval.ActorInterval import ActorInterval
from pandac.PandaModules import *


class SimpleWeapon:
  """Provides a simple weapon system - not very sophisticaed, but good enough to test shooting things."""
  def __init__(self,manager,xml):
    # Get the path to load weapons from...
    basePath = manager.get('paths').getConfig().find('weapons').get('path')

    # Load the weapon...
    meshPath = os.path.join(basePath,xml.find('egg').get('file'))
    self.mesh = Actor()
    self.mesh.loadModel(meshPath)
    self.mesh.setShaderAuto()

    # Get the camera interface, so we can zoom in when the player aims...
    self.camera = manager.get(xml.find('camera').get('plugin'))

    # Create our gun node - both the gun and the ray used for shooting track this - allows for gun jitter, kick back etc...
    parent = xml.find('parent')
    self.gunView = manager.get(parent.get('plugin')).getNode(parent.get('node')).attachNewNode('gun-view')

    # Parent the mesh to the gun view...
    self.mesh.reparentTo(self.gunView)

    # Set the animation going...
    self.state = False # False==casual, True==aim.
    self.nextState = False
    self.nextAni()

    # Create a ray cast to detect what the player is looking at... and what will be shot...
    self.space = manager.get('ode').getSpace()
    self.ray = OdeRayGeom(50.0)
    self.ray.setCategoryBits(BitMask32(0xfffffffe))
    self.ray.setCollideBits(BitMask32(0xfffffffe))

    # Get all the stuff we need to do the muzzle flash particle effect...
    flash = xml.find('muzzle_flash')
    self.flashManager = manager.get(flash.get('plugin'))
    self.flashEffect = flash.get('effect')
    self.flashBone = self.mesh.exposeJoint(None,"modelRoot",flash.get('bone'))
    self.flashPos = csp.getPos(flash.get('pos'))

    # Get all the stuff we need to do the bullet hit sparks effect...
    sparks = xml.find('sparks')
    self.sparksManager = manager.get(sparks.get('plugin'))
    self.sparksEffect = sparks.get('effect')

    # Create a quaternion that rotates +ve z to +ve y - used to point it in the weapon direction rather than up...
    self.zToY = Quat()
    self.zToY.setFromAxisAngle(-90.0,Vec3(1.0,0.0,0.0))

    # Variables to manage the firing state...
    self.firing = False # True if the trigger is being held.
    self.triggerTime = 0.0 # How long the trigger has been held for, so we know when to eject ammo.
    self.bulletRate = 1.0/12.5 # Used G36 as reference
    self.bulletSpeed = 920.0 # Used G36 as reference - muzzle velocity, not bothering with air resistance.
    self.bulletWeight = 0.004 # 5.56x45mm NATO
    

    # Arrange a task to handle the gun shooting...
    def gunControl(task):
      # Update the gun direction ray to follow the players view...
      self.ray.setPosition(self.gunView.getPos(render))
      self.ray.setQuaternion(self.zToY.multiply(self.gunView.getQuat(render)))

      # If the gun is firing update the trigger time, if a bullet is ejected do the maths...
      if self.firing:
        dt = globalClock.getDt()
        self.triggerTime += dt
        while self.triggerTime>self.bulletRate:
          self.triggerTime -= self.bulletRate
          hit,pos,norm = ray_cast.nearestHit(self.space,self.ray)

          # Create a muzzle flash effect...
          self.flashManager.doEffect(self.flashEffect, self.flashBone, True, self.flashPos)

          # Create an impact sparks effect...
          if hit!=None:
            # Calculate the reflection direction...
            rd = self.ray.getDirection()
            sparkDir = (norm * (2.0*norm.dot(rd))) - rd
            
            # Convert the reflection direction into a quaternion that will rotate +ve z to the required direction...
            try:
              ang = -math.acos(sparkDir[2])
            except:
              print 'Angle problem', sparkDir
              ang = 0.0
            axis = Vec3(0.0,0.0,1.0).cross(sparkDir)
            axis.normalize()
            sparkQuat = Quat()
            sparkQuat.setFromAxisAngleRad(ang,axis)
            
            # Set it going...
            self.sparksManager.doEffect(self.sparksEffect, render, False, pos, sparkQuat)
          
          # Impart some energy on the object...
          if hit!=None and hit.hasBody():
            body = hit.getBody()
            
            # Calculate the force required to supply the energy the bullet contains to the body...
            force = self.bulletWeight*self.bulletSpeed/0.05

            # Get the direction of travel of the bullet, multiply by force...
            d = self.ray.getDirection()
            d *= force

            # If the object is asleep awaken it...
            if not body.isEnabled():
              body.enable()

            # Add the force to the object...
            body.addForceAtPos(d,pos)

      return task.cont

    taskMgr.add(gunControl,'GunControl')


  def nextAni(self):
    self.state = self.nextState
    if self.state:
      ani = random.choice(('aim_wiggle_a','aim_wiggle_b','aim_wiggle_c'))
    else:
      ani = random.choice(('casual_wiggle_a','casual_wiggle_b','casual_wiggle_c'))
    self.mesh.pose(ani,0)
    self.interval = Sequence(self.mesh.actorInterval(ani),Func(self.nextAni))
    self.interval.start()

  def setAiming(self,s):
    if self.nextState!=s:
      self.interval.pause()
      self.nextState = s
      self.camera.setZoomed(s)
      
      def wib():
        self.interval.finish()
      
      if s: ani = 'casual_aim'
      else: ani = 'aim_casual'
      transition = Sequence(self.mesh.actorInterval(ani),Func(wib))
      transition.start()

  def setFiring(self,s):
    self.firing = s
    if self.firing:
      self.triggerTime = 0.0
