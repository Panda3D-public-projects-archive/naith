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

from direct.gui.DirectWaitBar import DirectWaitBar
from direct.interval.IntervalGlobal import LerpFunctionInterval

class Loading:
  """Does a loading screen - renders some stuff whilst a transition is happenning."""
  def __init__(self,manager,xml):
    self.reload(manager,xml)

  def reload(self,manager,xml):
    self.node = loader.loadModel('data/weapons/assault/assault') ###########################
    self.node.reparentTo(aspect2d)
    self.node.setHpr(90.0,0.0,0.0)
    self.waitBar = DirectWaitBar(parent = render2d, text = "", value = 0, pos = (0, 0, -0.5), scale = (1, 1, 0.1), frameColor = (0, 0, 0, 0), barColor = (.8, .8, .8, 1))
    LerpFunctionInterval(self.__setProgress, 2.5, 0.0, 100.0).start()

  def __setProgress(self, progress):
    self.waitBar["value"] = progress
    self.waitBar.setValue()

  def start(self):
    render.show()
    self.waitBar.hide()
    self.node.hide()

  def stop(self):
    render.hide()
    self.waitBar.show()
    self.node.show()

