# Traffic Stats Backend

A Firebase Cloud Functions backend written in Python.

## Prerequisites

- Python 3.13
- [Firebase CLI](https://firebase.google.com/docs/cli) (`npm install -g firebase-tools`)
- A Firebase project set up at [console.firebase.google.com](https://console.firebase.google.com)

## Setup

### 1. Clone and install dependencies

```bash
cd functions
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file inside the `functions/` folder:

```
FIREBASE_PROJECT_ID=your-project-id
```

### 3. Log in to Firebase

```bash
firebase login
firebase use your-project-id
```

## Running Locally

Start the Firebase emulators:

```bash
firebase emulators:start
```

This will start the Functions and Auth emulators. The terminal output will show the local URLs, typically:

- **Functions:** `http://127.0.0.1:5001/your-project-id/us-central1/api`
- **Auth:** `http://127.0.0.1:9099`
- **Emulator UI:** `http://127.0.0.1:4000`

> **Note:** Make sure `FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099` is set in your environment so the Admin SDK validates tokens against the local emulator instead of production Firebase.

## Running Tests

From the project root:

```bash
pytest functions/test/test_main.py
```
```bash
pytest functions/test/test_https_method_handlers.py
```

## Deploying to Production

```bash
firebase deploy --only functions
```

The production function URL will be printed in the terminal after a successful deploy.