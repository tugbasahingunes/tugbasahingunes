# 15 · Google Sheets & Forms Automation (Apps Script) / Virtual Assistant Workflows

**Client problem:** "People apply through a Google Form. Someone copies them, e-mails each person, and sends the boss a summary. Every day, by hand."

[`Code.gs`](Code.gs) automates it end-to-end:
- **New form answer** → unique application number, status "Yeni", personalised confirmation e-mail
- **Status edited** → "Son Güncelleme" timestamp filled automatically
- **Every morning 08:00** → summary e-mail to the manager (counts per status)
- One-click `setup()` installs all triggers

Required sheet columns: `Ad Soyad · E-posta · Başvuru No · Durum · Son Güncelleme`

Also offered: CRM-style trackers in Sheets, inbox/calendar organisation, appointment booking flows, Zapier/Make integrations, Notion workspaces, data entry and admin support as a virtual assistant.
