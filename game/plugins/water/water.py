# -*- coding: utf-8 -*-
# Copyright Reinier de Blois, Tom SF Haines
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

__all__ = ["Water"]

import os
from pandac.PandaModules import HeightfieldTesselator, PNMImage, Filename
from pandac.PandaModules import BitMask32, TransparencyAttrib, Texture
from pandac.PandaModules import RenderState, CullFaceAttrib, Fog
from pandac.PandaModules import Plane, PlaneNode, Vec4, Vec3, Point3, NodePath



def getWaterSurface(manager, polycount = 50000, size = (512,512)):
  # Get cache directory...
  cacheDir = manager.get('paths').getConfig().find('cache').get('path')

  # Check if the data required already exists...
  cachedWaterSurface = "%s/plane-%dx%d-%dk.bam" % (cacheDir, size[0], size[1], int(polycount/1000))
  try:
    return loader.loadModel(cachedWaterSurface)
  except:
    pass

  # Make cache directory if needed...
  if not os.path.isdir(cacheDir):
    os.mkdir(cacheDir)

  # Put in an image...
  img = PNMImage(*size)
  img.makeGrayscale()
  img.fill(0, 0, 0)
  img.write("%s/black-%dx%d.png" % (cacheDir,size[0],size[1]))

  # Put in a mesh...
  ht = HeightfieldTesselator("plane")
  assert ht.setHeightfield(Filename("%s/black-%dx%d.png" % (cacheDir,size[0],size[1])))
  ht.setPolyCount(polycount)
  ht.setFocalPoint(int(size[0] * 0.5), int(size[1] * 0.5))
  node = ht.generate()
  node.setPos(-0.5 * size[0], 0.5 * size[1], 0)
  node.flattenLight()
  node.writeBamFile(cachedWaterSurface)
  
  return node



class Water:
  """Represents a water surface"""
  def __init__(self,manager,xml):
    self.surface = getWaterSurface(manager)
    self.surface.reparentTo(render)
    self.surface.hide(BitMask32.bit(1)) # Invisible to reflection camera (speedup)
    self.surface.hide(BitMask32.bit(2)) # Invisible to volumetric lighting camera (speedup)
    self.surface.hide(BitMask32.bit(3)) # Invisible to shadow cameras (speedup)
    self.surface.setShader(loader.loadShader(manager.get('paths').getConfig().find('shaders').get('path')+'/water.cg'))
    self.surface.setShaderInput('time', 0.0, 0.0, 0.0, 0.0)
    ntex = loader.loadTexture(manager.get('paths').getConfig().find('textures').get('path')+'/water-normal.png')
    ntex.setMinfilter(Texture.FTLinearMipmapLinear)
    self.surface.setShaderInput('normal', ntex)
    self.surface.setShaderInput('camera', base.cam)
    self.surface.setTransparency(TransparencyAttrib.MDual, 10)
    self.surface.setTwoSided(True)

    self.surface.setShaderInput('waveInfo', Vec4(0.4, 0.4, 0.4, 0))
    self.surface.setShaderInput('param2', Vec4(-0.015,0.005, 0.05, 0.05))
    self.surface.setShaderInput('param3', Vec4(0.7, 0.3, 0, 0))
    self.surface.setShaderInput('param4', Vec4(2.0, 0.5, 0.5, 0.0))
    #self.surface.setShaderInput('speed', Vec4(-.8, -.4, -.9, .3))
    self.surface.setShaderInput('speed', Vec4(0.2, -1.2, -0.2, -0.7))
    self.surface.setShaderInput('deepcolor', Vec4(0.0,0.3,0.5,1.0))
    self.surface.setShaderInput('shallowcolor', Vec4(0.0,1.0,1.0,1.0))
    self.surface.setShaderInput('reflectioncolor', Vec4(0.95,1.0,1.0,1.0))
    self.surface.hide()

    self.wbuffer = base.win.makeTextureBuffer('water', 512, 512)
    self.wbuffer.setClearColorActive(True)
    self.wbuffer.setClearColor(base.win.getClearColor())
    self.wcamera = base.makeCamera(self.wbuffer)
    if manager.get('sky') != None and manager.get('sky').model != None:
      self.sky = manager.get('sky').model.copyTo(self.wcamera)
      self.sky.setTwoSided(True)
      self.sky.setSz(self.sky, -1)
      self.sky.setClipPlaneOff(1)
      self.sky.show()
      self.sky.hide(BitMask32.bit(0)) # Hide for normal camera
      self.sky.hide(BitMask32.bit(2)) # Hide for volumetric lighting camera
      self.sky.hide(BitMask32.bit(3)) # Hide for shadow camera(s), if any
    else:
      self.sky = None
    self.wcamera.reparentTo(render)
    self.wcamera.node().setLens(base.camLens)
    self.wcamera.node().setCameraMask(BitMask32.bit(1))
    self.surface.hide(BitMask32.bit(1))
    wtexture = self.wbuffer.getTexture()
    wtexture.setWrapU(Texture.WMClamp)
    wtexture.setWrapV(Texture.WMClamp)
    wtexture.setMinfilter(Texture.FTLinearMipmapLinear)
    self.surface.setShaderInput('reflection', wtexture)
    self.wplane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
    self.wplanenp = render.attachNewNode(PlaneNode('water', self.wplane))
    tmpnp = NodePath('StateInitializer')
    tmpnp.setClipPlane(self.wplanenp)
    tmpnp.setAttrib(CullFaceAttrib.makeReverse())
    self.wcamera.node().setInitialState(tmpnp.getState())

    #self.fog = Fog('UnderwaterFog')
    #self.fog.setColor(0.0,0.3,0.5)
    self.fogEnabled = False


  def start(self):
    self.updateTask = taskMgr.add(self.update, 'water-update')
    self.surface.show()
    
  def stop(self):
    self.surface.hide()
    taskMgr.remove(self.updateTask)

  def update(self, task):
    if base.cam.getX(render) < 0.0 and not self.fogEnabled:
      self.fogEnabled = True
    elif base.cam.getX(render) > 0.0 and self.fogEnabled:
      self.fogEnabled = False
    self.surface.setX(render, base.cam.getX(render))
    self.surface.setY(render, base.cam.getY(render))
    self.wcamera.setMat(base.cam.getMat(render) * self.wplane.getReflectionMat())
    self.surface.setShaderInput('time', task.time, 0.0, 0, 0)
    return task.cont
