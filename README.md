# Decart Python Starter

Minimal Python starter for running a Decart video transformation job.

## Setup (PowerShell)

### 1) Create a virtual environment

```powershell
python -m venv .venv
```

### 2) Install dependencies into the virtual environment

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3) Configure your Decart API key for the current shell session

```powershell
$env:DECART_API_KEY="{{DECART_API_KEY}}"
```

Use your real key value from the Decart dashboard in place of the placeholder.

## Verification run

Run the example against a public video URL:

```powershell
.\.venv\Scripts\python.exe main.py --video-url "https://samplelib.com/lib/preview/mp4/sample-5s.mp4" --prompt "Transform this video into a watercolor animation style" --output "transformed_video.mp4"
```

Expected behavior:
- You should see status updates (`pending`, `processing`, `completed`)
- The script should print `Saved output to transformed_video.mp4`

## Realtime Lucy for live streaming

Use the realtime launcher to transform your live camera feed and display the output window for streaming software (for example, OBS window capture).

### 1) Install/update dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2) Set your API key in the current session

```powershell
$env:DECART_API_KEY="{{DECART_API_KEY}}"
```

### 3) Discover camera indexes

```powershell
.\.venv\Scripts\python.exe realtime_live.py --list-cameras
```

### 4) Start Lucy realtime

```powershell
.\.venv\Scripts\python.exe realtime_live.py --camera-index 0 --model lucy-latest --prompt "Transform this into a cinematic live-stream style while preserving my face."
```

Optional character reference image:

```powershell
.\.venv\Scripts\python.exe realtime_live.py --camera-index 0 --model lucy-latest --prompt "Substitute the character in the video with the person in the reference image." --image ".\character.jpg"
```

Stop with `q` in the output window (or `Ctrl+C` in the terminal).

### 5) Stream in OBS

1. Add a `Window Capture` source.
2. Select the `Decart Lucy Realtime Output` window.
3. Hide or remove your raw camera source to avoid showing both feeds.

## Repository setup (GitHub)

Create a local commit and push to a new GitHub repository:

```powershell
git add .env.example .gitignore README.md main.py requirements.txt
git commit -m "Initial Decart starter setup" -m "Co-Authored-By: Oz <oz-agent@warp.dev>"
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin master
```

If `origin` already exists, update it:

```powershell
git remote set-url origin <YOUR_GITHUB_REPO_URL>
git push -u origin master
```

## Troubleshooting

- `Missing DECART_API_KEY environment variable`
  - Re-run: `$env:DECART_API_KEY="{{DECART_API_KEY}}"`
- `401 {"detail":"Invalid API key"}`
  - Replace the key with a valid active key from your account
- `404` while fetching input URL
  - Use a direct, publicly accessible media URL
- `422` about copyrighted IP
  - Change to a neutral prompt without restricted IP references
