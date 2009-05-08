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

from pandac.PandaModules import *
from direct.directbase import DirectStart

class Window:
  """This plugin creates a window for rendering into."""
  def __init__(self, manager, xml):
    base.openDefaultWindow()
    if base.win.getFbProperties().getMultisamples() > 0:
      render.setAntialias(AntialiasAttrib.MAuto)

  def screenshot(self):
      base.screenshot()

