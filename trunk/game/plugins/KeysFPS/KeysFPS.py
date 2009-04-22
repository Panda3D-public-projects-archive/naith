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



from pandac.PandaModules import *
from direct.showbase import DirectObject


class KeysFPS(DirectObject.DirectObject):
  """This intercepts the FPS typical keys, and sends the offsets to a configured NodePath."""
  def __init__(self,manager,xml):
    # Setup state variables...
    self.forward = 0
    self.backward = 0
    self.left = 0
    self.right = 0

    # Get the node to update...
    offset = xml.find('offset')
    if offset!=None:
      self.node = manager.get(offset.get('plugin')).getNode(offset.get('node'))
      self.speed = float(offset.get('speed'))
      self.slowSpeed = float(offset.get('slowSpeed'))
    else:
      self.node = None
      self.speed = 5.0
      self.slowSpeed = 2.5

    self.slow = False

    # Get the jump function call...
    jump = xml.find('jump')
    self.doJump = getattr(manager.get(jump.get('plugin')),jump.get('method'))

    # Get the weapon object to control...
    self.weapon = manager.get(xml.find('weapon').get('plugin'))
    
    # Setup the task that updates feet to be relative to whatever in temrs of velocity...
    taskMgr.add(self.keysTask,'Keys',sort=-100)


  def keysTask(self,task):
    if self.slow: speed = self.slowSpeed
    else: speed = self.speed
    
    walk = float(self.forward-self.backward) * speed
    strafe = float(self.right-self.left) * speed
    
    self.node.setPos(self.node,strafe,walk,0.0)
    
    return task.cont


  def setForward(self,state):
    self.forward = state

  def setBackward(self,state):
    self.backward = state

  def setLeft(self,state):
    self.left = state

  def setRight(self,state):
    self.right = state

  def jump(self):
    if not self.slow:
      self.doJump()


  def shoot(self):
    self.weapon.setFiring(True)

  def dontShoot(self):
    self.weapon.setFiring(False)

  def aim(self):
    self.slow = True
    self.weapon.setAiming(True)

  def relax(self):
    self.slow = False
    self.weapon.setAiming(False)


  def start(self):
    self.accept('w',self.setForward,[1])
    self.accept('w-up',self.setForward,[0])
    self.accept('s',self.setBackward,[1])
    self.accept('s-up',self.setBackward,[0])
    self.accept('a',self.setLeft,[1])
    self.accept('a-up',self.setLeft,[0])
    self.accept('d',self.setRight,[1])
    self.accept('d-up',self.setRight,[0])
    self.accept('space',self.jump)

    self.accept('mouse1',self.shoot)
    self.accept('mouse1-up',self.dontShoot)
    self.accept('mouse3',self.aim)
    self.accept('mouse3-up',self.relax)

  def stop(self):
    self.ignoreAll()

    self.forward = 0
    self.backward = 0
    self.left = 0
    self.right = 0


  def reload(self,manager,xml):
    pass # Wrong due to references of other objects taken