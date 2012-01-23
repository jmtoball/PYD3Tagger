# -*- coding: utf-8
from PYD3Tagger.tagger import Tagger
import shutil
import unittest

class TaggingTests(unittest.TestCase):
    """Some unit testing for the model"""
    
    @classmethod
    def setUpClass(self):
        self.tagger = Tagger()
        self.testdir = "../Testset/"
        self.testdir_deep = "../Woods of Ypres/"
        # Copy a fresh instance of the testfiles to the test directory
        shutil.rmtree(self.testdir)
        shutil.copytree("../TestsetClean/", self.testdir)
        self.testfile = self.testdir + "Woods of Ypres (Woods III_ Deepest Roots and Darkest Blues) - 01 - The Northern Cold.mp3"

    def test_open_file(self):
        self.tagger.add_file(self.testfile)
        self.assertEqual(len(self.tagger.files), 1)
        self.tagger.add_file(self.testfile)
        self.assertEqual(len(self.tagger.files), 1)

    def test_open_invalid_file(self):
        self.tagger.add_file("test.py")
        self.assertEqual(len(self.tagger.files), 0)

    def test_read(self):
        self.tagger.add_file(self.testfile)
        self.assertEqual(self.tagger.read_single(0, "artist"), [u"Woods of Ypres"])

    def test_write_single(self):
        self.tagger.add_file(self.testfile)
        self.assertEqual(self.tagger.read_single(0, "artist"), [u"Woods of Ypres"])
        self.tagger.write_single(0, "artist", "Ypres of Woods")
        self.tagger.save_all()
        self.tagger.add_file(self.testfile)
        self.assertEqual(self.tagger.read_single(0, "artist"), [u"Ypres of Woods"])
        self.tagger.write_single(0, "artist", "Woods of Ypres")
        self.tagger.save_all()
        self.tagger.add_file(self.testfile)
        self.assertEqual(self.tagger.read_single(0, "artist"), [u"Woods of Ypres"])

    def test_open_dir(self):
        self.tagger.add_dir(self.testdir) 
        self.assertEqual(len(self.tagger.files), 15)

    def test_read_all(self):
        self.tagger.add_dir(self.testdir)
        for i in range(0, len(self.tagger.files)): 
            self.assertEqual(self.tagger.read_single(i, "artist"), [u"Woods of Ypres"])

    def test_read_all_deep(self):
        self.tagger.add_dir(self.testdir_deep)
        for i in range(0, len(self.tagger.files)): 
            self.assertEqual(self.tagger.read_single(i, "artist"), [u"Woods of Ypres"])

    def test_write_all(self):
        self.tagger.add_dir(self.testdir)
        self.tagger.write_all("artist", "Woods of Ypresss")
        for i in range(0, len(self.tagger.files)): 
            self.assertEqual(self.tagger.read_single(i, "artist"), [u"Woods of Ypresss"])

    def test_write_image(self):
        self.tagger.add_file(self.testfile)
        self.tagger.write_single(0, "image", path="woods.jpg", name="test")
        images = self.tagger.read_single(0, "image")
        self.assertIsNotNone(images["test"])

    def test_get_type(self):
        self.tagger.add_file(self.testfile)
        type = self.tagger.get_type(0)
        type2 = self.tagger.read_single(0, "type")
        self.assertEqual(type, "mp3")
        # The .read()-version is wrapped in a list for consistency
        self.assertEqual(type2, ["mp3"]) 

    def test_swap(self):
        self.tagger.add_dir(self.testdir)
        file0 = self.tagger.files[0]
        file1 = self.tagger.files[1]
        self.tagger.swap(0, 1)
        self.assertEqual(file0, self.tagger.files[1])
        self.assertEqual(file1, self.tagger.files[0])

    def test_utf8(self):
        self.tagger.add_file(self.testfile)
        special = unicode("öäüß–…·§%&@€", "utf-8")
        self.tagger.write_single(0, "title", special)
        self.assertEqual(special, self.tagger.read_single(0, "title")[0])
        self.tagger.save_single(0)
        self.tagger.add_file(self.testfile)
        self.assertEqual(special, self.tagger.read_single(0, "title")[0])

if __name__ == '__main__':
    unittest.main()
