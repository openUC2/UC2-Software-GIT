import sys
from typing import Optional
from vimba import *


def print_preamble():
    print('///////////////////////////////////////')
    print('/// Vimba API List Features Example ///')
    print('///////////////////////////////////////\n')


def print_usage():
    print('Usage:')
    print('    python list_features.py [camera_id]')
    print('    python list_features.py [/h] [-h]')
    print()
    print('Parameters:')
    print('    camera_id   ID of the camera to use (using first camera if not specified)')
    print()


def abort(reason: str, return_code: int = 1, usage: bool = False):
    print(reason + '\n')

    if usage:
        print_usage()

    sys.exit(return_code)


def parse_args() -> Optional[str]:
    args = sys.argv[1:]
    argc = len(args)

    for arg in args:
        if arg in ('/h', '-h'):
            print_usage()
            sys.exit(0)

    if argc > 1:
        abort(reason="Invalid number of arguments. Abort.", return_code=2, usage=True)

    return None if argc == 0 else args[0]


def print_feature(feature):
    try:
        value = feature.get()

    except (AttributeError, VimbaFeatureError):
        value = None

    print('/// Feature name   : {}'.format(feature.get_name()))
    print('/// Display name   : {}'.format(feature.get_display_name()))
    print('/// Tooltip        : {}'.format(feature.get_tooltip()))
    print('/// Description    : {}'.format(feature.get_description()))
    print('/// SFNC Namespace : {}'.format(feature.get_sfnc_namespace()))
    print('/// Unit           : {}'.format(feature.get_unit()))
    print('/// Value          : {}\n'.format(str(value)))


def get_camera(camera_id: Optional[str]) -> Camera:
    with Vimba.get_instance() as vimba:
        if camera_id:
            try:
                return vimba.get_camera_by_id(camera_id)

            except VimbaCameraError:
                abort('Failed to access Camera \'{}\'. Abort.'.format(camera_id))

        else:
            cams = vimba.get_all_cameras()
            if not cams:
                abort('No Cameras accessible. Abort.')

            return cams[0]


def main():
    print_preamble()
    cam_id = parse_args()

    with Vimba.get_instance():
        with get_camera(cam_id) as cam:

            print('Print all features of camera \'{}\':'.format(cam.get_id()))
            for feature in cam.get_all_features():
                print_feature(feature)


if __name__ == '__main__':
    main()