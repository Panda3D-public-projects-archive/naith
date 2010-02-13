# -*- coding: utf-8 -*-
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

from pandac.PandaModules import Point2, Vec3, Vec4, NodePath, CardMaker, Shader, ColorBlendAttrib, Texture, BitMask32, TransparencyAttrib, OmniBoundingVolume
import os

class Sun:
  """Represents the sun, handles godrays, etc."""
  def __init__(self,manager,xml):
    self.updateTask = None

    self.sun = base.cam.attachNewNode('sun')
    loader.loadModel(manager.get('paths').getConfig().find('misc').get('path')+'/sphere').reparentTo(self.sun)
    self.sun.setScale(0.1)
    self.sun.setTwoSided(True)
    self.sun.setColorScale(10.0, 10.0, 10.0, 1.0, 10001)
    self.sun.setLightOff(1)
    self.sun.setShaderOff(1)
    self.sun.setFogOff(1)
    self.sun.setCompass()
    self.sun.setBin('background', 10)
    self.sun.setDepthWrite(False)
    self.sun.setDepthTest(False)
    # Workaround an annoyance in Panda. No idea why it's needed.
    self.sun.node().setBounds(OmniBoundingVolume())
    isa = xml.find('isa')
    inst = xml.find('instance')
    if isa != None or inst != None:
      if inst != None:
        orig = Vec3(float(inst.get('x', '0')), float(inst.get('y', '0')), float(inst.get('z', '0')))
      else:
        level = manager.get(isa.get('source'))
        orig = Vec3(level.getByIsA(isa.get('name'))[0].getPos(render))
      orig.normalize()
      self.sun.setPos(orig)
    
    godrays = xml.find('godrays')
    if godrays != None:
      self.vlbuffer = base.win.makeTextureBuffer('volumetric-lighting', base.win.getXSize()/2, base.win.getYSize()/2)
      self.vlbuffer.setClearColor(Vec4(0, 0, 0, 1))
      cam = base.makeCamera(self.vlbuffer)
      cam.node().setLens(base.camLens)
      cam.reparentTo(base.cam)
      initstatenode = NodePath('InitialState')
      initstatenode.setColorScale(0, 0, 0, 1, 10000)
      initstatenode.setShaderOff(10000)
      initstatenode.setLightOff(10000)
      initstatenode.setMaterialOff(10000)
      initstatenode.setTransparency(TransparencyAttrib.MBinary, 10000)
      cam.node().setCameraMask(BitMask32.bit(2))
      cam.node().setInitialState(initstatenode.getState())
      self.vltexture = self.vlbuffer.getTexture()
      self.vltexture.setWrapU(Texture.WMClamp)
      self.vltexture.setWrapV(Texture.WMClamp)
      card = CardMaker('VolumetricLightingCard')
      card.setFrameFullscreenQuad()
      self.finalQuad = render2d.attachNewNode(card.generate())
      self.finalQuad.setAttrib(ColorBlendAttrib.make(ColorBlendAttrib.MAdd, ColorBlendAttrib.OIncomingColor, ColorBlendAttrib.OFbufferColor))
      self.finalQuad.setShader(Shader.load(os.path.join(manager.get('paths').getConfig().find('shaders').get('path'), 'filter-vlight.cg')))
      self.finalQuad.setShaderInput('src', self.vltexture)
      self.finalQuad.setShaderInput('vlparams', 32, 0.9/32.0, 0.97, 0.5) # Note - first 32 is now hardcoded into shader for cards that don't support variable sized loops.
      self.finalQuad.setShaderInput('casterpos', 0.5, 0.5, 0, 0)
      # Last parameter to vlcolor is the exposure
      vlcolor = Vec4(float(godrays.get('r', '1')), float(godrays.get('g', '1')), float(godrays.get('b', '1')), 0.04)
      self.finalQuad.setShaderInput('vlcolor', vlcolor)
    else:
      self.finalQuad = None

  def start(self):
    if self.finalQuad!=None:
      self.updateTask = taskMgr.add(self.update, 'sky-update')
    
  def stop(self):
    if self.updateTask!=None:
      taskMgr.remove(self.updateTask)

  def update(self, task):
    casterpos = Point2()
    base.camLens.project(self.sun.getPos(base.cam), casterpos)
    self.finalQuad.setShaderInput('casterpos', Vec4(casterpos.getX() * 0.5 + 0.5, (casterpos.getY() * 0.5 + 0.5), 0, 0))
    return task.cont

