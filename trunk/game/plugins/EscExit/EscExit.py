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


class EscExit(DirectObject.DirectObject):
  """This arranges it so that the escape key causes the program to instantly exit. Note that it disables this feature during a transition - this is required otherwise this object could never be deleted."""
  def __init__(self,manager,xml):
    pass

  def start(self):
    self.accept('escape',sys.exit)

  def stop(self):
    self.ignore('escape')

  def reload(self,manager,xml):
    pass
