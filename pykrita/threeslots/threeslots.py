# This script is licensed CC 0 1.0, so that you can learn from it.

# ------ CC 0 1.0 ---------------

# The person who associated a work with this deed has dedicated the
# work to the public domain by waiving all of his or her rights to the
# work worldwide under copyright law, including all related and
# neighboring rights, to the extent allowed by law.

# You can copy, modify, distribute and perform the work, even for
# commercial purposes, all without asking permission.

# https://creativecommons.org/publicdomain/zero/1.0/legalcode

import krita

class ThreeSlotsExtension(krita.Extension):

    def __init__(self, parent):
        super(ThreeSlotsExtension, self).__init__(parent)

        self.num_slots = 4
        self.current_idx = None

        self.actions = []
        self.brushResourceList = [None] * self.num_slots
        self.brushSizeList = [None] * self.num_slots
        self.paintingOpacityList = [None] * self.num_slots
        #Monitor the erase toggle
        self.kritaEraserAction = None

    def setup(self):
        #print("setup")
        self.readSettings()

    def createActions(self, window):
        #print("createAct")
        self.loadActions(window)

    def readSettings(self):
        brushResourceList = Application.readSetting(
            "", "threeslots", "").split(',')

        if len(brushResourceList) == self.num_slots:
            #Convert brush names to resource pointers
            for idx, brush_string in enumerate(brushResourceList):
                allPresets = Application.resources("preset")
                if brush_string == "None" or brush_string not in allPresets:
                    self.brushResourceList[idx] = None
                else:
                    self.brushResourceList[idx] = allPresets[brush_string]

        brushSizeList = Application.readSetting(
            "", "threeslotsSize", "").split(',')

        if len(brushSizeList) == self.num_slots:
            for idx, brush_size in enumerate(brushSizeList):
                try:
                    self.brushSizeList[idx] = float(brush_size)
                except:
                    self.brushSizeList[idx] = None

        paintingOpacityList = Application.readSetting(
            "", "threeslotsOpacity", "").split(',')

        if len(paintingOpacityList) == self.num_slots:
            for idx, brush_opacity in enumerate(paintingOpacityList):
                try:
                    self.paintingOpacityList[idx] = float(brush_opacity)
                except:
                    self.paintingOpacityList[idx] = None

        #setting = Application.readSetting("", "threeslotsCurIdx", "0")
        #try:
        #    self.current_idx = int(setting)
        #except:
        #    self.current_idx = 0


    def writeSettings(self):
        #print("write")
        brushNameList = [None] * self.num_slots

        #Convert the resource pointers to brush names
        for idx, brush_res in enumerate(self.brushResourceList):
            if brush_res == None:
                continue
            brushNameList[idx] = brush_res.name()

        Application.writeSetting("", "threeslots", ','.join(map(str, brushNameList)))
        Application.writeSetting("", "threeslotsSize", ','.join(map(str, self.brushSizeList)))
        Application.writeSetting("", "threeslotsOpacity", ','.join(map(str, self.paintingOpacityList)))
        #Application.writeSetting("", "threeslotsCurIdx", str(self.current_idx))

    def loadActions(self, window):

        for index in range(self.num_slots):
            if index == 0:
                text_label = str(i18n("Activate Eraser (Slot {num})")).format(num = str(index + 1))
            else:
                text_label = str(i18n("Activate Brush (Slot {num})")).format(num = str(index + 1))
            action = window.createAction("activate_slot_" + str(index + 1), text_label, "")
            action.triggered.connect(self.activatePreset)

            action.preset = index
            self.actions.append(action)

    def initSlot(self):
        #TODO currently unused. This is intended to be used so the slot used on shutdown is restored on startup
        #Switch to the stored slot
        window = Application.activeWindow()

        if (window and len(window.views()) > 0):
            self.useSlot(self.current_idx, window)

    def activatePreset(self):
        cur_slot_idx = self.sender().preset
        old_slot_idx = self.current_idx

        if cur_slot_idx == 3:
            Application.action("KritaFill/KisToolGradient").trigger()
        else:
            Application.action("KritaShape/KisToolBrush").trigger()

        if self.kritaEraserAction == None:
            #Setup so that we can ensure the erase mode when manually switching brushes
            self.kritaEraserAction = Application.action("erase_action")
            self.kritaEraserAction.changed.connect(self.ensure_erase_mode)

        if cur_slot_idx == old_slot_idx:
            return

        window = Application.activeWindow()

        if (window and len(window.views()) > 0):
            if old_slot_idx != None:
                # Save the slot settings from the old slot we are switching away from
                self.brushSizeList[old_slot_idx] = window.views()[0].brushSize()
                self.paintingOpacityList[old_slot_idx] = window.views()[0].paintingOpacity()
                self.brushResourceList[old_slot_idx] = window.views()[0].currentBrushPreset()
            # Load setting from the slot we are switching to
            self.useSlot(cur_slot_idx, window)

    def useSlot(self, num_slot, window):
        #print(num_slot)
        #View->brushSize
        #View->currentBrushPreset
        #View->setBrushSize
        #View->setCurrentBrushPreset
        storedPreset = self.brushResourceList[num_slot]
        size = self.brushSizeList[num_slot]
        opacity = self.paintingOpacityList[num_slot]

        if storedPreset != None and size != None and opacity != None:
            #Activate brush preset
            window.views()[0].activateResource(storedPreset)
            #Restore saved brush size
            size = self.brushSizeList[num_slot]
            window.views()[0].setBrushSize(size)
            #Restore saved brush opacity
            opacity = self.paintingOpacityList[num_slot]
            window.views()[0].setPaintingOpacity(opacity)
        self.current_idx = num_slot

        #Ensure erase mode is correct
        if self.in_wrong_erase_mode():
            self.kritaEraserAction.trigger()

    def ensure_erase_mode(self):
        if self.in_wrong_erase_mode():
            self.startTimer(10)

    def in_wrong_erase_mode(self):
        #slot 0 is always in erase mode
        if self.current_idx == 0:
            if not self.kritaEraserAction.isChecked():
                return True
        else:
            if self.kritaEraserAction.isChecked():
                return True
        return False

    def timerEvent(self, event):
        #This is used to work around that we can't immediately switch eraser mode when the "changed" signal is triggered
        #print("Timer ID:", event.timerId())
        self.kritaEraserAction.trigger()
        self.killTimer(event.timerId())

