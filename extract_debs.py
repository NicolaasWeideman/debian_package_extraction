import argparse
import os
import glob
import ntpath
import subprocess
import stat
import time
import datetime

ELF_HEADER = b"\x7fELF"
TIME_FORMAT = "%H:%M:%S, %9A, %d-%m-%Y"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root', help='the root directory from where to search for all the .deb files')
    parser.add_argument('dest', help='the destination directory to which the debs will be extracted')
    parser.add_argument('--del_nonelfs', default=True, help='Delete all non-elf files after extracting a .deb')
    args = parser.parse_args()
    root_dir = args.root
    dest_dir_root = args.dest
    del_nonelfs = args.del_nonelfs
    print("Extracting all debs from {} to {}".format(root_dir, dest_dir_root))
    print("Deleting non-elf files: {}".format(del_nonelfs))
    break_counter = 0
    break_limit = -1

    global_start_time = time.localtime()
    print("Extraction started on: {}".format(time.strftime(TIME_FORMAT, global_start_time)))
    full_deb_file_names = set()
    # Recursively searching from the root directory
    print("Searching for .deb files:")
    for r, d, f in os.walk(root_dir):
        # Searching the directory for all .deb files
        for full_deb_file_name in glob.glob(os.path.join(r, '*.deb')):
            full_deb_file_names.add(full_deb_file_name)
            print("deb files found: {}".format(len(full_deb_file_names)), end = '\r', flush=True)
            break_counter += 1
            if break_limit >= 0 and break_counter >= break_limit:
                break
        if break_limit >= 0 and break_counter >= break_limit:
            break
    print("")
    total = len(full_deb_file_names)
    for i, full_deb_file_name in enumerate(full_deb_file_names):
            deb_file_name = ntpath.basename(full_deb_file_name)
            dest_dir = os.path.join(dest_dir_root, deb_file_name)
            os.mkdir(dest_dir)
            print("\r{}".format(' ' * os.get_terminal_size()[0]), end='\r', flush=True)
            print("({} / {}) Extracting {}".format(i + 1, total, full_deb_file_name), end='', flush=True)
            extract_deb(full_deb_file_name, deb_file_name, dest_dir)
            if del_nonelfs:
                print("\r{}".format(' ' * os.get_terminal_size()[0]), end='\r', flush=True)
                print("({} / {}) Deleting non-elfs {}".format(i + 1, total, dest_dir), end='', flush=True)
                delete_non_elfs(dest_dir)
    print("")
    global_end_time = time.localtime()
    print("Finished on: {}".format(time.strftime(TIME_FORMAT, global_end_time)))
    global_run_time = format_time_delta(global_start_time, global_end_time)
    print("Total time: {}".format(global_run_time))


def extract_deb(deb_file_path, deb_file_name, dest_dir):

    # TODO dpkg assumes the user has this installed. Maybe it would be better to extract manually? Wikipedia tells how this file should be structured: https://en.wikipedia.org/wiki/Deb_(file_format)
    p = subprocess.Popen(['dpkg', '-x', deb_file_path, dest_dir], cwd=dest_dir)
    p.wait()
    # Giving myself read and write permissions to all files and read/write/traverse permissions to directories (because apparently that's necessary)
    for root, dirs, files in os.walk(dest_dir):
        for d in dirs:
            full_dir_path = os.path.join(root, d)
            if not os.path.islink(full_dir_path):
                os.chmod(os.path.join(root, d), stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
        for f in files:
            full_file_path = os.path.join(root, f)
            if not os.path.islink(full_file_path):
                os.chmod(os.path.join(root, f), stat.S_IREAD | stat.S_IWRITE)

def delete_non_elfs(root_dir):
     for r, d, f in os.walk(root_dir):
        for file_name in f:
            full_file_name = os.path.join(r, file_name)
            # We don't want to delete something that may be somewhere else.
            if not os.path.islink(full_file_name) and not is_elf_file(full_file_name):
                os.remove(full_file_name)


def is_elf_file(full_file_name):
    with open(full_file_name, 'rb') as fd:
        header = fd.read(4)
        if header == ELF_HEADER:
            return True
    return False

def format_time_delta(start_time, end_time, short=False):
        start_time_datetime = datetime.datetime.fromtimestamp(time.mktime(start_time))
        end_time_datetime = datetime.datetime.fromtimestamp(time.mktime(end_time))
        time_delta_datetime = end_time_datetime - start_time_datetime
        seconds = int(time_delta_datetime.seconds)
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)
        if short:
                return "{0}:{1:02d}:{2:02d}:{3:02d}".format(days, hours, minutes, seconds)
        else:
                return "{0} days, {1} hours, {2:02d} minutes and {3:02d} seconds.".format(days, hours, minutes, seconds)

if __name__ == "__main__":
    main()
