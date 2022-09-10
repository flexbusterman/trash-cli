import os
from datetime import datetime
from typing.io import TextIO

from trashcli.empty.parser import Parser

from trashcli.empty.cleanable_trashcan import CleanableTrashcan
from trashcli.empty.delete_according_date import DeleteAccordingDate, \
    ContentReader
from trashcli.empty.emptier import Emptier
from trashcli.empty.errors import Errors
from trashcli.empty.file_remove_with_error_handling import \
    FileRemoveWithErrorHandling
from trashcli.empty.guard import Guard
from trashcli.empty.is_input_interactive import is_input_interactive
from trashcli.empty.main_loop import MainLoop
from trashcli.empty.parse_reply import parse_reply
from trashcli.empty.prepare_output_message import prepare_output_message
from trashcli.empty.user import User
from trashcli.fstab import Volumes, VolumesListing
from trashcli.list import TrashDirsSelector
from trashcli.trash import Clock, TrashDirReader, print_version, println, \
    my_input, EX_OK, DirReader, TopTrashDirRules


class EmptyCmd:
    def __init__(self,
                 argv0,  # type: str
                 out,  # type: TextIO
                 err,  # type: TextIO
                 volumes_listing,  # type: VolumesListing
                 now,  # type: () -> datetime
                 file_reader,  # type: TopTrashDirRules.Reader
                 dir_reader,  # type: DirReader
                 content_reader,  # type: ContentReader
                 file_remover,  # type: FileRemoveWithErrorHandling
                 version,  # type: str
                 volumes,  # type: Volumes
                 ):
        self.volumes = volumes
        self.file_remover = file_remover
        self.dir_reader = dir_reader
        self.file_reader = file_reader
        self.volumes_listing = volumes_listing
        self.argv0 = argv0
        self.out = out
        self.err = err
        self.version = version
        self.now = now
        self.content_reader = content_reader

    def run(self, args, environ, uid):
        program_name = os.path.basename(self.argv0)
        errors = Errors(program_name, self.err)
        clock = Clock(self.now, errors)
        parser = Parser()
        parsed = parser.parse(is_input_interactive(), args)

        if parsed.version:
            action = PrintVersionAction(self.out, self.version)
            action.run(program_name, parsed, environ, uid)
        elif parsed.print_time:
            action = PrintTimeAction(self.out, clock)
            action.run(program_name, parsed, environ, uid)
        else:
            action = EmptyAction(clock,
                                 self.file_remover,
                                 self.volumes_listing,
                                 self.file_reader,
                                 self.volumes,
                                 self.dir_reader,
                                 self.content_reader,
                                 errors)
            action.run(program_name, parsed, environ, uid)

        return EX_OK


class EmptyAction:
    def __init__(self, clock, file_remover, volumes_listing, file_reader,
                 volumes, dir_reader, content_reader, errors):
        file_remover_with_error = FileRemoveWithErrorHandling(
            file_remover,
            self.print_cannot_remove_error)
        trashcan = CleanableTrashcan(file_remover_with_error)
        self.selector = TrashDirsSelector.make(volumes_listing,
                                               file_reader,
                                               volumes)
        trash_dir_reader = TrashDirReader(dir_reader)
        main_loop = MainLoop(trash_dir_reader, trashcan)
        delete_mode = DeleteAccordingDate(content_reader,
                                          clock)
        user = User(prepare_output_message, my_input, parse_reply)
        self.emptier = Emptier(main_loop, delete_mode)
        self.guard = Guard(user)
        self.errors = errors

    def run(self, _program_name, parsed, environ, uid):
        trash_dirs = self.selector.select(parsed.all_users,
                                          parsed.user_specified_trash_dirs,
                                          environ,
                                          uid)
        delete_pass = self.guard.ask_the_user(parsed.interactive,
                                              trash_dirs)
        if delete_pass.ok_to_empty:
            self.emptier.do_empty(delete_pass.trash_dirs, environ,
                                  parsed.days)

    def print_cannot_remove_error(self, path):
        self.errors.print_error("cannot remove %s" % path)


class PrintTimeAction:
    def __init__(self, out, clock):
        self.out = out
        self.clock = clock

    def run(self, _program_name, _parsed, environ, uid):
        now_value = self.clock.get_now_value(environ)
        println(self.out,
                now_value.replace(microsecond=0).isoformat())


class PrintVersionAction:
    def __init__(self, out, version):
        self.out = out
        self.version = version

    def run(self, program_name, parsed, environ, uid):
        print_version(self.out, program_name, self.version)
