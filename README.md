# Webhook Receiver Application

This application receives GitHub webhook events (Push, Pull Request, Merge), stores them in MongoDB, and displays them in a simple UI.

## Project Structure

- `webhook-repo`: Backend Flask application and frontend UI.

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/boorrring/webhook-repo.git
cd webhook-repo
```

### 2. Set up Environment Variables

Create a `.env` file in the `webhook-repo` directory with the following content:

```
MONGODB_URI=your_mongodb_connection_string
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

### 5. Setting up Ngrok for Webhook Testing

To test GitHub webhooks locally, you'll need to expose your local server to the internet. Ngrok is a tool that creates a secure tunnel to your localhost.

1. Install Ngrok
   ```bash
   # On Linux/macOS using homebrew
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   ```

2. Start your Flask application
   ```bash
   python app.py
   ```

3. In a new terminal, start Ngrok to expose port 5000
   ```bash
   ngrok http 5000
   ```

4. Copy the HTTPS URL provided by Ngrok (looks like `https://xxxx-xx-xx-xxx-xx.ngrok.io`)

5. Configure GitHub Webhook:
   - Go to your GitHub repository
   - Navigate to Settings > Webhooks > Add webhook
   - Paste your Ngrok URL + "/webhook" (e.g., `https://xxxx-xx-xx-xxx-xx.ngrok.io/webhook`)
   - Set Content type to `application/json`
   - Select events you want to receive (e.g., Push events, Pull requests)
   - Click "Add webhook"

Note: Ngrok URLs change every time you restart Ngrok unless you have a paid account. You'll need to update your webhook URL in GitHub settings whenever the Ngrok URL changes.

## Event Formats

- **Push**: `{author} pushed to {to_branch} on {timestamp}`
- **Pull Request**: `{author} submitted a pull request from {from_branch} to {to_branch} on {timestamp}`
- **Merge**: `{author} merged branch {from_branch} to {to_branch} on {timestamp}`



