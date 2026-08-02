import argparse
from pipeline.coordinator import PipelineCoordinator


def main():
    """
    Entry point for the AI Video Generation Pipeline.
    Parses CLI arguments, initializes the PipelineCoordinator, and runs the pipeline.
    """
    parser = argparse.ArgumentParser(description="AI Video Generation Pipeline")
    parser.add_argument("--script", type=str, required=True, help="Input script file")
    parser.add_argument("--output", type=str, required=True, help="Output MP4 file")
    parser.add_argument("--config", type=str, default="config.yaml", help="Configuration file")

    args = parser.parse_args()

    # Initialize coordinator with config file path
    coordinator = PipelineCoordinator(args.config)

    # Run pipeline
    coordinator.run(args.script, args.output)


if __name__ == "__main__":
    main()
