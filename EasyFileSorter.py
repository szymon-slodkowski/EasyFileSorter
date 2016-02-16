import os
import shutil
from datetime import datetime
from optparse import OptionParser


class EFSError(Exception):
    pass


class EasyFileSorter(object):

    def __init__(self, source_dir, destination_dir, remove_original_files=False, overwrite=False):
        """
        Creates EasyFileSorter object

        :param source_dir: Path to source directory
        :param destination_dir: Path to destination directory
        :param remove_original_files: If remove_original_files=True files are removed from source directory
        (moved from source_dir to subdir in destination_dir), otherwise files are copied.
        :raise EFSError if destination directory does not exist
        :param overwrite: Indicates if in case of duplicated files names file should be overwritten
        or copied with new name.
        :rtype: EasyFileSorter
        :return: -
        """
        self.source_dir = source_dir
        self.destination_dir = destination_dir
        self.found_files = []
        self.remove_original_files = remove_original_files
        self.overwrite = overwrite
        if not os.path.isdir(self.source_dir):
            raise EFSError("{0} is not existing directory".format(self.source_dir))

    def scan_directory(self, recursive=False):
        """
        Looks for files self.source_dir directory
        :param recursive: If recursive=True then function is looking for files in source_dir an also in subdirectories.
        :return: -
        """
        found_files = []
        if not os.path.isdir(self.source_dir):
            raise EFSError()
        for root, directories, files in os.walk(self.source_dir):
            for file_name in files:
                found_files.append((root, file_name))
            if not recursive:
                break
        self.found_files = found_files

    def transfer_files(self):
        """
        This function is transfering found files from source directory to subdirectories in destination directory
        :return: -
        """
        for f in self.found_files:
            original_file = os.path.join(f[0], f[1])
            modification_timestamp = os.path.getmtime(original_file)
            modification_date = datetime.fromtimestamp(modification_timestamp)
            year = str(modification_date.year)
            month = modification_date.month
            day = modification_date.day
            new_path = os.path.join(self.destination_dir, year,
                                    "{0}-{1:02d}".format(year, month),
                                    "{0}-{1:02d}-{2:02d}".format(year, month, day))
            if not os.path.isdir(new_path):
                os.makedirs(new_path)
            if not self.overwrite:
                new_path = self._get_new_filename(destination_directory=new_path, filename=f[1])
            if self.remove_original_files:
                shutil.move(original_file, new_path)
            else:
                shutil.copy2(original_file, new_path)

    def _get_new_filename(self, destination_directory, filename):
        """
        Helper function to create unique file name (to omit issue with duplicated files names)
        :param destination_directory:
        :param filename:
        :rtype String
        :return: Unique file name (full path)
        """
        if os.path.exists(os.path.join(destination_directory, filename)):
            new_filename = os.path.splitext(filename)[0] + "_1" + os.path.splitext(filename)[1]
            return self._get_new_filename(destination_directory, new_filename)
        else:
            return os.path.join(destination_directory, filename)


def main():
    options_parser = OptionParser("usage: %prog [options]")
    options_parser.add_option("-s", "--src",
                              dest="src_dir",
                              type="string",
                              help="Sort file from given directory",
                              metavar="SOURCE_DIR")
    options_parser.add_option("-d", "--dst",
                              dest="dest_dir",
                              help="Transfer sorted files into given directory",
                              type="string",
                              metavar="DESTINATION_DIR")
    options_parser.add_option("-r", "--recursive",
                              action="store_true",
                              dest="recursive",
                              help="Find files recursively in source directory")
    options_parser.add_option("-m", "--move",
                              action="store_true",
                              dest="remove_original",
                              help="Moving files instead of copying. Please make note that original files are removed.")
    options_parser.add_option("-o", "--overwrite",
                              action="store_true",
                              dest="overwrite",
                              help="Overwrite existing file in case of duplicated filename."
                                   "If this option is not set: in case of filename's duplication,"
                                   "file is moved with new unique name.")
    (options, args) = options_parser.parse_args()

    if options.src_dir is None or options.dest_dir is None:
        options_parser.print_help()
        return
    s = EasyFileSorter("a", "b")
    s.scan_directory()
    file_sorter = EasyFileSorter(source_dir=options.src_dir,
                                 destination_dir=options.dest_dir,
                                 remove_original_files=options.remove_original,
                                 overwrite=options.overwrite)
    file_sorter.scan_directory(recursive=options.recursive)
    file_sorter.transfer_files()

if __name__ == '__main__':
    main()
