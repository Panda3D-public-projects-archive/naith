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


class Loading:
  """Does a loading screen - renders some stuff whilst a transition is happenning."""
  def __init__(self,manager,xml):
    self.reload(manager,xml)

  def reload(self,manager,xml):
    self.node = loader.loadModel('data/weapons/assault/assault') ###########################
    self.node.reparentTo(aspect2d)
    self.node.setHpr(90.0,0.0,0.0)


  def start(self):
    self.node.hide()

  def stop(self):
    self.node.show()