# Podcast Giveaway App

This project contains a minimal Flask application that lets users log in with a
YouTube account via Google OAuth (or a plain username) and view information
about several YouTube channels. It can be
embedded in a larger website by mounting the Flask app behind a reverse proxy
or using Flask's built-in server for development.

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Set the `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET`
   environment variables to enable Google sign-in. If these are not provided,
   the app falls back to a simple username form.

3. (Optional) Set the `YOUTUBE_API_KEY` environment variable to fetch channel
   names from the YouTube Data API. Without an API key the app will still
   display simple channel links.

4. Run the development server:

   ```bash
   python run.py
   ```

The app will be available at `http://localhost:5000`.

## Wallet Connection

On the channel list page you can click **Connect Wallet** to link a crypto
wallet. The page supports popular options including MetaMask, Coinbase Wallet
and WalletConnect using Web3Modal and ethers.js.

## Adding YouTube channels

To change which channels appear in the app, edit the `CHANNEL_IDS` list in
`app/routes.py`:

```python
CHANNEL_IDS = [
    "UCZY97wqlKHsx2qFibsMLLtg",
    "UCAI6Gk0R_1aGa76ShKFA78Q",
    "UCJfeceoPn3MSpdNM3n-DIWg",
]
```

Each item should be a YouTube channel ID. If you have a full channel URL (e.g.
`https://www.youtube.com/channel/UCZY97wqlKHsx2qFibsMLLtg`), copy the part
after `/channel/` and place it in the list. When the `YOUTUBE_API_KEY`
environment variable is set, the app will fetch the channel titles for you.

