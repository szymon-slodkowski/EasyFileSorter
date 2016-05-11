import exifread
import logging
import os
import shutil
import sys
from datetime import datetime
from optparse import OptionParser


class EFSError(Exception):
    pass


class EasyFileSorter(object):

    def __init__(self, source_dir, destination_dir, remove_original_files=False, overwrite=False, use_exif=False):
        """
        Creates EasyFileSorter object

        :param source_dir: Path to source directory
        :param destination_dir: Path to destination directory
        :param remove_original_files: If remove_original_files=True files are removed from source directory
        (moved from source_dir to subdir in destination_dir), otherwise files are copied.
        :param overwrite: Indicates if in case of duplicated files names file should be overwritten
        or copied with new name.
        :raise EFSError if destination directory does not exist
        :rtype: EasyFileSorter
        :return: -
        """
        logging.info("Initialise EasyFileSorter object")
        self._source_dir = source_dir
        self._destination_dir = destination_dir
        self._found_files = []
        self._remove_original_files = remove_original_files
        self._overwrite = overwrite
        self._use_exif = use_exif
        if not os.path.isdir(self._source_dir):
            raise EFSError("{0} is not existing directory".format(self._source_dir))

    def scan_directory(self, recursive=False):
        """
        Looks for files self.source_dir directory
        :param recursive: If recursive=True then function is looking for files in source_dir an also in subdirectories.
        :return: -
        """
        logging.info("Scan {0} directory (recursive?={1})".format(self._source_dir, recursive))
        found_files = []
        if not os.path.isdir(self._source_dir):
            raise EFSError()
        for root, directories, files in os.walk(self._source_dir):
            for file_name in files:
                found_files.append((root, file_name))
                logging.info("File found: {0}".format(file_name))
            if not recursive:
                break
        self._found_files = found_files
        logging.info("{0} files found".format(len(self._found_files)))

    def transfer_files(self):
        """
        This function is transfering found files from source directory to subdirectories in destination directory
        :return: -
        """
        for f in self._found_files:
            original_file = os.path.join(f[0], f[1])
            modification_date = self._get_date_from_file(original_file, self._use_exif)
            year = str(modification_date.year)
            month = modification_date.month
            day = modification_date.day
            new_path = os.path.join(self._destination_dir, year,
                                    "{0}-{1:02d}".format(year, month),
                                    "{0}-{1:02d}-{2:02d}".format(year, month, day))
            if not os.path.isdir(new_path):
                logging.info("Make new directory: {0}".format(new_path))
                os.makedirs(new_path)
            if not self._overwrite:
                new_path = self._get_new_filename(destination_directory=new_path, filename=f[1])
            if self._remove_original_files:
                logging.info("Move {0} to {1}".format(original_file, new_path))
                shutil.move(original_file, new_path)
            else:
                logging.info("Copy {0} to {1}".format(original_file, new_path))
                shutil.copy2(original_file, new_path)
        logging.info("All files transferred")

    def _get_date_from_file(self, path_to_file, use_exif=True):
        """
        This function is getting date from file. Date comes from EXIF (if use_exif is True)
        or file modification date (if cannot read from EXIF or use_exif is False)
        :param path_to_file: Full path to file
        :type path_to_file: string
        :param use_exif: Determine if date should be taken from EXIF
        :type use_exif: bool
        :return: Date of file
        :rtype: datetime
        """
        if use_exif:
            f = open(path_to_file, 'rb')
            tags = exifread.process_file(f)
            exif_date = None
            if "EXIF DateTimeOriginal" in tags:
                exif_date = tags["EXIF DateTimeOriginal"]
            elif "Image DateTimeOriginal" in tags:
                exif_date = tags["Image DateTimeOriginal"]
            elif "Image DateTime" in tags:
                exif_date = tags["Image DateTime"]
            elif "EXIF DateTimeDigitized" in tags:
                exif_date = tags["EXIF DateTimeDigitized"]

            try:
                return datetime.strptime(str(exif_date), '%Y:%m:%d %H:%M:%S')
            except ValueError as e:
                 logging.warning("Unable to read date from EXIF or given date is not valid: %s "
                                 "\nLet's read file modification date." % e.message)
                 return self._get_date_from_file(path_to_file, False)

        else:
            modification_timestamp = os.path.getmtime(path_to_file)
            return datetime.fromtimestamp(modification_timestamp)

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
    options_parser.add_option("-x", "--exiff",
                              action="store_true",
                              dest="exif",
                              help="Get creation date from EXIF. If option is set try to get cration date from EXIF."
                                   "If option is not set (or cannot read creation date from EXIF) "
                                   "then get file modification date.",
                              default=False)
    (options, args) = options_parser.parse_args()

    if options.src_dir is None or options.dest_dir is None:
        options_parser.print_help()
        sys.exit(1)
    file_sorter = EasyFileSorter(source_dir=options.src_dir,
                                 destination_dir=options.dest_dir,
                                 remove_original_files=options.remove_original,
                                 overwrite=options.overwrite,
                                 use_exif=options.exif)
    file_sorter.scan_directory(recursive=options.recursive)
    file_sorter.transfer_files()

if __name__ == '__main__':
    main()
