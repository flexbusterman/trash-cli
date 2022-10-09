import os

from tests.put.support.fake_fs.directory import Directory
from tests.put.support.fake_fs.file import File
from tests.put.support.my_file_not_found_error import MyFileNotFoundError


class FakeFs:
    def __init__(self):
        self.root = Directory('/')

    def ls(self, path):
        dir = self.find_dir_or_file(path)
        return dir.entries()

    def mkdir(self, path):
        dirname, basename = os.path.split(path)
        dir = self.find_dir_or_file(dirname)
        dir.add_dir(basename)

    def find_dir_or_file(self, path):  # type: (str) -> Directory or File
        if path == '/':
            return self.root
        cur_dir = self.root
        for component in self.components_for(path):
            try:
                cur_dir = cur_dir.get_file(component)
            except KeyError:
                raise MyFileNotFoundError(
                    "no such file or directory: %s" % path)
        return cur_dir

    def components_for(self, path):
        return path.split('/')[1:]

    def atomic_write(self, path, content):
        self.make_file(path, content)

    def read(self, path):
        dirname, basenane = os.path.split(path)
        dir = self.find_dir_or_file(dirname)
        return dir.get_entry(basenane).file.content

    def make_file(self, path, content=''):
        dirname, basename = os.path.split(path)
        dir = self.find_dir_or_file(dirname)
        dir.add_file(basename, content)

    def get_mod(self, path):
        entry = self.find_entry(path)
        return entry.mode

    def find_entry(self, path):
        dirname, basename = os.path.split(path)
        dir = self.find_dir_or_file(dirname)
        return dir.get_entry(basename)

    def chmod(self, path, mode):
        entry = self.find_entry(path)
        entry.mode = mode

    def isdir(self, path):
        file = self.find_dir_or_file(path)
        return isinstance(file, Directory)

    def exists(self, path):
        try:
            self.find_dir_or_file(path)
            return True
        except MyFileNotFoundError:
            return False

    def remove_file(self, path):
        dirname, basename = os.path.split(path)
        dir = self.find_dir_or_file(dirname)
        dir.remove(basename)

    def makedirs(self, path):
        cur_dir = self.root
        for component in self.components_for(path):
            try:
                cur_dir = cur_dir.get_file(component)
            except KeyError:
                cur_dir.add_dir(component)
                cur_dir = cur_dir.get_file(component)