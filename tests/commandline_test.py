#!/usr/bin/env python
# encoding: utf-8

import os
import time
from unittest import TestCase, main
from gi import require_version
require_version('Gtk', '3.0')
from gi.repository import Gtk
import vimiv.main as v_main
from vimiv.parser import parse_config

def refresh_gui(delay=0):
    time.sleep(delay)
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)


class CommandlineTest(TestCase):

    def setUp(self):
        self.settings = parse_config()
        self.vimiv = v_main.Vimiv(self.settings, [], 0)
        self.vimiv.main(True)

    def test_toggling(self):
        # Focusing
        self.vimiv.commandline.focus()
        self.assertEqual(self.vimiv.commandline.entry.get_text(), ":")
        # Leaving by deleting the colon
        self.vimiv.commandline.entry.set_text("")
        self.assertFalse(self.vimiv.commandline.box.is_visible())

    def test_run_command(self):
        before_command = self.vimiv.image.overzoom
        self.vimiv.commandline.entry.set_text(":set overzoom!")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        after_command = self.vimiv.image.overzoom
        self.assertNotEqual(before_command, after_command)

    def test_run_external(self):
        self.vimiv.commandline.entry.set_text(":!touch tmp_foo")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        time.sleep(0.1)  # Necessary so the entry is created
                          # (->multithreading...)
        files = os.listdir()
        self.assertTrue("tmp_foo" in files)
        os.remove("tmp_foo")

    def test_pipe(self):
        # Internal command
        before_command = self.vimiv.image.overzoom
        self.vimiv.commandline.entry.set_text(":!echo set overzoom! |")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        refresh_gui(0.05)
        after_command = self.vimiv.image.overzoom
        self.assertNotEqual(before_command, after_command)
        # Directory
        expected_dir = os.path.abspath("./testimages")
        self.vimiv.commandline.entry.set_text(":!ls -d testimages |")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        refresh_gui(0.05)
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Image
        expected_image = os.path.abspath("arch-logo.png")
        self.vimiv.commandline.entry.set_text(":!echo arch-logo.png |")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        refresh_gui(0.05)
        self.assertEqual(self.vimiv.paths[0], expected_image)
        os.chdir("..")

    def test_path(self):
        # Pass a directory
        expected_dir = os.path.abspath("./testimages")
        self.vimiv.commandline.entry.set_text(":./testimages")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Pass an image
        expected_image = os.path.abspath("arch-logo.png")
        self.vimiv.commandline.entry.set_text(":./arch-logo.png")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        self.assertEqual(self.vimiv.paths[0], expected_image)
        os.chdir("..")

    def test_search(self):
        self.vimiv.commandline.cmd_search()
        self.assertEqual(self.vimiv.commandline.entry.get_text(), "/")
        # Search should move into testimages
        expected_dir = os.path.abspath("./testimages")
        self.vimiv.commandline.entry.set_text("/test")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        dir_after = os.getcwd()
        self.assertEqual(expected_dir, dir_after)
        # Search should have these results
        self.vimiv.commandline.search_case = False
        self.vimiv.commandline.entry.set_text("/Ar")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        expected_search_results = ["arch_001.jpg", "arch-logo.png"]
        search_results = self.vimiv.commandline.search_names
        self.assertEqual(search_results, expected_search_results)
        # Moving forward to next result should work
        self.vimiv.commandline.search_move(1)
        self.assertEqual(self.vimiv.library.treepos, 1)
        # Searching case sensitively should have no results here
        self.vimiv.commandline.search_case = True
        self.vimiv.commandline.entry.set_text("/Ar")
        self.vimiv.commandline.handler(self.vimiv.commandline.entry)
        self.assertFalse(self.vimiv.commandline.search_names)

        os.chdir("..")


if __name__ == '__main__':
    main()
