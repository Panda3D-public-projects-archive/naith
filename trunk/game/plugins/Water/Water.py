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

__all__ = ["Water"]
import os
from pandac.PandaModules import HeightfieldTesselator, PNMImage, Filename
from pandac.PandaModules import BitMask32, TransparencyAttrib, Texture, Plane, PlaneNode, Vec4, Vec3, Point3, NodePath

POLYCOUNT = 50000
SIZE = (256, 256)
CACHEDFILE = "cache/plane-%dx%d-%dk.bam" % (SIZE[0], SIZE[1], int(POLYCOUNT / 1000))

def generateWaterSurface():
  if not os.path.isdir("cache"):
    os.mkdir("cache")
  img = PNMImage(*SIZE)
  img.makeGrayscale()
  img.fill(0, 0, 0)
  img.write("cache/black-%dx%d.png" % SIZE)
  ht = HeightfieldTesselator("plane")
  assert ht.setHeightfield(Filename("cache/black-%dx%d.png" % SIZE))
  ht.setPolyCount(POLYCOUNT)
  ht.setFocalPoint(SIZE[0] * 0.5, SIZE[1] * 0.5)
  node = ht.generate()
  node.setPos(-0.5 * SIZE[0], 0.5 * SIZE[1], 0)
  node.flattenLight()
  node.writeBamFile(CACHEDFILE)
  return node

class Water:
  """Represents a water surface"""
  def __init__(self,manager,xml):
    # If we don't have it, generate the water surface.
    if os.path.isfile(CACHEDFILE):
      self.surface = loader.loadModel(CACHEDFILE)
    else:
      self.surface = generateWaterSurface()
    self.surface.reparentTo(render)
    self.surface.setShader(loader.loadShader('data/shaders/water.cg'))
    self.surface.setShaderInput('time', 0.0, 0.0, 0.0, 0.0)
    ntex = loader.loadTexture('data/textures/water-normal.png')
    ntex.setMinfilter(Texture.FTLinearMipmapLinear)
    self.surface.setShaderInput('normal', ntex)
    self.surface.setShaderInput('light', manager.get('sky').sun)
    self.surface.setShaderInput('camera', base.cam)
    self.surface.setTransparency(TransparencyAttrib.MDual, 10)

    self.surface.setShaderInput('waveInfo', Vec4(0.2, 0.5, 0.5,0.1))
    self.surface.setShaderInput('param2', Vec4(-0.015,0.005, 0.05, 0.05))
    self.surface.setShaderInput('param3', Vec4(1.0, 0.3, 0, 0))
    self.surface.setShaderInput('param4', Vec4(5.0, 0.328, 0.471, 0.0))
    self.surface.setShaderInput('speed', Vec4(-0.5, 0.2, -0.7, -0.15))
    self.surface.setShaderInput('deepcolor', Vec4(0.0,0.3,0.5,1.0))
    self.surface.setShaderInput('shallowcolor', Vec4(0.0,1.0,1.0,1.0))
    self.surface.setShaderInput('reflectioncolor', Vec4(0.95,1.0,1.0,1.0))

    wbuffer = base.win.makeTextureBuffer('water', 512, 512)
    wbuffer.setClearColorActive(True)
    wbuffer.setClearColor(base.win.getClearColor())
    self.wcamera = base.makeCamera(wbuffer)
    self.sky = manager.get('sky').model.copyTo(self.wcamera)
    self.sky.setTwoSided(True)
    self.sky.setSz(self.sky, -1)
    self.sky.setClipPlaneOff(1)
    self.wcamera.reparentTo(render)
    self.wcamera.node().setLens(base.camLens)
    self.wcamera.node().setCameraMask(BitMask32.bit(1))
    #self.wcamera.node().setInitialState(RenderState.make(CullFaceAttrib.makeReverse()))
    self.surface.hide(BitMask32.bit(1))
    wtexture = wbuffer.getTexture()
    wtexture.setWrapU(Texture.WMClamp)
    wtexture.setWrapV(Texture.WMClamp)
    wtexture.setMinfilter(Texture.FTLinearMipmapLinear)
    self.surface.setShaderInput('reflection', wtexture)
    self.wplane = Plane(Vec3(0, 0, 1), Point3(0, 0, 0))
    self.wplanenp = render.attachNewNode(PlaneNode('water', self.wplane))
    tmpnp = NodePath('StateInitializer')
    tmpnp.setClipPlane(self.wplanenp)
    self.wcamera.node().setInitialState(tmpnp.getState())

    self.updateTask = taskMgr.add(self.update, 'water-update')

  def stop(self):
    taskMgr.remove(self.updateTask)

  def update(self, task):
    self.wcamera.setMat(base.cam.getMat(render) * self.wplane.getReflectionMat())
    self.surface.setShaderInput('time', task.time, 0.0, 0, 0)
    return task.cont
