import os
import wx
from PYD3Tagger.image import overlay


class TagFactory(object):
    """Produces Tag implemenetations according to a given type."""
   
    @staticmethod
    def create_tag(main, tag_type, tagger, file_id):
        """Returns an individual tag object specific for this file and tag type."""
        if tag_type == "tracknumber":
            return TracknumTag(main, tag_type, tagger, file_id)
        elif tag_type == "image":
            return ImageTag(main, tag_type, tagger, file_id)
        return Tag(main, tag_type, tagger, file_id)



class Tag(object):
    """Generic Tag class that supports the vast number of simple textual tags."""
    
    def __init__(self, main, tag_type, tagger, file_id):
        self.main = main
        self.widgets = {}
        self.widgets_sorted = []
        self.tagger = tagger
        self.tag_type = tag_type
        self.file_id = file_id
        self.file_type = None

    def get_tagval(self):
        """Reads the tag value from the model."""
        return self.tagger.read_single(self.file_id, self.tag_type)

    def fill(self):
        """Fills the widget with data from the model."""
        self.widgets['input'].ChangeValue(self.get_tagval()[0])

    def change(self, value):
        """Keeps track of changes to the widgets and keeps associated widgets consistent."""
        value = self.widgets['input'].GetValue()
        self.tagger.write_single(self.file_id, self.tag_type, value)
        self.main.refresh("list")
    
    def make_widgets(self, parent):
        """Creates the set of widgets utilized for the tag."""
        widgets = {} 
        widgets['label'] = wx.StaticText(parent, label=self.tag_type.capitalize())
        widgets['input'] = wx.TextCtrl(parent, size=wx.Size(380, -1))
        widgets['input'].Bind(wx.EVT_TEXT, self.change)
        widgets['sync'] = wx.Button(parent, label="Sync", size=wx.Size(80, 27))
        widgets['sync'].Bind(wx.EVT_BUTTON, self.sync)
        self.widgets = widgets
        self.widgets_sorted = [widgets['label'], widgets['input'], widgets['sync']] 

    def place_widgets(self, widgets, grid, row):
        """Places the widgets associated withthis tag on a grid sizer."""
        grid.Add(self.widgets['label'], pos=(row, 0), span=wx.GBSpan(1,1), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL) 
        grid.Add(self.widgets['input'], pos=(row, 1), span=wx.GBSpan(1,2)) 
        grid.Add(self.widgets['sync'], pos=(row, 3), span=wx.GBSpan(1,1)) 
        return row+1

    def get_widgets(self, parent):
        """Retrieves the set of widgets for display or modification."""
        if not self.widgets:
            self.widgets = {}
            self.widgets_sorted = []
            self.make_widgets(parent) 
            if not self.widgets_sorted:
                self.widgets_sorted = sorted(self.widgets.values())
        return self.widgets_sorted

    def sync(self, event):
        """Syncs this tag's value to other tags of the same type in the current set of files."""
        selection = self.main.get_selection()
        for file_id in selection:
            self.tagger.write_single(file_id, self.tag_type, self.get_tagval())
        self.main.refresh("list")


class TracknumTag(Tag):
    """Tag subclass that provides widgets and functions for tracknumbers."""
    
    def make_widgets(self, parent):
        widgets = {}
        widgets['label'] = wx.StaticText(parent, label=self.tag_type.capitalize())
        widgets['fill'] = wx.Button(parent, label="Autofill", size=wx.Size(80, 27))
        widgets['fill'].Bind(wx.EVT_BUTTON, self.fillnum)
        # Tracknumbers will be displayed in two individual widgets
        for field in ['num', 'tot']:
            widgets[field] = wx.TextCtrl(parent, size=wx.Size(50, -1))
            widgets[field].Bind(wx.EVT_TEXT, self.change)
        self.widgets = widgets

    def fill(self):
        value = self.get_tagval()[0]
        if value:
            values = value.split("/")
        if not value:
            values = ["0", "0"]
        elif len(values) == 1:
            values = [values[0], "0"]
        self.widgets['num'].ChangeValue(values[0])
        self.widgets['tot'].ChangeValue(values[1])

    def change(self, value):
        num = self.widgets['num'].GetValue()
        tot = self.widgets['tot'].GetValue()
        self.tagger.write_single(self.file_id, self.tag_type, num+"/"+tot)

    def fillnum(self, event):
        """Automatically fill the track numbers in the current selection."""
        selection = self.main.get_selection()
        if not selection:
            selection = range(0, len(self.tagger.get_ids()))
        tot = len(selection)
        for (i, field_id) in enumerate(selection):
            self.tagger.write_single(field_id, "tracknumber", str(i+1)+"/"+str(tot))
        self.main.refresh("both")

    def place_widgets(self, widgets, grid, row):
        grid.Add(self.widgets['label'], pos=(row, 0), span=wx.GBSpan(1,1), flag=wx.ALL|wx.ALIGN_CENTER_VERTICAL) 
        grid.Add(self.widgets['num'], pos=(row, 1), span=wx.GBSpan(1,1)) 
        grid.Add(self.widgets['tot'], pos=(row, 2), span=wx.GBSpan(1,1)) 
        grid.Add(self.widgets['fill'], pos=(row, 3), span=wx.GBSpan(1,1)) 
        return row+1


class ImageTag(Tag):
    """Tag subclass that provides widgets and functions for embedded images like cover images."""
    apic_name = "Cover (front)"
    
    def make_widgets(self, parent):
        widgets = {} 
        widgets['label'] = wx.StaticText(parent, label=self.tag_type.capitalize())
        widgets['browse'] = wx.FilePickerCtrl(parent)
        widgets['browse'].Bind(wx.EVT_FILEPICKER_CHANGED, self.change)
        cover = wx.Bitmap("default.png") # An empty jewelcase is a placeholder for the cover.
        widgets['img'] = wx.StaticBitmap(parent, -1, cover)
        widgets['sync'] = wx.Button(parent, label="Sync")
        widgets['sync'].Bind(wx.EVT_BUTTON, self.sync)
        self.widgets = widgets

    def fill(self):
        images = self.tagger.read_single(self.file_id, self.tag_type)
        print images
        if images and self.apic_name in images:
            bg = images[self.apic_name].name
            fg = "default.png"
            mask = "mask.png"
            # The Cover Image is overlayed by a jewelcase for some eyecandy.
            merged = overlay(fg, bg, mask)
            self.widgets['img'].SetBitmap(wx.Bitmap(merged))

    def change(self, event):
        self.path = event.GetPath()
        self.tagger.write_single(self.file_id, self.tag_type, path=self.path, name=self.apic_name)
        self.fill()

    def place_widgets(self, widgets, grid, row):
        # The image widgets span two rows in the editor, unlike most of the other widgets.
        grid.Add(self.widgets['label'], pos=(row, 0), span=wx.GBSpan(1,1), flag=wx.ALL)  
        grid.Add(self.widgets['img'], pos=(row, 1), span=wx.GBSpan(1, 2)) 
        grid.Add(self.widgets['browse'], pos=(row+1, 2), span=wx.GBSpan(1, 1)) 
        grid.Add(self.widgets['sync'], pos=(row+1, 3), span=wx.GBSpan(1, 1)) 
        return row+2

    def sync(self, event):
        selection = self.main.get_selection()
        # Unfortunately the widgets lose their value when the file is switched.
        # Consequently we cannot query the FilePicker widget for the file path.
        # Instead, the image is read from the 
        images = self.tagger.read_single(self.file_id, self.tag_type)
        if images:
            path = images.values()[0].name
            for file_id in selection:
                self.tagger.write_single(file_id, self.tag_type, path=path, name=self.apic_name)
        self.main.refresh("list")


