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



import os.path

from pandac.PandaModules import *
from direct.particles.ParticleEffect import ParticleEffect
from direct.interval.MetaInterval import Sequence
from direct.interval.FunctionInterval import *


class ParticleManager:
  """Simple particle system wrapper - put here in the hope that latter on a better way of doing things will exist and this will make the swap out easy."""
  def __init__(self,manager,xml):
    # Get the particle system path...
    basePath = manager.get('paths').getConfig().find('particles').get('path')
    
    # Enable the particle system...
    base.enableParticles()

    # Generate a database of particle effects from the xml - this consists of a name to request the effect by, a configuration file to load and how long to let it live before destroying it. (If omited it will live until a stop.)
    self.pdb = dict()
    for effect in xml.findall('effect'):
      new = dict()
      new['name'] = effect.get('name')
      self.pdb[new['name']] = new

      new['file'] = os.path.join(basePath,effect.get('file'))
      new['life'] = effect.get('lifetime',None)

    # This stores all current particle effects, indexed by their id - used by stop to end it all...
    self.effects = dict()


  def doEffect(self,name,source,track = False,pos = None,quat = None):
    """Creates the particle effect with the given name. source is the node to appear at - if track is false its initialised here and then remains fixed in world space, otherwise it moves with the source node. pos and quat are offset's in source's local coordinate sytem for the origin."""

    # Create node to store the particle effect in...
    if track:
      n = source.attachNewNode('')
      self.prepNode(n)
    else:
      n = render.attachNewNode('')
      self.prepNode(n)
      
      n.setPos(render,source.getPos(render))
      n.setQuat(render,source.getQuat(render))

    # Handle local offset/rotation...
    if pos!=None:
      n.setPos(n,pos)
    if quat!=None:
      n.setQuat(n,quat)

    # Create the particle effect...
    p = ParticleEffect()
    p.loadConfig(Filename(self.pdb[name]['file']))
    p.start(n)
    
    # Store effect in the effect database...
    self.effects[id(p)] = (p,n)

    # If the effect has a finite life arrange for it to be terminated...
    if self.pdb[name]['life']!=None:
      def kill(p):
        if self.effects.has_key(id(p)):
          self.effects[id(p)][0].cleanup()
          self.effects[id(p)][0].remove()
          del self.effects[id(p)]
      s = Sequence(Wait(float(self.pdb[name]['life'])),Func(kill,p))
      s.start()


  def prepNode(self,node):
    """Internal use only really - given a node this prepares it to be the parent of a paricle system."""
    node.setBin('fixed',0)
    node.setDepthWrite(False)
    node.setLightOff()
    node.setShaderOff()
  