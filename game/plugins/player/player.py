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



import math
import random

from pandac.PandaModules import *

import ray_cast


class Player:
  """A Player class - doesn't actually do that much, just arranges collision detection and provides a camera mount point, plus an interface for the controls to work with. All configured of course."""
  def __init__(self,manager,xml):
    # Create the nodes...
    self.stomach = render.attachNewNode('player-stomach')
    self.feet = self.stomach.attachNewNode('player-feet')
    self.neck = self.stomach.attachNewNode('player-neck')
    self.view = self.neck.attachNewNode('player-head')

    # Other variables...
    self.body = None
    self.colStanding = None
    self.colCrouching = None
    self.standCheck = None

    # Do the setup code...
    self.reload(manager,xml)


  def destroy(self):
    self.stomach.removeNode()
    self.feet.removeNode()
    self.neck.removeNode()
    self.view.removeNode()
    
    if self.body!=None:
      self.body.destroy()
    if self.colStanding!=None:
      self.colStanding.destroy()
    if self.colCrouching!=None:
      self.colCrouching.destroy()
    if self.standCheck!=None:
      self.standCheck.destroy()


  def reload(self,manager,xml):
    self.manager = manager

    # Get the players dimensions...
    size = xml.find('size')
    if size!=None:
      self.height = float(size.get('height',1.55))
      self.crouchHeight = float(size.get('crouchHeight',0.7))
      self.radius = float(size.get('radius', 0.3))
      self.headHeight = float(size.get('headHeight',1.4))
      self.crouchHeadHeight = float(size.get('crouchHeadHeight',0.6))
    else:
      self.height = 1.55
      self.crouchHeight = 0.7
      self.radius = 0.3
      self.headHeight = 1.4
      self.crouchHeadHeight = 0.6

    # Get the players power...
    power = xml.find('power')
    if power!=None:
      self.playerBaseImpulse = float(power.get('baseImpulse',15000.0))
      self.playerImpulse = float(power.get('feetImpulse',75000.0))
      self.crouchSpeed = float(power.get('crouchSpeed',4.0))
      self.jumpForce = float(power.get('jumpForce',16000.0))
      self.jumpThreshold = float(power.get('jumpLeeway',0.1))
    else:
      self.playerBaseImpulse = 15000.0 # Always avaliable - air control.
      self.playerImpulse = 75000.0 # Only when on ground
      self.crouchSpeed = 4.0
      self.jumpForce = 16000.0
      self.jumpThreshold = 0.1 # How long ago the player must of touched the floor for them to be allowed to jump - gives them a bit of lee way an copes with physics system jitter.

    # Get the players mass and terminal velocity...
    body = xml.find('body')
    if body!=None:
      self.mass = float(body.get('mass',70.0))
      self.airResistance = 9.8/(float(body.get('mass',30.0))**2.0)
    else:
      self.mass = 70.0
      self.airResistance = 9.8/(30.0**2.0)


    # Setup the node positions...
    self.stomach.setPos(render,0.0,0.0,0.5*self.height)
    self.view.setPos(render,0.0,0.0,0.0 + self.headHeight)

    # Get the physics object...
    physics = xml.find('physics')
    if physics!=None:
      odeName = physics.get('plugin','ode')
    else:
      odeName = 'ode'
    self.ode = manager.get(odeName)

    # Clean up any previous collision objects...
    if self.body!=None:
      self.body.destroy()
    if self.colStanding!=None:
      self.colStanding.destroy()
    if self.colCrouching!=None:
      self.colCrouching.destroy()
    if self.standCheck!=None:
      self.standCheck.destroy()

    # Setup the body...
    self.body = OdeBody(self.ode.getWorld())
    mass = OdeMass()
    mass.setCapsuleTotal(self.mass,3,self.radius,self.height - self.radius*2.0)
    self.body.setMass(mass)
    self.body.setPosition(self.stomach.getPos(render))
    self.body.setAutoDisableFlag(False)

    # Create a collision object - a capsule - we actually make two - one for standing, the other for crouching...
    self.colStanding = OdeCappedCylinderGeom(self.radius,self.height - self.radius*2.0)
    self.colStanding.setBody(self.body)
    self.colStanding.setCategoryBits(BitMask32(1))
    self.colStanding.setCollideBits(BitMask32(1))
    self.ode.getSpace().add(self.colStanding)
    self.ode.getSpace().setSurfaceType(self.colStanding,self.ode.getSurface('player'))

    self.colCrouching = OdeCappedCylinderGeom(self.radius,self.crouchHeight - self.radius*2.0)
    self.colCrouching.setBody(self.body)
    self.colCrouching.setCategoryBits(BitMask32(0))
    self.colCrouching.setCollideBits(BitMask32(0))
    self.ode.getSpace().add(self.colCrouching)
    self.ode.getSpace().setSurfaceType(self.colCrouching,self.ode.getSurface('player'))

    # Create a collision object ready for use when checking if the player can stand up or not - just a sphere with the relevant radius...
    self.standCheck = OdeSphereGeom(self.radius)
    self.standCheck.setCategoryBits(BitMask32(0xFFFFFFFE))
    self.standCheck.setCollideBits(BitMask32(0xFFFFFFFE))
    
    # We also need to store when a jump has been requested...
    self.doJump = False
    self.midJump = False
    self.surNormal = None # Surface normal the player is standing on.
    self.lastOnFloor = 0.0 # How long ago since the player was on the floor - we give a threshold before we stop allowing jumping. Needed as ODE tends to make you alternate between touching/not touching.

    # Need to know if we are crouching or not...
    self.crouching = False
    self.crouchingTarget = False

    # Used to slow the player down as they walk up a ramp...
    self.forceFalloff = 1.0


  # Player task - basically handles crouching as everything else is too physics engine dependent to be per frame...
  def playerTask(self,task):
    dt = globalClock.getDt()
    
    # Crouching - this switches between the two cylinders immediatly on a mode change...
    if self.crouching!=self.crouchingTarget:
      if self.crouchingTarget:
        # Going down - always possible...
        self.crouching = self.crouchingTarget

        self.colStanding.setCategoryBits(BitMask32(0))
        self.colStanding.setCollideBits(BitMask32(0))
        self.colCrouching.setCategoryBits(BitMask32(1))
        self.colCrouching.setCollideBits(BitMask32(1))

        offset = Vec3(0.0,0.0,0.5*(self.crouchHeight-self.height))
        self.body.setPosition(self.body.getPosition() + offset)
        self.stomach.setPos(self.stomach,offset)
        self.view.setPos(self.view,-offset)
      else:
        # Going up - need to check its safe to do so...
        pos = self.body.getPosition()

        canStand = True
        pos[2] += self.height - 0.5*self.crouchHeight
        space = self.ode.getSpace()

        sc = int(math.ceil((self.height-self.crouchHeight)/self.radius))
        for h in xrange(sc): # This is needed as a cylinder can miss collisions if tested this way.
          pos[2] -= self.radius
          self.standCheck.setPosition(pos)
          if ray_cast.collides(space,self.standCheck):
            canStand = False
            break

        if canStand:
          self.crouching = self.crouchingTarget

          self.colStanding.setCategoryBits(BitMask32(1))
          self.colStanding.setCollideBits(BitMask32(1))
          self.colCrouching.setCategoryBits(BitMask32(0))
          self.colCrouching.setCollideBits(BitMask32(0))

          offset = Vec3(0.0,0.0,0.5*(self.height-self.crouchHeight))
          self.body.setPosition(self.body.getPosition() + offset)
          self.stomach.setPos(self.stomach,offset)
          self.view.setPos(self.view,-offset)

    # Crouching - this makes the height head towards the correct height, to give the perception that crouching takes time...
    currentHeight = self.view.getZ() - self.neck.getZ()
    if self.crouching:
      targetHeight = self.crouchHeadHeight - 0.5*self.crouchHeight
      newHeight = max(targetHeight,currentHeight - self.crouchSpeed * dt)
    else:
      targetHeight = self.headHeight - 0.5*self.height
      newHeight = min(targetHeight,currentHeight + self.crouchSpeed * dt)
    self.view.setZ(newHeight)

    return task.cont


  def playerPrePhysics(self):
    # Get the stuff we need - current velocity, target velocity and length of time step...
    vel = self.body.getLinearVel()
    targVel = self.feet.getPos()
    dt = self.ode.getDt()

    # Check if the player is standing still or moving - if moving try and obtain the players target velocity, otherwsie try to stand still, incase the player is on a slope and otherwise liable to slide (Theres a threshold to keep behaviour nice - slope too steep and you will slide.)...
    if targVel.lengthSquared()<1e-2 and vel.lengthSquared()<1e-1:
      # Player standing still - head for last standing position...
      targVel = self.targPos - self.stomach.getPos()
      targVel /= 0.1 # Restoration time
      targVel[2] = 0.0 # Otherwise a vertical drop onto a slope can causes the player to do mini jumps to try and recover (!).
    else:
      # Player moving - use targVel and update last standing position...
      self.targPos = self.stomach.getPos()

      # Rotate the target velocity to account for the players facing direction...
      rot = Mat3()
      self.neck.getQuat().extractToMatrix(rot)
      targVel = rot.xformVecGeneral(targVel)


    # Find out if the player is touching the floor or not - we check if the bottom hemisphere has touched anything - this uses the lowest collision point from the last physics step...
    if (self.surNormal!=None) and (self.surNormal[2]>0.0):
      self.lastOnFloor = 0.0
    else:
      self.lastOnFloor += dt
    onFloor = self.lastOnFloor<self.jumpThreshold

    # Calculate the total force we would *like* to apply...
    force = targVel - vel
    force *= self.mass/dt
    
    # Cap the liked force by how strong the player actually is and fix the player to apply force in the direction of the floor...
    forceCap = self.playerBaseImpulse
    if onFloor: forceCap += self.playerImpulse
    forceCap *= dt

    if self.surNormal==None:
      force[2] = 0.0
    else:
      # This projects the force into the plane of the surface the player is standing on...
      fx  = force[0] * (1.0-self.surNormal[0]*self.surNormal[0])
      fx += force[1] * -self.surNormal[0]*self.surNormal[1]
      fx += force[2] * -self.surNormal[0]*self.surNormal[2]

      fy  = force[0] * -self.surNormal[1]*self.surNormal[0]
      fy += force[1] * (1.0-self.surNormal[1]*self.surNormal[1])
      fy += force[2] * -self.surNormal[1]*self.surNormal[2]

      fz  = force[0] * -self.surNormal[2]*self.surNormal[0]
      fz += force[1] * -self.surNormal[2]*self.surNormal[1]
      fz += force[2] * (1.0-self.surNormal[2]*self.surNormal[2])

      force[0] = fx
      force[1] = fy
      force[2] = fz

      # If the ramp is too steep, you get no force - and fall back down again...
      if force[2]>1e-3:
        forceCap *= max(self.surNormal[2] - 0.8,0.0)/(1.0-0.8)

    fLen = force.length()
    if fLen>forceCap:
      force *= forceCap/fLen

    # Add to the force so far any pending jump, if allowed...
    if self.doJump and onFloor and not self.midJump:
      force[2] += self.jumpForce
      self.midJump = True
    self.doJump = False

    # Apply air resistance to the player - only for falling - air resistance is direction dependent!
    if vel[2]<0.0:
      force[2] -= self.airResistance*vel[2]*vel[2]
      self.midJump = False

    # Apply the force...
    self.body.addForce(force)

    # Simple hack to limit how much air the player gets off the top of ramps - need a better solution. It still allows for some air, but other solutions involve the player punching through ramps...
    if (not onFloor) and (not self.midJump) and (vel[2]>0.0):
      vel[2] = 0.0
      self.body.setLinearVel(vel)
    
    # We have to reset the record of the lowest point the player is standing on ready for the collision callbacks to recalculate it ready for the next run of this handler...
    self.surNormal = None


  def playerPostPhysics(self):
    # Zero out all rotation...
    self.body.setQuaternion(Quat())
    self.body.setAngularVel(Vec3(0.0,0.0,0.0))
    
    # Update the panda node position to match the ode body position...
    pp = self.body.getPosition() + self.body.getLinearVel()*self.ode.getRemTime() # Interpolation from physics step for smoother movement - due to physics being on a constant frame rate.
    self.stomach.setPos(render,pp)


  def onPlayerCollide(self,entry,which):
    # Handles the players collisions - used to work out the orientation of the surface the player is standing on...
    for i in xrange(entry.getNumContacts()):
      n = entry.getContactGeom(i).getNormal()
      if which:
        n *= -1.0

      if self.surNormal==None or n[2]>self.surNormal[2]:
        self.surNormal = n


  def start(self):
    self.reset()
    
    # Arrange all the tasks/callbacks required...
    self.task = taskMgr.add(self.playerTask, 'PlayerTask')
    self.ode.regPreFunc('playerPrePhysics', self.playerPrePhysics)
    self.ode.regPostFunc('playerPostPhysics', self.playerPostPhysics)

    # To know if the player is on the floor or airborne we have to intecept collisions between the players capsules and everything else...
    self.ode.regCollisionCB(self.colStanding, self.onPlayerCollide)
    self.ode.regCollisionCB(self.colCrouching, self.onPlayerCollide)


  def stop(self):
    taskMgr.remove(self.task)
    self.ode.unregPreFunc('playerPrePhysics')
    self.ode.unregPostFunc('playerPostPhysics')

    self.ode.unregCollisionCB(self.colStanding)
    self.ode.unregCollisionCB(self.colCrouching)


  def reset(self):
    """Resets the player back to their starting position. (Leaves rotation alone - this is for debuging falling out the level kinda stuff.)"""
    start = self.manager.get('level').getByIsA('PlayerStart')
    if len(start)>0:
      start = random.choice(start) # If there are multiple player starts choose one at random!
      self.neck.setH(start.getH(render))
      self.stomach.setPos(start.getPos(render))
    else:
      self.neck.setH(0.0)
      self.stomach.setPos(Vec3(0.0,0.0,0.0))

    self.stomach.setPos(self.stomach,0.0,0.0,0.5*self.height)
    self.body.setPosition(self.stomach.getPos(render))
    self.body.setLinearVel(Vec3(0.0,0.0,0.0))

    self.targPos = self.stomach.getPos()


  def crouch(self):
    """Makes the player crouch, unless they are already doing so."""
    self.crouchingTarget = True

  def standup(self):
    """Makes the player stand up from crouching."""
    self.crouchingTarget = False

  def isCrouched(self):
    """Tells you if the player is crouching or not."""
    return self.crouching


  def jump(self):
    """Makes the player jump - only works when the player is touching the ground."""
    self.doJump = True


  def getNode(self,name):
    """Standard interface for exposing a node path to other plugins - this exposes 'view' as the players head position, and 'feet' as the players foot position."""
    if name=='view':
      return self.view
    elif name=='feet':
      return self.feet
    elif name=='stomach':
      return self.stomach
    elif name=='neck':
      return self.neck
    else:
      return None
