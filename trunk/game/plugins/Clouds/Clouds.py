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

import os, random
#from pandac.PandaModules import Point2, Vec3, Vec4, NodePath, CardMaker, Shader, ColorBlendAttrib, Texture
from pandac.PandaModules import *

class CloudObj():
  """An object to represent a single cloud cluster"""
  def __init__(self, filename, splat_texture, position, softness=0.5):
    
    # Each cloud has a .egg file and a splat texture associated with it
    self.model = loader.loadModel(filename)
    self.splat_texture = splat_texture
    
    # Attach this cloud's node and create the list of sprites
    self.cloud_node = render.attachNewNode("cloud")
    self.sprites = []
    
    # Set the cloud's position
    self.cloud_node.setPos(position)
    
    # Note - stratus type clouds use higher softness values
    # Cumulus clouds use lower softness values
    self.softness = softness
  
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
      cm.setFrame(tight_bounds[0].getX(), tight_bounds[1].getY(), tight_bounds[0].getX(), tight_bounds[1].getZ())
      
      # Choose a texture splat image based on the softness value XXX Not with the following lines commented out
      gauss_softness = random.gauss(self.softness, 0.3)
      for i in range(1,16):
        if (gauss_softness <= i*.0625) and (gauss_softness >= (i-1)*.0625): # XXX Use this line to use gaussian random textures
        #if (self.softness <= i*.0625) and (self.softness >= (i-1)*.0625): # XXX Use this line to NOT use gaussian random textures
          # i is the texture we're after. Note i=0 will be the bottom left 
          # texture, i=15 will be the top-right texture
          row,column = divmod(i, 4)
          cm.setUvRange((row*0.25, column*0.25), ((row+1)*0.25, ((column+1)*0.25)))
      
      # Create the sprite
      sprite = render.attachNewNode(cm.generate())
      sprite.setPos(self.cloud_node, sprite_midpoint)
      sprite.setTexture(self.splat_texture)
      sprite.setBillboardPointEye()
      #sprite.setBillboardAxis()
      #sprite.setTwoSided(True)
      #sprite.setBin('background', 20)
      sprite.setTransparency(TransparencyAttrib.MDual)
      sprite.setLightOff()
      
      # Calc the distance from the center of the cloud to this sprite
      distance = Vec3(sprite.getPos(self.cloud_node)).length()
      
      self.sprites.append([distance, sprite])
    
    # Remove the model from the scene, the sprites are all we want now
    self.model.removeNode()
    
    # Re-sort the sprites from closest to the core->furthest from the core
    self.sprites = sorted(self.sprites)
        

class Clouds:
  """This creates a cloud system based on artist input."""
  def __init__(self,manager,xml):
    # Get the path to load clouds from...
    basePath = manager.get('paths').getConfig().find('clouds').get('path')
    
    self.cloudlist = []
    xmlcloudlist = [x for x in xml.findall('cloud')]
    cloudsplattexture = loader.loadTexture(os.path.join(basePath, xml.find('splat').get('fname')))
    
    # See if the user is requesting a cloudbox or not
    self.cloudbox = None
    xmlcloudbox = xml.find('range')
    if xmlcloudbox != None:
      self.cloudbox = (Point3(int(xmlcloudbox.get('x1')),
                              int(xmlcloudbox.get('y1')),
                              int(xmlcloudbox.get('z1'))),
                       Point3(int(xmlcloudbox.get('x2')),
                              int(xmlcloudbox.get('y2')),
                              int(xmlcloudbox.get('z2'))))
     
    
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
        
        cloud = CloudObj(os.path.join(basePath, filename), cloudsplattexture, pos, softness)
        cloud.generate_sprites()
        self.cloudlist.append(cloud)
      else:
        # Default the cloud to (0,0,0)
        cloud = CloudObj(os.path.join(basePath, filename), cloudsplattexture, Point3(0,0,0), softness)
        cloud.generate_sprites()
        self.cloudlist.append(cloud)