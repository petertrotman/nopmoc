#!/usr/bin/env python

import argparse
import os
from pathlib import Path
from itertools import chain


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""
        Export all svgs for the symbols and footprints in the given directories
    """)

    parser.add_argument(
        'search_directories',
        nargs='+',
        help='list of directories in which to search for kicad libraries'
    )

    parser.add_argument(
        '-o',
        '--output',
        required=True,
        help='base directory for the output'
    )

    parser.add_argument(
        '-l',
        '--layers',
        default='*.Cu,*.Paste,*.SilkS',
        help='layers argument to pass to kicad-cli'
    )

    args = parser.parse_args()

    footprints_output_path = Path(args.output, 'footprints')
    footprints_output_path.mkdir(parents=True, exist_ok=True)
    symbols_output_path = Path(args.output, 'symbols')
    symbols_output_path.mkdir(parents=True, exist_ok=True)
    footprints_bw_output_path = Path(args.output, 'footprints_bw')
    footprints_bw_output_path.mkdir(parents=True, exist_ok=True)
    symbols_bw_output_path = Path(args.output, 'symbols_bw')
    symbols_bw_output_path.mkdir(parents=True, exist_ok=True)

    symbol_libraries_paths = list(chain.from_iterable(
        Path(p).glob('**/*.kicad_sym') for p in args.search_directories
    ))

    footprint_libraries_paths = list(chain.from_iterable(
        Path(p).glob('**/*.pretty') for p in args.search_directories
    ))

    for i, slp in enumerate(symbol_libraries_paths):
        library_name = slp.parts[-1].rsplit('.', 1)[0]

        print(
            f'[{i+1}/'
            f'{len(symbol_libraries_paths) + len(footprint_libraries_paths)}]',
            f'Processing {slp} ...'
        )

        command = (
            f'kicad-cli sym export svg '
            f'--layers \'{args.layers}\' '
            f'--output {Path(symbols_output_path, library_name)} '
            f'{slp}'
        )
        print(command)
        os.system(command)

        command = (
            f'kicad-cli fp export svg '
            f'--layers \'{args.layers}\' '
            f'--output {Path(symbols_bw_output_path, library_name)} '
            f'--black-and-white '
            f'{slp}'
        )
        print(command)
        os.system(command)

    for i, flp in enumerate(footprint_libraries_paths):
        library_name = flp.parts[-1].rsplit('.', 1)[0]

        print(
            f'[{i+1+len(symbol_libraries_paths)}/'
            f'{len(symbol_libraries_paths) + len(footprint_libraries_paths)}]',
            f'Processing {flp} ...'
        )

        command = (
            f'kicad-cli fp export svg '
            f'--layers \'{args.layers}\' '
            f'--output {Path(footprints_output_path, library_name)} '
            f'{flp}'
        )
        print(command)
        os.system(command)

        command = (
            f'kicad-cli fp export svg '
            f'--layers \'{args.layers}\' '
            f'--output {Path(footprints_bw_output_path, library_name)} '
            f'--black-and-white '
            f'{flp}'
        )
        print(command)
        os.system(command)
