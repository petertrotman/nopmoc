/* eslint-disable @typescript-eslint/no-explicit-any */

import { sqlite3Worker1Promiser } from '@sqlite.org/sqlite-wasm';
import type { ExecOptions, Sqlite3Worker1Promiser, PromiserClose, PromiserOpen,  PromiserExport, PromiserConfigGet, PromiserExec} from '@sqlite.org/sqlite-wasm';
declare module '@sqlite.org/sqlite-wasm' {
	type Sqlite3Worker1PromiserConfig = {
		onready: () => void;
		worker: any;
		generateMessageId: (messageObject: object) => string;
		debug: (message: object) => void;
		onunhandled: (event: object) => void;
	};

	// for reference - need to cast the promiser `as any` in use.
	// See: https://github.com/microsoft/TypeScript/issues/14107
	type PromiserCloseResult = { type: 'close', result: { filename: string | undefined } };
	function PromiserClose(type: 'close', args: { unlink?: boolean }): Promise<PromiserCloseResult>;

	type PromiserConfigGetResult = { type: 'config-get', result: { version: string; bigIntEnabled: boolean; vfsList: any } };
	function PromiserConfigGet(type: 'config-get', args?: object): Promise<PromiserConfigGetResult>;

	type PromiserExecResult = { type: 'exec'; result: ExecOptions };
	function PromiserExec(type: 'exec', args: string | ExecOptions): Promise<PromiserExecResult>;

	type PromiserExportResult = { type: 'export'; result: { byteArray: Uint8Array; filename: string; mimetype: string } };
	function PromiserExport(type: 'export', args?: object): Promise<PromiserExportResult>;

	type PromiserOpenResult = { type: 'open', result: { filename: string; dbId: string; persistent: boolean; vfs: string } };
	function PromiserOpen(type: 'open', args: { filename: string; vfs?: string }): Promise<PromiserOpenResult>;

	type Sqlite3Worker1Promiser =
		| typeof PromiserClose
		| typeof PromiserConfigGet
		| typeof PromiserExec
		| typeof PromiserExport
		| typeof PromiserOpen;

	export function sqlite3Worker1Promiser(): Sqlite3Worker1Promiser;
	export function sqlite3Worker1Promiser(onready: () => void): Sqlite3Worker1Promiser;
	export function sqlite3Worker1Promiser(config: Sqlite3Worker1PromiserConfig): Sqlite3Worker1Promiser;
}

class Db {
	promiser: Promise<Sqlite3Worker1Promiser>;

	constructor() {
		this.promiser = new Promise((resolve) => {
			const _promiser: Sqlite3Worker1Promiser =
				sqlite3Worker1Promiser(() => resolve(_promiser));
		});
	}

	async open(filename: string, vfs?: string) {
		const promiser = await this.promiser as typeof PromiserOpen;
		return promiser('open', { filename, vfs });
		// filename: 'file:mydb.sqlite3?vfs=opfs'
	}

	async close(closeArg?: { unlink: boolean }) {
		const promiser = await this.promiser as typeof PromiserClose;
		return promiser('close', closeArg || {});
	}

	async configGet() {
		const promiser = await this.promiser as typeof PromiserConfigGet;
		return promiser('config-get', {});
	}

	async export() {
		const promiser = await this.promiser as typeof PromiserExport;
		return promiser('export', {});
	}

	async exec(execArg: string | ExecOptions) {
		const promiser = await this.promiser as typeof PromiserExec;
		return promiser('exec', execArg);
	}
};

const db = new Db();
export default db;
