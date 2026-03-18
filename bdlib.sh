#!/usr/bin/env bash
# BD Library Manager - Shell wrapper for easy CLI usage
#
# Usage:
#   ./bdlib.sh [options] [input_path]
#
# Options:
#   -i, --input PATH       Input folder (required)
#   -o, --output PATH      Output folder
#   --dejpeg               Enable JPEG artifact removal
#   --dejpeg-model MODEL   DeJPEG model (default: fbcnn_color)
#   -q, --quality N        JXL quality 1-100 (default: 90)
#   -l, --lossless         Use lossless compression
#   -k, --keep-jxl         Keep intermediate JXL files
#   --single               Process single folder
#   --comicvine            Enrich metadata from Comic Vine
#   -t, --threads N         Number of threads
#   -jt, --jxl-threads N   JXL encoding threads
#   -v, --verbose          Verbose output
#   -h, --help             Show this help

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    cat << EOF
${GREEN}BD Library Manager${NC} - Comic archive preparation tool

${YELLOW}Usage:${NC}
    ./bdlib.sh [options] <input_path>

${YELLOW}Options:${NC}
    -o, --output PATH      Output folder
    --dejpeg               Enable JPEG artifact removal
    --dejpeg-model MODEL   DeJPEG model (default: fbcnn_color)
    -q, --quality N        JXL quality 1-100 (default: 90)
    -l, --lossless         Use lossless compression
    -k, --keep-jxl         Keep intermediate JXL files
    --single               Process single folder
    --comicvine            Enrich metadata from Comic Vine
    -t, --threads N        Number of threads
    -jt, --jxl-threads N  JXL encoding threads
    -v, --verbose          Verbose output
    -h, --help             Show this help

${YELLOW}Commands:${NC}
    info                   Show CLI help and available models
    test                   Run tests

${YELLOW}Available DeJPEG Models:${NC}
    fbcnn_color                    Fast JPEG artifact removal
    waifu2x_cunet_art             Classic anime/art
    waifu2x_cunet_photo           Classic photographic
    waifu2x_swin_unet_art         Modern anime/art
    waifu2x_swin_unet_photo       Modern photographic
    waifu2x_swin_unet_art_scan    Scanned art

    Noise levels: :noise0 to :noise3
    Scale: :scale2x (e.g., waifu2x_swin_unet_art:noise2:scale2x)

${YELLOW}Examples:${NC}
    ./bdlib.sh ./comics
    ./bdlib.sh ./comics --dejpeg
    ./bdlib.sh -i ./folder --dejpeg --dejpeg-model waifu2x_swin_unet_art:noise0
    ./bdlib.sh -i ./folder -q 85 --lossless --keep-jxl
    ./bdlib.sh -i ./folder --single
    ./bdlib.sh info
EOF
}

check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}Error: Virtual environment not found at $VENV_DIR${NC}"
        echo "Run: virtualenv .venv && source .venv/bin/activate && uv pip install -r requirements.txt"
        exit 1
    fi
}

run_python() {
    check_venv
    source "$VENV_DIR/bin/activate"
    exec python -m "$@"
}

show_info() {
    run_python bdlib.cli.main --help
}

run_tests() {
    check_venv
    source "$VENV_DIR/bin/activate"
    cd "$SCRIPT_DIR"
    exec python -m pytest tests/ -v
}

# Check for commands first
if [[ "$1" == "info" ]]; then
    show_info
    exit 0
elif [[ "$1" == "test" ]]; then
    run_tests
    exit 0
elif [[ "$1" == "help" || "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

# Build command arguments
# Note: The CLI uses positional 'input' argument, not -i
ARGS=()
INPUT_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output)
            ARGS+=("-o" "$2")
            shift 2
            ;;
        --dejpeg)
            ARGS+=("$1")
            shift
            ;;
        --dejpeg-model)
            ARGS+=("--dejpeg-model" "$2")
            shift 2
            ;;
        -q|--quality)
            ARGS+=("-q" "$2")
            shift 2
            ;;
        -l|--lossless)
            ARGS+=("$1")
            shift
            ;;
        -k|--keep-jxl)
            ARGS+=("$1")
            shift
            ;;
        --single)
            ARGS+=("$1")
            shift
            ;;
        --comicvine)
            ARGS+=("$1")
            shift
            ;;
        -t|--threads)
            ARGS+=("-t" "$2")
            shift 2
            ;;
        -jt|--jxl-threads)
            ARGS+=("-jt" "$2")
            shift 2
            ;;
        -v|--verbose)
            ARGS+=("$1")
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
        *)
            # It's the input path (positional argument)
            if [ -z "$INPUT_PATH" ]; then
                INPUT_PATH="$1"
                # Don't add to ARGS yet - add at end
            fi
            shift
            ;;
    esac
done

# Check for required input
if [ -z "$INPUT_PATH" ]; then
    echo -e "${RED}Error: Input path is required${NC}"
    echo "Run './bdlib.sh help' for usage"
    exit 1
fi

# Run the CLI with input as last positional argument
run_python bdlib.cli.main "${ARGS[@]}" "$INPUT_PATH"
