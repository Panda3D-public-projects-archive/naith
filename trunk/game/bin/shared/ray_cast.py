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



import math

from pandac.PandaModules import *


def nearestHit(space,ray):
  """Collides the given ray with the space provided by the ode module - returns (None,None,None) if it fails to hit anything or a tuple of (geom,position,normal) of the closest point that it does hit."""
  bestGeom = None
  bestPos = None
  bestMan = None
  bestNorm = None

  rayPos = ray.getPosition()

  for i in xrange(space.getNumGeoms()):
    geom = space.getGeom(i)

    testA = (geom.getCollideBits() & ray.getCollideBits()).isZero()
    testB = (ray.getCollideBits() & geom.getCollideBits()).isZero()
    if (not testA) or (not testB):
      cc = OdeUtil.collide(ray,geom)
      for j in xrange(cc.getNumContacts()):
        pos = cc.getContactPoint(j)
        norm = cc.getContactGeom(j).getNormal()
        
        man = sum(map(lambda i: abs(pos[i]-rayPos[i]),xrange(3)))
        if (bestMan==None) or (man<bestMan):
          bestGeom = geom
          bestPos = pos
          bestMan = man
          bestNorm = norm

  # Tempory code, needed until 1.6.2 (I think)...
  if bestNorm!=None:
    nl = bestNorm.length()
    if not (nl<1.5 and nl>0.5): # Writen like this for a very good reason - do not touch unless you understand Nan!
      bestNorm = -ray.getDirection()

  return (bestGeom,bestPos,bestNorm)

#def nearestHit(space,ray):
  #"""Collides the given ray with the space provided by the ode module - returns (None,None,None) if it fails to hit anything or a tuple of (geom,position,normal) of the closest point that it does hit."""
  #bestPos = None
  #bestNorm = None
  #bestGeom = None
  #bestDepth = None

  #cc = OdeUtil.collide(ray,OdeUtil.spaceToGeom(space))
  #for i in xrange(cc.getNumContacts()):
    #cg = cc.getContactGeom(i)
    #depth = cg.getDepth()
    #if bestDepth==None or bestDepth>depth:
      #bestPos = cg.getPos()
      #bestNorm = cg.getNormal()
      #bestGeom = cg.getG1()
      #if bestGeom==ray:
        #bestGeom = cg.getG2()
      #bestDepth = depth

  #return (bestGeom,bestPos,bestNorm)
  
  
def collides(space,obj):
  """Not really ray related, but similar to above. Tests if the given obj collides with anything in the given space - returns True if it does, False if it does not."""
  for i in xrange(space.getNumGeoms()):
    geom = space.getGeom(i)

    testA = (geom.getCollideBits() & obj.getCollideBits()).isZero()
    testB = (obj.getCollideBits() & geom.getCollideBits()).isZero()
    if (not testA) or (not testB):
      cc = OdeUtil.collide(obj,geom)
      if cc.getNumContacts()!=0:
        return True

  return False