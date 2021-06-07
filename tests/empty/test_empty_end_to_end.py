import os
import unittest

from trashcli import trash
from .. import run_command
from ..fake_trash_dir import FakeTrashDir
from ..files import make_file
from ..support import MyPath, list_files_in_dir


class TestEmptyEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = MyPath.make_temp_dir()

    def test_help(self):
        result = run_command.run_command(self.tmp_dir, "trash-empty",
                                         ['--help'])
        self.assertEqual(["""\
Usage: trash-empty [days]

Purge trashed files.

Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit

Report bugs to https://github.com/andreafrancia/trash-cli/issues
""", '', 0],
                         [result.stdout,
                          result.stderr,
                          result.exit_code])

    def test_h(self):
        result = run_command.run_command(self.tmp_dir, "trash-empty",
                                         ['-h'])
        self.assertEqual(["""\
Usage: trash-empty [days]

Purge trashed files.

Options:
  --version   show program's version number and exit
  -h, --help  show this help message and exit

Report bugs to https://github.com/andreafrancia/trash-cli/issues
""", '', 0],
                         [result.stdout,
                          result.stderr,
                          result.exit_code])

    def test_version(self):
        result = run_command.run_command(self.tmp_dir, "trash-empty",
                                         ['--version'])
        self.assertEqual(['trash-empty %s\n' % trash.version, '', 0],
                         [result.stdout,
                          result.stderr,
                          result.exit_code])

    def test_on_invalid_option(self):
        result = run_command.run_command(self.tmp_dir, "trash-empty",
                                         ['--wrong-option'])

        self.assertEqual(['',
                          "trash-empty: invalid option -- 'wrong-option'\n",
                          64],
                         result.all)

    def test_on_print_time(self):
        result = run_command.run_command(
            self.tmp_dir, "trash-empty",
            ['--print-time'],
            env={'TRASH_DATE': '1970-12-31T23:59:59'})

        self.assertEqual(['1970-12-31T23:59:59\n',
                          '',
                          0],
                         result.all)

    def test_on_trash_date_not_parsable(self):
        result = run_command.run_command(
            self.tmp_dir, "trash-empty",
            ['--print-time'],
            env={'TRASH_DATE': 'not a valid date'})

        self.assertEqual(['trash-empty: invalid TRASH_DATE: not a valid date\n',
                          0],
                         [result.stderr, result.exit_code])

    def tearDown(self):
        self.tmp_dir.clean_up()


class TestEmptyEndToEndWithTrashDir(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = MyPath.make_temp_dir()
        self.trash_dir = self.tmp_dir / 'trash-dir'
        self.fake_trash_dir = FakeTrashDir(self.trash_dir)

    def test_add_trashed_file(self):
        self.fake_trash_dir.add_trashed_file('foo', '/foo', 'FOO')

        assert self.list_trash(self.trash_dir) == ['foo.trashinfo', 'foo']

    def test_trash_dir(self):
        self.fake_trash_dir.add_trashed_file('foo', '/foo', 'FOO')

        result = run_command.run_command(self.tmp_dir, "trash-empty",
                                         ['--trash-dir', self.trash_dir])

        assert [result.all, self.list_trash(self.trash_dir)] == \
               [['', '', 0], []]

    def test_xdg_data_home(self):
        xdg_data_home = self.tmp_dir / 'xdg'
        FakeTrashDir(xdg_data_home / 'Trash').add_trashed_file('foo', '/foo', 'FOO')

        result = run_command.run_command(self.tmp_dir, "trash-empty",
                                         [], env={'XDG_DATA_HOME': xdg_data_home})

        assert [result.all, self.list_trash(xdg_data_home / 'Trash')] == \
               [['', '', 0], []]

    def test_non_trash_info_is_not_deleted(self):
        make_file(self.trash_dir / 'info' / 'non-trashinfo')

        result = run_command.run_command(self.tmp_dir, "trash-empty",
                                         ['--trash-dir', self.trash_dir])

        assert [result.all, self.list_trash(self.trash_dir)] == \
               [['', '', 0], ['non-trashinfo']]

    def test_orphan_are_deleted(self):
        make_file(self.trash_dir / 'files' / 'orphan')
        os.makedirs(self.trash_dir / 'files' / 'orphan dir')

        result = run_command.run_command(self.tmp_dir, "trash-empty",
                                         ['--trash-dir', self.trash_dir])

        assert [result.all, self.list_trash(self.trash_dir)] == \
               [['', '', 0], []]

    def list_trash(self, trash_dir):
        return list_files_in_dir(trash_dir / 'info') + \
               list_files_in_dir(trash_dir / 'files')

    def tearDown(self):
        self.tmp_dir.clean_up()
