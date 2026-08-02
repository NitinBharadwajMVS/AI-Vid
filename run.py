import argparse
from config.loader import load_config
from pipeline.coordinator import PipelineCoordinator

def main():
    """
    Entry point for the AI Video Generation Pipeline.
    Parses CLI arguments, loads configuration, and runs the pipeline.
    """
    parser = argparse.ArgumentParser(description="AI Video Generation Pipeline")
    parser.add_argument("--script", type=str, required=True, help="Input script file")
    parser.add_argument("--output", type=str, required=True, help="Output MP4 file")
    parser.add_argument("--config", type=str, default="config.yaml", help="Configuration file")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize coordinator
    coordinator = PipelineCoordinator(config)
    
    # Run pipeline
    coordinator.run(args.script, args.output)

if __name__ == "__main__":
    main()
