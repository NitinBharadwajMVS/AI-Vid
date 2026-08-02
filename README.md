# AI Video Generation Pipeline

Project overview:
This is an AI Video Generation Pipeline that takes a text script as input and generates an MP4 video as output.

Folder structure:
- pipeline/: Core pipeline coordination.
- planner/: Scene planning and script parsing.
- voice/: Text-to-speech generation.
- assets/: Image and video asset generation.
- alignment/: Audio-visual alignment.
- renderer/: Final video rendering.
- interfaces/: Data models and interfaces.
- utils/: Helper functions.
- config/: Configuration management.
- scripts/: Sample scripts and inputs.
- scene_specs/: Intermediate scene specification files.
- output/: Final generated videos.
- logs/: System logs.
- temp/: Temporary files.
- cache/: Cached assets and intermediate results.

Setup instructions:
1. Create a virtual environment.
2. Run `pip install -r requirements.txt`.
3. Update `config.yaml` as needed.
4. Run the pipeline with: `python run.py --script input.txt --output output.mp4`

Current status:
Project scaffold completed.
