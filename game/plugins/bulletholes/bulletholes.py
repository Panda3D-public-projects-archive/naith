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

from panda3d.core import CardMaker, Texture, ModelRoot, ColorBlendAttrib, TransparencyAttrib, DecalEffect, NodePath, Point2, Point3, BitMask32
from random import random

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

  def makeNew(self, pos, nor, parent = None):
    """Makes a new bullet hole."""
    if parent == None:
      parent = self.container
    else:
      # Add a subnode to the parent, if it's not already there
      child = parent.find('bullet-holes')
      if child.isEmpty():
        parent = parent.attachNewNode('bullet-holes')
      else:
        parent = child
    newhole = NodePath(self.card.generate())
    newhole.reparentTo(parent)
    newhole.lookAt(render, Point3(newhole.getPos(render) - nor))
    newhole.setR(newhole, random() * 360.0)
    newhole.setPos(render, pos)
    # Offset it a little to avoid z-fighting
    # Increase this value if you still see it.
    newhole.setY(newhole, -.001 - random() * 0.01)
    del newhole
    # We don't want one batch per bullet hole, so flatten it.
    # This could be made smarter to preserve culling, but
    # I have yet to see a performance loss.
    # The clearTexture() is a necessary hack.
    parent.clearTexture()
    parent.flattenStrong()
    parent.setTexture(self.texture)
    parent.setTransparency(TransparencyAttrib.MDual)
    parent.setShaderOff(1)
    parent.hide(BitMask32.bit(2)) # Invisible to volumetric lighting camera (speedup)
    parent.hide(BitMask32.bit(3)) # Invisible to shadow cameras (speedup)

  def destroy(self):
    self.container.removeNode()

