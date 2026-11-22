# 07 · Mobile App Development (React Native / Expo)

**Client problem:** "I need a simple Android + iOS app for my small business / idea. Not a 6-month project."

**This example: Bütçe Takip:** a personal budget tracker
- Income/expense entry with categories, Turkish currency formatting
- Monthly summary cards and category bars
- Offline storage (AsyncStorage), long-press to delete
- Business logic in `src/logic.js` with unit tests (`npm test`), separate from UI

```bash
npm install
npx expo start      # scan the QR code with Expo Go on your phone
```

Good fit for: MVPs, internal tools, form/data-collection apps, booking or appointment apps, educational apps for children. Firebase/Supabase back-ends and Play Store / App Store publishing supported.
