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

import os
from pandac.PandaModules import Point2, Vec3, Vec4, NodePath, CardMaker, Shader, ColorBlendAttrib, Texture, BitMask32

class Sky:
  """This loads a skydome/box/whatever the user specified."""
  def __init__(self,manager,xml):
    # Set the background color first
    background = xml.find("background")
    if background != None:
      base.setBackgroundColor(Vec4(float(background.get('r')), float(background.get('g')), float(background.get('b')), 1))

    # Get the path to load skies from...
    basePath = manager.get('paths').getConfig().find('skies').get('path')

    self.sun = base.cam.attachNewNode('sun')
    self.sun.setLightOff(1)
    self.sun.setShaderOff(1)
    self.sun.setFogOff(1)
    self.sun.setCompass()
    self.sun.setBin('background', 10)
    self.sun.setDepthWrite(False)
    self.sun.setDepthTest(False)
    sunorigin = xml.find('sunorigin')
    if sunorigin != None:
      orig = Vec3(float(sunorigin.get('x')), float(sunorigin.get('y')), float(sunorigin.get('z')))
      orig.normalize()
      self.sun.setPos(orig)

    self.model = None
    self.updateTask = None
    skydome = xml.find('skydome')
    if skydome != None:
      self.model = loader.loadModel(os.path.join(basePath, 'skydome'))
      self.model.setLightOff(1)
      self.model.setShaderOff(1)
      self.model.setFogOff(1)
      self.model.setCompass()
      self.model.setBin('background', 10)
      self.model.setDepthWrite(False)
      self.model.setDepthTest(False)
      self.model.setColor(1, 1, 1, 1)
      self.model.setTexture(loader.loadTexture(os.path.join(basePath, skydome.get('filename'))))
      self.model.setTag('sun', 'True')
      self.model.reparentTo(base.cam)
      # Hide from the reflection camera
      self.model.hide(BitMask32.bit(1))

      godrays = xml.find('godrays')
      sunmask = xml.find('sunmask')
      if godrays != None and sunmask != None:
        self.vlbuffer = base.win.makeTextureBuffer('VolumetricLighting', base.win.getXSize()/2, base.win.getYSize()/2)
        self.vlbuffer.setClearColor(Vec4(0, 0, 0, 1))
        cam = base.makeCamera(self.vlbuffer)
        cam.node().setLens(base.camLens)
        cam.reparentTo(base.cam)
        initstatenode = NodePath('InitialState')
        initstatenode.setColorScale(0, 0, 0, 1, 10000)
        initstatenode.setShaderOff(10000)
        initstatenode.setMaterialOff(10000)
        tagstatenode = NodePath('SunOverrideState')
        tagstatenode.setColorScale(1, 1, 1, 1, 10001)
        tagstatenode.setTexture(loader.loadTexture(os.path.join(basePath, sunmask.get('filename'))))
        cam.node().setInitialState(initstatenode.getState())
        cam.node().setTagStateKey('sun')
        cam.node().setTagState('True', tagstatenode.getState())
        self.vltexture = self.vlbuffer.getTexture()
        self.vltexture.setWrapU(Texture.WMClamp)
        self.vltexture.setWrapV(Texture.WMClamp)
        card = CardMaker('VolumetricLightingCard')
        card.setFrameFullscreenQuad()
        self.finalQuad = render2d.attachNewNode(card.generate())
        self.finalQuad.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd))
        self.finalQuad.setShader(Shader.load(os.path.join(manager.get('paths').getConfig().find('shaders').get('path'), 'filter-vlight.cg')))
        self.finalQuad.setShaderInput('src', self.vltexture)
        self.finalQuad.setShaderInput('vlparams', 32, 1.0/32.0, 1.0, 0.03)
        self.finalQuad.setShaderInput('casterpos', 0.5, 0.5, 0, 0)
        vlcolor = Vec4(float(godrays.get('r', '1')), float(godrays.get('g', '1')), float(godrays.get('b', '1')), 1)
        self.finalQuad.setShaderInput('vlcolor', vlcolor)
        self.updateTask = taskMgr.add(self.update, 'sky-update')

  def stop(self):
    taskMgr.remove(self.updateTask)

  def update(self, task):
    casterpos = Point2()
    base.camLens.project(self.sun.getPos(base.cam), casterpos)
    self.finalQuad.setShaderInput('casterpos', Vec4(casterpos.getX() * 0.5 + 0.5, (casterpos.getY() * 0.5 + 0.5), 0, 0))
    return task.cont
