import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root = path.dirname(fileURLToPath(import.meta.url));
const reviewedIndex = process.argv.indexOf('--reviewed');
const independent = reviewedIndex >= 0;
const aiMode = independent || process.argv.includes('--ai-review');
const out = path.join(root, independent ? 'outputs/relay-reviewed-01a15bec' : aiMode ? 'outputs/relay-ai-review-01a15bec' : 'outputs/relay-review-20261021');
const rows = (await fs.readFile(path.join(root, 'data/review_reports.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse);
const ai = aiMode ? JSON.parse(await fs.readFile(independent ? path.resolve(process.argv[reviewedIndex+1]) : path.join(root, 'evidence/ai-review-20261021.json'), 'utf8')) : null;
const byId = new Map(ai ? ai.judgments.map(r => [r.id, r]) : []);
if (aiMode) {
  const sourceHash = createHash('sha256').update(await fs.readFile(path.join(root, 'data/review_reports.jsonl'))).digest('hex');
  if (ai.independent_human_review !== false || ai.reports_sha256 !== sourceHash || byId.size !== 60 || ai.judgments.length !== 60 || rows.some(r => !byId.has(r.id))) throw new Error('Invalid AI annotation provenance or report coverage.');
}
const wb = Workbook.create();
const reviewName = 'Review';
const guideName = aiMode ? 'Provenance' : 'Guide';
const review = wb.worksheets.add(reviewName);
const guide = wb.worksheets.add(guideName);
for (const sheet of [review, guide]) {
  sheet.showGridLines = false;
  sheet.getRange(sheet === review ? 'A1:F67' : aiMode ? 'A1:C29' : 'A1:C25').format.font = {name:'Arial',size:11,color:'#242821'};
}
review.tabColor = '#30392C';
review.getRange('A2').values = [[aiMode ? 'Report review' : 'Incident label review']];
review.getRange('A2').format.font = {size:16,bold:true};
review.getRange('B3').values = [[aiMode ? '21 October 2026' : '60 synthetic reports. Use Guide. Choose labels without consulting AI or predictions.']];
review.getRange('B4').values = [[aiMode ? '' : 'Complete the four amber columns. Add a brief reason, especially for unclear cases.']];
review.getRange('A6:F6').values = [["Report ID","Original report",'Category','Urgency','Needs clarification','Reason / missing facts']];
const categoryLabels = {delay:'Delivery delay',missing:'Missing shipment',damage:'Cargo damage',temperature:'Temperature issue',safety:'Safety & security',documentation:'Documents & customs',unclear:'Unclear'};
review.getRange('A7:F66').values = rows.map(r=>{
  const a = byId.get(r.id);
  return a ? [r.id,r.text,categoryLabels[a.category],a.urgency[0].toUpperCase()+a.urgency.slice(1),a.clarification ? 'Yes' : 'No',a.reason] : [r.id,r.text,null,null,null,null];
});
review.getRange('A6:F6').format = {fill:'#30392C',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'},rowHeight:30,wrapText:true,horizontalAlignment:'center'};
review.getRange('A7:F66').format = {rowHeight:aiMode ? 64 : 112,verticalAlignment:'top',wrapText:true};
review.getRange('C7:F66').format.fill = aiMode ? '#F4F3F8' : '#FFF5DB';
if (aiMode) {
  review.getRange('C7:D66').conditionalFormats.add('containsText',{text:'Unclear',format:{fill:'#FFF0D0',font:{color:'#754B17',bold:true}}});
  review.getRange('D7:D66').conditionalFormats.add('containsText',{text:'Urgent',format:{fill:'#FBEBDD',font:{color:'#804A21'}}});
  review.getRange('E7:E66').conditionalFormats.add('containsText',{text:'Yes',format:{fill:'#FFF0D0',font:{color:'#754B17'}}});
  const table = review.tables.add('A6:F66',true,'ReviewedReports');
  table.style = 'TableStyleLight1';
  table.showFilterButton = true;
}
const widths = aiMode ? [16,68,25,16,22,56] : [16,94,25,16,22,44];
widths.forEach((w,i)=>review.getRange(`${String.fromCharCode(65+i)}1:${String.fromCharCode(65+i)}66`).format.columnWidth=w);
if (aiMode) {
  [112,460,180,110,150,420].forEach((w,i)=>review.getRange(`${String.fromCharCode(65+i)}1:${String.fromCharCode(65+i)}66`).format.columnWidthPx=w);
  review.getRange('A7:B66').format.fill = '#FFFFFF';
  review.getRange('A7:F66').format.borders = {insideHorizontal:{style:'thin',color:'#E5E4EA'}};
}
review.getRange('A7:A66').format.font = {name:'Arial',size:10,color:'#60665C'};
review.freezePanes.freezeRows(6);
review.freezePanes.freezeColumns(1);
const categories = ['Delivery delay','Missing shipment','Cargo damage','Temperature issue','Safety & security','Documents & customs','Unclear'];
review.getRange('C7:C66').dataValidation = {rule:{type:'list',values:categories}};
review.getRange('D7:D66').dataValidation = {rule:{type:'list',values:['Urgent','Routine','Unclear']}};
review.getRange('E7:E66').dataValidation = {rule:{type:'list',values:['Yes','No']}};
review.getRange('G1:G66').format.columnWidth = 3;

guide.getRange('A2').values = [[aiMode ? 'Review provenance' : 'Independent review guide']];
guide.getRange('A2').format.font = {size:16,bold:true};
guide.getRange('A4:B5').values = [['Reviewer name',aiMode ? ai.reviewer : null],['Review date',aiMode ? new Date('2026-10-21T00:00:00Z') : null]];
if (aiMode) guide.getRange('A6:B6').values = [['Reviewer type','agent']];
if (aiMode) guide.getRange('B5').setNumberFormat('yyyy-mm-dd');
guide.getRange('B4:B5').format.fill = aiMode ? '#F4F3F8' : '#FFF5DB';
const guideRows = independent ? [
 ['Review source','A separate Codex agent reviewed all 60 reports in a fresh context at the user\'s request.'],
 ['Method',ai.method],
 ['Isolation','The reviewer received only the original report text and written label guide. Parent history, previous labels, classifiers and predictions were excluded.'],
 ['Uncertainty','Unclear values and written reasons are preserved exactly as returned. No judgments were changed to improve classifier scores.'],
 ['Reviewer identity','This is an independent agent review, not human or logistics-operator validation. AI tools and collaboration are acknowledged in the project attribution.'],
 ['Urgent','An ongoing physical/security hazard, uncontrolled temperature exposure, or a critical safety-system consequence requires immediate attention.'],
 ['Clarification','Material facts are missing or conflicting, or multiple issues need separate handling. Urgent does not automatically mean clarification.'],
 ['Guide ambiguity','The reviewer documented ambiguous safety-system routing, historical records and uncertain urgency. These limits remain in the evidence.'],
 ['Source','Original synthetic logistics reports, authored with Codex. Original report text and order are retained.'],
 ['Source checksum',ai.reports_sha256],
 ['Freeze','The original agent output, input hashes, label file and model/evaluator hashes are preserved before scoring.'],
 ['Evaluation','The held-out test uses these frozen judgments. Classifiers were not tuned on them.'],
 ['Original workbook','The initial blank review workbook and existing human review records are unchanged.'],
 ['Source record','The original reviewer JSON and full provenance are included in the repository evaluation evidence.'],
] : aiMode ? [
 ['Review source','AI second-pass judgments from OpenAI Codex. The same assistant helped author the synthetic reports.'],
 ['Independence','This is not independent human review. No human name or completed human judgment is fabricated.'],
 ['Method','Each report was read against the written category and urgency guide. Original draft labels and classifier predictions were not consulted during this pass.'],
 ['Uncertainty','Unclear values are retained when the report cannot support a category or urgency judgment. Each report has a written reason.'],
 ['Urgent','Ongoing physical/security hazard, uncontrolled temperature exposure, or a shipment blocking restoration of a critical safety system.'],
 ['Routine','No immediate threat is described. Customer emphasis alone is insufficient. Closed incidents and controlled records are routine.'],
 ['Clarification','Yes when material facts conflict or are missing, or multiple issues need separate handling. Urgency alone does not imply clarification.'],
 ['Delay or missing','A located shipment that is late or stuck en route is a delay. Cargo or contents that cannot be located are missing.'],
 ['Historical records','Resolved safety records remain with the safety team. Cold-chain records remain with quality. Record requests alone are not urgent.'],
 ['Multiple issues','An active physical hazard takes priority over cargo damage. Explain ambiguity or additional handling in the reason.'],
 ['Report source','Original fictional logistics reports authored with Codex on 21 October 2026. Original report text and order are retained.'],
 ['Original workbook','The original blind review sheet is unchanged. This copy uses a different sheet name and AI-prefixed columns.'],
 ['Evaluation status','These AI annotations do not populate human review, freeze human labels, alter the models, or produce independent final test scores.'],
 ['Independent check','The assessment asks for independent label review and allows AI assistance. This second pass alone does not demonstrate a separate reviewer check.'],
] : [
 ['Review method','Read the report and assign labels from the definitions below. Generated labels and model predictions are deliberately absent.'],
 ['Delivery delay','Located, intact shipment with a late arrival or handover. Team: Transport operations.'],
 ['Missing shipment','Cargo or contents cannot be found, are short, or reached an unconfirmed place. Team: Shipment tracing.'],
 ['Cargo damage','Physical damage is the primary issue; no continuing hazard. Team: Claims & recovery.'],
 ['Temperature issue','Cold-chain performance, excursion evidence or temperature records. Team: Cold-chain quality.'],
 ['Safety & security','Injury, unsafe conditions, hazardous substances, fire, theft, threats or security. Team: Safety & security.'],
 ['Documents & customs','Invoice, permit, declaration, clearance or proof of delivery. Team: Trade compliance.'],
 ['Unclear category','There is not enough information to choose a primary category. Do not guess.'],
 ['Urgent','Immediate attention: an ongoing physical/security hazard, uncontained temperature excursion, or a shipment blocking restoration of a critical safety system.'],
 ['Routine','No immediate threat is described. A loud subject line or inconvenience alone is not urgent.'],
 ['Unclear urgency','Material facts needed to judge urgency are missing. Missing information is not proof of safety.'],
 ['Needs clarification: Yes','Facts are missing, accounts conflict, or multiple issues need separate handling. Urgency alone does not imply missing information.'],
 ['Multiple issues','Choose the greatest immediate consequence. Active safety hazard comes first, then temperature exposure, then the main operational cause. Mark Yes when separate handling or facts are needed.'],
 ['Save and return','Complete all 60 rows, put your name/date above, save this workbook and return it. Leave unknown labels as Unclear and explain the missing information.'],
 ['Data provenance','Original fictional reports authored with OpenAI Codex on 21 October 2026. No real logistics operator records. Shuffled IDs do not encode the expected category.'],
 ['Keep review independent','Use the written guide and your judgment. Do not ask an AI to label these reports or inspect draft labels. Corrections will be preserved when the reviewed test set is frozen.'],
];
guide.getRange(`A7:B${6+guideRows.length}`).values = guideRows;
guide.getRange(`A7:B${6+guideRows.length}`).format = {wrapText:true,verticalAlignment:'top',rowHeight:aiMode ? 40 : 64};
if (aiMode) guideRows.forEach((row,index)=>{
  guide.getRange(`A${index+7}:B${index+7}`).format.rowHeight = Math.max(40,Math.ceil(String(row[1]).length/110)*14+12);
});
guide.getRange('A1:A22').format.columnWidth = 28;
guide.getRange('B1:B22').format.columnWidth = 105;
guide.getRange('A7:A22').format.font = {name:'Arial',size:11,bold:true};
guide.getRange('A7:B7').format.borders = {bottom:{style:'thin',color:'#B4B9AF'}};
if (aiMode) {
  guide.getRange('A23:B23').values = [['Review counts','Reports']];
  guide.getRange('A23:B23').format = {fill:'#30392C',font:{name:'Arial',size:11,bold:true,color:'#FFFFFF'}};
  guide.getRange('A24:A29').values = [['Reviewed'],['Urgent'],['Routine'],['Unclear urgency'],['Needs clarification'],['Unclear category']];
  guide.getRange('B24:B29').formulas = [["=COUNTA('Review'!A7:A66)"],["=COUNTIFS('Review'!D7:D66,\"Urgent\")"],["=COUNTIFS('Review'!D7:D66,\"Routine\")"],["=COUNTIFS('Review'!D7:D66,\"Unclear\")"],["=COUNTIFS('Review'!E7:E66,\"Yes\")"],["=COUNTIFS('Review'!C7:C66,\"Unclear\")"]];
  guide.getRange('A23:B29').format.rowHeight = 25;
  guide.getRange('B24:B29').setNumberFormat('0');
}
wb.recalculate();
await fs.mkdir(out,{recursive:true});
console.log((await wb.inspect({kind:'table',range:`'${reviewName}'!A6:F8`,include:'values',tableMaxRows:3,tableMaxCols:6,maxChars:2300})).ndjson);
if (aiMode) {
  const expected = [60,ai.judgments.filter(a=>a.urgency==='urgent').length,ai.judgments.filter(a=>a.urgency==='routine').length,ai.judgments.filter(a=>a.urgency==='unclear').length,ai.judgments.filter(a=>a.clarification).length,ai.judgments.filter(a=>a.category==='unclear').length];
  const actual = guide.getRange('B24:B29').values.map(row=>row[0]);
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw new Error(`Count mismatch: ${actual} / ${expected}`);
  const prior = review.getRange('D7').values[0][0];
  review.getRange('D7').values = [['Unclear']];
  wb.recalculate();
  if (guide.getRange('B27').values[0][0] !== expected[3] + (prior === 'Unclear' ? 0 : 1)) throw new Error('Summary did not recalculate after an urgency edit.');
  review.getRange('D7').values = [[prior]];
  wb.recalculate();
  if (JSON.stringify(guide.getRange('B24:B29').values.map(row=>row[0])) !== JSON.stringify(expected)) throw new Error('Summary was not restored after verification.');
  console.log((await wb.inspect({kind:'table',range:'Provenance!A23:B29',include:'values,formulas',tableMaxRows:7,tableMaxCols:2,maxChars:1800})).ndjson);
}
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:10},summary:'Formula error scan'})).ndjson);
for(const [sheetName,range,file] of [[reviewName,'A1:F9','review-preview.png'],[guideName,'A1:B15','guide-preview.png'],...(aiMode ? [[reviewName,'A21:F25','uncertainty-preview.png'],[guideName,'A23:B29','counts-preview.png']] : [])]) {
 const preview=await wb.render({sheetName,range,scale:1.25,format:'png'});
 await fs.writeFile(path.join(out,file),new Uint8Array(await preview.arrayBuffer()));
}
const filename = 'review_60_reports.xlsx';
await (await SpreadsheetFile.exportXlsx(wb)).save(path.join(out,filename));
if (independent) {
  const publicDirectory = path.join(root,'output/review');
  await fs.mkdir(publicDirectory,{recursive:true});
  await fs.copyFile(path.join(out,filename),path.join(publicDirectory,filename));
}
console.log(JSON.stringify({reports:rows.length,label_source:independent ? 'independent agent review' : aiMode ? 'AI-assisted review' : 'blank human review template',workbook:path.join(out,filename)}));
