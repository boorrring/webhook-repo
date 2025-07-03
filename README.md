# Webhook Receiver Application

This application receives GitHub webhook events (Push, Pull Request, Merge), stores them in MongoDB, and displays them in a simple UI.

## Project Structure

- `webhook-repo`: Backend Flask application and frontend UI.

## Setup Instructions

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd webhook-repo
```

### 2. Set up Environment Variables

Create a `.env` file in the `webhook-repo` directory with the following content:

```
MONGODB_URI=your_mongodb_connection_string
GITHUB_WEBHOOK_SECRET=your_github_webhook_secret
```

- `MONGODB_URI`: Your MongoDB connection string (e.g., `mongodb://localhost:27017/webhook_events`).
- `GITHUB_WEBHOOK_SECRET`: The secret key you configure in your GitHub webhook settings for security.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python app.py
```

### 5. Configure GitHub Webhook

In your GitHub repository (action-repo):

1. Go to `Settings` -> `Webhooks`.
2. Click `Add webhook`.
3. Set `Payload URL` to your deployed Flask application's webhook endpoint (e.g., `http://your-domain.com/webhook`).
4. Set `Content type` to `application/json`.
5. Enter your `GITHUB_WEBHOOK_SECRET` in the `Secret` field.
6. Select individual events: `Pushes`, `Pull requests`.
7. Click `Add webhook`.

## Event Formats

- **Push**: `{author} pushed to {to_branch} on {timestamp}`
- **Pull Request**: `{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp}`
- **Merge (Bonus)**: `{author} merged branch {from_branch} to {to_branch} on {timestamp}`



