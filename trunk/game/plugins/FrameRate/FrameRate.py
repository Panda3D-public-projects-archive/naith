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



import sys
from direct.showbase import DirectObject


class FrameRate(DirectObject.DirectObject):
  """Toggles displaying the framerate with F12."""
  def __init__(self,manager,xml):
    self.state = False

  def toggle(self):
      self.state = not self.state
      base.setFrameRateMeter(self.state)

  def start(self):
    self.accept('f12',self.toggle)

  def stop(self):
    self.ignore('f12')

  def reload(self,manager,xml):
    pass
