# ***********************************************************************
# *                                                                     *
# * Copyright (c) 2019 Hakan Seven <hakanseven12@gmail.com>             *
# *                                                                     *
# * This program is free software; you can redistribute it and/or modify*
# * it under the terms of the GNU Lesser General Public License (LGPL)  *
# * as published by the Free Software Foundation; either version 3 of   *
# * the License, or (at your option) any later version.                 *
# * for detail see the LICENCE text file.                               *
# *                                                                     *
# * This program is distributed in the hope that it will be useful,     *
# * but WITHOUT ANY WARRANTY; without even the implied warranty of      *
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the       *
# * GNU Library General Public License for more details.                *
# *                                                                     *
# * You should have received a copy of the GNU Library General Public   *
# * License along with this program; if not, write to the Free Software *
# * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307*
# * USA                                                                 *
# *                                                                     *
# ***********************************************************************
import FreeCAD as App
import FreeCADGui as Gui
import os
from PySide.QtGui import QIcon, QAction, QPalette, QColor
from PySide.QtWidgets import (
    QListWidgetItem,
    QTableWidgetItem,
    QListWidget,
    QTableWidget,
    QSpinBox,
    QWidget,
    QToolBar,
    QComboBox,
    QPushButton,
    QToolButton,
    QTabWidget,
)
from PySide.QtCore import Qt, SIGNAL, QTimer, QRect
import sys
import json
from datetime import datetime
import shutil
import Standard_Functions_RIbbon as StandardFunctions
import Parameters_Ribbon

# Get the resources
pathIcons = Parameters_Ribbon.ICON_LOCATION
pathStylSheets = Parameters_Ribbon.STYLESHEET_LOCATION
pathUI = Parameters_Ribbon.UI_LOCATION
pathBackup = Parameters_Ribbon.BACKUP_LOCATION
sys.path.append(pathIcons)
sys.path.append(pathStylSheets)
sys.path.append(pathUI)
sys.path.append(pathBackup)

# import graphical created Ui. (With QtDesigner or QtCreator)
import Design_ui as Design_ui

# Define the translation
translate = App.Qt.translate


class LoadDialog(Design_ui.Ui_Form):

    # Define list of the workbenches, toolbars and commands on class level
    List_Workbenches = []
    StringList_Toolbars = []
    List_Commands = []

    # Create lists for the several list in the json file.
    List_IgnoredToolbars = []
    List_IconOnlyToolbars = []
    List_QuickAccessCommands = []
    List_IgnoredWorkbenches = []
    Dict_RibbonCommandPanel = {}
    List_SortedCommands = []
    List_SortedToolbars = []
    Dict_CustomToolbars = {}

    ShowText = False

    def __init__(self):
        # Makes "self.on_CreateBOM_clicked" listen to the changed control values instead initial values
        super(LoadDialog, self).__init__()

        # # this will create a Qt widget from our ui file
        self.form = Gui.PySideUic.loadUi(os.path.join(pathUI, "Design.ui"))

        # Make sure that the dialog stays on top
        self.form.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # Set the window title
        self.form.setWindowTitle("Ribbon design")

        # Get the style from the main window and use it for this form
        mw = Gui.getMainWindow()
        palette = mw.palette()
        self.form.setPalette(palette)
        Style = mw.style()
        self.form.setStyle(Style)

        # # Set the default size of the form
        # Geometry = self.form.geometry()
        # Geometry.setWidth(580)
        # self.form.setGeometry(Geometry)

        # region - create the lists ------------------------------------------------------------------
        #
        # Create a list of all workbenches with their icon
        self.List_Workbenches.clear()
        List_Workbenches = Gui.listWorkbenches().copy()
        for WorkBenchName in List_Workbenches:
            if str(WorkBenchName) != "" or WorkBenchName is not None:
                if str(WorkBenchName) != "NoneWorkbench":
                    Icon = None
                    IconName = str(Gui.getWorkbench(WorkBenchName).Icon)
                    if IconName != "":
                        Icon = Gui.getIcon(IconName)
                    WorkbenchTitle = Gui.getWorkbench(WorkBenchName).MenuText
                    self.List_Workbenches.append(
                        [str(WorkBenchName), Icon, WorkbenchTitle]
                    )

        # Create a list of all toolbars
        self.StringList_Toolbars.clear()
        # Store the current active workbench
        ActiveWB = Gui.activeWorkbench().name()
        # Go through the list of workbenches
        for WorkBench in self.List_Workbenches:
            # Activate the workbench. Otherwise, .listToolbars() returns empty
            Gui.activateWorkbench(WorkBench[0])
            # Get the toolbars of this workbench
            wbToolbars: list = Gui.getWorkbench(WorkBench[0]).listToolbars()
            # Go through the toolbars
            for Toolbar in wbToolbars:
                # Go through the list of toolbars. If already present, skip it.
                # Otherwise add it the the list.
                IsInList = False
                for i in range(len(self.StringList_Toolbars)):
                    if Toolbar == self.StringList_Toolbars[i][0]:
                        IsInList = True

                if IsInList is False:
                    self.StringList_Toolbars.append([Toolbar, WorkBench[2]])
        CustomToolbars = self.List_ReturnCustomToolbars()
        for Customtoolbar in CustomToolbars:
            self.StringList_Toolbars.append(Customtoolbar)
        # re-activate the workbench that was stored.
        Gui.activateWorkbench(ActiveWB)

        # Create a list of all commands with their icon
        self.List_Commands.clear()
        # Create a list of command names
        CommandNames = []
        for i in range(len(self.List_Workbenches)):
            WorkBench = Gui.getWorkbench(self.List_Workbenches[i][0])
            ToolbarItems = WorkBench.getToolbarItems()

            for key, value in ToolbarItems.items():
                for j in range(len(value)):
                    Item = [value[j], self.List_Workbenches[i][0]]
                    # if CommandNames.__contains__(Item) is False:
                    IsInList = False
                    for k in range(len(CommandNames)):
                        if CommandNames[k][0] == value[j]:
                            IsInList = True
                    if IsInList is False:
                        CommandNames.append(Item)

        # Go through the list
        for CommandName in CommandNames:
            # get the command with this name
            command = Gui.Command.get(CommandName[0])
            WorkBenchName = CommandName[1]
            if command is not None:
                # get the icon for this command
                if command.getInfo()["pixmap"] != "":
                    Icon = Gui.getIcon(command.getInfo()["pixmap"])
                else:
                    Icon = None
                MenuName = command.getInfo()["menuText"].replace("&", "")
                self.List_Commands.append(
                    [CommandName[0], Icon, MenuName, WorkBenchName]
                )
        # add also custom commands
        Toolbars = self.List_ReturnCustomToolbars()
        for Toolbar in Toolbars:
            WorkbenchTitle = Toolbar[1]
            for WorkBench in self.List_Workbenches:
                if WorkbenchTitle == WorkBench[2]:
                    WorkBenchName = WorkBench[0]
                    for CustomCommand in Toolbar[2]:
                        command = Gui.Command.get(CustomCommand)
                        if command.getInfo()["pixmap"] != "":
                            Icon = Gui.getIcon(command.getInfo()["pixmap"])
                        else:
                            Icon = None
                        MenuName = command.getInfo()["menuText"].replace("&", "")
                        self.List_Commands.append(
                            [CustomCommand, Icon, MenuName, WorkBenchName]
                        )

        #
        # endregion ----------------------------------------------------------------------

        # Read the jason file and fill the lists
        self.ReadJson()

        # Clear all listWidgets
        self.form.WorkbenchList.clear()
        self.form.WorkbenchesAvailable.clear()
        self.form.WorkbenchesSelected.clear()
        self.form.ToolbarsToExclude.clear()
        self.form.ToolbarsExcluded.clear()
        self.form.CommandsAvailable.clear()
        self.form.CommandsSelected.clear()
        self.form.ToolbarsAvailable.clear()
        self.form.ToolbarsSelected.clear()
        self.form.ToolbarsOrder.clear()

        # region - Load all controls------------------------------------------------------------------
        #
        # -- Ribbon design tab --
        # Add all workbenches to the ListItem Widget. In this case a dropdown list.
        self.addWorkbenches()
        # Add all toolbars of the selected workbench to the toolbar list(dropdown)
        self.on_WorkbenchList__TextChanged()
        self.on_WorkbenchList_2__textChanged(False)

        # load the commands in the table.
        self.on_ToolbarList__TextChanged()

        # -- Excluded toolbars --
        self.ExcludedToolbars()

        # -- Quick access toolbar tab --
        # Add all commands to the listbox for the quick access toolbar
        self.QuickAccessCommands()

        # -- Custom panel tab --
        self.form.CustomToolbarSelector.addItem("New")
        for key, value in self.Dict_CustomToolbars["customToolbars"].items():
            self.form.CustomToolbarSelector.addItem(key)
        #
        # endregion-----------------------------------------------------------------------------------

        # region - connect controls with functions----------------------------------------------------
        #
        #
        # --- QuickCommandsTab ------------------
        #
        # Connect Add/Remove and move events to the buttons on the QuickAccess Tab
        self.form.Add_Command.connect(
            self.form.Add_Command, SIGNAL("clicked()"), self.on_AddCommand_clicked
        )
        self.form.Remove_Command.connect(
            self.form.Remove_Command, SIGNAL("clicked()"), self.on_RemoveCommand_clicked
        )
        self.form.MoveUp_Command.connect(
            self.form.MoveUp_Command, SIGNAL("clicked()"), self.on_MoveUpCommand_clicked
        )
        self.form.MoveDown_Command.connect(
            self.form.MoveDown_Command,
            SIGNAL("clicked()"),
            self.on_MoveDownCommand_clicked,
        )

        # Connect the filter for the quick commands on the quickcommands tab
        def FilterQuickCommands_1():
            self.on_ListCategory_1_TextChanged()

        # Connect the filter for the quick commands on the quickcommands tab
        self.form.ListCategory_1.currentTextChanged.connect(FilterQuickCommands_1)
        # Connect the searchbar for the quick commands on the quick commands tab
        self.form.SearchBar_1.textChanged.connect(self.on_SearchBar_1_TextChanged)

        #
        # --- ExcludePanelsTab ------------------
        #
        # Connect LoadToolbars with the dropdown ToolbarList on the Ribbon design tab
        def FilterQuickCommands_2():
            self.on_ListCategory_2_TextChanged()

        # Connect the filter for the toolbars on the toolbar tab
        self.form.ListCategory_2.currentTextChanged.connect(FilterQuickCommands_2)
        # Connect the searchbar for the toolbars on the toolbar tab
        self.form.SearchBar_2.textChanged.connect(self.on_SearchBar_2_TextChanged)
        # Connect Add/Remove events to the buttons on the Toolbars Tab
        self.form.Add_Toolbar.connect(
            self.form.Add_Toolbar, SIGNAL("clicked()"), self.on_AddToolbar_clicked
        )
        self.form.Remove_Toolbar.connect(
            self.form.Remove_Toolbar, SIGNAL("clicked()"), self.on_RemoveToolbar_clicked
        )

        #
        # --- IncludeWorkbenchTab ------------------
        #
        # Connect Add/Remove events to the buttons on the Workbench Tab
        self.form.Add_Workbench.connect(
            self.form.Add_Workbench, SIGNAL("clicked()"), self.on_AddWorkbench_clicked
        )
        self.form.Remove_Workbench.connect(
            self.form.Remove_Workbench,
            SIGNAL("clicked()"),
            self.on_RemoveWorkbench_clicked,
        )

        #
        # --- CustomPanelsTab ------------------
        #
        # Connect move and events to the buttons on the Custom Panels Tab
        self.form.MoveUp_PanelCommand.connect(
            self.form.MoveUp_PanelCommand,
            SIGNAL("clicked()"),
            self.on_MoveUp_PanelCommand_clicked,
        )
        self.form.MoveDown_PanelCommand.connect(
            self.form.MoveDown_PanelCommand,
            SIGNAL("clicked()"),
            self.on_MoveDown_PanelCommand_clicked,
        )

        # Connect Add events to the buttons on the Custom Panels Tab for adding commands to the panel
        self.form.Add_Panel.connect(
            self.form.Add_Panel, SIGNAL("clicked()"), self.on_AddPanel_clicked
        )

        self.form.AddCustomToolbar.connect(
            self.form.AddCustomToolbar,
            SIGNAL("clicked()"),
            self.on_AddCustomToolbar_clicked,
        )

        # Connect custom toolbar selector on the Custom Panels Tab
        def CustomToolbarSelect():
            self.on_CustomToolbarSelector_clicked()

        self.form.CustomToolbarSelector.currentTextChanged.connect(CustomToolbarSelect)

        self.form.RemovePanel.connect(
            self.form.RemovePanel, SIGNAL("clicked()"), self.on_RemovePanel_clicked
        )

        #
        # --- RibbonDesignTab ------------------
        #
        # Connect LoadWorkbenches with the dropdown WorkbenchList on the Ribbon design tab
        def LoadWorkbenches():
            self.on_WorkbenchList__TextChanged()

        self.form.WorkbenchList.currentTextChanged.connect(LoadWorkbenches)

        # Connect LoadToolbars with the dropdown ToolbarList on the Ribbon design tab
        def LoadToolbars():
            self.on_ToolbarList__TextChanged()

        self.form.ToolbarList.currentTextChanged.connect(LoadToolbars)

        # Connect the icon only checkbox
        self.form.IconOnly.clicked.connect(self.on_IconOnly_clicked)
        # Connect a click event on the tablewidgit on the Ribbon design tab
        self.form.tableWidget.itemClicked.connect(self.on_tableCell_clicked)

        # Connect move events to the buttons on the Ribbon design Tab
        self.form.MoveUp_RibbonCommand.connect(
            self.form.MoveUp_RibbonCommand,
            SIGNAL("clicked()"),
            self.on_MoveUpTableWidget_clicked,
        )
        self.form.MoveDown_RibbonCommand.connect(
            self.form.MoveDown_RibbonCommand,
            SIGNAL("clicked()"),
            self.on_MoveDownTableWidget_clicked,
        )
        self.form.MoveUp_Toolbar.connect(
            self.form.MoveUp_Toolbar,
            SIGNAL("clicked()"),
            self.on_MoveUp_Toolbar_clicked,
        )
        self.form.MoveDown_Toolbar.connect(
            self.form.MoveDown_Toolbar,
            SIGNAL("clicked()"),
            self.on_MoveDown_Toolbar_clicked,
        )
        self.form.ToolbarsOrder.indexesMoved.connect(self.on_ToolbarsOrder_changed)

        # --- Form controls ------------------
        #
        # Connect the button GenerateJson with the function on_GenerateJson_clicked
        def GenerateJson():
            self.on_GenerateJson_clicked(self)

        self.form.GenerateJson.connect(
            self.form.GenerateJson, SIGNAL("clicked()"), GenerateJson
        )

        # Connect the button GenerateJsonExit with the function on_GenerateJsonExit_clicked
        def GenerateJsonExit():
            self.on_GenerateJsonExit_clicked(self)

        self.form.GenerateJsonExit.connect(
            self.form.GenerateJsonExit, SIGNAL("clicked()"), GenerateJsonExit
        )

        self.form.RestoreJson.connect(
            self.form.RestoreJson, SIGNAL("clicked()"), self.on_RestoreJson_clicked
        )
        self.form.ResetJson.connect(
            self.form.ResetJson, SIGNAL("clicked()"), self.on_ResetJson_clicked
        )

        # Connect LoadWorkbenches with the dropdown WorkbenchList on the Ribbon design tab
        def LoadWorkbenches_2():
            self.on_WorkbenchList_2__textChanged()

        self.form.WorkbenchList_2.currentTextChanged.connect(LoadWorkbenches_2)

        # connect the change of the current tab event to a function to set the size per tab
        self.form.tabWidget.currentChanged.connect(self.on_tabBar_currentIndex)
        # Connect the cancel button
        self.form.Cancel.clicked.connect(self.on_Cancel_clicked)
        # endregion

        # region - Modifiy controls-------------------------------------------------------------------
        #
        # -- TabWidget
        # Set the first tab activated
        self.form.tabWidget.setCurrentWidget(self.form.tabWidget.widget(0))
        # -- Ribbon design tab --
        # Settings for the table widget
        self.form.tableWidget.setEnabled(True)
        self.form.tableWidget.horizontalHeader().setVisible(True)
        self.form.tableWidget.setColumnWidth(0, 300)
        self.form.tableWidget.resizeColumnToContents(1)
        self.form.tableWidget.resizeColumnToContents(2)
        self.form.tableWidget.resizeColumnToContents(3)
        #
        self.form.label_4.hide()
        self.form.MoveDown_Toolbar.hide()
        self.form.MoveUp_Toolbar.hide()
        self.form.ToolbarsOrder.hide()
        # endregion

        return

    # region - Control functions----------------------------------------------------------------------
    # Add all toolbars of the selected workbench to the toolbar list(QComboBox)
    #
    # region - QuickCommands tab
    def on_ListCategory_1_TextChanged(self):
        self.form.CommandsAvailable.clear()

        ShadowList = []  # List to add the commands and prevent duplicates
        IsInList = False

        for ToolbarCommand in self.List_Commands:
            IsInList = ShadowList.__contains__(ToolbarCommand[0])

            if IsInList is False:
                WorkbenchTitle = Gui.getWorkbench(ToolbarCommand[3]).MenuText
                if (
                    WorkbenchTitle == self.form.ListCategory_1.currentText()
                    or self.form.ListCategory_1.currentText() == "All"
                ):
                    Command = Gui.Command.get(ToolbarCommand[0])

                    # Define a new ListWidgetItem.
                    textAddition = ""
                    Icon = QIcon(ToolbarCommand[1])
                    action = Command.getAction()
                    try:
                        if len(action) > 1:
                            Icon = action[0].icon()
                            textAddition = "..."
                    except Exception:
                        pass
                    ListWidgetItem = QListWidgetItem()
                    ListWidgetItem.setText(ToolbarCommand[2] + textAddition)
                    ListWidgetItem.setIcon(Icon)
                    ListWidgetItem.setToolTip(
                        ToolbarCommand[0]
                    )  # Use the tooltip to store the actual command.

                    # Add the ListWidgetItem to the correct ListWidget
                    if Icon is not None:
                        self.form.CommandsAvailable.addItem(ListWidgetItem)
            ShadowList.append(ToolbarCommand[0])
        return

    def on_SearchBar_1_TextChanged(self):
        self.form.CommandsAvailable.clear()

        ShadowList = []  # List to add the commands and prevent duplicates
        IsInList = False

        for ToolbarCommand in self.List_Commands:
            IsInList = ShadowList.__contains__(ToolbarCommand[0])

            if IsInList is False:
                if (
                    ToolbarCommand[2]
                    .lower()
                    .startswith(self.form.SearchBar_1.text().lower())
                ):
                    Command = Gui.Command.get(ToolbarCommand[0])

                    # Define a new ListWidgetItem.
                    textAddition = ""
                    Icon = QIcon(ToolbarCommand[1])
                    action = Command.getAction()
                    try:
                        if len(action) > 1:
                            Icon = action[0].icon()
                            textAddition = "..."
                    except Exception:
                        pass
                    ListWidgetItem = QListWidgetItem()
                    ListWidgetItem.setText(ToolbarCommand[2] + textAddition)
                    ListWidgetItem.setIcon(Icon)
                    ListWidgetItem.setToolTip(
                        ToolbarCommand[0]
                    )  # Use the tooltip to store the actual command.

                    # Add the ListWidgetItem to the correct ListWidget
                    if Icon is not None:
                        self.form.CommandsAvailable.addItem(ListWidgetItem)
            ShadowList.append(ToolbarCommand[0])
        return

    def on_AddCommand_clicked(self):
        self.AddItem(
            SourceWidget=self.form.CommandsAvailable,
            DestinationWidget=self.form.CommandsSelected,
        )

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_RemoveCommand_clicked(self):
        self.AddItem(
            SourceWidget=self.form.CommandsSelected,
            DestinationWidget=self.form.CommandsAvailable,
        )

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_MoveUpCommand_clicked(self):
        self.MoveItem(ListWidget=self.form.CommandsSelected, Up=True)

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_MoveDownCommand_clicked(self):
        self.MoveItem(ListWidget=self.form.CommandsSelected, Up=False)

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    # endregion

    # region - Exclude panels tab
    def on_ListCategory_2_TextChanged(self):
        self.form.ToolbarsToExclude.clear()

        for Toolbar in self.StringList_Toolbars:
            WorkbenchTitle = Toolbar[1]
            if (
                WorkbenchTitle == self.form.ListCategory_2.currentText()
                or self.form.ListCategory_2.currentText() == "All"
            ):

                ListWidgetItem = QListWidgetItem()
                ListWidgetItem.setText(Toolbar[0])

                # Add the ListWidgetItem to the correct ListWidget
                self.form.ToolbarsToExclude.addItem(ListWidgetItem)

    def on_SearchBar_2_TextChanged(self):
        self.form.ToolbarsToExclude.clear()

        for Toolbar in self.StringList_Toolbars:
            if Toolbar[0].lower().startswith(self.form.SearchBar_2.text().lower()):
                ListWidgetItem = QListWidgetItem()
                ListWidgetItem.setText(Toolbar[0])

                # Add the ListWidgetItem to the correct ListWidget
                self.form.ToolbarsToExclude.addItem(ListWidgetItem)

    def on_AddToolbar_clicked(self):
        self.AddItem(
            SourceWidget=self.form.ToolbarsToExclude,
            DestinationWidget=self.form.ToolbarsExcluded,
        )

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_RemoveToolbar_clicked(self):
        self.AddItem(
            SourceWidget=self.form.ToolbarsExcluded,
            DestinationWidget=self.form.ToolbarsToExclude,
        )

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    # endregion

    # region - Include workbench tab
    def on_AddWorkbench_clicked(self):
        self.AddItem(
            SourceWidget=self.form.WorkbenchesAvailable,
            DestinationWidget=self.form.WorkbenchesSelected,
        )

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_RemoveWorkbench_clicked(self):
        self.AddItem(
            SourceWidget=self.form.WorkbenchesSelected,
            DestinationWidget=self.form.WorkbenchesAvailable,
        )

    # endregion

    # region - Custom panels tab
    def on_WorkbenchList_2__textChanged(
        self, setCustomToolbarSelector: bool = False, CurrentText=""
    ):
        # Set the workbench name.
        WorkBenchName = ""
        WorkBenchTitle = ""
        for WorkBench in self.List_Workbenches:
            if WorkBench[2] == self.form.WorkbenchList_2.currentText():
                WorkBenchName = WorkBench[0]
                WorkBenchTitle = WorkBench[2]

        # Get the toolbars of the workbench
        wbToolbars = Gui.getWorkbench(WorkBenchName).listToolbars()
        CustomToolbars = self.List_ReturnCustomToolbars()
        for CustomToolbar in CustomToolbars:
            if CustomToolbar[1] == WorkBenchTitle:
                wbToolbars.append(CustomToolbar[0])

        # Get the workbench
        WorkBench = Gui.getWorkbench(WorkBenchName)

        # Clear the listwidget before filling it
        self.form.ToolbarsAvailable.clear()

        # Go through the toolbars and check if they must be ignored.
        for Toolbar in wbToolbars:
            IsIgnored = False
            for IgnoredToolbar in self.List_IgnoredToolbars:
                if Toolbar == IgnoredToolbar:
                    IsIgnored = True

            # If the are not to be ignored, add them to the listwidget
            if IsIgnored is False:
                ListWidgetItem = QListWidgetItem()
                ListWidgetItem.setText(Toolbar)
                self.form.ToolbarsAvailable.addItem(ListWidgetItem)

                if setCustomToolbarSelector is True:
                    self.form.CustomToolbarSelector.setCurrentText("New")

                if CurrentText != "":
                    self.form.WorkbenchList_2.setCurrentText(CurrentText)
        return

    def on_MoveUp_PanelCommand_clicked(self):
        self.MoveItem(ListWidget=self.form.ToolbarsSelected, Up=True)

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_MoveDown_PanelCommand_clicked(self):
        self.MoveItem(ListWidget=self.form.ToolbarsSelected, Up=False)

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_AddPanel_clicked(self):
        SelectedToolbars = self.form.ToolbarsAvailable.selectedItems()

        # Go through the list of workbenches
        for WorkBenchItem in self.List_Workbenches:
            # If the workbench title maches the selected workbench, continue
            if WorkBenchItem[2] == self.form.WorkbenchList_2.currentText():
                WorkBench = Gui.getWorkbench(WorkBenchItem[0])

                # Get the dict with the toolbars of this workbench
                ToolbarItems = WorkBench.getToolbarItems()
                CustomCommands = self.Dict_ReturnCustomToolbars(WorkBenchItem[0])
                ToolbarItems.update(CustomCommands)
                for key, value in ToolbarItems.items():
                    # Go through the selected items, if they mach continue
                    for i in range(len(SelectedToolbars)):
                        if key == SelectedToolbars[i].text():
                            for j in range(len(value)):
                                # Get the command
                                Command = Gui.Command.get(value[j])
                                if Command is None:
                                    continue
                                MenuName = Command.getInfo()["menuText"]

                                # get the icon for this command if there isn't one, leave it None
                                Icon = Gui.getIcon(Command.getInfo()["pixmap"])
                                action = Command.getAction()
                                try:
                                    if len(action) > 1:
                                        Icon = action[0].icon()
                                except Exception:
                                    pass

                                # Define a new ListWidgetItem.
                                ListWidgetItem = QListWidgetItem()
                                ListWidgetItem.setText(MenuName)
                                icon = QIcon(Icon)
                                ListWidgetItem.setIcon(icon)
                                ListWidgetItem.setData(
                                    Qt.ItemDataRole.UserRole, key
                                )  # add here the toolbar name as hidden data

                                IsInList = False
                                for k in range(self.form.ToolbarsSelected.count()):
                                    if (
                                        self.form.ToolbarsSelected.item(k).text()
                                        == ListWidgetItem.text()
                                    ):
                                        IsInList = True

                                if IsInList is False:
                                    self.form.ToolbarsSelected.addItem(ListWidgetItem)

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_AddCustomToolbar_clicked(self):
        CustomPanelTitle = ""
        if self.form.ToolbarName.text() != "":
            CustomPanelTitle = self.form.ToolbarName.text()
        if self.form.ToolbarName.text() == "":
            StandardFunctions.Mbox(
                "Enter a name for your custom panel first!", "", 0, "Warning"
            )
            return

        # Go through the list of workbenches
        for WorkBenchItem in self.List_Workbenches:
            # If the workbench title maches the selected workbench, continue
            if WorkBenchItem[2] == self.form.WorkbenchList_2.currentText():
                WorkBenchName = WorkBenchItem[0]

                # Create item that defines the custom toolbar
                Commands = []
                for i in range(self.form.ToolbarsSelected.count()):
                    ListWidgetItem = self.form.ToolbarsSelected.item(i)
                    MenuName = ListWidgetItem.text()

                    for j in range(len(self.List_Commands)):
                        if (
                            self.List_Commands[j][2] == MenuName
                            and self.List_Commands[j][3] == WorkBenchName
                        ):
                            Command = self.List_Commands[j][0]
                            Commands.append(Command)

                    OriginalToolbar = ListWidgetItem.data(Qt.ItemDataRole.UserRole)

                    self.add_keys_nested_dict(
                        self.Dict_CustomToolbars,
                        ["customToolbars", CustomPanelTitle, "commands", MenuName],
                    )
                    self.add_keys_nested_dict(
                        self.Dict_CustomToolbars,
                        ["customToolbars", CustomPanelTitle, "workbench"],
                    )

                    self.Dict_CustomToolbars["customToolbars"][CustomPanelTitle][
                        "commands"
                    ][MenuName] = OriginalToolbar
                    self.Dict_CustomToolbars["customToolbars"][CustomPanelTitle][
                        "workbench"
                    ] = WorkBenchName

                IsInList = False
                for CustomToolbar in self.Dict_CustomToolbars["customToolbars"]:
                    if CustomToolbar == CustomPanelTitle:
                        IsInList = True

                if IsInList is False:
                    self.form.CustomToolbarSelector.addItem(CustomPanelTitle)
                    self.form.CustomToolbarSelector.setCurrentText(CustomPanelTitle)

                ToolbarOrder = []
                for i2 in range(self.form.ToolbarsOrder.count()):
                    ToolbarOrder.append(self.form.ToolbarsOrder.item(i2).text())
                self.add_keys_nested_dict(
                    self.Dict_RibbonCommandPanel,
                    ["workbenches", WorkBenchName, "toolbars", "order"],
                )
                self.Dict_RibbonCommandPanel["workbenches"][WorkBenchName]["toolbars"][
                    "order"
                ] = ToolbarOrder

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_CustomToolbarSelector_clicked(self):
        self.form.ToolbarsSelected.clear()

        # If the selected item is "new", clear the list widgets and exit
        if self.form.CustomToolbarSelector.currentText() == "New":
            self.form.ToolbarsAvailable.clear()
            self.form.ToolbarName.clear()
            return

        # Get the current custom toolbar and load the commands
        CustomPanelTitle = self.form.CustomToolbarSelector.currentText()
        for item in self.Dict_CustomToolbars["customToolbars"].keys():
            if item == CustomPanelTitle:
                for key, value in self.Dict_CustomToolbars["customToolbars"][
                    CustomPanelTitle
                ]["commands"].items():
                    ShadowList = (
                        []
                    )  # Create a shadow list. To check if items are already existing.
                    for CommandListItem in self.List_Commands:
                        # Check if the items is already there
                        IsInList = ShadowList.__contains__(CommandListItem[0])
                        # if not, continue
                        if IsInList is False:
                            if CommandListItem[2] == key:
                                Command = Gui.Command.get(CommandListItem[0])
                                # Define a new ListWidgetItem.
                                ListWidgetItem = QListWidgetItem()
                                ListWidgetItem.setText(CommandListItem[2])
                                Icon = QIcon(CommandListItem[1])
                                action = Command.getAction()
                                try:
                                    if len(action) > 1:
                                        Icon = action[0].icon()
                                except Exception:
                                    pass
                                ListWidgetItem.setIcon(Icon)

                                if ListWidgetItem.text() != "":
                                    self.form.ToolbarsSelected.addItem(ListWidgetItem)

                        # Add the command to the shadow list
                        ShadowList.append(CommandListItem[0])

                # Set the workbench selector to the workbench to which this custom toolbar belongs
                WorkBenchTitle = ""
                for WorkbenchItem in self.List_Workbenches:
                    if (
                        WorkbenchItem[0]
                        == self.Dict_CustomToolbars["customToolbars"][CustomPanelTitle][
                            "workbench"
                        ]
                    ):
                        WorkBenchTitle = WorkbenchItem[2]
                self.on_WorkbenchList_2__textChanged(False, WorkBenchTitle)

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_RemovePanel_clicked(self):
        CustomPanelTitle = self.form.CustomToolbarSelector.currentText()

        for key, value in self.Dict_CustomToolbars["customToolbars"].items():
            if key == CustomPanelTitle:
                # Get the name of the workbench
                WorkbenchName = self.Dict_CustomToolbars["customToolbars"][key]
                # remove the custom toolbar from the custom toolbar dict.
                del self.Dict_CustomToolbars["customToolbars"][key]["workbench"]
                # remove the custom toolbar from the combobox
                for i in range(self.form.CustomToolbarSelector.count()):
                    if self.form.CustomToolbarSelector.itemText(i) == key:
                        self.form.CustomToolbarSelector.removeItem(i)

                # remove the custom toolbar also from the workbenches dict
                del self.Dict_RibbonCommandPanel["workbenches"][WorkbenchName][
                    "toolbars"
                ][key]

                # Enable the apply button
                self.form.GenerateJson.setEnabled(True)

                return

        return

    # endregion

    # region - Ribbon design tab
    def on_tabBar_currentIndex(self):
        if self.form.tabWidget.currentIndex() == 4:
            # Set the default size of the form
            Geometry = self.form.geometry()
            Geometry.setWidth(940)
            self.form.setGeometry(Geometry)

            self.form.label_4.show()
            self.form.MoveDown_Toolbar.show()
            self.form.MoveUp_Toolbar.show()
            self.form.ToolbarsOrder.show()
        else:
            self.form.label_4.hide()
            self.form.MoveDown_Toolbar.hide()
            self.form.MoveUp_Toolbar.hide()
            self.form.ToolbarsOrder.hide()
            # Set the default size of the form
            Geometry = self.form.geometry()
            Geometry.setWidth(580)
            self.form.setGeometry(Geometry)

    def on_WorkbenchList__TextChanged(self):
        # Set the workbench name.
        WorkBenchName = ""
        WorkBenchTitle = ""
        for WorkBench in self.List_Workbenches:
            if WorkBench[2] == self.form.WorkbenchList.currentText():
                WorkBenchName = WorkBench[0]
                WorkBenchTitle = WorkBench[2]

        # Get the toolbars of the workbench
        wbToolbars: list = Gui.getWorkbench(WorkBenchName).listToolbars()
        CustomToolbars = self.List_ReturnCustomToolbars()
        for CustomToolbar in CustomToolbars:
            if CustomToolbar[1] == WorkBenchTitle:
                wbToolbars.append(CustomToolbar[0])
        CustomPanel = self.List_AddCustomToolbarsToWorkbench()
        for CustomToolbar in CustomPanel:
            if CustomToolbar[1] == WorkBenchTitle:
                wbToolbars.append(CustomToolbar[0])

        # Clear the listwidget before filling it
        self.form.ToolbarList.clear()

        # Go through the toolbars and check if they must be ignored.
        for Toolbar in wbToolbars:
            IsIgnored = False
            for IgnoredToolbar in self.List_IgnoredToolbars:
                if Toolbar == IgnoredToolbar:
                    IsIgnored = True

            # If the are not to be ignored, add them to the listwidget
            if IsIgnored is False:
                if Toolbar != "":
                    self.form.ToolbarList.addItem(Toolbar, "")

        self.form.ToolbarsOrder.clear()

        # Sort the Toolbars according the sorted list
        def SortToolbars(Toolbar):
            try:
                position = self.List_SortedToolbars.index(Toolbar)
            except Exception:
                position = 999999

            return position

        wbToolbars.sort(key=SortToolbars)
        for Toolbar in wbToolbars:
            IsIgnored = False
            for IgnoredToolbar in self.List_IgnoredToolbars:
                if Toolbar == IgnoredToolbar:
                    IsIgnored = True

            # If the are not to be ignored, add them to the listwidget
            if IsIgnored is False:
                if Toolbar != "":
                    # Define a new ListWidgetItem.
                    ListWidgetItem = QListWidgetItem()
                    ListWidgetItem.setText(Toolbar)
                    self.form.ToolbarsOrder.addItem(ListWidgetItem)

        # Update the combobox ToolbarList
        self.on_ToolbarList__TextChanged
        return

    def on_ToolbarList__TextChanged(self):
        # Clear the table
        self.form.tableWidget.setRowCount(0)

        ShadowList = []  # Create a shadow list. To check if items are already existing.

        # Get the correct workbench name
        WorkBenchName = ""
        for WorkBench in self.List_Workbenches:
            if WorkBench[2] == self.form.WorkbenchList.currentText():
                WorkBenchName = WorkBench[0]

        # Get the workbench object
        Workbench = Gui.getWorkbench(WorkBenchName)
        # Get the toolbar name
        Toolbar = self.form.ToolbarList.currentText()
        # Copy the workbench Toolbars
        Commands = Workbench.getToolbarItems().copy()
        CustomCommands = self.Dict_ReturnCustomToolbars(WorkBenchName)
        Commands.update(CustomCommands)
        CustomPanelCommands = self.Dict_AddCustomToolbarsToWorkbench(WorkBenchName)
        Commands.update(CustomPanelCommands)

        # Get the commands in this toolbar
        ToolbarCommands = []
        for key in Commands:
            if key == Toolbar:
                ToolbarCommands = Commands[key]

        # Sort the Toolbarcommands according the sorted list
        def SortCommands(item):
            try:
                Command = Gui.Command.get(item)
                MenuName = Command.getInfo()["menuText"].replace("&", "")
                position = self.List_SortedCommands.index(MenuName)
            except Exception:
                position = 999999

            return position

        ToolbarCommands.sort(key=SortCommands)

        # Go through the list of toolbar commands
        for ToolbarCommand in ToolbarCommands:
            # Get the command
            Command = Gui.Command.get(ToolbarCommand)
            if Command is None:
                continue
            CommandName = Command.getInfo()["name"]

            # Check if the items is already there
            IsInList = ShadowList.__contains__(CommandName)
            # if not, continue
            if IsInList is False:
                # Get the text
                MenuName = Command.getInfo()["menuText"].replace("&", "")
                textAddition = ""
                IconName = ""
                # get the icon for this command if there isn't one, leave it None
                Icon = Gui.getIcon(Command.getInfo()["pixmap"])
                IconName = Command.getInfo()["pixmap"]
                action = Command.getAction()
                try:
                    if len(action) > 1:
                        Icon = action[0].icon()
                        textAddition = "..."
                except Exception:
                    pass

                # Set the default check states
                checked_small = Qt.CheckState.Checked
                checked_medium = Qt.CheckState.Unchecked
                checked_large = Qt.CheckState.Unchecked
                # set the default size
                Size = "small"

                # Go through the toolbars in the Json Ribbon list
                for WorkBenchName in self.Dict_RibbonCommandPanel["workbenches"]:
                    try:
                        for i in range(len(self.List_Workbenches)):
                            if self.List_Workbenches[i][0] == WorkBenchName:
                                MenuName = self.Dict_RibbonCommandPanel["workbenches"][
                                    WorkBenchName
                                ]["toolbars"][Toolbar]["commands"][CommandName]["text"]
                                Size = self.Dict_RibbonCommandPanel["workbenches"][
                                    WorkBenchName
                                ]["toolbars"][Toolbar]["commands"][CommandName]["size"]

                                if Size == "medium":
                                    checked_small = Qt.CheckState.Unchecked
                                    checked_medium = Qt.CheckState.Checked
                                    checked_large = Qt.CheckState.Unchecked
                                if Size == "large":
                                    checked_small = Qt.CheckState.Unchecked
                                    checked_medium = Qt.CheckState.Unchecked
                                    checked_large = Qt.CheckState.Checked
                                Icon_Json_Name = self.Dict_RibbonCommandPanel[
                                    "workbenches"
                                ][WorkBenchName]["toolbars"][Toolbar]["commands"][
                                    CommandName
                                ][
                                    "icon"
                                ]
                                if Icon_Json_Name != "":
                                    Icon = Gui.getIcon(Icon_Json_Name)
                    except Exception:
                        continue

                # Create the row in the table
                # add a row to the table widget
                self.form.tableWidget.insertRow(self.form.tableWidget.rowCount())

                # Fill the table widget ----------------------------------------------------------------------------------
                #
                # Define a table widget item
                TableWidgetItem = QTableWidgetItem()
                TableWidgetItem.setText(MenuName + textAddition)
                if (
                    Icon is not None
                ):  # At the moment, settings icon size for most dropdowns do not work properly
                    TableWidgetItem.setIcon(Icon)
                if Icon is None:
                    TableWidgetItem.setFlags(
                        TableWidgetItem.flags() & ~Qt.ItemFlag.ItemIsEnabled
                    )
                # Get the last rownumber and set this row with the TableWidgetItem
                RowNumber = self.form.tableWidget.rowCount() - 1

                # Add the first cell with the table widget
                self.form.tableWidget.setItem(RowNumber, 0, TableWidgetItem)

                # Create the second cell and set the checkstate according the checkstate as defined ealier
                Icon_small = QTableWidgetItem()
                Icon_small.setCheckState(checked_small)
                self.form.tableWidget.setItem(RowNumber, 1, Icon_small)

                # Create the third cell and set the checkstate according the checkstate as defined ealier
                Icon_medium = QTableWidgetItem()
                Icon_medium.setCheckState(checked_medium)
                self.form.tableWidget.setItem(RowNumber, 2, Icon_medium)

                # Create the last cell and set the checkstate according the checkstate as defined ealier
                Icon_large = QTableWidgetItem()
                Icon_large.setCheckState(checked_large)
                self.form.tableWidget.setItem(RowNumber, 3, Icon_large)

                # Double check the workbench name
                WorkbenchTitle = self.form.WorkbenchList.currentText()
                for item in self.List_Workbenches:
                    if item[2] == WorkbenchTitle:
                        WorkBenchName = item[0]

                # Define the order based on the order in this table widget
                Order = []
                for i in range(self.form.tableWidget.rowCount()):
                    Order.append(
                        QTableWidgetItem(self.form.tableWidget.item(i, 0))
                        .text()
                        .replace("...", "")
                    )

                # Add or update the dict for the Ribbon command panel
                self.add_keys_nested_dict(
                    self.Dict_RibbonCommandPanel,
                    ["workbenches", WorkBenchName, "toolbars", Toolbar, "order"],
                )
                self.add_keys_nested_dict(
                    self.Dict_RibbonCommandPanel,
                    [
                        "workbenches",
                        WorkBenchName,
                        "toolbars",
                        Toolbar,
                        "commands",
                        CommandName,
                    ],
                )
                self.Dict_RibbonCommandPanel["workbenches"][WorkBenchName]["toolbars"][
                    Toolbar
                ]["order"] = Order
                self.Dict_RibbonCommandPanel["workbenches"][WorkBenchName]["toolbars"][
                    Toolbar
                ]["commands"][CommandName] = {
                    "size": Size,
                    "text": MenuName,
                    "icon": IconName,
                }

                # Set the IconOnlyToolbars control
                Toolbar = self.form.ToolbarList.currentText()

                for item in self.List_IconOnlyToolbars:
                    if item == Toolbar:
                        self.form.IconOnly.setChecked(True)

                # Add the command to the shadow list
                ShadowList.append(CommandName)
        return

    def on_IconOnly_clicked(self):
        if self.form.IconOnly.isChecked() is True:
            toolbar = self.form.ToolbarList.currentText()

            isInList = False
            for item in self.List_IconOnlyToolbars:
                if item == toolbar:
                    isInList = True

            if isInList is False:
                self.List_IconOnlyToolbars.append(toolbar)

        if self.form.IconOnly.isChecked() is False:
            toolbar = self.form.ToolbarList.currentText()

            isInList = False
            for item in self.List_IconOnlyToolbars:
                if item == toolbar:
                    isInList = True

            if isInList is True:
                self.List_IconOnlyToolbars.remove(toolbar)

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_tableCell_clicked(self, Item):
        # Get the row and column of the clicked item (cell)
        row = Item.row()
        column = Item.column()
        if column == 0:
            return

        # Get the checkedstate from the clicked cell
        CheckState = self.form.tableWidget.item(row, column).checkState()
        # Go through the cells in the row. If checkstate is checkd, uncheck the other cells in the row
        for i3 in range(1, self.form.tableWidget.columnCount()):
            if CheckState == Qt.CheckState.Checked:
                if i3 == column:
                    self.form.tableWidget.item(row, i3).setCheckState(
                        Qt.CheckState.Checked
                    )
                else:
                    self.form.tableWidget.item(row, i3).setCheckState(
                        Qt.CheckState.Unchecked
                    )
        self.UpdateData()
        self.on_ToolbarsOrder_changed()

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)
        return

    def on_MoveUpTableWidget_clicked(self):
        self.MoveItem_TableWidget(self.form.tableWidget, True)

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_MoveDownTableWidget_clicked(self):
        self.MoveItem_TableWidget(self.form.tableWidget, False)

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_MoveUp_Toolbar_clicked(self):
        self.MoveItem(self.form.ToolbarsOrder, True)
        self.on_ToolbarsOrder_changed()

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_MoveDown_Toolbar_clicked(self):
        self.MoveItem(self.form.ToolbarsOrder, False)
        self.on_ToolbarsOrder_changed()

        # Enable the apply button
        self.form.GenerateJson.setEnabled(True)

        return

    def on_ToolbarsOrder_changed(self):
        # Get the correct workbench name
        WorkBenchName = ""
        for WorkBench in self.List_Workbenches:
            if WorkBench[2] == self.form.WorkbenchList.currentText():
                WorkBenchName = WorkBench[0]

        ToolbarOrder = []
        for i2 in range(self.form.ToolbarsOrder.count()):
            ToolbarOrder.append(self.form.ToolbarsOrder.item(i2).text())
        self.add_keys_nested_dict(
            self.Dict_RibbonCommandPanel,
            [
                "workbenches",
                WorkBenchName,
                "toolbars",
                "order",
            ],
        )
        self.Dict_RibbonCommandPanel["workbenches"][WorkBenchName]["toolbars"][
            "order"
        ] = ToolbarOrder

    # endregion

    # region - Form buttons tab
    def on_RestoreJson_clicked(self):
        self.form.setWindowFlags(Qt.WindowType.WindowStaysOnBottomHint)
        # get the path for the Json file
        JsonPath = os.path.dirname(__file__)
        JsonFile = os.path.join(JsonPath, "RibbonStructure.json")

        BackupFiles = []
        # returns a list of names (with extension, without full path) of all files
        # in backup path
        for name in os.listdir(pathBackup):
            if os.path.isfile(os.path.join(pathBackup, name)):
                if name.lower().endswith("json"):
                    BackupFiles.append(name)

        if len(BackupFiles) > 0:
            SelectedDile = StandardFunctions.Mbox(
                "Select backup file", "", 21, "NoIcon", BackupFiles[0], BackupFiles
            )
            BackupFile = os.path.join(pathBackup, SelectedDile)
            result = shutil.copy(BackupFile, JsonFile)
            StandardFunctions.Print(
                f"Ribbonbar set back to settings from: {result}!", "Warning"
            )
            StandardFunctions.Mbox(f"Settings reset to {SelectedDile}!")

        self.form.close()
        return

    def on_ResetJson_clicked(self):
        self.form.setWindowFlags(Qt.WindowType.WindowStaysOnBottomHint)
        # get the path for the Json file
        JsonPath = os.path.dirname(__file__)
        JsonFile = os.path.join(JsonPath, "RibbonStructure.json")

        BackupFile = [os.path.join(JsonPath, "RibbonStructure_default.json")]

        result = shutil.copy(BackupFile, JsonFile)
        StandardFunctions.Print(f"Ribbonbar reset from {result}!", "Warning")
        StandardFunctions.Mbox("Settings reset to default!")

        self.form.close()
        return

    @staticmethod
    def on_GenerateJson_clicked(self):
        self.WriteJson()
        # Set the button disabled
        self.form.GenerateJson.setDisabled(True)
        return

    @staticmethod
    def on_GenerateJsonExit_clicked(self):
        self.WriteJson()
        # Close the form
        self.form.close()
        return

    @staticmethod
    def on_Cancel_clicked(self):
        # Close the form
        self.form.close()
        return

    # endregion

    # endregion---------------------------------------------------------------------------------------

    # region - Functions------------------------------------------------------------------------------
    def addWorkbenches(self):
        """Fill the Workbenches available, selected and workbench list"""
        self.form.WorkbenchList.clear()
        self.form.WorkbenchesAvailable.clear()
        self.form.WorkbenchesSelected.clear()
        self.form.WorkbenchList_2.clear()

        self.form.ListCategory_1.addItem("All")
        self.form.ListCategory_2.addItem("All")

        for workbench in self.List_Workbenches:
            # Default a workbench is selected
            # if in List_IgnoredWorkbenches, set IsSelected to false
            IsSelected = True
            for IgnoredWorkbench in self.List_IgnoredWorkbenches:
                if workbench[2] == IgnoredWorkbench:
                    IsSelected = False

            # Define a new ListWidgetItem.
            ListWidgetItem = QListWidgetItem()
            ListWidgetItem.setText(workbench[2])
            icon = QIcon(workbench[1])
            ListWidgetItem.setIcon(icon)

            # Add the ListWidgetItem to the correct ListWidget
            if IsSelected is False:
                self.form.WorkbenchesAvailable.addItem(ListWidgetItem)
            if IsSelected is True:
                self.form.WorkbenchesSelected.addItem(ListWidgetItem)
                self.form.WorkbenchList.addItem(icon, workbench[2])
                # Add the ListWidgetItem also to the second WorkbenchList.
                self.form.WorkbenchList_2.addItem(icon, workbench[2])

            # Add the ListWidgetItem also to the categoryListWidgets
            self.form.ListCategory_1.addItem(icon, workbench[2])
            self.form.ListCategory_2.addItem(icon, workbench[2])

        self.form.ListCategory_1.setCurrentText("All")
        self.form.ListCategory_2.setCurrentText("All")

        # Set the text in the combobox to the name of the active workbench
        self.form.WorkbenchList.setCurrentText(Gui.activeWorkbench().name())
        self.form.WorkbenchList_2.setCurrentText(Gui.activeWorkbench().name())

        return

    def ExcludedToolbars(self):
        self.form.ToolbarsToExclude.clear()
        self.form.ToolbarsExcluded.clear()

        for Toolbar in self.StringList_Toolbars:
            IsSelected = False
            for IgnoredToolbar in self.List_IgnoredToolbars:
                if Toolbar[0] == IgnoredToolbar:
                    IsSelected = True

            if Toolbar[0] != "":
                ListWidgetItem = QListWidgetItem()
                ListWidgetItem.setText(Toolbar[0])
                if IsSelected is False:
                    self.form.ToolbarsToExclude.addItem(ListWidgetItem)
                if IsSelected is True:
                    self.form.ToolbarsExcluded.addItem(ListWidgetItem)
        return

    def QuickAccessCommands(self):
        """Fill the Quick Commands Available and Selected"""
        self.form.CommandsAvailable.clear()
        self.form.CommandsSelected.clear()

        ShadowList = []  # List to add the commands and prevent duplicates
        IsInList = False

        for ToolbarCommand in self.List_Commands:
            IsInList = ShadowList.__contains__(ToolbarCommand[0])

            if IsInList is False:
                Command = Gui.Command.get(ToolbarCommand[0])
                # Default a command is not selected
                # If in List_QuickAccessCommands set IsSelected to True
                IsSelected = False
                for QuickCommand in self.List_QuickAccessCommands:
                    if ToolbarCommand[0] == QuickCommand:
                        IsSelected = True

                # Define a new ListWidgetItem.
                textAddition = ""
                Icon = QIcon(ToolbarCommand[1])
                action = Command.getAction()
                try:
                    if len(action) > 1:
                        Icon = action[0].icon()
                        textAddition = "..."
                except Exception:
                    pass
                ListWidgetItem = QListWidgetItem()
                ListWidgetItem.setText(ToolbarCommand[2] + textAddition)
                ListWidgetItem.setIcon(Icon)
                ListWidgetItem.setToolTip(
                    ToolbarCommand[0]
                )  # Use the tooltip to store the actual command.

                # Add the ListWidgetItem to the correct ListWidget
                if Icon is not None:
                    if IsSelected is False:
                        self.form.CommandsAvailable.addItem(ListWidgetItem)
                    if IsSelected is True:
                        self.form.CommandsSelected.addItem(ListWidgetItem)
            ShadowList.append(ToolbarCommand[0])
        return

    def UpdateData(self):
        for i1 in range(self.form.tableWidget.rowCount()):
            row = i1

            WorkbenchTitle = self.form.WorkbenchList.currentText()
            WorkBenchName = ""
            try:
                for WorkbenchItem in self.List_Workbenches:
                    if WorkbenchItem[2] == WorkbenchTitle:
                        WorkBenchName = WorkbenchItem[0]

                        # get the name of the toolbar
                        Toolbar = self.form.ToolbarList.currentText()
                        # create a empty size string
                        Size = "small"
                        # Defien empty strings for the command name and icon name
                        CommandName = ""
                        IconName = ""
                        # Get the command text from the first cell in the row
                        MenuName = (
                            self.form.tableWidget.item(row, 0).text().replace("...", "")
                        )

                        # Go through the list with all available commands.
                        # If the commandText is in this list, get the command name.
                        for i3 in range(len(self.List_Commands)):
                            if (
                                MenuName == self.List_Commands[i3][2]
                                and WorkBenchName == self.List_Commands[i3][3]
                            ):
                                CommandName = self.List_Commands[i3][0]
                                Command = Gui.Command.get(CommandName)
                                IconName = Command.getInfo()["pixmap"]

                                # There are a few dropdown buttons that need to be corrected
                                if CommandName == "PartDesign_CompSketches":
                                    MenuName = "Create sketch"

                                # Get the checkedstate from the clicked cell
                                # CheckState = self.form.tableWidget.item(row, column).checkState()
                                # Go through the cells in the row. If checkstate is checkd, uncheck the other cells in the row
                                for i4 in range(1, self.form.tableWidget.columnCount()):
                                    CheckState = self.form.tableWidget.item(
                                        row, i4
                                    ).checkState()
                                    if CheckState == Qt.CheckState.Checked:
                                        if i4 == 1:
                                            Size = "small"
                                        if i4 == 2:
                                            Size = "medium"
                                        if i4 == 3:
                                            Size = "large"

                                Order = []
                                for i5 in range(self.form.tableWidget.rowCount()):
                                    Order.append(
                                        self.form.tableWidget.item(i5, 0)
                                        .text()
                                        .replace("...", "")
                                    )

                                self.add_keys_nested_dict(
                                    self.Dict_RibbonCommandPanel,
                                    [
                                        "workbenches",
                                        WorkBenchName,
                                        "toolbars",
                                        Toolbar,
                                        "order",
                                    ],
                                )
                                self.add_keys_nested_dict(
                                    self.Dict_RibbonCommandPanel,
                                    [
                                        "workbenches",
                                        WorkBenchName,
                                        "toolbars",
                                        Toolbar,
                                        "commands",
                                        CommandName,
                                    ],
                                )

                                self.Dict_RibbonCommandPanel["workbenches"][
                                    WorkBenchName
                                ]["toolbars"][Toolbar]["order"] = Order
                                self.Dict_RibbonCommandPanel["workbenches"][
                                    WorkBenchName
                                ]["toolbars"][Toolbar]["commands"][CommandName] = {
                                    "size": Size,
                                    "text": MenuName,
                                    "icon": IconName,
                                }
            except Exception:
                continue
        return

    def ReadJson(self):
        """Read the Json file and fill the lists and set settings"""
        # OPen the JsonFile and load the data
        JsonFile = open(os.path.join(os.path.dirname(__file__), "RibbonStructure.json"))
        data = json.load(JsonFile)

        # Get all the ignored toolbars
        for IgnoredToolbar in data["ignoredToolbars"]:
            self.List_IgnoredToolbars.append(IgnoredToolbar)

        # Get all the icon only toolbars
        for IconOnlyToolbar in data["iconOnlyToolbars"]:
            self.List_IconOnlyToolbars.append(IconOnlyToolbar)

        # Get all the quick access command
        for QuickAccessCommand in data["quickAccessCommands"]:
            self.List_QuickAccessCommands.append(QuickAccessCommand)

        # Get all the ignored workbenches
        for IgnoredWorkbench in data["ignoredWorkbenches"]:
            self.List_IgnoredWorkbenches.append(IgnoredWorkbench)

        # Get the showtext value
        self.ShowText_Small = bool(data["showTextSmall"])
        self.ShowText_Medium = bool(data["showTextMedium"])
        self.ShowText_Large = bool(data["showTextLarge"])

        # Get all the custom toolbars
        self.Dict_CustomToolbars["customToolbars"] = data["customToolbars"]

        # Get the dict with the customized date for the buttons
        self.Dict_RibbonCommandPanel["workbenches"] = data["workbenches"]

        try:
            for Workbench in self.Dict_RibbonCommandPanel["workbenches"]:
                for toolbar in self.Dict_RibbonCommandPanel["workbenches"][Workbench][
                    "toolbars"
                ]:
                    for orderItem in self.Dict_RibbonCommandPanel["workbenches"][
                        Workbench
                    ]["toolbars"]["order"]:
                        self.List_SortedToolbars.append(orderItem)
        except Exception:
            pass

        try:
            for Workbench in self.Dict_RibbonCommandPanel["workbenches"]:
                for toolbar in self.Dict_RibbonCommandPanel["workbenches"][Workbench][
                    "toolbars"
                ]:
                    for orderItem in self.Dict_RibbonCommandPanel["workbenches"][
                        Workbench
                    ]["toolbars"][toolbar]["order"]:
                        self.List_SortedCommands.append(orderItem)
        except Exception:
            pass

        JsonFile.close()
        return

    def WriteJson(self):
        # Create the internal lists
        List_IgnoredToolbars = []
        List_IconOnlyToolbars = []
        List_QuickAccessCommands = []
        List_IgnoredWorkbenches = []

        # IgnoredToolbars
        ExcludedToolbars = self.ListWidgetItems(self.form.ToolbarsExcluded)
        for i1 in range(len(ExcludedToolbars)):
            IgnoredToolbar = ExcludedToolbars[i1].text()
            List_IgnoredToolbars.append(IgnoredToolbar)

        # IconOnlyToolbars
        List_IconOnlyToolbars = self.List_IconOnlyToolbars

        # QuickAccessCommands
        SelectedCommands = self.ListWidgetItems(self.form.CommandsSelected)
        for i2 in range(len(SelectedCommands)):
            QuickAccessCommand = SelectedCommands[i2].toolTip()
            List_QuickAccessCommands.append(QuickAccessCommand)

        # IgnoredWorkbences
        AvailableWorkbenches = self.ListWidgetItems(self.form.WorkbenchesAvailable)
        for i3 in range(len(AvailableWorkbenches)):
            IgnoredWorkbench = AvailableWorkbenches[i3].text()
            List_IgnoredWorkbenches.append(IgnoredWorkbench)

        # Create a resulting dict
        resultingDict = {}
        # add the various lists to the resulting dict.
        resultingDict["ignoredToolbars"] = List_IgnoredToolbars
        resultingDict["iconOnlyToolbars"] = List_IconOnlyToolbars
        resultingDict["quickAccessCommands"] = List_QuickAccessCommands
        resultingDict["ignoredWorkbenches"] = List_IgnoredWorkbenches
        # resultingDict["CustomToolbars"] = Dict_CustomToolbars
        resultingDict.update(self.Dict_CustomToolbars)
        # Add the show text property to the dict
        resultingDict["showText"] = self.ShowText

        # RibbonTabs
        # Get the Ribbon dictionary
        resultingDict.update(self.Dict_RibbonCommandPanel)

        # get the path for the Json file
        JsonPath = os.path.dirname(__file__)
        JsonFile = os.path.join(JsonPath, "RibbonStructure.json")

        # create a copy and rename it as a backup if enabled
        if Parameters_Ribbon.ENABLE_BACKUP is True:
            Suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            BackupName = f"RibbonStructure_{Suffix}.json"
            BackupFile = os.path.join(pathBackup, BackupName)
            shutil.copy(JsonFile, BackupFile)

        # Writing to sample.json
        with open(JsonFile, "w") as outfile:
            json.dump(resultingDict, outfile, indent=4)

        outfile.close()
        return

    def add_keys_nested_dict(self, dict, keys):
        for key in keys:
            if key not in dict:
                dict[key] = {}
            dict = dict[key]
        try:
            dict.setdefault(keys[-1], 1)
        except Exception:
            pass
        return

    def ListWidgetItems(self, ListWidget: QListWidget) -> list:
        items = []
        for x in range(ListWidget.count()):
            items.append(ListWidget.item(x))

        return items

    def AddItem(self, SourceWidget: QListWidget, DestinationWidget: QListWidget):
        """Move a list item widgtet from one list to another

        Args:
            SourceWidget (QListWidget): _description_
            DestinationWidget (QListWidget): _description_
        """
        Values = SourceWidget.selectedItems()

        # Go through the items
        for Value in Values:
            # Get the item text
            DestinationItem = QListWidgetItem(Value)

            # Add the item to the list with current items
            DestinationWidget.addItem(DestinationItem)

            # Go through the items on the list with items to add.
            for i in range(SourceWidget.count()):
                # Get the item
                SourceItem = SourceWidget.item(i)
                # If the item is not none and the item text is equeal to itemText,
                # remove it from the columns to add list.
                if SourceItem is not None:
                    if SourceItem.text() == DestinationItem.text():
                        SourceWidget.takeItem(i)

        return

    def MoveItem(self, ListWidget: QListWidget, Up: bool = True):
        # Get the current row
        Row = ListWidget.currentRow()
        # remove the current row
        Item = ListWidget.takeItem(Row)
        # Add the just removed row, one row higher on the list
        if Up is True:
            ListWidget.insertItem(Row - 1, Item)
            # Set the moved row, to the current row
            ListWidget.setCurrentRow(Row - 1)
        if Up is False:
            ListWidget.insertItem(Row + 1, Item)
            # Set the moved row, to the current row
            ListWidget.setCurrentRow(Row + 1)

        return

    def MoveItem_TableWidget(self, TableWidget: QTableWidget, Up: bool = True):
        row = TableWidget.currentRow()
        column = TableWidget.currentColumn()
        if Up is False:
            if row < TableWidget.rowCount() - 1:
                TableWidget.insertRow(row + 2)
                for i in range(TableWidget.columnCount()):
                    item = TableWidget.takeItem(row, i)
                    TableWidget.setItem(row + 2, i, item)
                    TableWidget.setCurrentCell(row + 2, column)
                TableWidget.removeRow(row)

        if Up is True:
            if row > 0:
                TableWidget.insertRow(row - 1)
                for i in range(TableWidget.columnCount()):
                    item = TableWidget.takeItem(row + 1, i)
                    TableWidget.setItem(row - 1, i, item)
                    TableWidget.setCurrentCell(row - 1, column)
                TableWidget.removeRow(row + 1)

        self.UpdateData()
        return

    def List_ReturnCustomToolbars(self):
        # Get the main window of FreeCAD
        mw = Gui.getMainWindow()
        Toolbars = []

        List_Workbenches = Gui.listWorkbenches().copy()
        for WorkBenchName in List_Workbenches:
            WorkbenchTitle = Gui.getWorkbench(WorkBenchName).MenuText
            if str(WorkBenchName) != "" or WorkBenchName is not None:
                if str(WorkBenchName) != "NoneWorkbench":
                    CustomToolbars: list = App.ParamGet(
                        "User parameter:BaseApp/Workbench/" + WorkBenchName + "/Toolbar"
                    ).GetGroups()

                    for Group in CustomToolbars:
                        Parameter = App.ParamGet(
                            "User parameter:BaseApp/Workbench/"
                            + WorkBenchName
                            + "/Toolbar/"
                            + Group
                        )
                        Name = Parameter.GetString("Name")

                        ListCommands = []
                        # get list of all buttons in toolbar
                        TB = mw.findChildren(QToolBar, Name)
                        allButtons: list = TB[0].findChildren(QToolButton)
                        for button in allButtons:
                            if button.text() == "":
                                continue

                            action = button.defaultAction()
                            if action is not None:
                                Command = action.objectName()
                                ListCommands.append(Command)

                        Toolbars.append([Name, WorkbenchTitle, ListCommands])

        return Toolbars

    def Dict_ReturnCustomToolbars(self, WorkBenchName):
        # Get the main window of FreeCAD
        mw = Gui.getMainWindow()
        Toolbars = {}

        if str(WorkBenchName) != "" or WorkBenchName is not None:
            if str(WorkBenchName) != "NoneWorkbench":
                CustomToolbars: list = App.ParamGet(
                    "User parameter:BaseApp/Workbench/" + WorkBenchName + "/Toolbar"
                ).GetGroups()

                for Group in CustomToolbars:
                    Parameter = App.ParamGet(
                        "User parameter:BaseApp/Workbench/"
                        + WorkBenchName
                        + "/Toolbar/"
                        + Group
                    )
                    Name = Parameter.GetString("Name")

                    if Name != "":
                        ListCommands = []
                        # get list of all buttons in toolbar
                        TB = mw.findChildren(QToolBar, Name)
                        allButtons: list = TB[0].findChildren(QToolButton)
                        for button in allButtons:
                            if button.text() == "":
                                continue
                            action = button.defaultAction()
                            Command = action.objectName()
                            ListCommands.append(Command)

                            Toolbars[Name] = ListCommands

        return Toolbars

    def Dict_AddCustomToolbarsToWorkbench(self, WorkBenchName):
        Toolbars = {}

        for CustomToolbar in self.Dict_CustomToolbars["customToolbars"]:
            ListCommands = []
            Commands = self.Dict_CustomToolbars["customToolbars"][CustomToolbar][
                "commands"
            ]
            Workbench = self.Dict_CustomToolbars["customToolbars"][CustomToolbar][
                "workbench"
            ]

            if Workbench == WorkBenchName:
                for key, value in Commands.items():
                    for i in range(len(self.List_Commands)):
                        if self.List_Commands[i][2] == key:
                            Command = self.List_Commands[i][0]
                            ListCommands.append(Command)

                    if self.List_IgnoredToolbars.__contains__(value) is False:
                        self.List_IgnoredToolbars.append(value)

                Toolbars[CustomToolbar] = ListCommands

        return Toolbars

    def List_AddCustomToolbarsToWorkbench(self):
        Toolbars = []

        List_Workbenches = Gui.listWorkbenches().copy()
        for WorkBenchName in List_Workbenches:
            WorkbenchTitle = Gui.getWorkbench(WorkBenchName).MenuText
            if str(WorkBenchName) != "" or WorkBenchName is not None:
                if str(WorkBenchName) != "NoneWorkbench":
                    for CustomToolbar in self.Dict_CustomToolbars["customToolbars"]:
                        ListCommands = []
                        Commands = self.Dict_CustomToolbars["customToolbars"][
                            CustomToolbar
                        ]["commands"]
                        Workbench = self.Dict_CustomToolbars["customToolbars"][
                            CustomToolbar
                        ]["workbench"]

                        WorkbenchTitle = Gui.getWorkbench(WorkBenchName).MenuText

                        if Workbench == WorkBenchName:
                            for key, value in Commands.items():
                                for i in range(len(self.List_Commands)):
                                    if self.List_Commands[i][2] == key:
                                        Command = self.List_Commands[i][0]
                                        ListCommands.append(Command)

                                if (
                                    self.List_IgnoredToolbars.__contains__(value)
                                    is False
                                ):
                                    self.List_IgnoredToolbars.append(value)

                            Toolbars.append(
                                [CustomToolbar, WorkbenchTitle, ListCommands]
                            )

        return Toolbars

    # endregion


def main():
    # Get the form
    Dialog = LoadDialog().form
    # Show the form
    Dialog.show()

    return