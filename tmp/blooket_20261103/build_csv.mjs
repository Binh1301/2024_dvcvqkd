import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook } from '@oai/artifact-tool';

const root = path.dirname(fileURLToPath(import.meta.url));
const questions = JSON.parse(await fs.readFile(path.join(root, 'questions.json'), 'utf8'));
const headers = JSON.parse(await fs.readFile(path.join(root, 'headers.json'), 'utf8'));
const rows = questions.map((q, i) => {
  let question = `${q.label}: ${q.jp}\n${q.vi}`;
  if (i === 36) {
    question += '\nLuồng mail: ① Client → Mail server (gửi); ② Mail server → Client (nhận); ③ Mail server → Mail server (chuyển tiếp).';
  }
  return [i + 1, question, ...q.answers.map(a => a.jp), 60, 'ABCD'.indexOf(q.correct) + 1];
});

const workbook = Workbook.create();
const sheet = workbook.worksheets.add('Blooket');
sheet.getRange('A1:H63').values = [headers, ...rows];
workbook.recalculate();
const authored = sheet.getRange('A1:H63').values;
if (JSON.stringify(authored) !== JSON.stringify([headers, ...rows])) {
  throw new Error('Workbook values changed during authoring');
}
const check = await workbook.inspect({kind: 'table', range: 'Blooket!A61:H63', tableMaxRows: 3, tableMaxCols: 8, maxChars: 1200});
console.log(check.ndjson);

// CSV has no cell formatting. Quote every field and preserve the template's headers.
const csv = '\ufeff' + authored.map(row => row.map(value => '"' + String(value ?? '').replaceAll('"', '""') + '"').join(',')).join('\r\n') + '\r\n';
const outputDir = path.resolve(root, '../../outputs/blooket_20261103');
await fs.mkdir(outputDir, {recursive: true});
const destination = path.join(outputDir, 'Blooket_On_Nhat_Chuyen_Nganh_1_62_cau.csv');
await fs.writeFile(destination, csv, 'utf8');
console.log(JSON.stringify({output: destination, questions: rows.length, answers: rows.length * 4, encoding: 'UTF-8 with BOM'}));
