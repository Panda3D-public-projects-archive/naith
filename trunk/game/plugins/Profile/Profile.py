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



import subprocess

from direct.showbase import DirectObject
from pandac.PandaModules import *

class Profile(DirectObject.DirectObject):
  """Connects to pstats, if pstats is not running on the local computer it will set a copy running regardless."""
  def __init__(self,manager,xml):
    self.pstats = None

  def go(self):
    if (PStatClient.connect()==0):
      # No pstat server - create it, then try and connect again...
      self.pstats = subprocess.Popen(['pstats'])

      # Need to give pstats some time to warm up - use a do latter task...
      def tryAgain(task):
        PStatClient.connect()
      taskMgr.doMethodLater(0.5,tryAgain,'pstats again')

  def start(self):
    self.accept('f10',self.go)

  def stop(self):
    self.ignore('f10')

  def reload(self,manager,xml):
    pass

  def destroy(self):
    if self.pstats!=None:
      self.pstats.kill()
