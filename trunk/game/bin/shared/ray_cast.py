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



import math

from pandac.PandaModules import *


def nearestHit(space,ray):
  """Collides the given ray with the space provided by the ode module - returns (None,None) if it fails to hit anything or a tuple of (geom,position) of the closest point that it does hit."""
  bestGeom = None
  bestPos = None
  bestMan = None

  rayPos = ray.getPosition()

  for i in xrange(space.getNumGeoms()):
    geom = space.getGeom(i)

    testA = (geom.getCollideBits() & ray.getCollideBits()).isZero()
    testB = (ray.getCollideBits() & geom.getCollideBits()).isZero()
    if (not testA) or (not testB):
      cc = OdeUtil.collide(ray,geom)
      for j in xrange(cc.getNumContacts()):
        try:
          # 1.6.0 code...
          contact = cc.getContact(j)
          pos = contact.getGeom().getPos()
        except:
          # 1.6.1 code...
          pos = cc.getContactPoint(j)

        man = sum(map(lambda i: abs(pos[i]-rayPos[i]),xrange(3)))
        if (bestMan==None) or (man<bestMan):
          bestGeom = geom
          bestPos = pos
          bestMan = man

  return (bestGeom,bestPos)