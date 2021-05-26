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



from panda3d.core import *
from direct.showbase import DirectObject


class MethodOnKey(DirectObject.DirectObject):
  """This intercepts a single key press, calling a named method of a named plugin when intercepted."""
  def __init__(self,manager,xml):
    self.reload(manager,xml)

  def reload(self,manager,xml):
    self.actions = []
    for action in xml.findall('action'):
      a = getattr(manager.get(action.get('plugin')),action.get('method'))
      k = action.get('key')
      self.actions.append((k,a))

  def action(self,i):
    self.actions[i][1]()

  def start(self):
    for i in range(len(self.actions)):
      self.accept(self.actions[i][0],self.action,[i])

  def stop(self):
    self.ignoreAll()
