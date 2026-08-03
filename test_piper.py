import traceback
from pipeline.coordinator import PipelineCoordinator
from voice.providers.piper import PiperVoiceProvider


def main():
    try:
        # 1. Load configuration via PipelineCoordinator
        coordinator = PipelineCoordinator("config.yaml")
        config = coordinator.config

        # 2. Instantiate PiperVoiceProvider
        provider = PiperVoiceProvider(config)

        # 3. Execute synthesis test
        text = "Hello! This is the first real test of my AI Video Generation Pipeline."
        output_path = "temp/audio/test.wav"

        print("Starting TTS synthesis test...")
        metadata = provider.synthesize(text, output_path)

        # 4. Print VoiceMetadata and success message
        print("\n--- VoiceMetadata Result ---")
        print(f"Audio File Path: {metadata.audio_file_path}")
        print(f"Audio Duration : {metadata.audio_duration} seconds")
        print(f"Provider       : {metadata.provider}")
        print(f"Voice ID       : {metadata.voice_id}")
        print(f"Speed          : {metadata.speed}")
        print(f"Pitch          : {metadata.pitch}")
        print("----------------------------\n")
        print("SUCCESS: Piper TTS synthesis completed successfully!")

    except Exception as e:
        # 5. Exception handling and full traceback print
        print(f"\nFAILURE: Exception occurred during Piper synthesis test.")
        print(f"Exception Type   : {type(e).__name__}")
        print(f"Exception Message: {e}\n")
        print("--- Full Traceback ---")
        traceback.print_exc()


if __name__ == "__main__":
    main()
