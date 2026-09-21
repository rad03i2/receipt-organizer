# Security Policy

## Supported version
The latest `main` branch and latest tagged release are supported.

## Data model and privacy
Receipt Organizer is local-first. It does not transmit receipt records, use analytics, or require credentials. The SQLite database is not encrypted. Anyone who can read the database file may be able to read its contents, so use normal operating-system permissions and encrypted storage where appropriate.

Exports may contain financial information. Store and share them carefully. The project intentionally refuses to overwrite an existing export unless `--force` is supplied.

## Reporting a vulnerability
Please report security issues privately to the maintainer through GitHub's private vulnerability reporting feature when available. Do not publish sensitive exploit details in a public issue before a fix is available.

## Scope
Security reports about SQL handling, unsafe file writes, data corruption, dependency/build integrity, or unexpected network behavior are welcome. Feature requests belong in normal issues.

Maintainer: Radwan Abdulhadi Ahmed (@rad03i2)
