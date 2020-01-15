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


def eggToOde(np,surfaceType): # ,depth = 0
  """Given a node path, usually from an egg that has been octreed, this constructs the same structure in ode, using a space for each node with tri-meshes within. Implimented as a generator so it doesn't screw with the framerate; final yield will return the root geom, or None if there was nothing to collide with. (This geom will probably be a space, but only probably.)"""
  output = []
  np.flattenLight()

  # Check if there is any mesh data at this level that we need to turn into a trimesh...
  if np.node().isGeomNode(): # np.node().getClassType()==CollisionNode.getClassType()
    tmd = OdeTriMeshData(np,True)
    tmg = OdeTriMeshGeom(tmd)
    
    nt = np.getNetTransform()
    tmg.setPosition(nt.getPos())
    tmg.setQuaternion(nt.getQuat())
    
    output.append(tmg)
    #print ('|'*depth) + 'geom, ' + str(np.node().getClassType()) + ', ' + str(tmg.getNumTriangles())
  else:
    #print ('|'*depth) + 'notgeom, ' + str(np.node().getClassType())
    # Check the children for useful data...
    children = np.getChildren()
    for child in children:
      for r in eggToOde(child,surfaceType): # ,depth+1
        yield None
        geom = r
      if geom!=None:
        output.append(geom)

  if len(output)==0:
    yield None
  else:
    space = OdeSimpleSpace()
    for geom in output:
      space.add(geom)
      space.setSurfaceType(geom,surfaceType)
    yield OdeUtil.spaceToGeom(space)
