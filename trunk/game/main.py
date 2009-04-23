# Copyright Tom SF hHaines
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



# Entry point - sets up the plugin system by giving it the config file to load and then releases panda to do its thing...

import direct.directbase.DirectStart
from direct.task import Task

from bin.manager import *

import sys

#messenger.toggleVerbose()

plugin = Manager()

def firstLight(task):
  cn = sys.argv[1]
  print 'Starting configuration', cn
  plugin.transition(cn)
  return Task.done

taskMgr.add(firstLight,'firstLight')
run()
