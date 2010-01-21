# -*- coding: utf-8 -*-
# Copyright 2009 Reinier de Blois, Tom SF Haines
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
from direct.directbase import DirectStart
from sys import exit
import datetime



class Window:
  """This plugin creates a window for rendering into."""
  def __init__(self, manager, xml):
    base.openDefaultWindow()
    render.setAntialias(AntialiasAttrib.MAuto)
    base.setBackgroundColor(0.0, 0.0, 0.0)

    self.task = None

  def reload(self,manager,xml):
    pass

  screenshot = lambda self: base.screenshot()
  wireframe  = lambda self: base.toggleWireframe()


  def record(self,task):
    base.screenshot(defaultFilename=False,namePrefix=('video|%s|%04i.jpg'%(self.video,self.frameNum)))
    self.frameNum += 1
    return task.cont

  def toggleRecording(self):
    if self.task==None:
      self.frameNum = 0
      self.video = datetime.datetime.now().strftime('%Y-%m-%d|%H:%M:%S')
      self.task = taskMgr.add(self.record,'RecordFrames')
      globalClock.setMode(ClockObject.MNonRealTime)
      globalClock.setFrameRate(25.0)
      print 'started recording'
    else:
      globalClock.setMode(ClockObject.MNormal)
      taskMgr.remove(self.task)
      self.task = None
      print 'ended recording'
