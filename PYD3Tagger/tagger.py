import imghdr
import mutagen
from mutagen import id3
import os
import tempfile

class Tagger(object):
    """The Tagger is the model carrying out the actual tagging."""
    
    class MediaFile(object):
        """This class holds tag information used here."""
        
        def __init__(self, simple, complex, path):
            self.simple = simple
            self.complex = complex
            self.path = path
            self.type = self.complex.__class__.__name__.lower()
        

    def __init__(self):
        self.files = {}

    def add_file(self, path, file_id=0):
        """Add a single File to the Tagger."""
        if file_id == 0:
            self.files = {}
        if os.path.exists(path):
            tagger = mutagen.File(path, easy=True)
            if tagger != None:
                self.files[file_id] = self.MediaFile(tagger, mutagen.File(path), path)

    def add_dir(self, path):
        """Add a whole directory to the Tagger."""
        self.files = {}
        files_to_add = []
        directories = os.walk(path)
        for dirpath, dirs, files in directories:
            for single_file in files:
                files_to_add.append(os.path.join(dirpath,single_file))    
        self.add_files(sorted(files_to_add))

    def add_files(self, paths):
        """Add a bunch of directories to the Tagger."""
        self.files = {}
        for path in paths:
            self.add_file(path, len(self.files))

    def get_ids(self):
        """Returns a list of ids identifying individual files."""
        return self.files.keys()

    def get_type(self, file_id):
        """Returns the type of the given file."""
        return self.files[file_id].type

    def get_path(self, file_id):
        """Returns the path of the given file."""
        return self.files[file_id].path

    def swap(self, id1, id2):
        """Swaps two files around in the file list."""
        tmp = self.files[id1]
        self.files[id1] = self.files[id2]
        self.files[id2] = tmp
        
    def write_single(self, file_id, key, value="", **kwargs):
        """Write a single tag value for a single file."""
        if key == "image":
            if self.files[file_id].type == "mp3":
                path = kwargs.get("path")
                image_type = imghdr.what(path)
                if image_type in ["gif", "jpeg", "png"]:
                    if self.get_type(file_id) == "mp3": 
                        file = self.files[file_id].complex
                        image = open(path, 'rb').read()
                        file.tags.add(id3.APIC(3, 'image/'+image_type, 3, kwargs.get("name"), image)) 
                else:
                    # We fail silently if an invalid image format is given.
                    pass
            else:
                #TODO: Handle more file types.
                pass
        else:
            # All other tag types are handled generically
            self.files[file_id].simple[key] = value

    def write_all(self, key, value):
        """Write a single value to multiple files."""
        for file_id in self.files.keys():
            self.write_single(file_id, key, value)

    def save_all(self):
        """Write changes in all files to disk."""
        # TODO: Only save changed files (Keep track of writes)
        for file_id in self.files.keys():
            self.save_single(file_id)
        
    def save_single(self, file_id):
        """Write changes to a single file to disk."""
        print self.files[file_id].complex
        if self.files[file_id].complex:
            self.files[file_id].complex.save()
        file = self.files[file_id].simple
        # We are working with two separate tagging-objects.
        # A simple one for textual and a complex one for media fields.
        # The complex variant is saved first, the simple variant is then
        # reinstantiated from the changed file and changes are applied.
        changeable_file = mutagen.File(self.files[file_id].path, easy=True)
        for key in self.files[file_id].simple:
           changeable_file[key] = file[key] 
        changeable_file.save()
        self.files[file_id].simple = changeable_file

    def read_all(self, file_id):
        """Returns the whole metadata dictionary associated with this file."""
        return self.files[file_id].simple

    def read_single(self, file_id, key):
        """Retrieve data for a specific file and tag type."""
        images = {}
        # Images are handled differently
        if key == "image":
            # Only MP3 is currently supported
            if self.files[file_id].type == "mp3":
                tags = self.files[file_id].complex
                for tag in tags:
                    if tag.startswith("APIC:"):
                        # The embedded images are extracted to tempfiles
                        tmp = tempfile.NamedTemporaryFile()          
                        tmp.write(tags[tag].data)
                        tmp.flush()
                        images[tag[5:]] = tmp
                return images
            else:
                # Currently Image options will be invisible or fal silently
                # TODO: Other file types.
                pass
        elif key == "path":
            return [self.get_path(file_id)]
        elif key == "type":
            return [self.get_type(file_id)]
        elif key not in self.files[file_id].simple:
            return [""]
        return self.files[file_id].simple[key]

    def print_debug(self):
        """Prints the available data for debugging or informational purposes."""
        for file_id in self.files:
            print("###########################" +str(file_id)+":")
            print("###################### Simple") 
            print(self.files[file_id])
            print("###################### Complex") 
            print(self.files[file_id].complex)
            print("###################### Path") 
            print(self.files[file_id].path)
            print("###################### Type") 
            print(self.files[file_id].type)

