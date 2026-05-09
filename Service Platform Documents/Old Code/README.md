# BrixaPlatform Core

## Status: FACTORY CLEAN

This directory contains the immutable **Core Infrastructure** for the BrixaWares ecosystem. It is designed to be the starting point for every new application.

## Contents

| App | Purpose | Status |
| :--- | :--- | :--- |
| `core` | Global Config (Preferences, Values) | ✅ Ready |
| `identity` | Users, Roles, Permissions | ✅ Ready |
| `audit` | Sessions, Event Logging | ✅ Ready |
| `lifecycle`| State Machine Framework | ✅ Ready |
| `files` | File Storage Infrastructure | ✅ Ready |
| `app_shell`| UI Navigation & Layout | ✅ Ready |
| `backup` | Database Backup Utility | ✅ Ready |
| `numbering`| Identity Generation Service | ✅ Cleaned (Signals removed) |

## Usage Rules

1.  **Strict Independence**: This Core does NOT know about Clients, Invoices, or Products.
2.  **No Business Logic**: Do not add "Features" to this folder. Add them to your App.
3.  **Migration**: When starting a new project, copy this entire folder first.
4.  **Numbering**: The `numbering` app is a passive service. You must implement the wiring (signals) in your App or Shared layer.

## Setup

1.  Create a virtual environment.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run migrations: `python manage.py migrate`
4.  Create superuser: `python manage.py createsuperuser`
5.  Run server: `python manage.py runserver`
