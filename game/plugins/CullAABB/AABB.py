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



class AABB:
  """Defines an axis aligned bounding box."""
  def __init__(self,low,high):
    self.x = (low[0],high[0])
    self.y = (low[1],high[1])
    self.z = (low[2],high[2])
    self.bounds = (self.x,self.y,self.z)

    self.centre = (0.5*(self.x[0]+self.x[1]),0.5*(self.y[0]+self.y[1]),0.5*(self.z[0]+self.z[1]))
    self.volume = (self.x[1]-self.x[0]) * (self.y[1]-self.y[0]) * (self.z[1]-self.z[0])

  def within(self,node):
    """Given a NodePath returns True if its in the AABB, False if it isn't."""
    pos = node.getPos()
    return pos[0]>=self.x[0] and pos[0]<=self.x[1] and pos[1]>=self.y[0] and pos[1]<=self.y[1] and pos[2]>=self.z[0] and pos[2]<=self.z[1]

  def __str__(self):
    return '{'+str(self.x)+','+str(self.y)+','+str(self.z)+'}'



aabbLambda = 1e-3
aabbCutCost = 2.0


class SetAABB:
  """A set of AABB's - uses a kd tree with hieuristic dimension detection to subdivide at each point. Each level keeps a list of aabb's that cross the dividing line."""
  def __init__(self,aabbs):
    """Given a list of AABB's."""
    # Work out what happens for dividing on each dimension - sort by the AABB's centres and then select the centre aabb by volume, then try dividing by the sides & centre of the centre aabb and count how many nodes are intercepted with a cost for offsetting too far - select the dimension division with the least divided nodes...
    # Get half the volume...
    totVolume = sum(map(lambda x:x.volume,aabbs))
    halfVolume = totVolume*0.5

    # Variables we are finding the best option for...
    bestDimension = 0
    bestCutPoint = 0.0
    bestCost = 1e20
    bestLow = []
    bestMid = aabbs
    bestHigh = []
    
    # Try each dimension, with multiple centre choice, store the best...
    for dim in xrange(3):
      byDim = sorted(aabbs,key=lambda x: x.centre[dim])
      centre = 0
      volume = 0.0
      while centre+1<len(byDim) and volume<halfVolume:
        volume += byDim[centre].voume
        centre += 1

      options = (byDim[centre].bounds[dim][0]-aabbLambda, byDim[centre].centre[dim], byDim[centre].bounds[dim][1]+aabbLambda)
      for cutPoint in options:
        cost = 0.0
        lowVol = 0.0
        highVol = 0.0
      
        low = []
        mid = []
        high = []
      
        for aabb in byDim:
          if aabb.bounds[dim][1]<cutPoint:
            lowVol += aabb.volume
            low.append(aabb)
          elif aabb.bounds[dim][0]>cutPoint:
            highVol += aabb.volume
            high.append(aabb)
          else:
            cost += aabb.volume*aabbCutCost
            mid.append(aabb)
          cost += math.fabs(lowVol-highVol)
      
        if cost<bestCost:
          bestDimension = dim
          bestCutPoint = cutPoint
          bestCost = cost
          bestLow = low
          bestMid = mid
          bestHigh = high

    # We have our bests - we now make this actual object, and then recurse to make the full tree...
    zeroCount = 0
    if len(bestLow)==0: zeroCount += 1
    if len(bestMid)==0: zeroCount += 1
    if len(bestHigh)==0: zeroCount += 1
    
    if zeroCount==2:
      self.leaf = True
      self.data = bestLow + bestMid + bestHigh
    else:
      self.leaf = False
      self.splitDim = bestDimension
      self.split = bestCutPoint
      self.low = SetAABB(bestLow)
      self.mid = SetAABB(bestMid)
      self.high = SetAABB(bestHigh)


  def within(self,node):
    """Returns an AABB that contains the given node, or None is none do."""
    if self.leaf:
      for aabb in self.data:
        if aabb.within(node):
          return aabb
      return None
    else:
      res = self.mid.within(node)
      if res!=None: return res
      
      if node.getPos()[self.splitDim]<self.split:
        res = self.low.within(node)
        if res!=None: return res
      else:
        res = self.high.within(node)
        if res!=None: return res
