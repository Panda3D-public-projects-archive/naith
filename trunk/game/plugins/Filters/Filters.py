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


from pandac.PandaModules import LightRampAttrib
from direct.filter.CommonFilters import CommonFilters

class Filters:
  """Class handles postprocessing filters and effects"""
  def __init__(self,manager,xml):
    self.cf = CommonFilters(base.win, base.cam)
    
    hdr = xml.find('hdr')
    if hdr!=None:
      hdrtype = hdr.get('type')
      assert hdrtype in ['0', '1', '2']
      render.setAttrib(getattr(LightRampAttrib, "makeHdr" + hdrtype)())
    
    perpixel = xml.find('perpixel')
    if perpixel!=None:
      render.setShaderAuto()
    
    bloom = xml.find('bloom')
    if bloom!=None:
      self.cf.setBloom(size=bloom.get('size', 'medium'))
    base.bufferViewer.toggleEnable()
