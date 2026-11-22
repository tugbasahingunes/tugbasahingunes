/**
 * Google Sheets + Forms automation for a small business / training centre.
 * - onFormSubmit: new form answer -> status, ID, confirmation e-mail
 * - dailySummary: e-mails a summary every morning (time-driven trigger)
 * - onEdit: timestamps status changes
 * Install: Extensions > Apps Script, paste, run setup() once.
 */
const SHEET = "Başvurular";
const ADMIN = "admin@example.com"; // client's address

function setup() {
  ScriptApp.getProjectTriggers().forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger("onFormSubmit").forSpreadsheet(SpreadsheetApp.getActive()).onFormSubmit().create();
  ScriptApp.newTrigger("dailySummary").timeBased().everyDays(1).atHour(8).create();
}

function onFormSubmit(e) {
  const sh = e.range.getSheet();
  const row = e.range.getRow();
  const headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  const col = name => headers.indexOf(name) + 1;
  const id = "BSV-" + Utilities.formatDate(new Date(), "Europe/Istanbul", "yyMMdd") + "-" + row;
  sh.getRange(row, col("Başvuru No")).setValue(id);
  sh.getRange(row, col("Durum")).setValue("Yeni");
  const email = e.namedValues["E-posta"] && e.namedValues["E-posta"][0];
  const name = e.namedValues["Ad Soyad"] && e.namedValues["Ad Soyad"][0];
  if (email) {
    MailApp.sendEmail({
      to: email,
      subject: "Başvurunuz alındı (" + id + ")",
      htmlBody: `Merhaba ${name},<br><br>Başvurunuz bize ulaştı. Başvuru numaranız: <b>${id}</b>.<br>En geç 2 iş günü içinde dönüş yapacağız.`
    });
  }
}

function onEdit(e) {
  const sh = e.range.getSheet();
  if (sh.getName() !== SHEET) return;
  const headers = sh.getRange(1, 1, 1, sh.getLastColumn()).getValues()[0];
  if (e.range.getColumn() === headers.indexOf("Durum") + 1) {
    sh.getRange(e.range.getRow(), headers.indexOf("Son Güncelleme") + 1).setValue(new Date());
  }
}

function dailySummary() {
  const data = SpreadsheetApp.getActive().getSheetByName(SHEET).getDataRange().getValues();
  const h = data.shift(); const s = h.indexOf("Durum");
  const counts = data.reduce((a, r) => (a[r[s]] = (a[r[s]] || 0) + 1, a), {});
  const body = Object.entries(counts).map(([k, v]) => `${k}: ${v}`).join("\n");
  MailApp.sendEmail(ADMIN, "Günlük başvuru özeti", `Toplam ${data.length} başvuru\n\n${body}`);
}
