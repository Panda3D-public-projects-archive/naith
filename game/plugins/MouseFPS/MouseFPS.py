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



from pandac.PandaModules import *
import direct.directbase.DirectStart


class MouseFPS:
  """Provides fps style mouse control, sending the data to arbitary nodes"""
  def __init__(self,manager,xml):
    self.reload(manager,xml)


  def reload(self,manager,xml):
    # Variables needed by mouse simulation...
    self.originX = 0
    self.originY = 0
    self.speed = 0.1
    self.minY = -45.0
    self.maxY = 45.0

    speed = xml.find('speed')
    if speed!=None:
      self.speed = float(speed.get('val'))

    # Get the nodes to be updated by the mouse movement...
    xRot = xml.find('x-rot')
    if xRot!=None:
      self.xNode = manager.get(xRot.get('plugin')).getNode(xRot.get('node'))
    else:
      self.xNode = None

    yRot = xml.find('y-rot')
    if yRot!=None:
      self.yNode = manager.get(yRot.get('plugin')).getNode(yRot.get('node'))
      self.maxY = float(yRot.get('max'))
      self.minY = float(yRot.get('min'))
    else:
      self.yNode = None


  def start(self):
    # Get rid of the mouse cursor...
    props = WindowProperties()
    props.setCursorHidden(True)
    base.win.requestProperties(props)

    # Set the mouse task going...
    self.task = taskMgr.add(self.mouseTask,'Mouse',sort=-100)

  def stop(self):
    # Re-enable the mouse cursor...
    props = WindowProperties()
    props.setCursorHidden(False)
    base.win.requestProperties(props)

    # Stop the mouse task...
    taskMgr.remove(self.task)
    self.task = None


  def mouseTask(self,task):
    md = base.win.getPointer(0)
    ox = md.getX() - self.originX
    oy = md.getY() - self.originY
    self.originX = md.getX()
    self.originY = md.getY()

    # The if statement is not necessary - it exists so if you start the program with the mouse cursor outside the window and then move it into the window the camera will not jerk. It of course could prevent really fast rotation in game.
    if abs(ox)<base.win.getXSize()//3 and abs(oy)<base.win.getYSize()//3:
      if self.xNode: self.xNode.setH(self.xNode.getH() - ox*self.speed)
      if self.yNode: self.yNode.setP(min(max(self.yNode.getP() - oy*self.speed,self.minY),self.maxY))

    xoob = self.originX<base.win.getXSize()//4 or self.originX>(base.win.getXSize()*3)//4
    yoob = self.originY<base.win.getYSize()//4 or self.originY>(base.win.getYSize()*3)//4
    if xoob or yoob:
      cx = base.win.getXSize()//2
      cy = base.win.getYSize()//2
      if base.win.movePointer(0,cx,cy):
        self.originX = cx
        self.originY = cy

    return task.cont