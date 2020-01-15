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


from panda3d.core import *

from aabb import *


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
      print 'Found',len(self.bounds),'bounding boxes for the culling system'

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
      print 'Found',len(self.portals),'portals for the culling system'

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
