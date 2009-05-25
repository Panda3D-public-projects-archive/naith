# Copyright Reinier de Blois
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

from pandac.PandaModules import CardMaker, Texture, ModelRoot, ColorBlendAttrib, DecalEffect, NodePath, Point2, Point3

BULLETHOLE_SIZE = 0.05

class BulletHoles:
  """The name says it all."""
  def __init__(self,manager,xml):
    self.texture = loader.loadTexture('data/textures/bullet-hole.png')
    self.texture.setMinfilter(Texture.FTLinearMipmapLinear)
    self.container = render.attachNewNode(ModelRoot('bullet-holes'))
    self.card = CardMaker('bullet-hole')
    s = BULLETHOLE_SIZE * 0.5
    self.card.setFrame(-s, s, -s, s)
    self.card.setUvRange(Point2(0, 0), Point2(1, 1))

  def makeNew(self, pos, nor):
    newhole = NodePath(self.card.generate())
    newhole.reparentTo(self.container)
    newhole.lookAt(-Point3(nor))
    newhole.setPos(pos)
    # Offset it a little to avoid z-fighting
    # Increase this value if you still see it.
    newhole.setY(newhole, -.005)
    # We don't want one batch per bullet hole, so flatten it.
    # This could be made smarter to preserve culling, but
    # I have yet to see a performance loss.
    self.container.flattenStrong()
    self.container.setTexture(self.texture)
    self.container.setTransparency(True)
    self.container.setShaderOff(1)

  def destroy(self):
    self.container.removeNode()

