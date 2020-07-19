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


from panda3d.core import LightRampAttrib
from direct.filter.CommonFilters import CommonFilters

class Filters:
  """Class handles postprocessing filters and effects"""
  def __init__(self,manager,xml):
    self.cf = CommonFilters(base.win,base.cam)
    self.reload(manager,xml)


  def reload(self,manager,xml):
    hdr = xml.find('hdr')
    if hdr!=None:
      self.hdrtype = hdr.get('type')
      assert self.hdrtype in ['0', '1', '2']
    else:
      self.hdrtype = None

    self.perpixel =  xml.find('perpixel')!=None

    bloom = xml.find('bloom')
    if bloom!=None:
      self.bloomSize = bloom.get('size', 'medium')
    else:
      self.bloomSize = None

    self.showbuffers = xml.find('showbuffers')!=None


  def start(self):
    if self.hdrtype!=None:
      render.setAttrib(getattr(LightRampAttrib, "makeHdr" + self.hdrtype)())

    if self.perpixel:
      render.setShaderAuto()

    if self.bloomSize!=None:
      self.cf.setBloom(size=self.bloomSize)

    if self.showbuffers:
      base.bufferViewer.toggleEnable()


  def stop(self):
    if self.hdrtype!=None:
      render.clearAttrib(LightRampAttrib.getClassType())

    if self.perpixel:
      render.setShaderOff()
    
    if self.bloomSize!=None:
      self.cf.delBloom()
    
    if self.showbuffers:
      base.bufferViewer.toggleEnable()
