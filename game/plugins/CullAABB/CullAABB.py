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


class CullAABB:
  def __init__(self,manager,xml):
    self.reload(manager,xml)

  def reload(self,manager,xml):
    # Get the level plugin to load the culling AABB's from...
    levelXML = xml.find('level')
    if levelXML!=None:
      levelPlugin = levelXML.get('plugin','level')
    else:
      levelPlugin = 'level'
    level = manager.get(levelPlugin)

    # Load the AABB's into a list of bounds...
    bounds = []
    for node in level.getByIsA('CullAABB'):
      minP = Point3()
      maxP = Point3()
      node.calcTightBounds(minP,maxP)
      bounds.append(((minP[0],maxP[0]),(minP[1],maxP[1]),(minP[2],maxP[2])))

    # If debug print them out...
    if xml.find('debug')!=None:
      print 'bounds = ',bounds