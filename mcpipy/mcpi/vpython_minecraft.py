#
# Use this in place of minecraft.py to test simple scripts without Minecraft
# if you have vpython installed. This only supports a small subset of the full API.
#
# This gets substituted for Minecraft.py if you have the VPYTHON_MCPI environment
# variable set to something. If you have a Linux-style commandline, you can run
# demo scripts against vpython as follows:
#   VPYTHON_MCPI=1 python trefoil2.py
#

from __future__ import absolute_import
from visual import *
import thread
from .util import flatten,floorFlatten
from .block import Block
from .vec3 import Vec3
from os import environ
import time

materialList = [None for i in range(Block.MAX_MATERIAL+1)]
materialList[Block.MATERIAL_DEFAULT] = materials.plastic
materialList[Block.MATERIAL_WOOD] = materials.wood
materialList[Block.MATERIAL_STONE] = materials.rough
materialList[Block.MATERIAL_PLASTIC] = materials.plastic
materialList[Block.MATERIAL_EMISSIVE] = materials.emissive
materialList[Block.MATERIAL_ROUGH] = materials.rough

originalsleep = None

def getMaterial(block):
    return materialList[block.getMaterial()]    

def getColorScaled(block):
    r,g,b,opacity = block.getRGBA()
    return (r/255.,g/255.,b/255.),opacity/255.
    
class Ignore(object):
    def undefinedFunction(self, *args):
        return []
        
    def __getattr__(self,name):
        return self.undefinedFunction        

class PlayerCommand:
    def __init__(self, mc):
        self.mc = mc

    def getPos(self):
        return Vec3(self.mc.x,self.mc.y,self.mc.z)
        
    def getTilePos(self):
        return Vec3(int(floor(self.mc.x)),int(floor(self.mc.y)),int(floor(self.mc.z)))
        
    def getRotation(self):
        return self.mc.yaw

    def getPitch(self):
        return self.mc.pitch
        
    def setTilePos(self, *args):
        args = tuple(int(x) for x in floorFlatten(args))
        self.mc.x = args[0]
        self.mc.y = args[1]
        self.mc.z = args[2]
        self.mc.updatePosition()
        
    def setPos(self, *args):
        args = tuple(float(x) for x in flatten(args))
        self.mc.x = args[0]
        self.mc.y = args[1]
        self.mc.z = args[2]
        self.mc.updatePosition()
        
    def setRotation(self, yaw):
        self.mc.yaw = yaw
        self.mc.updatePosition()
        
    def setPitch(self, pitch):
        self.mc.yaw = yaw
        self.mc.updatePosition()
        
    def undefinedFunction(self, *args):
        return []
        
    def __getattr__(self,name):
        return self.undefinedFunction        

class EntityCommand:
    def __init__(self, playerCommand):
        self.playerCommand = playerCommand
        
    def passToPlayer(self,function,*args):
        args = tuple(flatten(args))
        getattr(self.playerCommand, function)(args[1:])
        
    def __getattr__(self,name):
        return lambda(args): self.passToPlayer(self,name,args)
        
class Minecraft:
    def __init__(self, connection=None, autoId=True):
        self.scene = {}
        self.x = 0.5
        self.y = 0.5
        self.z = 0.5
        self.yaw = 0
        self.pitch = 0

        self.events = Ignore()
        self.player = PlayerCommand(self)
        self.entity = EntityCommand(self.player)
        
        self.me = cone(pos=(self.x-0.5,self.y,self.z-0.5), axis=(1,0,0), radius=0.5, color=color.red, visible=False)
        scene.bind('keydown', self.keyInput)
        
    def undefinedFunction(self, *args):
        return []
        
    def __getattr__(self,name):
        print(name)
        return self.undefinedFunction        

    def keyInput(self,evt):        
        if evt.key == 'w':
            self.x -= .25 * -sin(radians(self.yaw))
            self.z -= .25 * cos(radians(self.yaw))
            self.updatePosition()
        elif evt.key == 's':
            self.x += .25 * -sin(radians(self.yaw))
            self.z += .25 * cos(radians(self.yaw))
            self.updatePosition()
        elif evt.key == 'a':
            self.x += .25 * -sin(radians(self.yaw+90))
            self.z += .25 * cos(radians(self.yaw+90))
            self.updatePosition()
        elif evt.key == 'd':
            self.x += .25 * -sin(radians(self.yaw-90))
            self.z += .25 * cos(radians(self.yaw-90))
            self.updatePosition()
        elif evt.key == 'q':
            self.yaw -= 45/2.
            self.updatePosition()
        elif evt.key == 'e':
            self.yaw += 45./2.
            self.updatePosition()
        elif evt.key == ' ':
            self.y += 0.25
            self.updatePosition()
        elif evt.key == '.':
            self.y -= 0.25
            self.updatePosition()
        
    def updatePosition(self):
        self.yaw %= 360.
        axis = (sin(radians(self.yaw)), 0, -cos(radians(self.yaw)))
        self.me.pos = (self.x-0.5,self.y,self.z-0.5)        
        self.me.axis = axis
        self.me.visible = True
        
    def moveAround(self):
        while True:
            originalsleep(0.05)
            if self.needUpdate:
                self.updatePosition()
                
    def postToChat(self, message):
        print(message)
        
    def setBlockWithNBT(self, *args):
        self.setBlock(*args)
		
    def setBlocksWithNBT(self, *args):
        self.setBlocks(*args)
		
    def setBlock(self, *args):
        args = map(int, list(floorFlatten(args)))
        for i in range(len(args), 5):
            args.append(0)
            
        coords = tuple(args[0:3])
		
        if args[3] == 0:
            if coords in self.scene:
                self.scene[coords].visible = False
                del self.scene[coords]
        else:
            c,opacity = getColorScaled(Block(args[3],args[4]))
            if coords in self.scene:
                self.scene[coords].visible = False
                del self.scene[coords]            
            m = getMaterial(Block(args[3],args[4]))
            self.scene[coords] = box(pos=tuple(coords), length=1, height=1, width=1, color=c, opacity=opacity, material=m)
            self.scene[coords].mcBlock = (args[3],args[4])

    def getHeight(self, *args):
        args = map(int, list(floorFlatten(args)))
        x0 = args[0]
        z0 = args[1]
        h = -20
        for (x,y,z) in self.scene:
            if x == x0 and z == z0 and y > h:
                h = y
        return h
        
    def getBlock(self, *args):
        coords = tuple(int(x) for x in floorFlatten(args))
        if coords in self.scene:
            return self.scene[coords].mcBlock[0]

    def getBlockWithData(self, *args):
        coords = tuple(int(x) for x in floorFlatten(args))
        if coords in self.scene:
            b = self.scene[coords]
            return b.mcBlock[0]
            
    def getBlockWithNBT(self, *args):
        return self.getBlockWithData(*args)

    def setBlocks(self, *args):
        args = map(int, list(floorFlatten(args)))
        for i in range(len(args), 8):
            args.append(0)
            
        if args[6] == 0:
            for x in range(min(args[0],args[3]),max(args[0],args[3])+1):
                for y in range(min(args[1],args[4]),max(args[1],args[4])+1):
                    for z in range(min(args[2],args[5]),max(args[2],args[5])+1):
                        if (x,y,z) in self.scene:
                            self.scene[(x,y,z)].visible = False
                            del self.scene[(x,y,z)]
        else:
            c,opacity = getColorScaled(Block(args[6],args[7]))
            m = getMaterial(Block(args[6],args[7]))
            for x in range(min(args[0],args[3]),max(args[0],args[3])+1):
                for y in range(min(args[1],args[4]),max(args[1],args[4])+1):
                    for z in range(min(args[2],args[5]),max(args[2],args[5])+1):
                        coords = (x,y,z)
                        if coords in self.scene:
                            self.scene[coords].visible = False
                            del self.scene[coords]
                        self.scene[coords] = box(pos=coords, length=1, height=1, width=1, color=c, opacity=opacity, material=m)
                        self.scene[coords].mcBlock = (args[6],args[7])

    @staticmethod
    def create(address = None, port = None):
        return Minecraft()

# monkey-patch normal sleep function with visual python's
originalsleep = time.sleep
time.sleep = sleep
