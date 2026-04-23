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

## Troubleshooting

- `Missing DECART_API_KEY environment variable`
  - Re-run: `$env:DECART_API_KEY="{{DECART_API_KEY}}"`
- `401 {"detail":"Invalid API key"}`
  - Replace the key with a valid active key from your account
- `404` while fetching input URL
  - Use a direct, publicly accessible media URL
- `422` about copyrighted IP
  - Change to a neutral prompt without restricted IP references
