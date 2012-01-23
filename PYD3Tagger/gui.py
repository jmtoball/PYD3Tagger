# -*- coding: utf-8
import os
import wx
from PYD3Tagger.image import overlay
from PYD3Tagger.tagger import Tagger
from PYD3Tagger.tag_widgets import *

# TODO:
# musicbrainz/cddb/last.fm-connection for autofilling

class TagEditor(wx.Frame):
    """The core of the graphical tagger frontend."""

    # Typical tags to be enabled by default
    default_tags = ["artist", "title", "album", "genre", "tracknumber", "image"]

    def __init__(self, parent=None, title="TagEditor"):
        """Initializes GUI elements and the model."""
        wx.Frame.__init__(self, parent, title=title, style=wx.DEFAULT_FRAME_STYLE ^ wx.RESIZE_BORDER)
        icon = wx.Icon("tag.png", wx.BITMAP_TYPE_PNG)
        self.SetIcon(icon)
        self.tagger = Tagger()
        self.tags = {}
        self.dirname = ''
        self.cur_id = 0
        self.selected_tags = self.default_tags

        # Basically, the Program consists of three main regions:
        # | Menu     |
        # ------------ 
        # | Editor   |
        # ------------ 
        # | Filelist |
        self.menubar()
        self.mainpane = wx.Panel(self)
        self.mainsizer = wx.BoxSizer(wx.HORIZONTAL)
        self.editpane = wx.GridBagSizer(hgap=28, vgap=5)
        self.fill_editor(True)
        self.listpane = self.filelist(self.mainpane)

        self.mainsizer.Add(self.editpane, 1, wx.EXPAND|wx.ALL, 10)
        self.mainsizer.Add(self.listpane, 1, wx.EXPAND|wx.ALL, 0)

        self.Show(True)
        self.Center()

        self.refresh("initial")

    def menubar(self):
        """Hooks a simple menu bar into the frame."""
        menubar = wx.MenuBar()
        filemenu = wx.Menu()

        menubar.action_open = filemenu.Append(wx.ID_ANY, "Tag F&iles", "Open Files for Tagging")
        menubar.action_open_dir = filemenu.Append(wx.ID_ANY, "Tag F&olders", "Open Files for Tagging")
        menubar.action_save = filemenu.Append(wx.ID_ANY, "&Save", "Write Tags to Files")
        menubar.action_exit =filemenu.Append(wx.ID_ANY, "&Quit", "Exit PYD3Tagger")

        self.Bind(wx.EVT_MENU, self.open, menubar.action_open)
        self.Bind(wx.EVT_MENU, self.open_dir, menubar.action_open_dir)
        self.Bind(wx.EVT_MENU, self.save, menubar.action_save)
        self.Bind(wx.EVT_MENU, self.exit, menubar.action_exit)

        menubar.Append(filemenu, "&File")
        self.menubar = menubar
        self.SetMenuBar(menubar)
 
    def fill_editor(self, initial=False):
        """Replaces the tag editor contents with updated values or a different set of widgets."""
        self.editpane.Clear(True) # We have to clear old elements before adding new ones

        # We only show a subset of the ID3/Ogg/Flac-Metadata to keep things simple.
        # TODO: Add Setting for available tag types
        row = 0
        for tag_type in self.selected_tags:
            if tag_type != "image" or not self.tagger.get_ids() or self.tagger.get_type(self.cur_id) == "mp3":
                tag = TagFactory.create_tag(self, tag_type, self.tagger, self.cur_id) 
                widgets = tag.get_widgets(self.mainpane)
                row = tag.place_widgets(widgets, self.editpane, row)
                self.tags[tag_type] = tag
                if self.tagger.get_ids():
                    tag.fill()

        # When we first initialize the Widgets there is no file to edit, so widgets are greyed out.
        children = self.GetChildren()
        for child in children:
            child.Enable(not initial)
            self.menubar.action_save.Enable(not initial)

    def filelist(self, main, refresh=False):
        # TODO: Refactor into wx.ListCtrl subclass together with swapup, -down, etc.
        # TODO: Drag and Drop Support for reordering
        """Adds a tabular list structure for the file selection."""
        up = wx.Button(main, label="Up")
        up.Bind(wx.EVT_BUTTON, self.swapup)
        down = wx.Button(main, label="Down")
        down.Bind(wx.EVT_BUTTON, self.swapdown)
        listsizer = wx.BoxSizer(wx.VERTICAL)
        listbuttons = wx.BoxSizer(wx.HORIZONTAL)
        listbuttons.Add(up, wx.ALL, 5)
        listbuttons.Add(down, 0, wx.ALIGN_RIGHT|wx.ALL, 5)

        listsizer.Add(listbuttons, 0, wx.ALIGN_RIGHT)
        filelist = wx.ListCtrl(main, style=wx.LC_REPORT, size=(630, 200))
        for (i, title) in enumerate(["#", "Artist", "Album", "Title", "Path"]):
            filelist.InsertColumn(i, title)
        self.filelist = filelist
        listsizer.Add(filelist, 1, wx.EXPAND|wx.ALL, 0)

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.select_file, self.filelist)
        return listsizer

    def swapup(self, event):
        """Swap list items upwards."""
        items = self.get_selection()
        for item in items:
            if item-1 >= 0:
                self.tagger.swap(item, item-1)
        self.refresh("list")

    def swapdown(self, event):
        """Bubble list items down."""
        items = self.get_selection()[::-1]
        for item in items:
            if item+1 < len(self.tagger.get_ids()):
                self.tagger.swap(item, item+1)
        self.refresh("list")

    def fill_filelist(self):
        """Change or exchange the entries in the file list."""
        for file_id in self.tagger.get_ids():
            tracknumber = self.tagger.read_single(file_id, "tracknumber")[0]
            if self.filelist.GetItemCount() > file_id:
                self.filelist.SetStringItem(file_id, 0, tracknumber)
            else:
                self.filelist.InsertStringItem(file_id, tracknumber)
            for (i, tag) in enumerate(["artist", "album", "title", "path"]):
                self.filelist.SetStringItem(file_id, i+1, self.tagger.read_single(file_id, tag)[0])
        for i in range(0, self.filelist.GetColumnCount()):
            self.filelist.SetColumnWidth(i, wx.LIST_AUTOSIZE)

    def get_selection(self):
        """Retrieve the list items that are currently selected."""
        selection = []
        selected = self.filelist.GetFirstSelected(self)
        while selected != -1:
            selection.append(selected)
            selected = self.filelist.GetNextSelected(selected)
        return selection

    def select_file(self, event):
        """Change the currently edited file to the selected one."""
        self.cur_id = event.GetIndex()   
        self.refresh("editor")

    def refresh(self, type):  
        """Redraw and refill parts of the application."""
        if type in ["editor", "list", "both"]:
            if type != "list":
                self.fill_editor()
            if type != "editor":
                self.fill_filelist()
            self.Refresh()
        self.mainpane.SetSizerAndFit(self.mainsizer)
        self.SetSizeHints(self.GetBestSize().width, self.GetBestSize().height) 
         
    def exit(self, event):
        """Exit ;-)"""
        self.Close(True)

    def open(self, event):
        """File-opening dialog."""
        dlg = wx.FileDialog(self, "Choose files to tag", self.dirname, "", "*.*", wx.OPEN|wx.MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            files = dlg.GetPaths()
            self.dirname = dlg.GetDirectory()
            self.tagger.add_files(files)
            self.refresh("both")
        dlg.Destroy()
    
    def open_dir(self, event):
        """Directory-open dialog."""
        dlg = wx.DirDialog(self, "Choose a folder to tag", self.dirname)
        if dlg.ShowModal() == wx.ID_OK:
            directory = dlg.GetPath()
            self.dirname = directory
            self.tagger.add_dir(directory)
            self.refresh("both")
        dlg.Destroy()

    def save(self, event):
        """Save the changed to file."""
        self.tagger.save_all()

app = wx.App(False)
TagEditor()   
app.MainLoop()
