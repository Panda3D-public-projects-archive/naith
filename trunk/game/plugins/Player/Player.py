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



import math

from pandac.PandaModules import *


class Player:
  """A Player class - doesn't actually do that much, just arranges collision detection and provides a camera mount point, plus an interface for the controls to work with. All configured of course."""
  def __init__(self,manager,xml):
    self.manager = manager
    
    # Get the players dimensions, and other stuff...
    self.height = 1.7
    self.crouchHeight = 0.7
    self.radius = 0.3
    self.headHeight = 1.6
    self.crouchHeadHeight = 0.6
    self.crouchSpeed = 4.0
    
    self.playerBaseImpulse = 15000.0 # Always avaliable - air control.
    self.playerImpulse = 75000.0 # Only when on ground
    
    self.jumpForce = 16000.0
    self.jumpThreshold = 0.1 # How long ago the player must of touched the floor for them to be allowed to jump - gives them a bit of lee way.
    
    self.mass = 70.0
    self.airResistance = 9.8/(30.0**2.0) # 30m/s is terminal velocity - not realistic but any faster and we have a problem - could punch through the floor.

    # Create the players stomach node path - this is in the centre of the player, and is used by the collision system...
    self.stomach = render.attachNewNode('player-stomach')
    self.stomach.setPos(render,0.0,0.0,0.5*self.height)

    # Create the players feet node path - this is the node path updated by the rotation and movement controls...
    self.feet = self.stomach.attachNewNode('player-feet')

    # Create the players neck node - this rotates, the body follows...
    self.neck = self.stomach.attachNewNode('player-neck')

    # Create the players head node path, where the players head is - used to get the view in the right position...
    self.view = self.neck.attachNewNode('player-head')
    self.view.setPos(render,0.0,0.0,0.0 + self.headHeight)

    # Setup the body...
    ode = manager.get('ode')
    self.body = OdeBody(ode.getWorld())
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
    ode.getSpace().add(self.colStanding)
    ode.getSpace().setSurfaceType(self.colStanding,ode.getSurface('player'))

    self.colCrouching = OdeCappedCylinderGeom(self.radius,self.crouchHeight - self.radius*2.0)
    self.colCrouching.setBody(self.body)
    self.colCrouching.setCategoryBits(BitMask32(0))
    self.colCrouching.setCollideBits(BitMask32(0))
    ode.getSpace().add(self.colCrouching)
    ode.getSpace().setSurfaceType(self.colCrouching,ode.getSurface('player'))

    # We also need to store that a jump has been requested...
    self.doJump = False
    self.midJump = False
    self.lowVert = None # Lowest point of collision for the player each frame - to detect if they are on the floor or not
    self.lastOnFloor = 0.0 # How long ago since the player was on the floor - we give a threshold before we stop allowing jumping. Needed as ODE tends to make you alternate between touching/not touching.

    # Need to know if we are crouching or not...
    self.crouching = False
    self.crouchingTarget = False
    

    # Arrange for the players stomach to track the players feet. Well, manage most of the physics at any rate...
    def playerTask(task):
      # Get the stuff we need - current velocity, target velocity and length of time step...
      vel = self.body.getLinearVel()
      targVel = self.feet.getPos()
      self.feet.setPos(0.0,0.0,0.0)
      dt = globalClock.getDt()
      
      # Find out if the player is touching the floor or not - we check if the bottom hemisphere has touched anything - this uses the lowest collision point callback setup below...
      playerLoc = self.stomach.getPos(render)
      if self.crouching: # radius is reduces below to prevent the player climbing really steep ramps.
        playerKneeHeight = playerLoc[2] - self.crouchHeight*0.5 + self.radius*0.75
      else:
        playerKneeHeight = playerLoc[2] - self.height*0.5 + self.radius*0.75
      if (self.lowVert!=None) and (self.lowVert[2]<playerKneeHeight):
        self.lastOnFloor = 0.0
      else:
        self.lastOnFloor += dt
      onFloor = self.lastOnFloor<self.jumpThreshold

      # Update feet direction to be pointing in the same direction as the neck - so we walk forwards...
      self.feet.setQuat(self.neck.getQuat())

      # Calculate the total force we would *like* to apply...
      force = targVel - vel
      force *= self.mass/dt

      # Cap the liked force by how strong the player actually is...
      forceCap = self.playerBaseImpulse
      if onFloor: forceCap += self.playerImpulse
      forceCap *= dt # Not really ideal - should really do this per physics step.
      
      force[0] = max(min(force[0],forceCap),-forceCap)
      force[1] = max(min(force[1],forceCap),-forceCap)
      force[2] = 0.0 # Can't fight gravity

      # Add to the liked force any pending jump, if allowed...
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

      # Simple hack to limit how much air the player gets off the top of ramps - need a better solution. It still allows for some air and other solutions involve the player punching through ramps...
      if (not onFloor) and (not self.midJump) and (vel[2]>0.0):
        vel[2] = 0.0
        self.body.setLinearVel(vel)

      # Crouching - this switches between the two cylinders immediatly on a mode change...
      if self.crouching!=self.crouchingTarget:
        self.crouching = self.crouchingTarget
        if self.crouching:
          # Going down...
          self.colStanding.setCategoryBits(BitMask32(0))
          self.colStanding.setCollideBits(BitMask32(0))
          self.colCrouching.setCategoryBits(BitMask32(1))
          self.colCrouching.setCollideBits(BitMask32(1))

          offset = Vec3(0.0,0.0,0.5*(self.crouchHeight-self.height))
          self.body.setPosition(self.body.getPosition() + offset)
          self.stomach.setPos(self.stomach,offset)
          self.view.setPos(self.view,-offset)
        else:
          # Going up...
          self.colStanding.setCategoryBits(BitMask32(1))
          self.colStanding.setCollideBits(BitMask32(1))
          self.colCrouching.setCategoryBits(BitMask32(0))
          self.colCrouching.setCollideBits(BitMask32(0))

          offset = Vec3(0.0,0.0,0.5*(self.height-self.crouchHeight))
          self.body.setPosition(self.body.getPosition() + offset)
          self.stomach.setPos(self.stomach,offset)
          self.view.setPos(self.view,-offset)

      # Crouching - this makes the height height head towards the correct height, to give the perception that crouching takes time...
      currentHeight = self.view.getZ() - self.neck.getZ()
      if self.crouching:
        targetHeight = self.crouchHeadHeight - 0.5*self.crouchHeight
        newHeight = max(targetHeight,currentHeight - self.crouchSpeed * dt)
      else:
        targetHeight = self.headHeight - 0.5*self.height
        newHeight = min(targetHeight,currentHeight + self.crouchSpeed * dt)
      self.view.setZ(newHeight)

      return task.cont

    taskMgr.add(playerTask,'Player')


    # Need a pre-collision thing going, to reset the position the player is effectivly standing on...
    def playerStandReset():
      self.lowVert = None

    ode.regPreFunc('playerStandReset',playerStandReset)


    # We also need the player to stay upright - for stability this must be updated after every physics time step rather than every frame, we also take this opportunity to move the stomach to match the collision object...
    def playerStandUp():
      self.body.setQuaternion(Quat())
      self.body.setTorque(0.0,0.0,0.0)
      self.stomach.setPos(render,self.body.getPosition())

    ode.regPostFunc('playerStandUp',playerStandUp)


    # To know if the player is on the floor or airborne we have to intecept collisions between the players capsule and everything else...
    def onPlayerCollide(entry,which):
      try:
        # 1.6.0 code...
        for i in xrange(entry.getNumContactPoints()):
          v = entry.getContactPoint(i)
          if self.lowVert==None or self.lowVert[2]>v[2]:
            self.lowVert = v
      except:
        # 1.6.1 code...
        for i in xrange(entry.getNumContacts()):
          v = entry.getContactPoint(i)
          if self.lowVert==None or self.lowVert[2]>v[2]:
            self.lowVert = v

    ode.regCollisionCB(self.colStanding,onPlayerCollide)
    ode.regCollisionCB(self.colCrouching,onPlayerCollide)


  def start(self):
    # Get the players starting position and rotation...
    start = self.manager.get('level').getByIsA('PlayerStart')
    if len(start)>0:
      start = start[0]
      self.neck.setH(start.getH(render))
      self.stomach.setPos(start.getPos(render))
      self.stomach.setPos(self.stomach,0.0,0.0,0.5*self.height)
      self.body.setPosition(self.stomach.getPos(render))


  def crouch(self):
    """Makes the player crouch, unless they are already doing so."""
    self.crouchingTarget = True

  def standup(self):
    """Makes the player stand up from crouching."""
    self.crouchingTarget = False

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