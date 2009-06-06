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

from pandac.PandaModules import TextNode
from direct.showbase.DirectObject import DirectObject
from direct.gui.DirectGui import DirectFrame, DirectEntry
from direct.gui.OnscreenText import OnscreenText
import sys, traceback
from collections import Callable

TEXT_MARGIN = (0.03, -0.06)

class DeveloperConsole(DirectObject):
  """The name says it all."""
  def __init__(self,manager,xml):
    self.manager = manager
    font = loader.loadFont("cmss12")
    self.frame = DirectFrame(parent = base.a2dTopCenter, text_align = TextNode.ALeft, text_pos = (-base.getAspectRatio() + TEXT_MARGIN[0], TEXT_MARGIN[1]), text_scale = 0.05, text_fg = (1, 1, 1, 1), frameSize = (-2.0, 2.0, -0.5, 0.0), frameColor = (0, 0, 0, 0.5), text = '', text_font = font)
    self.entry = DirectEntry(parent = base.a2dTopLeft, command = self.command, scale = 0.05, width = 1000.0, pos = (-0.02, 0, -0.48), relief = None, text_pos = (1.5, 0, 0), text_fg = (0.5, 0, 0, 1), rolloverSound = None, clickSound = None, text_font = font)
    self.otext = OnscreenText(parent = self.entry, scale = 1, align = TextNode.ALeft, pos = (1, 0, 0), fg = (1, 1, 1, 1), text = ':', font = font)
    self.lines = [''] * 8
    self.commands = []  # All previously sent commands
    self.cscroll = None # Index of currently navigated command, None if current
    self.command = ''   # Currently entered command
    self.pure = bool(xml.get('pure'))
    self.hide()
  
  def prevCommand(self):
    if self.hidden: return
    if len(self.commands) == 0: return
    if self.cscroll == None:
      self.cscroll = len(self.commands)
      self.command = self.entry.get()
    elif self.cscroll <= 0:
      return
    else:
      self.commands[self.cscroll] = self.entry.get()
    self.cscroll -= 1
    self.entry.set(self.commands[self.cscroll])
    self.entry.setCursorPosition(len(self.commands[self.cscroll]))
  
  def nextCommand(self):
    if self.hidden: return
    if len(self.commands) == 0: return
    if self.cscroll == None: return
    self.commands[self.cscroll] = self.entry.get()
    self.cscroll += 1
    if self.cscroll >= len(self.commands):
      self.cscroll = None
      self.entry.set(self.command)
      self.entry.setCursorPosition(len(self.command))
    else:
      self.entry.set(self.commands[self.cscroll])
      self.entry.setCursorPosition(len(self.commands[self.cscroll]))
  
  def addText(self, lines):
    if isinstance(lines, list):
      self.lines += lines
      self.frame['text'] = '\n'.join(self.lines[-8:])
    else:
      self.addText(lines.strip('\n').split('\n'))
  
  def command(self, text):
    if not self.hidden:
      self.cscroll = None
      self.command = ''
      self.entry.set('')
      self.entry['focus'] = True
      self.addText(': ' + text)
      if len(text) == 0:
        # Nothing was entered.
        return
      if len(self.commands) == 0 or self.commands[-1] != text:
        self.commands.append(text)
      
      # Insert plugins into the local namespace
      manager = self.manager
      for plugin in self.manager.named.keys():
        locals()[plugin] = self.manager.named[plugin]
      
      # Run it and print the output.
      try:
        output = eval(text)
        if isinstance(output, Callable) and not self.pure:
          output = output()
        if output != None:
          self.addText(str(output))
      except:
        # Whoops! Print out a traceback.
        self.addText(traceback.format_exc())

  def toggle(self):
    if self.hidden:
      self.show()
    else:
      self.hide()

  def show(self):
    self.accept('arrow_up', self.prevCommand)
    self.accept('arrow_up-repeat', self.prevCommand)
    self.accept('arrow_down', self.nextCommand)
    self.accept('arrow_down-repeat', self.nextCommand)
    self.hidden = False
    self.entry['focus'] = True
    self.frame.show()
    self.entry.show()
    self.otext.show()

  def hide(self):
    self.ignoreAll()
    self.hidden = True
    self.entry['focus'] = False
    self.frame.hide()
    self.entry.hide()
    self.otext.hide()

  def destroy(self):
    self.ignoreAll()
    self.frame.destroy()
    self.entry.destroy()
    self.otext.destroy()

