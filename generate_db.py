#!/usr/bin/env python

from collections.abc import Iterable
from itertools import chain
from kiutils.symbol import SymbolLib, Symbol, SymbolPin
from kiutils.footprint import Footprint
from pathlib import Path
import argparse
import os
import sqlite3

__location__ = os.path.realpath(
    os.path.join(
        os.getcwd(),
        os.path.dirname(__file__)
    )
)


def init_db(db: sqlite3.Connection) -> None:
    """Initialise the database at the given location with the schema"""

    db.executescript("""
        CREATE TABLE IF NOT EXISTS
        symbols(
            name TEXT,
            library TEXT
        );
        CREATE TABLE IF NOT EXISTS
        symbol_properties(
            symbol_rowid references symbols(rowid),
            key TEXT,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS
        symbol_pins(
            symbol_rowid REFERENCES symbols(rowid),
            number TEXT,
            name TEXT,
            electrical_type TEXT,
            is_alternate BOOL DEFAULT false
        );
        CREATE TABLE IF NOT EXISTS
        footprints(
            name TEXT,
            library TEXT,
            description TEXT,
            tags TEXT,
            pads INTEGER
        );
        CREATE TABLE IF NOT EXISTS
        footprint_properties(
            footprint_rowid REFERENCES footprints(rowid),
            key TEXT,
            value TEXT
        );
    """)


def insert_library(lib: SymbolLib, db: sqlite3.Connection) -> int:
    """Iterate through all the symbols in the given symbol library
    and add them to the database supplied by the connection.
    Returns the number of symbols processed."""

    library_name = Path(lib.filePath).parts[-1].rsplit('.', 1)[0]

    for symbol in lib.symbols:
        insert_symbol(symbol, library_name, db)

    return len(lib.symbols)


def insert_symbol(
        symbol: Symbol,
        library_name: str,
        db: sqlite3.Connection):
    """Add the symbol to the db with the given connection
    including all the associated properties and pins"""

    cur = db.cursor()

    # Insert symbol
    cur.execute(
        """INSERT INTO symbols(name, library) VALUES (?, ?);""",
        (symbol.entryName, library_name)
    )
    symbol_rowid = cur.lastrowid

    # Insert symbol properties
    cur.executemany(
        """
        INSERT INTO symbol_properties(symbol_rowid, key, value)
        VALUES (?, ?, ?);
        """,
        ((symbol_rowid, p.key, p.value) for p in symbol.properties)
    )

    # Insert pins
    cur.executemany(
        """
        INSERT INTO symbol_pins(
            symbol_rowid,
            number,
            name,
            electrical_type,
            is_alternate
        )
        VALUES (?, ?, ?, ?, false);
        """,
        (
            (symbol_rowid, p.number, p.name, p.electricalType)
            for p in symbol_pins(symbol)
        )
    )

    # Insert alternate pins
    cur.executemany(
        """
        INSERT INTO symbol_pins(
            symbol_rowid,
            number,
            name,
            electrical_type,
            is_alternate
        )
        VALUES (?, ?, ?, ?, true);
        """,
        chain.from_iterable(
            (
                (symbol_rowid, p.number, a.pinName, a.electricalType)
                for a in p.alternatePins
            ) for p in symbol_pins(symbol)
        )
    )


def symbol_pins(symbol: Symbol) -> Iterable[SymbolPin]:
    """Recurse through the symbol and all symbol units
    to get all of the pins associated with the symbol"""

    return chain(
        symbol.pins,
        chain.from_iterable(symbol_pins(u) for u in symbol.units)
    )


def insert_footprint(
        footprint: Footprint,
        library_name: str,
        db: sqlite3.Connection):
    """Insert the footprint into the database."""

    cur = db.cursor()

    cur.execute("""
        INSERT INTO footprints(name, library, description, tags, pads)
        VALUES (?, ?, ?, ?, ?);
    """, (
        footprint.entryName,
        library_name,
        footprint.description,
        footprint.tags,
        len(list(
            p for p in footprint.pads
            if isinstance(p.number, int) or len(p.number) > 0
        ))
    ))

    footprint_rowid = cur.lastrowid

    cur.executemany("""
        INSERT INTO footprint_properties(footprint_rowid, key, value)
        VALUES (?, ?, ?);
    """, ((footprint_rowid, p.key, p.value) for p in footprint.properties))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="""
        Generate the sqlite database containing data
        from the supplied kicad symbols libraries
    """)

    parser.add_argument(
        'sqlite_db',
        help='file path to the sqlite database to be created'
    )
    parser.add_argument(
        'search_directories',
        nargs='+',
        help='list of directories in which to search '
             'for kicad symbols libraries'
    )

    args = parser.parse_args()
    symbol_library_paths = list(chain.from_iterable(
        Path(p).glob('**/*.kicad_sym') for p in args.search_directories
    ))
    footprint_library_paths = list(chain.from_iterable(
        Path(p).glob('**/*.pretty') for p in args.search_directories
    ))

    with sqlite3.connect(args.sqlite_db) as db:
        print(f'Initialising database {args.sqlite_db}...', end=' ')
        init_db(db)
        print('success', end='\n\n')

        for i, slp in enumerate(symbol_library_paths):
            print(
                f'[{i+1}/'
                f'{len(symbol_library_paths) + len(footprint_library_paths)}]',
                f'Processing symbols from {slp}...',
                end=' '
            )
            lib = SymbolLib.from_file(slp)
            symbols_added = insert_library(lib, db)

            print(f'complete: {symbols_added} symbols added')

        for i, flp in enumerate(footprint_library_paths):
            print(
                f'[{i+1 + len(symbol_library_paths)}/'
                f'{len(symbol_library_paths) + len(footprint_library_paths)}]',
                f'Processing footprints from {flp}...',
                end=' '
            )
            library_name = flp.parts[-1].rsplit('.', 1)[0]
            footprint_paths = list(flp.glob('**/*.kicad_mod'))
            for fp in footprint_paths:
                insert_footprint(Footprint.from_file(fp), library_name, db)

            print(f'complete: {len(footprint_paths)} footprints added')
