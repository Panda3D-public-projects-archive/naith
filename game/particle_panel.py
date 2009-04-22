#! /usr/bin/env python

# Particle panel - copied from Panda examples and then editted for extra functionality - original authors Shao Zhang, Phil Saltzman.
# Useful for editting the various particles contained within this directory.

import sys
from pandac.PandaModules import *
from direct.showbase import DirectObject
import direct.directbase.DirectStart


# Get the particle panel up - requires tk...
import _tkinter
base.startTk()
from direct.tkpanels.ParticlePanel import ParticlePanel


# Create the particle panel...
pp = ParticlePanel()
base.setBackgroundColor(0.0,0.0,0.0)

# Setup some basic rotating around code...
class MouseRot(DirectObject.DirectObject):
  def __init__(self):
    base.disableMouse()
    self.centre = render.attachNewNode('cam-centre')
    base.camera.reparentTo(self.centre)
    base.camera.setY(-10.0)

    self.prevX = 0.0
    self.prevY = 0.0
    self.mouseDown = False
    
    taskMgr.add(self.mouseTask,'Mouse')

    self.accept('mouse1',self.down)
    self.accept('mouse1-up',self.up)
    self.accept('escape',sys.exit)

  def down(self):
    self.mouseDown = True
    md = base.win.getPointer(0)
    self.prevX = md.getX()
    self.prevY = md.getY()

  def up(self):
    self.mouseDown = False

  def mouseTask(self,task):
    if self.mouseDown:
      md = base.win.getPointer(0)

      dX = md.getX() - self.prevX
      dY = md.getY() - self.prevY

      self.centre.setHpr(self.centre,dX,dY,0.0)
      
      self.prevX = md.getX()
      self.prevY = md.getY()

    return task.cont


mr = MouseRot()


# Set panda going...
run()  