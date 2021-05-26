# -*- coding: utf-8 -*-
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
from __future__ import print_function


from panda3d.core import *



import math



class AABB:
  """Defines an axis aligned bounding box."""
  def __init__(self,low,high):
    self.x = [low[0],high[0]]
    self.y = [low[1],high[1]]
    self.z = [low[2],high[2]]
    self.bounds = [self.x,self.y,self.z]

    self.centre = (0.5*(self.x[0]+self.x[1]),0.5*(self.y[0]+self.y[1]),0.5*(self.z[0]+self.z[1]))
    self.volume = (self.x[1]-self.x[0]) * (self.y[1]-self.y[0]) * (self.z[1]-self.z[0])

  def within(self,node):
    """Given a NodePath returns True if its in the AABB, False if it isn't."""
    pos = node.getPos(render)
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
    totVolume = sum(list(map(lambda x:x.volume,aabbs)))
    halfVolume = totVolume*0.5

    # Variables we are finding the best option for...
    bestDimension = 0
    bestCutPoint = 0.0
    bestCost = 1e20
    bestLow = []
    bestMid = aabbs
    bestHigh = []
    
    # Try each dimension, with multiple centre choice, store the best...
    for dim in range(3):
      byDim = sorted(aabbs,key=lambda x: x.centre[dim])
      centre = 0
      volume = 0.0
      while centre+1<len(byDim) and volume<halfVolume:
        volume += byDim[centre].volume
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
    if len(bestHigh)==0: zeroCount += 1
    
    if zeroCount!=2:
      self.leaf = True
      self.data = bestLow + bestMid + bestHigh
    else:
      self.leaf = False
      self.splitDim = bestDimension
      self.split = bestCutPoint

      self.low = SetAABB(bestLow)

      if len(bestMid)!=0:
        self.mid = SetAABB(bestMid)
      else:
        self.mid = None

      self.high = SetAABB(bestHigh)


  def within(self,node):
    """Returns an AABB that contains the given node, or None is none do."""
    if self.leaf:
      for aabb in self.data:
        if aabb.within(node):
          return aabb
      return None
    else:
      if self.mid:
        res = self.mid.within(node)
        if res!=None: return res
      
      if node.getPos(render)[self.splitDim]<self.split:
        res = self.low.within(node)
        if res!=None: return res
      else:
        res = self.high.within(node)
        if res!=None: return res
      return None



class Portal:
  """Defines a portal by its 4 vertices."""
  def __init__(self):
    self.verts = [(1.0,0.0,1.0),(-1.0,0.0,1.0),(-1.0,0.0,-1.0),(1.0,0.0,-1.0)]
    self.aabb1 = None
    self.aabb2 = None

  def fromFace(self,aabb,dim,side):
    """Setup the portal from a face of the given aabb - you specify the dim of the face, with side==False meaning the low side and side==True meaning the high side. Will be anti-clockwise looking at it from inside the cube."""
    if side:
      side = 1
    else:
      side = 0

    # Define square2d, remap it to 3D coordinates based on dim and side...
    square2d = [(0,0),(0,1),(1,1),(1,0)]
    def incDim(base):
      ret = [0,0,0]
      ret[(dim+1)%3] = base[0]
      ret[(dim+2)%3] = base[1]
      ret[dim] = side
      return ret
    square3d = list(map(incDim,square2d))

    # Extract the 4 coordinates...
    self.verts = []
    for index in square3d:
      coord = list(map(lambda d: aabb.bounds[d][index[d]],range(3)))
      self.verts.append(coord)

    # If needed reorder them so its anticlockwise ordering from the view of the centre of the aabb...
    offsetC = list(map(lambda x: list(map(lambda a,b: a-b,x,aabb.centre)),self.verts))
    ind = sum(list(map(lambda i:offsetC[1][i]*(offsetC[0][(i+1)%3]*offsetC[2][(i+2)%3] - offsetC[0][(i+2)%3]*offsetC[2][(i+1)%3]),range(3))))
    if ind<0.0:
      self.verts = [self.verts[0],self.verts[3],self.verts[2],self.verts[1]]

  def setupPortal(self,portal,portalNode,flip):
    if flip:
      order = [0,3,2,2]
    else:
      order = [0,1,2,3]

    c = list(map(lambda i:sum(list(map(lambda x:x[i],self.verts)))/4.0,range(3)))

    portalNode.setPos(render,Vec3(c[0],c[1],c[2]))

    portal.clearVertices()
    for o in order:
      portal.addVertex(Point3(self.verts[o][0] - c[0],self.verts[o][1] - c[1],self.verts[o][2] - c[2]))



def findPortals(aabbs,overlap = 1e-3):
  """Given a list of AABB's this finds all intersections and creates portals. To store the portals creates a variable in each aabb, portals = [[[],[]],[[],[]],[[],[]]] - first index is dimension, second index is low (0) and high (1), final list is all portals using that face. Returns the portals as a list. Will throw an error if the geometry is bad. Will modify the dimensions of the given aabb's to account for overlap."""
  # Before we start add the portal variable to each aabb...
  for aabb in aabbs:
    aabb.portals = [[[],[]],[[],[]],[[],[]]]
  
  # We process each dimension seperatly - this first loop is over the dimensions...
  ret = []
  for dim in range(3):
    otherDim = [0,1,2]
    del otherDim[dim]

    # Iterate all aabbs and create a push event and pop event for each - push it on when you reach the minimum, pop it when you get to the maximum. (True,d,aabb) to push, (False,d,aabb) to pop...
    events = []
    for aabb in aabbs:
      events.append((True,aabb.bounds[dim][0],aabb))
      events.append((False,aabb.bounds[dim][1],aabb))

    # Sort the events...
    events.sort(key=lambda x: x[1])

    # Iterate through the events in sequence - each time a aabb is pushed or popped check if it intercepts a face larger than it - if so add the relevant portal... (Partial interception is considered an error as it results in ambiguous behaviour. Multiple interception is also not allowed as its an entire face that intercepts from our point of view. (Larger face can have multiple intercepts of course.))
    state = dict() # Index by id of aabb's
    for event in events:
      if not event[0]:
        # Pop event - remove its aabb from the state...
        del state[id(event[2])]
        
      # Check event aabb against existing aabbs for being the smaller face...
      done = False
      for key,aabb in state.items():
        # Verify that the sorting dimension is not contained, i.e. they overlap so a portal can be created...
        if (event[2].bounds[dim][0]>aabb.bounds[dim][0]) == (event[2].bounds[dim][1]<aabb.bounds[dim][1]):
          continue

        # Check if bounds overlap, done such that we can detect corner overlaps...
        withinCount = [0,0,0]
        for od in otherDim:
          if event[2].bounds[od][0]>aabb.bounds[od][0] and event[2].bounds[od][0]<aabb.bounds[od][1]:
            withinCount[od] += 1
          if event[2].bounds[od][1]>aabb.bounds[od][0] and event[2].bounds[od][1]<aabb.bounds[od][1]:
            withinCount[od] += 1

        if sum(withinCount)==4:
          if done:
            raise Exception('Double interception - each culling aabb face can only intrecept one other cube as a fully contained face')
          done = True

          # We have an interception - update the relevant aabb to have only the slightest overlap then create the portal and finally arrange for all the links...
          if event[0]:
            event[2].bounds[dim][0] = aabb.bounds[dim][1] - overlap
            evSide = 0
          else:
            event[2].bounds[dim][1] = aabb.bounds[dim][0] + overlap
            evSide = 1
          
          portal = Portal()
          portal.fromFace(event[2],dim,not event[0])
          ret.append(portal)

          portal.aabb1 = event[2]
          portal.aabb2 = aabb
          event[2].portals[dim][evSide].append(portal)
          aabb.portals[dim][(evSide+1)%2].append(portal)

        elif len(list(filter(lambda x:x>0,withinCount)))==2:
          exp = 'Partial interception - culling aabbs can not intecept at corners/edges due to undefinable behaviour - must only overlap with one face fully contained within another.'
          exp += ' dimension = ' + str(dim) + '; within = ' + str(withinCount) + '; '
          exp += str(event[2]) + ' against ' + str(aabb)
          raise Exception(exp)

      if event[0]:
        # Push event - add the events aabb to the state...
        state[id(event[2])] = event[2]

  return ret


class CullAABB:
  def __init__(self,manager,xml):
    self.bounds = []
    self.portals = []
    
    self.reload(manager,xml)

  def destroy(self):
    for portal in self.portals:
      portal.portal1 = None
      portal.portal2 = None
      portal.portalNode1.removeNode()
      portal.portalNode2.removeNode()
      
    for aabb in self.bounds:
      children = aabb.cell.getChildren()
      for child in children:
        child.reparentTo(aabb.cell.getParent())

      aabb.cell.removeNode()

    self.camBound = None


  def reload(self,manager,xml):
    # Clean up any previous stuff...
    self.destroy()

    # Get the level plugin to load the culling AABB's from...
    levelXML = xml.find('level')
    if levelXML!=None:
      levelPlugin = levelXML.get('plugin','level')
    else:
      levelPlugin = 'level'
    level = manager.get(levelPlugin)

    # Load the AABB's into a list of bounds...
    self.bounds = []
    for node in level.getByIsA('CullAABB'):
      low = Point3()
      high = Point3()
      node.calcTightBounds(low,high)
      self.bounds.append(AABB(low,high))

    if xml.find('debug')!=None:
      print( 'Found',len(self.bounds),'bounding boxes for the culling system')

    # Generate a cell for each bounding box...
    for aabb in self.bounds:
      aabb.cell = render.attachNewNode('cell')
      aabb.cell.setPos(aabb.centre[0],aabb.centre[1],aabb.centre[2])
      aabb.cell.hide()

    # Generate a KD tree of aabb's that is used to quickly work out where a given location is in the culling structure...
    self.kd = SetAABB(self.bounds)

    # Generate the portal list...
    self.portals = findPortals(self.bounds)
    if xml.find('debug')!=None:
      print( 'Found',len(self.portals),'portals for the culling system')

    # Go through and create the portals - a pair for each scenario...
    for portal in self.portals:
      portal.portal1 = PortalNode('portal1')
      portal.portalNode1 = portal.aabb1.cell.attachNewNode(portal.portal1)
      portal.portal1.setCellIn(portal.aabb1.cell)
      portal.portal1.setCellOut(portal.aabb2.cell)
      portal.setupPortal(portal.portal1,portal.portalNode1,False)
      
      portal.portal2 = PortalNode('portal2')
      portal.portalNode2 = portal.aabb2.cell.attachNewNode(portal.portal2)
      portal.portal2.setCellIn(portal.aabb2.cell)
      portal.portal2.setCellOut(portal.aabb1.cell)
      portal.setupPortal(portal.portal2,portal.portalNode2,True)

    # Setup assorted variables...
    self.camBound = None # AABB that the camera is in.


  def camCellUpdate(self,task):
    # Determine if the camera has moved cell, if so update cell visibility...
    if self.camBound!=None:
      if not self.camBound.within(base.camera):
        newBound = self.kd.within(base.camera)
        if newBound!=None:
          self.camBound.cell.hide()
          self.camBound = newBound
          self.camBound.cell.show()
    else:
      self.camBound = self.kd.within(base.camera)
      if self.camBound:
        self.camBound.cell.show()
    return task.cont


  def start(self):
    self.task = taskMgr.add(self.camCellUpdate,'Culling Updater')

  def stop(self):
    taskMgr.remove(self.task)

  def cullStatic(self,node):
    """Given a node path that doesn't move, or has a limited movement range known to be within an entire culling aabb, this adds it to the culling system by reparenting it to the correct cell.
    If there is no cell it belongs in it reparents it to render as a fallback."""
    bound = self.kd.within(node)
    if bound!=None:
      node.reparentTo(bound.cell)
      node.setPos(node,-bound.cell.getPos())
    else:
      node.reparentTo(render)
