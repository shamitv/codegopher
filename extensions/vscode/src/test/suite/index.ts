import * as fs from "node:fs/promises";
import * as path from "node:path";

import Mocha from "mocha";
import * as vscode from "vscode";

async function collectTests(directory: string): Promise<string[]> {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  const files = await Promise.all(
    entries.map(async (entry) => {
      const resolved = path.resolve(directory, entry.name);
      if (entry.isDirectory()) {
        return collectTests(resolved);
      }
      if (entry.isFile() && entry.name.endsWith(".test.js")) {
        return [resolved];
      }
      return [];
    })
  );

  return files.flat();
}

export async function run(): Promise<void> {
  const mocha = new Mocha({
    color: true,
    ui: "tdd"
  });

  const testsRoot = path.resolve(__dirname);
  const testFiles = await collectTests(testsRoot);

  for (const file of testFiles) {
    mocha.addFile(file);
  }

  try {
    await new Promise<void>((resolve, reject) => {
      mocha.run((failures) => {
        if (failures > 0) {
          reject(new Error(`${failures} test(s) failed.`));
          return;
        }
        resolve();
      });
    });
  } finally {
    await vscode.commands.executeCommand("workbench.action.closeWindow");
  }
}
