# -*- coding: utf-8 -*-
# Copyright Aaron Snoswell
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

import posixpath, random
#from pandac.PandaModules import Point2, Vec3, Vec4, NodePath, CardMaker, Shader, ColorBlendAttrib, Texture
from pandac.PandaModules import *
from direct.task.Task import Task
from direct.interval.IntervalGlobal import *

class CloudObj():
  """An object to represent a single cloud cluster"""
  def __init__(self, filename, splat_texture, position, softness=0.5, visibility=0.5):
    
    # Each cloud has a .egg file and a splat texture associated with it
    self.model = loader.loadModel(filename)
    self.splat_texture = splat_texture
    
    # Attach this cloud's node and create the list of sprites
    self.cloud_node = base.cam.attachNewNode("cloud"+str(random.random()))
    self.cloud_node.setCompass()
    self.sprites = []
    
    # The cloud has a value that represents how formated or dissolved it is
    self.visibility = visibility
    
    # This is used for the fading in and out
    self.longest_dist = 0
    
    # Set the cloud's position
    self.cloud_node.setPos(base.cam, position)
    
    # Note - stratus type clouds use higher softness values
    # Cumulus clouds use lower softness values
    self.softness = softness
  
  def set_visibility(self, vis):
    """Sets the visibility of the cloud, the futher away from the center each sprite is, the less visibile"""
    self.visibility = vis
    for sprite in self.sprites:
      sprite[1].setAlphaScale((1.0-sprite[0])*vis)
  
  def _getmiddle(self, points):
    """Returns the center of a sequence of 3-space points"""
    num, x, y, z = 0, 0, 0, 0
    for point in points:
      x += point.getX()
      y += point.getY()
      z += point.getZ()
      num += 1
    
    return Point3(x*1.0/num,y*1.0/num,z*1.0/num)
  
  def generate_sprites(self):
    """Replaces each object in the model with a sprite"""
    
    cm = CardMaker("spritemaker")
    
    # Create each sprite
    for cloudobj in self.model.getChild(0).getChildren():
      tight_bounds = cloudobj.getTightBounds()
      sprite_midpoint = self._getmiddle(tight_bounds)
      
      #Set the size of the billboard, !roughly based on the size of the box
      cm.setFrame(tight_bounds[0].getX(), tight_bounds[1].getY(), tight_bounds[0].getZ(), tight_bounds[1].getZ())
      
      # Choose a texture splat image based on the softness value
      tmpsoftness = random.gauss(self.softness, 0.1); num = 0;
      if tmpsoftness <= 1*.0625: pass
      elif tmpsoftness <= 2*.0625: num = 1
      elif tmpsoftness <= 3*.0625: num = 2
      elif tmpsoftness <= 4*.0625: num = 3
      elif tmpsoftness <= 5*.0625: num = 4
      elif tmpsoftness <= 6*.0625: num = 5
      elif tmpsoftness <= 7*.0625: num = 6
      elif tmpsoftness <= 8*.0625: num = 7
      elif tmpsoftness <= 9*.0625: num = 8
      elif tmpsoftness <= 10*.0625: num = 9
      elif tmpsoftness <= 11*.0625: num = 10
      elif tmpsoftness <= 12*.0625: num = 11
      elif tmpsoftness <= 13*.0625: num = 12
      elif tmpsoftness <= 14*.0625: num = 13
      elif tmpsoftness <= 15*.0625: num = 14
      else: num = 15
      row,column = divmod(num, 4)
      cm.setUvRange((row*0.25, column*0.25), ((row+1)*0.25, ((column+1)*0.25)))
      
      # Create the sprite
      sprite = self.cloud_node.attachNewNode(cm.generate())
      sprite.setPos(self.cloud_node, sprite_midpoint)
      sprite.setTexture(self.splat_texture)
      sprite.setBillboardPointEye()
      #sprite.setBillboardAxis()
      sprite.setTwoSided(True)
      #sprite.setBin('background', 20)
      sprite.setTransparency(TransparencyAttrib.MDual)
      sprite.setLightOff()
      
      # Calc the distance from the center of the cloud to this sprite
      distance = Vec3(sprite.getPos(self.cloud_node)).length()
      if self.longest_dist < distance: self.longest_dist = distance
      
      self.sprites.append([distance, sprite])
    
    # Remove the model from the scene, the sprites are all we want now
    self.model.removeNode()
    
    # Re-sort the sprites from closest to the core->furthest from the core
    # While we're at it, we pre-calc the normalised distances
    self.sprites = sorted(self.sprites)
    for sprite in self.sprites:
      sprite[0] = sprite[0] / self.longest_dist
    
    # Set the visibility of the cloud
    self.set_visibility(self.visibility)
        

class Clouds:
  """This creates a cloud system based on artist input."""
  def __init__(self,manager,xml):
    # Get the path to load clouds from...
    basePath = manager.get('paths').getConfig().find('clouds').get('path')
    
    self.cloudlist = []
    xmlcloudlist = [x for x in xml.findall('cloud')]
    cloudsplattexture = loader.loadTexture(posixpath.join(basePath, xml.find('splat').get('fname')))
    
    # XXX See if the user is requesting a cloudbox or a position
    # Needs to be handled much better than this
    self.cloudbox = None
    self.cloudpos = None
    xmlcloudbox = xml.find('range')
    xmlcloudpos = xml.find('pos')
    if xmlcloudbox != None:
      self.cloudbox = (Point3(int(xmlcloudbox.get('x1')),
                              int(xmlcloudbox.get('y1')),
                              int(xmlcloudbox.get('z1'))),
                       Point3(int(xmlcloudbox.get('x2')),
                              int(xmlcloudbox.get('y2')),
                              int(xmlcloudbox.get('z2'))))
    if xmlcloudpos != None:
      self.cloudpos = Point3(int(xmlcloudpos.get('x')),
                             int(xmlcloudpos.get('y')),
                             int(xmlcloudpos.get('z')))
     
    
    # Iterate over each of the requested clouds
    for cloud in xrange(len(xmlcloudlist)):
      # Read the values from the xml file
      filename = str(xmlcloudlist[cloud].get('filename'))
      softness = float(xmlcloudlist[cloud].get('softness'))
      
      # Set the cloud in the list
      if self.cloudbox:
        # Chose a random position for the cloud
        pos = Point3(random.randint(self.cloudbox[0].getX(), self.cloudbox[1].getX()),
                     random.randint(self.cloudbox[0].getY(), self.cloudbox[1].getY()),
                     random.randint(self.cloudbox[0].getZ(), self.cloudbox[1].getZ()))
        
        cloud = CloudObj(posixpath.join(basePath, filename), cloudsplattexture, pos, softness)
        cloud.generate_sprites()
        self.cloudlist.append(cloud)
      else:
        # Default the cloud to (0,0,0)
        cloud = CloudObj(posixpath.join(basePath, filename), cloudsplattexture, self.cloudpos, softness)
        cloud.generate_sprites()
        self.cloudlist.append(cloud)
      
      
      # Create a testing lerp of the cloud's vis
      cloudfadeout = LerpFunc(cloud.set_visibility, 10, 1, 0, 'easeInOut')
      cloudfadein = LerpFunc(cloud.set_visibility, 10, 0, 1, 'easeInOut')
      cloudsequence = Sequence(cloudfadeout,cloudfadein)
      cloudsequence.loop()
         
