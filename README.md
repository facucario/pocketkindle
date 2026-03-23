# PocketKindle

A lightweight Kindle-friendly web app to read your Instapaper articles.

## Quick start

1. Create an Instapaper API application and obtain:
   - `INSTAPAPER_CONSUMER_KEY`
   - `INSTAPAPER_CONSUMER_SECRET`
2. Set environment variables:

   ```bash
   export INSTAPAPER_CONSUMER_KEY=your_key
   export INSTAPAPER_CONSUMER_SECRET=your_secret
   export POCKETKINDLE_SECRET_KEY=some_random_secret
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:

   ```bash
   python app.py
   ```

5. Open the app in the Kindle browser (or a normal browser for testing) at:

   `http://<your_host>:8000/`

## Notes

- The app uses Instapaper's Full API and xAuth to authenticate.
- All heavy work happens on the server; pages are simple HTML optimized for Kindle.
