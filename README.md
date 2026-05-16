# fork-amazon
Yeah, fork 'em

These docker images are designed to download audiobooks (calibre) and automatically parse ebooks downloaded from your Amazon account.  Ideally it would run directly on your media center.

## 🛠️ Automated Setup & Configuration

Before deploying the containers, use the provided initialization script to automatically configure your environment. This ensures correct permissions (PUID/PGID), system timezone, and media mount points.

### 1. Initialize the Environment
Run the initialization script from the project root:
```bash
./init-env.py
```
This script will auto-detect your user credentials and interactively prompt you for your preferred media and config directory locations, creating them if necessary.

### 2. Review and Verify
Before running `docker compose`, it is important to review the generated configuration:
- **Environment**: Open [`.env`](./.env) to verify the paths and IDs.
- **Service Specs**: Review the service definitions in [./calibre/docker-compose.yaml](./calibre/docker-compose.yaml) and [./libation/docker-compose.yaml](./libation/docker-compose.yaml).

### 3. Load Variables (Optional)
To export the `.env` variables into your current terminal session for manual commands:
```bash
source load-env.sh
```

---

## Part 1: Audiobooks (Libation)

Since you are headless, we will use Libation's integrated **web GUI mode** or initialization commands via terminal execution to authenticate.

### 1. Create your Directories

```bash
mkdir -p ~/config
mkdir -p /mnt/data/media/audiobooks

```

### 2. Add to your Docker Compose

Add this block to your main `docker-compose.yml` file:

See ./libation/docker-compose.yaml and ./.env

### 3. Run and Authenticate Headless

1. Start the container: `docker compose up -d libation`
2. Open the container's interactive terminal to log into Audible:
```bash
docker exec -it libation LibationCli add-user
```

3. Follow the terminal prompts. Libation will print out a long Amazon login URL. **Copy that URL, paste it into the web browser on your desktop computer**, and log into your Amazon account.
4. Once logged in, your browser will land on a blank page or a redirect loop. **Copy the new URL from your browser's address bar**, go back to your Ubuntu terminal, paste it into the prompt, and press enter.
5. Libation is now permanently authorized and will silently download and strip DRM from everything in your Audible account, outputting raw `.m4b` files to your media folder.

---

## Part 2: Ebooks (Calibre-Web Automated)

For your Kindle files, Calibre-Web Automated (CWA) needs an ingest folder to watch.

### 1. Create your Directories

```bash
mkdir -p ~/config
mkdir -p /mnt/data/media/library
mkdir -p /mnt/data/downloads
```

### 2. Add to your Docker Compose

Append this service to your stack:

See ./calibre/docker-compose.yaml and ./.env

### 3. Spin up and Configure De-DRM

1. Run `docker compose up -d calibre-web-automated`.
2. Navigate to `http://<your-ubuntu-server-ip>:8213` in your desktop browser.
3. Access the Calibre interface inside the container. You'll need to add the standard **DeDRM** plugin (or NoDRM).
4. In the plugin settings, input your physical **Kindle's Serial Number**. (This is critical: Amazon encrypts files uniquely to your hardware. The serial number acts as the master key to decrypt them).

### 4. Handling the "Automatic Download" Catch

Because Amazon continuously blocks automated scripts from scraping Kindle books directly over the web, the most bulletproof setup for an Ubuntu server involves a slight hybrid approach:

* **Option A (Browser Extension Sync):** Install a browser extension like *Download Kindle Books* on your everyday desktop computer. When you buy a book, you click it to download the `.azw3` via Amazon's "Manage Your Content and Devices" interface. Set your desktop's download path to automatically drop those files directly into your Ubuntu server's `/mnt/storage/media/ebooks/ingest` folder (via an SSHFS mount, Samba share, or Syncthing).
* **Option B (Android Container Scraping):** Advanced users spin up an Android-in-a-container image (`redroid`) on their server, install an old version of Kindle for Android (v4.x), and use a cron script to pull sync'd files out of the virtual Android filesystem straight into the CWA ingest directory.

The moment the file lands in `/cwa-ingest`, the container takes over entirely—un-DRMing it, converting it to clean `.epub`, fetching high-res artwork, and organizing the folder structures without you touching a thing.

You don't actually need the physical Kindle in your hands (or even turned on) to get the serial number, which is a lifesaver if the battery is dead.

The easiest and most accurate way to get it is directly from your Amazon account.

### Method 1: The Amazon Website (Recommended)

Since you need the number exactly as Amazon sees it, pulling it from your account profile prevents any typos.

1. Go to Amazon's website and log into your account.
2. Hover over **Account & Lists** in the top-right corner and select **Content and Devices**.
3. Click on the **Devices** tab near the top of the page.
4. Click on the **Kindle** icon to show all Kindle e-readers registered to your account.
5. Click on your specific old Kindle. A summary box will pop open showing the device details, including a **16-character Serial Number**.
6. Copy this number exactly.

---

### Method 2: On the Physical Kindle

If you have the Kindle charged up and running, you can find it in the settings menu. Depending on how old the device is, the menu layout changes slightly:

* **For Most Kindles (Touchscreen / Paperwhite):** Tap the **Menu** button (three dots or lines in the top right) → **Settings** → **Device Options** → **Device Info**.
* **For Very Old Kindles (With physical keyboards/buttons, e.g., Kindle 3/Keyboard):** Press the **Home** button → Press the **Menu** button → Select **Settings**. The serial number will be printed at the bottom of the screen.
* **First & Second Gen Kindles (Kindle 1, 2, or DX):** Flip the Kindle over. Amazon actually printed the serial number directly on the plastic back casing at the bottom (or underneath the removable back cover on the Kindle 1).

---

### Putting it into Calibre-Web Automated

Once you have that 16-character string (it usually starts with characters like `B00`, `G09`, etc.), navigate to your Calibre interface at `http://<your-server-ip>:8213`.

1. Go to **Preferences** → **Plugins**.
2. Expand the **File Type plugins** section and customize the **DeDRM** (or NoDRM) plugin.
3. Choose **eInk Kindle ebooks** from the configuration configuration configuration menu.
4. Click the **Add (+)** button and paste your serial number here (remove any spaces).

Save it and restart your container. Now, whenever you drop an Amazon book into your ingest folder, the container will use that serial number to automatically unlock it.