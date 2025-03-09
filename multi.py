from kikit import panelize_ui_impl as ki
from kikit.units import mm, deg
from kikit.panelize import Panel, BasicGridPosition, Origin
from pcbnewTransition.pcbnew import LoadBoard, VECTOR2I
from pcbnewTransition import pcbnew
from itertools import chain


############### Custom config
board1_path = "..\\tt-ecp5-cb\\tt-ecp5-cb.kicad_pcb"
board2_path = "..\\mini-dvhstx\\mini-dvhstx.kicad_pcb"
output_path = ".\\ecp5_and_dvhstx.kicad_pcb"

board_spacing = 3*mm

################ KiKit Panel Config (Only deviations from default)

framing={
		"type": "railstb", #only rail on top and bottom
		"vspace" : "3mm", # space between board and rail
		"width": "6mm" # Width of the rail
	}
	
cuts =  {
		"type": "mousebites",
        "drill": "0.6mm",
        "spacing": "1mm"
	}
tabs = { #Add tabs between board and board as well as board and rail
		"type":"fixed",
		"vwidth": "5mm",
        "hwidth": "5mm",
        "vcount": 2,
        "hcount": 2,
        "mindistance" : "12mm",
        "maxLength": "20mm"
	}
tooling = {
        "type": "4hole",
        "hoffset": "5mm",
        "voffset": "3mm",
        "size": "2mm"
    }
fiducials = {
        "type": "4fid",
        "hoffset": "10mm",
        "voffset": "3.85mm",
        "coppersize": "1mm",
        "opening": "2mm",
    }

# Obtain full config by combining above with default
preset = ki.obtainPreset([], tabs=tabs, cuts=cuts, framing=framing, tooling=tooling, fiducials=fiducials)



################ Adjusted `panelize_ui#doPanelization`

# Prepare			
board1 = LoadBoard(board1_path)
board2 = LoadBoard(board2_path)
panel = Panel(output_path)


panel.inheritDesignSettings(board1)
panel.inheritProperties(board1)
panel.inheritTitleBlock(board1)




###### Manually build layout. Inspired by `panelize_ui_impl#buildLayout`
sourceArea1 = ki.readSourceArea(preset["source"], board1)
sourceArea2 = ki.readSourceArea(preset["source"], board2)

substrateCount = len(panel.substrates) # Store number of previous boards (probably 0)
# Prepare renaming nets and references
netRenamer = lambda x, y: "Board_{n}-{orig}".format(n=x, orig=y)
refRenamer = lambda x, y: f"{y}" if x == 0 else f"DV_{y}"

# Actually place the individual boards
# Use existing grid positioner
# Place two boards above each other
panelOrigin = VECTOR2I(0,0)
placer = BasicGridPosition(board_spacing, board_spacing) #HorSpace, VerSpace
area1 = panel.appendBoard(board1_path, panelOrigin + placer.position(0,0, None) , origin=Origin.Center, sourceArea=sourceArea1, netRenamer=netRenamer, refRenamer=refRenamer)
area2 = panel.appendBoard(board2_path, panelOrigin + VECTOR2I(37300000,-2300000), origin=Origin.Center, sourceArea=sourceArea2, netRenamer=netRenamer, refRenamer=refRenamer,  inheritDrc=False)


substrates = panel.substrates[substrateCount:] # Collect set of newly added boards

# Prepare frame and partition
framingSubstrates = ki.dummyFramingSubstrate(substrates, preset)
panel.buildPartitionLineFromBB(framingSubstrates)
backboneCuts = ki.buildBackBone(preset["layout"], panel, substrates, preset)


######## --------------------- Continue doPanelization

tabCuts = ki.buildTabs(preset, panel, substrates, framingSubstrates)

frameCuts = ki.buildFraming(preset, panel)


ki.buildTooling(preset, panel)
ki.buildFiducials(preset, panel)
for textSection in ["text", "text2", "text3", "text4"]:
	ki.buildText(preset[textSection], panel)
ki.buildPostprocessing(preset["post"], panel)

ki.makeTabCuts(preset, panel, tabCuts)
ki.makeOtherCuts(preset, panel, chain(backboneCuts, frameCuts))


ki.buildCopperfill(preset["copperfill"], panel)

ki.setStackup(preset["source"], panel)
ki.setPageSize(preset["page"], panel, board1)
ki.positionPanel(preset["page"], panel)

ki.runUserScript(preset["post"], panel)

ki.buildDebugAnnotation(preset["debug"], panel)

panel.save(reconstructArcs=preset["post"]["reconstructarcs"],
		   refillAllZones=preset["post"]["refillzones"])