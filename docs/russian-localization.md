# Russian localization test build

This fork carries an initial Russian localization for phone and Wear OS.

## Scope of the first APK

- Russian Android resources under app/src/main/res/values-ru/.
- Russian Wear OS resources under wear/src/main/res/values-ru/.
- ru advertised in both Android locale configs.
- Debug APK keeps the upstream .nativeDebug application id suffix, so it can be installed next to the production Calino app.
- CI validates resource-key and format-placeholder parity before building.
- CI uploads the phone and Wear debug APKs as the calino-ru-debug artifact.

This is a test translation. Wording is expected to be refined from device feedback before an upstream-quality localization is considered complete.

## Known follow-up work

The first APK translates the UI, but it does not yet promise Russian natural-language Quick Add parsing. Russian typed month/date parsing is also a separate behavior change and should be implemented and tested independently from resource translation.
