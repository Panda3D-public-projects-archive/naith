# -*- coding: utf-8 -*-
# Copyright Tom SF Haines, Aaron Snoswell
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


from pandac.PandaModules import NodePath, VBase4, BitMask32
from pandac.PandaModules import DirectionalLight as PDirectionalLight

class DirLight:
  """Creates a simple directional light"""
  def __init__(self,manager,xml):
    self.light = PDirectionalLight('dlight')
    self.lightNode = NodePath(self.light)
    self.lightNode.setCompass()
    if hasattr(self.lightNode.node(), "setCameraMask"):
      self.lightNode.node().setCameraMask(BitMask32.bit(3))

    self.reload(manager,xml)


  def reload(self,manager,xml):
    color = xml.find('color')
    if color!=None:
      self.light.setColor(VBase4(float(color.get('r')), float(color.get('g')), float(color.get('b')), 1.0))

    pos = xml.find('pos')
    if pos!=None:
      self.lightNode.setPos(float(pos.get('x')), float(pos.get('y')), float(pos.get('z')))
    else:
      self.lightNode.setPos(0, 0, 0)

    lookAt = xml.find('lookAt')
    if lookAt!=None:
      self.lightNode.lookAt(float(lookAt.get('x')), float(lookAt.get('y')), float(lookAt.get('z')))

    lens = xml.find('lens')
    if lens!=None and hasattr(self.lightNode.node(), 'getLens'):
      if bool(int(lens.get('auto'))):
        self.lightNode.reparentTo(base.camera)
      else:
        self.lightNode.reparentTo(render)
      lobj = self.lightNode.node().getLens()
      lobj.setNearFar(float(lens.get('near', 1.0)), float(lens.get('far', 100000.0)))
      lobj.setFilmSize(float(lens.get('width', 1.0)), float(lens.get('height', 1.0)))
      lobj.setFilmOffset(float(lens.get('x', 0.0)), float(lens.get('y', 0.0)))

    if hasattr(self.lightNode.node(), 'setShadowCaster'):
      shadows = xml.find('shadows')
      if shadows!=None:
        self.lightNode.node().setShadowCaster(True, int(shadows.get('width', 512)), int(shadows.get('height', 512)), int(shadows.get('sort', -10)))
        #self.lightNode.node().setPushBias(float(shadows.get('bias', 0.5)))
      else:
        self.lightNode.node().setShadowCaster(False)

  def start(self):
    render.setLight(self.lightNode)

  def stop(self):
    render.clearLight(self.lightNode)
