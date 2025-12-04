# Austin Water Home Assistant Integration

This custom integration logs into the [Austin WaterSmart portal](https://austintx.watersmart.com/) to download hourly water usage data and expose it as a Home Assistant sensor. It supports optional 2FA by reading one-time codes from a Namecheap-hosted IMAP mailbox.

## Features
- Logs into the WaterSmart portal with your portal credentials.
- Detects a verification challenge and polls a Namecheap IMAP mailbox for the code.
- Downloads the hourly usage CSV from `https://austintx.watersmart.com/index.php/Download/hourly?combined=0` and parses it into structured data.
- Provides a sensor with the most recent hourly gallon reading and an attribute containing the full history for graphing.

## Installation
### Option 1: Manual copy
1. Copy the `custom_components/austin_water` folder into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. From **Settings → Devices & Services**, click **Add Integration** and search for **Austin Water**.

### Option 2: HACS (recommended)
1. In Home Assistant, open **HACS → Integrations → Custom repositories**.
2. Add this repository URL (e.g., `https://github.com/your-user/austin-water-ha`) with category **Integration**.
3. Install the **Austin WaterSmart** integration from the HACS list and restart Home Assistant when prompted.
4. Proceed to **Settings → Devices & Services → Add Integration** and select **Austin Water**.

## Configuration
The setup flow prompts for:
- **WaterSmart Email/Password**: Your portal credentials.
- **Namecheap IMAP settings (optional)**: Host, port, username, password, and folder that receive verification emails.
- **Subject filter and wait time**: Used to locate the verification email and how long to wait for it.

After adding the integration, an options flow lets you adjust the polling interval (seconds). By default, data refreshes hourly.

## Data Model
The sensor exposes:
- **State**: Gallons from the most recent hourly reading.
- **Attributes**:
  - `last_update`: Timestamp of the latest reading (UTC).
  - `usage`: Array of parsed CSV rows with account number, read date, meter reading, gallons, leak flags, and meter class.

## Notes
- The login and 2FA endpoints are implemented with best-effort guesses based on the public portal structure. If the portal changes, adjust `LOGIN_PATH` and `VERIFY_PATH` in `custom_components/austin_water/const.py`.
- Namecheap IMAP polling marks matched messages as seen to avoid reusing codes.
- All network calls use Home Assistant's shared `aiohttp` session.
