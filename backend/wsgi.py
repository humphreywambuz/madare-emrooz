from pathlib import Path

from dotenv import load_dotenv

# Read backend/.env before the app reads its settings. Variables already set in the
# environment win, so a production server can set them there instead.
load_dotenv(Path(__file__).with_name(".env"))

from app import create_app  # noqa: E402

app = create_app()
