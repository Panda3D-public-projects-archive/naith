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



from pandac.PandaModules import *
import direct.directbase.DirectStart


class Camera:
  """Does camera set up - will probably end up with lots of options."""
  def __init__(self,manager,xml):
    base.disableMouse()

    pos = xml.find('pos')
    if pos!=None:
      base.camera.setPos(float(pos.get('x')),float(pos.get('y')),float(pos.get('z')))

    lookAt = xml.find('lookAt')
    if lookAt!=None:
      base.camera.lookAt(float(lookAt.get('x')),float(lookAt.get('y')),float(lookAt.get('z')))

    fov = xml.find('fov')
    self.zoomed = False
    if fov!=None:
      self.normal = float(fov.get('deg'))
      self.zoom = float(fov.get('zoom'))
      self.speed = (self.normal-self.zoom) / float(fov.get('zoomTime'))
      
      base.camLens.setFov(self.normal)
      base.camLens.setNearFar(float(fov.get('near')),float(fov.get('far')))


      def trackZoom(task):
        fov = base.camLens.getFov()[0]
        if self.zoomed:
          fov = max(self.zoom,fov - self.speed*globalClock.getDt())
        else:
          fov = min(self.normal,fov + self.speed*globalClock.getDt())
        base.camLens.setFov(fov)
        return task.cont

      taskMgr.add(trackZoom,'Camera Zoom Control')

    track = xml.find('track')
    if track!=None:
      base.camera.reparentTo(manager.get(track.get('plugin')).getNode(track.get('node')))

  def setZoomed(self,s):
    self.zoomed = s