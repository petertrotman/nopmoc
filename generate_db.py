#!/usr/bin/env python

from collections.abc import Iterable
from itertools import chain
from kiutils.symbol import SymbolLib, Symbol, SymbolPin
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
    """Initialise the database at the given location with
    the schema defined in schema.sql"""
    with open(Path(__location__, 'schema.sql')) as f:
        sql_script = f.read()
        db.executescript(sql_script)


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
        db: sqlite3.Connection
) -> None:
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
        INSERT INTO properties(symbol_rowid, key, value)
        VALUES (?, ?, ?);
        """,
        ((symbol_rowid, p.key, p.value) for p in symbol.properties)
    )

    # Insert pins
    cur.executemany(
        """
        INSERT INTO pins(
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
        INSERT INTO pins(
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
    symbols_added = 0
    lib_paths = list(chain.from_iterable(
        Path(p).glob('**/*.kicad_sym') for p in args.search_directories
    ))

    with sqlite3.connect(args.sqlite_db) as db:
        print(f'Initialising database {args.sqlite_db}...', end=' ')
        init_db(db)
        print('success', end='\n\n')

        for i, library_path in enumerate(lib_paths):
            print(
                f'[{i+1}/{len(lib_paths)}]',
                f'Processing library {library_path}...',
                end=' '
            )
            lib = SymbolLib.from_file(library_path)
            _symbols_added = insert_library(lib, db)

            print(f'success, {_symbols_added} symbols added')
            symbols_added += _symbols_added

    print(
        "\nSuccess.",
        f"Inserted {len(lib_paths)} libraries",
        f"containing {symbols_added} symbols"
    )
