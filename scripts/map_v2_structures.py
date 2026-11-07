"""Plans originaux reproductibles : format JSON de blocs, lu par FKMapV2Builder.

Ces fichiers ne sont pas des schematics WorldEdit. Leur placement est vérifié sur Paper.
"""
from pathlib import Path
import json
import math
import random

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "maps/v2/structures"


class Structure:
    def __init__(self, name):
        self.name, self.blocks, self.loot = name, {}, []
        self.random = random.Random(name)

    def put(self, x, y, z, block):
        self.blocks[x, y, z] = block if ":" in block else "minecraft:" + block

    def box(self, x1, y1, z1, x2, y2, z2, block):
        for x in range(x1, x2 + 1):
            for y in range(y1, y2 + 1):
                for z in range(z1, z2 + 1): self.put(x, y, z, block)

    def floor(self, radius, block="mossy_stone_bricks"):
        for x in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                if x*x + z*z <= radius*radius:
                    self.put(x, -1, z, block if self.random.random() > .22 else "cracked_stone_bricks")

    def chest(self, x, y, z, items):
        self.put(x, y, z, "chest[facing=south,type=single,waterlogged=false]")
        self.loot.append({"x": x, "y": y, "z": z, "items": [{"material": m, "amount": n} for m, n in items]})

    def save(self):
        values = [[x, y, z, b] for (x, y, z), b in sorted(self.blocks.items())]
        data = {"schema": 1, "name": self.name, "license": "MIT — FallenKingdomYC, création originale",
                "blocks": values, "loot": self.loot}
        (OUT / (self.name + ".json")).write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")


def generate():
    OUT.mkdir(parents=True, exist_ok=True)
    s = Structure("temple-des-racines")
    s.box(-11, -1, -9, 11, -1, 9, "stone_bricks")
    for x in range(-11, 12):
        for z in range(-9, 10):
            if s.random.random() < .28: s.put(x, -1, z, "mossy_stone_bricks")
    for x in (-9, 9):
        for z in (-7, -2, 3, 8):
            h = 7 if z < 4 else 4
            s.box(x-1, 0, z-1, x+1, 0, z+1, "chiseled_stone_bricks")
            s.box(x, 1, z, x, h, z, "stone_bricks")
            s.box(x-1, h+1, z-1, x+1, h+1, z+1, "mossy_stone_brick_slab[type=bottom,waterlogged=false]")
            if z < 0:
                s.box(x, h+2, z, x, h+2, z+4, "stone_bricks")
                s.put(x+(-1 if x>0 else 1), h, z, "vine[north=false,south=false,east=false,west=true,up=false]")
    s.box(-4, 0, -6, 4, 1, -4, "mossy_stone_bricks")
    s.box(-2, 2, -6, 2, 2, -4, "chiseled_stone_bricks")
    s.chest(0, 3, -5, [("GOLD_INGOT", 4), ("LAPIS_LAZULI", 12), ("BOOK", 3), ("BREAD", 6)])
    for x,z in ((-6,6),(5,5),(-5,-3),(4,7)):
        s.put(x,0,z,"mossy_cobblestone"); s.put(x+1,0,z,"stone_brick_slab[type=bottom,waterlogged=false]")
    s.save()

    s = Structure("mine-des-brumes")
    for x in (-9,-3,3,9):
        s.box(x,0,-3,x,5,-3,"stripped_spruce_log[axis=y]")
        s.box(x,0,3,x,5,3,"stripped_spruce_log[axis=y]")
        s.box(x,5,-3,x,5,3,"spruce_log[axis=z]")
        s.put(x,4,0,"lantern[hanging=true,waterlogged=false]")
    s.box(-9,-1,-3,9,-1,3,"spruce_planks")
    for x in range(-9,10): s.put(x,0,0,"rail[shape=east_west,waterlogged=false]")
    s.box(7,0,-7,13,3,-5,"air")
    s.box(7,-1,-7,13,-1,-5,"cobblestone")
    s.box(7,0,-8,13,0,-8,"spruce_planks")
    s.box(7,4,-8,13,4,-4,"spruce_slab[type=bottom,waterlogged=false]")
    for x,z in ((7,-8),(13,-8),(7,-4),(13,-4)): s.box(x,0,z,x,3,z,"spruce_log[axis=y]")
    s.chest(10,0,-6,[("IRON_INGOT",10),("COAL",16),("COPPER_INGOT",12),("IRON_PICKAXE",1)])
    # Galerie descendante réellement creusée, supports en bois tous les cinq blocs.
    for z in range(4,25):
        y = -min(8,(z-4)//2)
        s.box(-1,y,z,1,y+2,z,"air")
        s.box(-1,y-1,z,1,y-1,z,"stone")
        if z%2==0: s.put(0,y-1,z,"cobblestone_stairs[facing=north,half=bottom,shape=straight,waterlogged=false]")
        if z%5==0:
            for x in (-2,2): s.box(x,y,z,x,y+2,z,"spruce_log[axis=y]")
            s.box(-2,y+3,z,2,y+3,z,"spruce_log[axis=x]")
            s.put(1,y,z,"torch")
    s.save()

    s = Structure("tour-des-vents")
    s.floor(7,"cobblestone")
    for y in range(11):
        for x in range(-5,6):
            for z in range(-5,6):
                radius=x*x+z*z
                if 16<=radius<=29 and not (z>=3 and y<4 and abs(x)<=1) and not (x<-1 and y>5 and z>0):
                    s.put(x,y,z,"mossy_cobblestone" if s.random.random()<.25 else "stone_bricks")
    for x in range(-4,5):
        for z in range(-4,5):
            if x*x+z*z<16: s.put(x,6,z,"spruce_planks")
    for y in range(7):
        s.put(4,y,0,"ladder[facing=west,waterlogged=false]")
    s.put(4,6,0,"air")
    s.chest(-2,7,-1,[("ARROW",16),("BREAD",6),("COAL",8)])
    s.put(0,7,-3,"lantern[hanging=false,waterlogged=false]")
    s.save()

    s = Structure("camp-des-eclaireurs")
    for cx,cz,color in ((-7,-5,"brown"),(7,-4,"gray"),(-5,7,"green")):
        for dz in range(-3,4):
            for dx in range(-3,4):
                y=3-abs(dx)
                if y>=0: s.put(cx+dx,y,cz+dz,color+"_wool")
        for dz in (-3,3): s.box(cx,0,cz+dz,cx,3,cz+dz,"oak_fence")
        s.box(cx-2,0,cz-2,cx+2,1,cz+2,"air")
    s.put(0,0,0,"campfire[lit=false,signal_fire=false,waterlogged=false,facing=north]")
    for x,z in ((-2,0),(2,0),(0,2),(0,-2)): s.put(x,0,z,"stripped_spruce_log[axis=x]")
    s.chest(5,0,6,[("COOKED_BEEF",10),("ARROW",12),("SHIELD",1),("LEATHER",6)])
    s.save()

    s = Structure("sanctuaire-des-sources")
    for i in range(8):
        angle=i*math.pi/4; x=round(9*math.cos(angle)); z=round(9*math.sin(angle)); height=3+i%3
        s.box(x,0,z,x,height,z,"mossy_cobblestone")
        s.put(x,height+1,z,"mossy_stone_brick_slab[type=bottom,waterlogged=false]")
    for x in range(-3,4):
        for z in range(-3,4):
            if x*x+z*z<=9:
                s.put(x,-2,z,"clay"); s.put(x,-1,z,"water[level=0]")
    s.box(0,0,-7,0,8,-7,"oak_log[axis=y]")
    for x in range(-4,5):
        for y in range(6,11):
            for z in range(-11,-2):
                if x*x+(z+7)**2+(y-8)**2<22: s.put(x,y,z,"oak_leaves[persistent=true,distance=1,waterlogged=false]")
    s.box(0,0,-7,0,8,-7,"oak_log[axis=y]")
    s.chest(7,0,-3,[("BREAD",8),("BOOK",3),("LAPIS_LAZULI",8),("TORCH",16)])
    s.save()

    s = Structure("crypte-des-veilleurs")
    s.box(-9,-14,-9,9,-14,9,"deepslate_tiles")
    s.box(-9,-13,-9,9,-7,9,"deepslate_bricks")
    s.box(-8,-13,-8,8,-8,8,"air")
    for x in (-6,6):
        for z in (-6,0,6): s.box(x,-13,z,x,-8,z,"polished_deepslate")
    for x,z in ((-7,-7),(7,-7),(-7,7),(7,7)): s.put(x,-12,z,"lantern[hanging=false,waterlogged=false]")
    # Escalier de surface au sud, entièrement à pied, deux blocs de haut minimum.
    for step in range(15):
        z=23-step; y=-step
        s.box(-1,y,z,1,y+3,z,"air")
        s.box(-1,y-1,z,1,y-1,z,"stone_brick_stairs[facing=south,half=bottom,shape=straight,waterlogged=false]")
    s.box(-1,-13,8,1,-10,10,"air")
    s.chest(0,-13,-6,[("DIAMOND",2),("IRON_INGOT",6),("BREAD",8),("BOOK",2)])
    for x,z in ((-3,-3),(3,-3)): s.put(x,-13,z,"chiseled_deepslate")
    s.save()

    s = Structure("cercle-des-quatre-vents")
    s.floor(15,"stone_bricks")
    for x in range(-15,16):
        for z in range(-15,16):
            r=x*x+z*z
            if 150<r<225: s.put(x,-1,z,"gravel" if s.random.random()<.5 else "mossy_stone_bricks")
    for x,z,color in ((-9,-9,"red"),(9,-9,"blue"),(-9,9,"green"),(9,9,"yellow")):
        s.box(x,0,z,x,5,z,"andesite_wall")
        s.put(x,6,z,color+"_banner[rotation=0]")
        s.put(x,0,z+1,"lantern[hanging=false,waterlogged=false]")
    s.box(-1,0,-1,1,0,1,"chiseled_stone_bricks")
    s.put(0,1,0,"lodestone")
    # Le bloc décoratif central peut être miné comme toute structure neutre ; aucun butin ici.
    s.save()


if __name__ == "__main__":
    generate()
    print(f"Sept plans originaux écrits : {OUT}")
