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



class Global:
  """This provides global access to lumps of configuration xml - allows other plugin objects to get at the xml it is given."""
  def __init__(self,manager,xml):
    self.xml = xml

  def reload(self,manager,xml):
    self.xml = xml

  def getConfig(self):
    return self.xml