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
from direct.showbase import DirectObject


class MethodOnKey(DirectObject.DirectObject):
  """This intercepts a single key press, calling a named method of a named plugin when intercepted."""
  def __init__(self,manager,xml):
    self.reload(manager,xml)

  def reload(self,manager,xml):
    action = xml.find('action')
    self.doAction = getattr(manager.get(action.get('plugin')),action.get('method'))
    self.key = action.get('key')

  def action(self):
    self.doAction()

  def start(self):
    self.accept(self.key,self.action)

  def stop(self):
    self.ignoreAll()